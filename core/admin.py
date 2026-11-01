from django.contrib import admin
from .models import UserProfile, Category, FoodItem, Cart, CartItem, Order, OrderItem

admin.site.register(UserProfile)
admin.site.register(Category)
admin.site.register(FoodItem)

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'created_at']
    inlines = [CartItemInline]

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'payment_method', 'payment_status', 'total_price', 'transaction_id', 'get_delivery_address', 'created_at']
    list_filter = ['status', 'payment_method', 'payment_status', 'created_at']
    search_fields = ['id', 'user__username', 'transaction_id']
    inlines = [OrderItemInline]
