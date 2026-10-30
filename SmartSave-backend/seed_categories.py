"""Seed initial product categories."""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from marketplace.models import Category

categories = [
    ("Vegetables", "vegetables", "Fresh farm vegetables", "🥦", 1),
    ("Fruits", "fruits", "Fresh seasonal fruits", "🍎", 2),
    ("Grains", "grains", "Cereal grains and legumes", "🌾", 3),
    ("Livestock", "livestock", "Live animals and meat", "🐄", 4),
    ("Dairy", "dairy", "Milk, cheese, and dairy products", "🥛", 5),
    ("Poultry", "poultry", "Chicken, eggs, and poultry", "🐔", 6),
    ("Seeds", "seeds", "Agricultural seeds and seedlings", "🌱", 7),
    ("Fertilizers", "fertilizers", "Organic and chemical fertilizers", "🧪", 8),
]

for name, slug, desc, icon, order in categories:
    Category.objects.get_or_create(
        name=name,
        defaults={
            "slug": slug,
            "description": desc,
            "icon": icon,
            "display_order": order,
        },
    )

print(f"✅ Seeded {Category.objects.count()} categories")