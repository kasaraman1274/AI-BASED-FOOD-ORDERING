import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_food.settings')
django.setup()

from core.models import FoodItem
from django.core.files.base import ContentFile
import urllib.request
import glob

def run():
    os.makedirs(os.path.join('media', 'food_images'), exist_ok=True)
    
    base_artifact_dir = r"C:\Users\Abhiram\.gemini\antigravity\brain\02de66bf-8e70-49a5-a60b-e72099ccdfb4"
    margherita_imgs = glob.glob(os.path.join(base_artifact_dir, 'margherita_pizza*.png'))
    pepperoni_imgs = glob.glob(os.path.join(base_artifact_dir, 'pepperoni_pizza*.png'))
    
    items = FoodItem.objects.all()
    
    for item in items:
        keyword = 'food'
        if 'Burger' in item.name.lower(): keyword = 'burger'
        elif 'Pizza' in item.name.lower(): keyword = 'pizza'
        elif 'Pasta' in item.name.lower(): keyword = 'pasta'
        elif 'Cola' in item.name.lower() or 'Lemonade' in item.name.lower(): keyword = 'drink'
        elif 'Brownie' in item.name.lower() or 'Cheesecake' in item.name.lower(): keyword = 'dessert'
        
        url = f"https://loremflickr.com/600/400/{keyword}"
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req)
            image_content = response.read()
            item.image.save(f"{item.name.replace(' ', '_')}.jpg", ContentFile(image_content), save=True)
            print(f"Successfully processed real photo image for {item.name}")
        except Exception as e:
            print(f"Error for {item.name}: {e}")

if __name__ == '__main__':
    run()
