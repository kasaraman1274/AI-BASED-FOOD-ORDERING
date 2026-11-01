import json
import re
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from core.models import FoodItem, Category, Cart, CartItem, Order
from .nlp_engine import predict_intent
from .multilingual import detect_language, t, get_quick_replies, SUPPORTED_LANGUAGES

TRANSLITERATIONS = {
    # Hindi to English food terms
    'पेपरोनी': 'pepperoni', 'मार्गेरीटा': 'margherita', 'पिज़्ज़ा': 'pizza', 'पिज़्ज़ा': 'pizza',
    'बर्गर': 'burger', 'चीज़बर्गर': 'cheeseburger', 'चिकन': 'chicken', 'ब्राउनी': 'brownie',
    'चीज़केक': 'cheesecake', 'पास्ता': 'pasta', 'कोला': 'cola', 'फ्राइज़': 'fries',
    'गार्लिक': 'garlic', 'ब्रेड': 'bread', 'सलाद': 'salad', 'पेने': 'penne',
    # Spanish to English food terms
    'hamburguesa': 'burger', 'hamburguesas': 'burgers', 'queso': 'cheese',
    'patatas': 'fries', 'papas': 'fries', 'ensalada': 'salad', 'tarta': 'cheesecake'
}

def normalize_text_for_dishes(text):
    """Normalize multilingual dish keywords into standard English food tokens."""
    t_lower = text.lower()
    for src, dst in TRANSLITERATIONS.items():
        t_lower = t_lower.replace(src, dst)
    return t_lower

def get_user_cart(request):
    """Retrieve or create a cart for the current authenticated user or guest session."""
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, _ = Cart.objects.get_or_create(session_key=session_key)
        return cart

def get_cart_stats(cart):
    """Return total count of items and total price in cart."""
    count = sum(item.quantity for item in cart.items.all())
    total = float(cart.get_total_price())
    return count, total

def format_food_item_dict(item):
    """Convert FoodItem to JSON-serializable dictionary with image URL."""
    image_url = item.image.url if item.image else ''
    return {
        'id': item.id,
        'name': item.name,
        'category': item.category.name if item.category else '',
        'price': str(item.price),
        'description': item.description,
        'image_url': image_url,
    }

def match_best_food_item(text):
    """Intelligently match a food item from the database using whole-word overlap and transliteration."""
    text_norm = normalize_text_for_dishes(text)
    tokens = set(re.findall(r'[a-z]+', text_norm))
    all_items = list(FoodItem.objects.filter(is_available=True).select_related('category'))

    # 1. Exact full name match
    for item in all_items:
        if item.name.lower() in text_norm:
            return item

    # 2. Maximum whole-word overlap
    best_item = None
    best_score = 0
    for item in all_items:
        item_words = set(re.findall(r'[a-z]+', item.name.lower()))
        item_words = {w for w in item_words if len(w) > 2 and w not in {'with', 'and', 'the'}}
        overlap = tokens.intersection(item_words)
        if len(overlap) > best_score:
            best_score = len(overlap)
            best_item = item

    if best_score >= 1:
        return best_item
    return None

