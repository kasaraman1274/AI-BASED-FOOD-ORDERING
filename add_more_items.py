import os
import django
import urllib.request
from django.core.files.base import ContentFile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_food.settings')
django.setup()

from core.models import Category, FoodItem

def run():
    print("Starting to add more items...")
    new_categories = ['Salads', 'Sides', 'Ice Cream', 'Burgers (Veg)', 'Sushi']
    for c in new_categories:
        Category.objects.get_or_create(name=c, slug=c.lower().replace(' ', '-'))
        
    new_items = [
        {"cat": "Salads", "name": "Caesar Salad", "desc": "Crisp romaine lettuce, parmesan cheese, and croutons topped with caesar dressing.", "price": 250},
        {"cat": "Salads", "name": "Greek Salad", "desc": "Fresh cucumbers, tomatoes, feta cheese, and Kalamata olives.", "price": 220},
        {"cat": "Sides", "name": "Garlic Bread", "desc": "Toasted artisan bread heavily coated with garlic herb butter.", "price": 150},
        {"cat": "Sides", "name": "French Fries", "desc": "Crispy golden french fries served with ketchup and mayo.", "price": 120},
        {"cat": "Ice Cream", "name": "Vanilla Bean Ice Cream", "desc": "Rich and extremely creamy classic vanilla ice cream.", "price": 180},
        {"cat": "Ice Cream", "name": "Chocolate Chip Cookie Dough", "desc": "Chocolate ice cream loaded generously with cookie dough chunks.", "price": 200},
        {"cat": "Burgers (Veg)", "name": "Spicy Paneer Burger", "desc": "Crispy marinated paneer patty with spicy ghost pepper mayo.", "price": 180},
        {"cat": "Burgers (Veg)", "name": "Aloo Tikki Burger", "desc": "Classic Indian street style potato patty burger with mint chutney.", "price": 120},
        {"cat": "Sushi", "name": "California Sushi Roll", "desc": "Delicious crab meat, fresh avocado, and cucumber sushi roll.", "price": 450},
        {"cat": "Sushi", "name": "Spicy Tuna Roll", "desc": "Fresh high-grade tuna with spicy mayo wrapped in premium seaweed.", "price": 480},
    ]
    
    for row in new_items:
        cat = Category.objects.get(name=row['cat'])
        item, created = FoodItem.objects.get_or_create(
            name=row['name'],
            defaults={
                'category': cat,
                'description': row['desc'],
                'price': row['price'],
                'popularity_score': 85
            }
        )
        if created or not item.image:
            keyword = 'food'
            if 'Salad' in item.name: keyword = 'salad'
            elif 'Garlic' in item.name or 'Fries' in item.name: keyword = 'sides,food'
            elif 'Ice Cream' in item.name: keyword = 'icecream,dessert'
            elif 'Burger' in item.name: keyword = 'burger'
            elif 'Sushi' in item.name or 'Roll' in item.name: keyword = 'sushi'
            
            url = f"https://loremflickr.com/600/400/{keyword}"
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                response = urllib.request.urlopen(req)
                image_content = response.read()
                item.image.save(f"{item.name.replace(' ', '_')}.jpg", ContentFile(image_content), save=True)
                print(f"Added item and downloaded image for {item.name}")
            except Exception as e:
                print(f"Error getting image for {item.name}: {e}")
        else:
            print(f"Skipped {item.name} as it already exists.")
            
    print("Done adding items.")

if __name__ == '__main__':
    run()
