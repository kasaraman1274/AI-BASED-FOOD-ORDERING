import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_food.settings')
django.setup()

from core.models import Category, FoodItem

def create_items():
    categories = ['Pizza', 'Burger', 'Pasta', 'Beverages', 'Desserts']
    cat_objs = {}
    for c in categories:
        obj, created = Category.objects.get_or_create(name=c, slug=c.lower())
        cat_objs[c] = obj

    food_items = [
        {"category": "Pizza", "name": "Margherita Pizza", "description": "Classic cheese and tomato pizza.", "price": 12.99, "popularity_score": 90},
        {"category": "Pizza", "name": "Pepperoni Pizza", "description": "Spicy pepperoni layered with mozzarella cheese.", "price": 14.99, "popularity_score": 95},
        {"category": "Burger", "name": "Classic Cheeseburger", "description": "Juicy beef patty with cheese, lettuce, and tomato.", "price": 9.99, "popularity_score": 85},
        {"category": "Burger", "name": "Crispy Chicken Burger", "description": "Crispy chicken breast with mayo and lettuce.", "price": 10.99, "popularity_score": 80},
        {"category": "Pasta", "name": "Spaghetti Carbonara", "description": "Creamy pasta with bacon and parmesan.", "price": 13.99, "popularity_score": 88},
        {"category": "Pasta", "name": "Penne Arrabbiata", "description": "Spicy tomato sauce over penne pasta.", "price": 11.99, "popularity_score": 75},
        {"category": "Beverages", "name": "Cold Cola", "description": "Refreshing chilled cola.", "price": 2.99, "popularity_score": 70},
        {"category": "Beverages", "name": "Fresh Lemonade", "description": "Freshly squeezed lemon juice.", "price": 3.99, "popularity_score": 78},
        {"category": "Desserts", "name": "Chocolate Fudge Brownie", "description": "Fudge brownie served hot.", "price": 5.99, "popularity_score": 92},
        {"category": "Desserts", "name": "New York Cheesecake", "description": "New York style cheesecake slice.", "price": 6.99, "popularity_score": 89},
    ]

    for item in food_items:
        obj, created = FoodItem.objects.get_or_create(
            name=item['name'],
            defaults={
                'category': cat_objs[item['category']],
                'description': item['description'],
                'price': item['price'],
                'popularity_score': item['popularity_score'],
                'is_available': True
            }
        )
        if created:
            print(f"Added menu item: {item['name']}")
        else:
            print(f"Skipped menu item (already exists): {item['name']}")
            
    print("Menu items processed successfully!")

if __name__ == '__main__':
    create_items()
