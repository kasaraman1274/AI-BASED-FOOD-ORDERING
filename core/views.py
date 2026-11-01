from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm, UserProfileForm
from .models import UserProfile, Category, FoodItem, Cart, CartItem, Order, OrderItem

import uuid
import random
import time
import re
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from django.http import JsonResponse

def mask_identifier(identifier, is_email=True):
    """Mask email or phone number for safe display."""
    if is_email and '@' in identifier:
        user_part, domain = identifier.split('@', 1)
        if len(user_part) <= 2:
            masked_user = user_part[0] + '*'
        else:
            masked_user = user_part[0] + '*' * (len(user_part) - 2) + user_part[-1]
        return f"{masked_user}@{domain}"
    else:
        digits = re.sub(r'\D', '', identifier)
        if len(digits) >= 10:
            return f"+91 {digits[:2]}******{digits[-2:]}"
        elif len(digits) > 4:
            return f"{digits[:2]}***{digits[-2:]}"
        return identifier

def find_or_create_otp_user(identifier):
    """Find existing user by email, phone, or username; or create a new user."""
    identifier = identifier.strip()
    is_email = '@' in identifier and '.' in identifier
    
    if is_email:
        email = identifier.lower()
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            user = User.objects.filter(username__iexact=email).first()
        if not user:
            base_username = re.sub(r'[^a-zA-Z0-9_]', '', email.split('@')[0]) or 'user'
            username = base_username
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{random.randint(1000, 9999)}"
            user = User.objects.create_user(username=username, email=email)
            UserProfile.objects.get_or_create(user=user)
        return user, True, email
    else:
        phone_digits = re.sub(r'\D', '', identifier)
        phone_10 = phone_digits[-10:] if len(phone_digits) >= 10 else phone_digits
        
        profile = UserProfile.objects.filter(phone_number__icontains=phone_10).first() if phone_10 else None
        if profile:
            user = profile.user
        else:
            user = User.objects.filter(username=phone_10).first() if phone_10 else None
            if not user and phone_10:
                user = User.objects.filter(username=f"user_{phone_10}").first()
                
        if not user:
            username = f"user_{phone_10}" if phone_10 else f"user_{random.randint(10000, 99999)}"
            while User.objects.filter(username=username).exists():
                username = f"{username}_{random.randint(100, 999)}"
            user = User.objects.create_user(username=username)
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.phone_number = phone_10
            profile.save()
            
        return user, False, phone_10

