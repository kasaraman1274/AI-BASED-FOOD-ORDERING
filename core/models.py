from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    house_number = models.CharField(max_length=100, blank=True, null=True, verbose_name='House / Flat No.')
    village = models.CharField(max_length=100, blank=True, null=True, verbose_name='Village / Locality')
    district = models.CharField(max_length=100, blank=True, null=True, verbose_name='District')
    state = models.CharField(max_length=100, blank=True, null=True, verbose_name='State')
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)

    def get_full_address(self):
        parts = [self.house_number, self.village, self.district, self.state]
        return ', '.join(p for p in parts if p)

    def __str__(self):
        return self.user.username

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

class FoodItem(models.Model):
    category = models.ForeignKey(Category, related_name='food_items', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    image = models.ImageField(upload_to='food_images/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    popularity_score = models.IntegerField(default=0)

    def __str__(self):
        return self.name

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def get_total_price(self):
        return self.quantity * self.food_item.price

class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Preparing', 'Preparing'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),
    )
    PAYMENT_METHOD_CHOICES = (
        ('cod', 'Cash on Delivery'),
        ('upi', 'UPI / QR Code'),
        ('card', 'Credit / Debit Card'),
        ('netbanking', 'Net Banking'),
    )
    PAYMENT_STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cod')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    delivery_house_number = models.CharField(max_length=100, blank=True, default='', verbose_name='House / Flat No.')
    delivery_village = models.CharField(max_length=100, blank=True, default='', verbose_name='Village / Locality')
    delivery_district = models.CharField(max_length=100, blank=True, default='', verbose_name='District')
    delivery_state = models.CharField(max_length=100, blank=True, default='', verbose_name='State')
    created_at = models.DateTimeField(auto_now_add=True)

    def get_delivery_address(self):
        parts = [self.delivery_house_number, self.delivery_village,
                 self.delivery_district, self.delivery_state]
        return ', '.join(p for p in parts if p)

    def get_payment_method_title(self):
        return dict(self.PAYMENT_METHOD_CHOICES).get(self.payment_method, self.payment_method)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username} ({self.get_payment_method_title()})"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.food_item.name} in Order #{self.order.id}"
