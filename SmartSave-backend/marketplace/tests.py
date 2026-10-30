from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Category, Product


class MarketplaceTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.category = Category.objects.create(
            name="Vegetables", slug="vegetables"
        )
        self.farmer = self.User.objects.create_user(
            email="farmer@test.com",
            username="farmer1",
            password="StrongPass123",
            role="farmer",
        )

    def test_product_creation(self):
        product = Product.objects.create(
            name="Tomatoes",
            description="Fresh tomatoes from the hills",
            category=self.category,
            farmer=self.farmer,
            quantity=50,
            price_per_unit=500,
            unit="kg",
            district="Kigali",
        )
        self.assertEqual(product.name, "Tomatoes")
        self.assertEqual(product.category.name, "Vegetables")
        self.assertEqual(product.farmer.email, "farmer@test.com")

    def test_product_str(self):
        product = Product.objects.create(
            name="Avocados",
            description="Creamy avocados",
            category=self.category,
            farmer=self.farmer,
            quantity=80,
            price_per_unit=720,
            unit="kg",
        )
        self.assertEqual(str(product), "Avocados")

    def test_category_str(self):
        self.assertEqual(str(self.category), "Vegetables")

    def test_product_average_rating_default(self):
        product = Product.objects.create(
            name="Bananas",
            description="Sweet bananas",
            category=self.category,
            farmer=self.farmer,
            quantity=100,
            price_per_unit=300,
            unit="kg",
        )
        self.assertEqual(product.average_rating, 0)
        self.assertEqual(product.review_count, 0)