@csrf_exempt
def chat_api(request):
    """
    Multilingual conversational AI API endpoint.
    Handles dynamic DB queries for food items, recommendations, order tracking, and cart management
    in English, Hindi, and Spanish.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    try:
        try:
            body_str = request.body.decode('utf-8')
        except UnicodeDecodeError:
            body_str = request.body.decode('latin-1')
        data = json.loads(body_str)
    except Exception:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)

    user_message = data.get('message', '').strip()
    client_lang = data.get('lang')  # Optional explicit language from client ('en', 'hi', 'es')

    if not user_message:
        return JsonResponse({'error': 'Message not provided'}, status=400)

    cart = get_user_cart(request)
    pred = predict_intent(user_message, preferred_lang=client_lang)
    tag = pred['tag']
    entities = pred.get('entities', {})
    quantity = entities.get('quantity', 1)
    detected_lang = pred.get('detected_lang', client_lang or 'en')

    action = pred.get('action')
    items_payload = []

    matched_item = match_best_food_item(user_message)

    # Detect addition keywords across English, Hindi, and Spanish
    add_words = ['add', 'order', 'buy', 'get me', 'जोड़ो', 'डालो', 'दीजिए', 'चाहिए', 'añadir', 'agregar', 'pedir', 'poner']
    is_add_request = (tag == 'add_to_cart') or (matched_item and any(w in user_message.lower() for w in add_words))

    # Detect price keywords across languages
    price_words = ['how much', 'what is the price', "what's the price", 'price of', 'cost of', 'rate of', 'कितने', 'कीमत', 'दाम', 'cuánto', 'cuanto', 'precio', 'costo']
    is_price_request = (tag == 'price_query') or any(w in user_message.lower() for w in price_words)

    # 1. ADD TO CART INTENT
    if is_add_request:
        if matched_item:
            cart_item, created = CartItem.objects.get_or_create(cart=cart, food_item=matched_item)
            if not created:
                cart_item.quantity += quantity
            else:
                cart_item.quantity = quantity
            cart_item.save()

            matched_item.popularity_score += quantity
            matched_item.save(update_fields=['popularity_score'])

            count, total = get_cart_stats(cart)
            item_total = f"{(float(matched_item.price) * quantity):.2f}"
            response_text = t('ADDED_TO_CART', detected_lang, quantity=quantity, item_name=matched_item.name, item_total=item_total)
            action = "ITEM_ADDED"
            items_payload = [format_food_item_dict(matched_item)]
            quick_replies = get_quick_replies('cart', detected_lang)
        else:
            response_text = t('ITEM_NOT_FOUND_SUGGEST', detected_lang)
            top_dishes = FoodItem.objects.filter(is_available=True).order_by('-popularity_score')[:3]
            items_payload = [format_food_item_dict(i) for i in top_dishes]
            quick_replies = get_quick_replies('food', detected_lang)

    # 2. PRICE QUERY
    elif is_price_request:
        if matched_item:
            response_text = t('PRICE_RESPONSE', detected_lang, item_name=matched_item.name, price=matched_item.price, description=matched_item.description)
            items_payload = [format_food_item_dict(matched_item)]
            quick_replies = [f"+ {matched_item.name}"] + get_quick_replies('food', detected_lang)[:2]
        else:
            price_limit = entities.get('price_limit')
            if price_limit:
                budget_items = FoodItem.objects.filter(is_available=True, price__lte=price_limit).order_by('price')[:4]
                if budget_items.exists():
                    response_text = t('BUDGET_FOUND', detected_lang, price_limit=int(price_limit))
                    items_payload = [format_food_item_dict(i) for i in budget_items]
                    quick_replies = get_quick_replies('food', detected_lang)
                else:
                    response_text = t('BUDGET_NONE', detected_lang, price_limit=int(price_limit))
                    quick_replies = get_quick_replies('default', detected_lang)
            else:
                response_text = pred['response']
                quick_replies = get_quick_replies('default', detected_lang)

    # 3. ORDER STATUS TRACKING
    elif tag == 'order_status':
        if request.user.is_authenticated:
            last_order = Order.objects.filter(user=request.user).order_by('-created_at').first()
            if last_order:
                order_items = last_order.items.select_related('food_item')
                items_str = ", ".join([f"{it.quantity}x {it.food_item.name}" for it in order_items[:4]])
                
                status_key = f"STATUS_{last_order.status.replace(' ', '_')}"
                status_desc = t(status_key, detected_lang)
                address_str = last_order.get_delivery_address() or ("Address on file" if detected_lang == 'en' else ("दर्ज पता" if detected_lang == 'hi' else "Dirección registrada"))

                response_text = t(
                    'ORDER_STATUS_TEMPLATE', detected_lang,
                    order_id=last_order.id,
                    status_desc=status_desc,
                    items_str=items_str,
                    total_price=last_order.total_price,
                    address=address_str,
                    date=last_order.created_at.strftime('%b %d, %Y %I:%M %p')
                )
                action = "SHOW_ORDER_STATUS"
                quick_replies = get_quick_replies('order', detected_lang)
            else:
                response_text = t('ORDER_STATUS_NONE', detected_lang)
                quick_replies = get_quick_replies('default', detected_lang)
        else:
            response_text = t('ORDER_STATUS_LOGIN_REQUIRED', detected_lang)
            action = "LOGIN_REDIRECT"
            quick_replies = get_quick_replies('auth', detected_lang)

    # 4. CART STATUS
    elif tag == 'cart':
        cart_items = cart.items.select_related('food_item')
        if cart_items.exists():
            items_list = "\n".join([f"• **{it.food_item.name}** x{it.quantity} — ₹{it.get_total_price():.2f}" for it in cart_items])
            count, total = get_cart_stats(cart)
            response_text = t('CART_SUMMARY', detected_lang, count=count, items_list=items_list, total=f"{total:.2f}")
            action = "SHOW_CART"
            quick_replies = get_quick_replies('cart', detected_lang)
        else:
            response_text = t('CART_EMPTY', detected_lang)
            top_dishes = FoodItem.objects.filter(is_available=True).order_by('-popularity_score')[:3]
            items_payload = [format_food_item_dict(i) for i in top_dishes]
            quick_replies = get_quick_replies('default', detected_lang)

    # 5. CLEAR CART
    elif tag == 'clear_cart':
        cart.items.all().delete()
        response_text = t('CART_CLEARED', detected_lang)
        action = "CART_CLEARED"
        quick_replies = get_quick_replies('default', detected_lang)

    # 6. RECOMMENDATIONS
    elif tag == 'recommendation':
        top_dishes = FoodItem.objects.filter(is_available=True).order_by('-popularity_score')[:3]
        items_payload = [format_food_item_dict(i) for i in top_dishes]
        response_text = t('RECOMMEND_HEADER', detected_lang)
        quick_replies = get_quick_replies('default', detected_lang)

    # 7. PIZZA CATEGORY
    elif tag == 'pizza':
        pizza_items = FoodItem.objects.filter(is_available=True, category__name__icontains='pizza')[:4]
        if pizza_items.exists():
            response_text = t('PIZZA_HEADER', detected_lang)
            items_payload = [format_food_item_dict(i) for i in pizza_items]
            quick_replies = get_quick_replies('food', detected_lang)

    # 8. BURGER CATEGORY
    elif tag == 'burger':
        burger_items = FoodItem.objects.filter(is_available=True, category__name__icontains='burger')[:4]
        if burger_items.exists():
            response_text = t('BURGER_HEADER', detected_lang)
            items_payload = [format_food_item_dict(i) for i in burger_items]
            quick_replies = get_quick_replies('food', detected_lang)

    # 9. DESSERT CATEGORY
    elif tag == 'dessert':
        dessert_items = FoodItem.objects.filter(is_available=True, category__name__in=['Desserts', 'Ice Cream'])[:4]
        if dessert_items.exists():
            response_text = t('DESSERT_HEADER', detected_lang)
            items_payload = [format_food_item_dict(i) for i in dessert_items]
            quick_replies = get_quick_replies('food', detected_lang)

    # 10. VEG QUERY
    elif tag == 'veg_query':
        veg_items = FoodItem.objects.filter(
            is_available=True,
            category__name__in=['Salads', 'Burgers (Veg)', 'Sides', 'Desserts', 'Ice Cream']
        ) | FoodItem.objects.filter(is_available=True, name__icontains='Margherita')
        veg_items = veg_items.distinct()[:4]
        if veg_items.exists():
            response_text = t('VEG_HEADER', detected_lang)
            items_payload = [format_food_item_dict(i) for i in veg_items]
            quick_replies = get_quick_replies('food', detected_lang)

    # 11. NON-VEG QUERY
    elif tag == 'nonveg_query':
        nonveg_items = FoodItem.objects.filter(
            is_available=True,
            name__iregex=r'(chicken|pepperoni|carbonara|tuna|sushi)'
        )[:4]
        if nonveg_items.exists():
            response_text = t('NONVEG_HEADER', detected_lang)
            items_payload = [format_food_item_dict(i) for i in nonveg_items]
            quick_replies = get_quick_replies('food', detected_lang)

    # 12. GENERAL OR DISH SEARCH
    elif tag == 'search_food' and matched_item:
        response_text = t('SEARCH_FOUND', detected_lang, item_name=matched_item.name)
        items_payload = [format_food_item_dict(matched_item)]
        quick_replies = [f"+ {matched_item.name}"] + get_quick_replies('food', detected_lang)[:2]

    else:
        response_text = pred['response']
        quick_replies = get_quick_replies('default', detected_lang)

    cart_count, cart_total = get_cart_stats(cart)
    btn_add_text = SUPPORTED_LANGUAGES.get(detected_lang, {}).get('btn_add', '+ Add')

    return JsonResponse({
        'response': response_text,
        'action': action,
        'quick_replies': quick_replies,
        'items': items_payload,
        'cart_count': cart_count,
        'cart_total': cart_total,
        'lang': detected_lang,
        'btn_add_text': btn_add_text
    })

@csrf_exempt
def add_to_cart_api(request):
    """
    Direct endpoint to add an item to the cart via AJAX from chat cards.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        item_id = int(data.get('item_id', 0))
        quantity = int(data.get('quantity', 1))
        client_lang = data.get('lang', 'en')
    except Exception:
        return JsonResponse({'error': 'Invalid request parameters'}, status=400)

    try:
        food_item = FoodItem.objects.get(id=item_id, is_available=True)
    except FoodItem.DoesNotExist:
        return JsonResponse({'error': 'Food item not found'}, status=404)

    cart = get_user_cart(request)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, food_item=food_item)
    if not created:
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
    cart_item.save()

    food_item.popularity_score += quantity
    food_item.save(update_fields=['popularity_score'])

    cart_count, cart_total = get_cart_stats(cart)
    msg = t('ADDED_TO_CART', client_lang, quantity=quantity, item_name=food_item.name, item_total=f"{(float(food_item.price)*quantity):.2f}")

    return JsonResponse({
        'success': True,
        'message': msg,
        'item_name': food_item.name,
        'cart_count': cart_count,
        'cart_total': cart_total,
        'lang': client_lang
    })