def home(request):
    featured_items = FoodItem.objects.filter(is_available=True).order_by('-popularity_score')[:4]
    return render(request, 'core/home.html', {'featured_items': featured_items})

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            UserProfile.objects.create(user=user)
            messages.success(request, 'Registration successful. You can now login.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'core/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.GET.get('reset') == '1':
        request.session.pop('otp_auth', None)
        return redirect('login')

    otp_auth = request.session.get('otp_auth')
    if otp_auth and time.time() > otp_auth.get('expires_at', 0):
        request.session.pop('otp_auth', None)
        otp_auth = None

    otp_step = 'verify' if otp_auth else 'send'
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('accept', '')

    if request.method == 'POST':
        action = request.POST.get('action', '')

        # 1. SEND OTP
        if action == 'send_otp':
            identifier = request.POST.get('identifier', '').strip()
            if not identifier:
                messages.error(request, "Please enter your email address or mobile number.")
                if is_ajax:
                    return JsonResponse({'success': False, 'message': 'Please enter email or phone number.'})
                return render(request, 'core/login.html', {'otp_step': 'send', 'form': AuthenticationForm()})

            user, is_email, clean_id = find_or_create_otp_user(identifier)
            otp = f"{random.randint(100000, 999999)}"
            masked = mask_identifier(clean_id, is_email)
            channel = 'Email' if is_email else 'SMS'

            request.session['otp_auth'] = {
                'otp': otp,
                'user_id': user.id,
                'identifier': clean_id,
                'is_email': is_email,
                'masked': masked,
                'channel': channel,
                'created_at': time.time(),
                'expires_at': time.time() + 600,
            }

            if is_email:
                try:
                    send_mail(
                        subject='Your AI Foodie Login OTP',
                        message=f"Hello {user.first_name or user.username},\n\nYour one-time login OTP is: {otp}\n\nThis OTP is valid for 10 minutes. Do not share it with anyone.\n\nHappy Ordering!\nTeam AI Foodie",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email or clean_id],
                        fail_silently=True,
                    )
                except Exception:
                    pass

            messages.info(request, f"🔑 Verification OTP: {otp} (sent via {channel} to {masked})")
            if is_ajax:
                return JsonResponse({'success': True, 'step': 'verify', 'masked': masked, 'channel': channel, 'otp_demo': otp})
            return redirect('login')

        # 2. VERIFY OTP
        elif action == 'verify_otp':
            entered_otp = request.POST.get('otp', '').strip().replace(' ', '')
            if not otp_auth:
                messages.error(request, "OTP session expired or not found. Please request a new code.")
                if is_ajax:
                    return JsonResponse({'success': False, 'message': 'Session expired. Please request OTP again.'})
                return redirect('login')

            if time.time() > otp_auth.get('expires_at', 0):
                messages.error(request, "OTP has expired. Please request a new code.")
                request.session.pop('otp_auth', None)
                if is_ajax:
                    return JsonResponse({'success': False, 'message': 'OTP has expired.'})
                return redirect('login')

            if entered_otp != otp_auth.get('otp'):
                messages.error(request, "Incorrect OTP code. Please enter the valid 6-digit code.")
                if is_ajax:
                    return JsonResponse({'success': False, 'message': 'Incorrect OTP code.'})
                return render(request, 'core/login.html', {
                    'otp_step': 'verify',
                    'otp_auth': otp_auth,
                    'form': AuthenticationForm(),
                    'next': request.POST.get('next', '')
                })

            # Correct OTP
            user = User.objects.get(id=otp_auth['user_id'])
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            request.session.pop('otp_auth', None)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.POST.get('next') or request.GET.get('next') or 'home'
            if is_ajax:
                return JsonResponse({'success': True, 'redirect_url': next_url})
            return redirect(next_url)

        # 3. RESEND OTP
        elif action == 'resend_otp':
            if otp_auth:
                new_otp = f"{random.randint(100000, 999999)}"
                otp_auth['otp'] = new_otp
                otp_auth['created_at'] = time.time()
                otp_auth['expires_at'] = time.time() + 600
                request.session['otp_auth'] = otp_auth
                if otp_auth.get('is_email'):
                    try:
                        send_mail(
                            subject='Your New AI Foodie Login OTP',
                            message=f"Your new one-time login OTP is: {new_otp}\n\nValid for 10 minutes.",
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[otp_auth.get('identifier')],
                            fail_silently=True,
                        )
                    except Exception:
                        pass
                messages.info(request, f"🔑 New OTP sent: {new_otp}")
                if is_ajax:
                    return JsonResponse({'success': True, 'otp_demo': new_otp})
            return redirect('login')

        # 4. PASSWORD LOGIN FALLBACK
        elif action == 'password_login' or 'username' in request.POST:
            form = AuthenticationForm(request, data=request.POST)
            if form.is_valid():
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password')
                user = authenticate(username=username, password=password)
                if user is not None:
                    login(request, user)
                    messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                    next_url = request.POST.get('next') or request.GET.get('next') or 'home'
                    return redirect(next_url)
            messages.error(request, "Invalid username or password.")
            return render(request, 'core/login.html', {
                'otp_step': otp_step,
                'otp_auth': otp_auth,
                'form': form,
                'active_tab': 'password'
            })

    form = AuthenticationForm()
    return render(request, 'core/login.html', {
        'otp_step': otp_step,
        'otp_auth': otp_auth,
        'form': form,
        'next': request.GET.get('next', ''),
        'active_tab': request.GET.get('tab', 'otp')
    })

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def profile_view(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)
        
    return render(request, 'core/profile.html', {'form': form, 'orders': orders})

def menu(request):
    category_slug = request.GET.get('category')
    search_query = request.GET.get('q')
    
    items = FoodItem.objects.filter(is_available=True)
    if category_slug:
        items = items.filter(category__slug=category_slug)
    if search_query:
        items = items.filter(name__icontains=search_query)
        
    categories = Category.objects.all()
    return render(request, 'core/menu.html', {'items': items, 'categories': categories})

def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        return cart
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
        return cart

def cart_view(request):
    cart = get_or_create_cart(request)
    return render(request, 'core/cart.html', {'cart': cart})

def add_to_cart(request, item_id):
    cart = get_or_create_cart(request)
    food_item = get_object_or_404(FoodItem, id=item_id)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, food_item=food_item)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    messages.success(request, f"{food_item.name} added to your cart.")
    return redirect('menu')

@login_required
def checkout(request):
    cart = get_or_create_cart(request)
    if cart.items.count() == 0:
        messages.warning(request, "Your cart is empty.")
        return redirect('menu')

    if request.method == 'POST':
        profile = request.user.userprofile
        house_number = request.POST.get('house_number') or profile.house_number or ''
        village      = request.POST.get('village')      or profile.village      or ''
        district     = request.POST.get('district')     or profile.district     or ''
        state        = request.POST.get('state')        or profile.state        or ''

        payment_method = request.POST.get('payment_method', 'cod').lower().strip()
        if payment_method not in ['cod', 'upi', 'card', 'netbanking']:
            payment_method = 'cod'

        transaction_id = None
        payment_status = 'Pending'

        if payment_method == 'cod':
            payment_status = 'Pending'
            transaction_id = f"COD-{uuid.uuid4().hex[:8].upper()}"
        elif payment_method == 'upi':
            upi_id = request.POST.get('upi_id', '').strip()
            payment_status = 'Completed'
            transaction_id = f"UPI-{uuid.uuid4().hex[:10].upper()}"
        elif payment_method == 'card':
            card_number = request.POST.get('card_number', '').replace(' ', '').strip()
            last4 = card_number[-4:] if len(card_number) >= 4 else '1234'
            payment_status = 'Completed'
            transaction_id = f"CARD-{uuid.uuid4().hex[:8].upper()}-*{last4}"
        elif payment_method == 'netbanking':
            bank_name = request.POST.get('bank_name', 'BANK').strip()
            prefix = ''.join(c for c in bank_name if c.isalnum())[:4].upper() or 'NB'
            payment_status = 'Completed'
            transaction_id = f"NB-{prefix}-{uuid.uuid4().hex[:8].upper()}"

        order = Order.objects.create(
            user=request.user,
            total_price=cart.get_total_price(),
            payment_method=payment_method,
            payment_status=payment_status,
            transaction_id=transaction_id,
            delivery_house_number=house_number,
            delivery_village=village,
            delivery_district=district,
            delivery_state=state,
        )

        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                food_item=item.food_item,
                quantity=item.quantity,
                price=item.food_item.price
            )
            item.food_item.popularity_score += item.quantity
            item.food_item.save()

        cart.items.all().delete()
        messages.success(request, f"Order #{order.id} placed successfully!")
        return redirect('order_confirmation', order_id=order.id)

    return render(request, 'core/checkout.html', {'cart': cart})

@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'core/order_confirmation.html', {'order': order})

def update_cart_item(request, item_id, action):
    """Increase or decrease quantity of a cart item."""
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    if action == 'increase':
        cart_item.quantity += 1
        cart_item.save()
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    return redirect('cart')

def remove_from_cart(request, item_id):
    """Remove a specific item from the cart."""
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    cart_item.delete()
    messages.success(request, f"{cart_item.food_item.name} removed from cart.")
    return redirect('cart')
