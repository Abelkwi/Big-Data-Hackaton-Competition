from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import BuyerProfile, FarmerProfile, Profile
from marketplace.models import Category, Product
from orders.models import Order, OrderItem


class AccountRegistrationTests(TestCase):
    def test_register_creates_user_and_profile(self):
        response = self.client.post(
            reverse('accounts:register'),
            {
                'username': 'farmer1',
                'email': 'farmer1@example.com',
                'password1': 'StrongPass123',
                'password2': 'StrongPass123',
                'role': 'farmer',
            },
        )

        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(username='farmer1')
        self.assertEqual(user.role, 'farmer')

    def test_register_accepts_public_form_without_username_field(self):
        response = self.client.post(
            reverse('accounts:register'),
            {
                'email': 'public@example.com',
                'password1': 'StrongPass123',
                'password2': 'StrongPass123',
                'role': 'buyer',
            },
        )

        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(email='public@example.com')
        self.assertEqual(user.role, 'buyer')

    def test_login_works_with_email_address(self):
        get_user_model().objects.create_user(
            username='tester',
            email='tester@example.com',
            password='StrongPass123',
        )

        response = self.client.post(
            reverse('accounts:login'),
            {'username': 'tester@example.com', 'password': 'StrongPass123'},
        )

        self.assertEqual(response.status_code, 302)


@override_settings(GOOGLE_OAUTH_CLIENT_ID="test-client-id")
class GoogleLoginTests(TestCase):
    endpoint = "/api/auth/google/"
    verified_claims = {
        "sub": "google-user-123",
        "email": "google-user@example.com",
        "email_verified": True,
        "given_name": "Google",
        "family_name": "User",
    }

    @patch("accounts.api_views.verify_google_id_token", return_value=verified_claims)
    def test_google_login_creates_buyer_and_returns_jwts(self, verify_token):
        response = self.client.post(
            self.endpoint,
            {"credential": "valid-google-token"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        user = get_user_model().objects.get(email="google-user@example.com")
        self.assertEqual(user.role, "buyer")
        self.assertTrue(user.is_verified)
        self.assertEqual(user.first_name, "Google")
        self.assertTrue(Profile.objects.filter(user=user).exists())
        self.assertTrue(BuyerProfile.objects.filter(profile=user.profile).exists())
        self.assertTrue(response.json()["access"])
        self.assertTrue(response.json()["refresh"])
        verify_token.assert_called_once_with("valid-google-token", "test-client-id")

    @patch("accounts.api_views.verify_google_id_token", return_value=verified_claims)
    def test_google_login_preserves_existing_account_role(self, verify_token):
        user = get_user_model().objects.create_user(
            username="existing-farmer",
            email="google-user@example.com",
            password="StrongPass123",
            role="farmer",
        )
        FarmerProfile.objects.create(profile=user.profile)

        response = self.client.post(
            self.endpoint,
            {"credential": "valid-google-token"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.role, "farmer")
        self.assertEqual(
            get_user_model().objects.filter(email="google-user@example.com").count(),
            1,
        )

    @patch(
        "accounts.api_views.verify_google_id_token",
        return_value={**verified_claims, "email_verified": False},
    )
    def test_google_login_rejects_unverified_email(self, verify_token):
        response = self.client.post(
            self.endpoint,
            {"credential": "unverified-google-token"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)
        self.assertFalse(
            get_user_model().objects.filter(email="google-user@example.com").exists()
        )

    def test_google_login_rejects_malformed_token(self):
        response = self.client.post(
            self.endpoint,
            {"credential": "not-a-jwt"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)

    @override_settings(GOOGLE_OAUTH_CLIENT_ID="")
    def test_google_login_reports_missing_server_configuration(self):
        response = self.client.post(
            self.endpoint,
            {"credential": "valid-google-token"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 503)

    @patch("accounts.api_views.verify_google_id_token", return_value=verified_claims)
    def test_google_verify_returns_verified_email(self, verify_token):
        response = self.client.post(
            "/api/auth/google/verify/",
            {"credential": "valid-google-token"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "email": "google-user@example.com",
            "email_verified": True,
        })

    @patch("accounts.api_views.verify_google_id_token", return_value=verified_claims)
    def test_farmer_registration_requires_matching_verified_google_email(self, verify_token):
        response = self.client.post(
            "/api/auth/register/farmer/",
            {
                "email": "google-user@example.com",
                "username": "google-user",
                "password": "StrongPass123",
                "password2": "StrongPass123",
                "google_credential": "valid-google-token",
                "province": "Eastern Province",
                "district": "Bugesera",
                "sector": "Gashora",
                "cell": "Biryogo",
                "village": "Kagarama",
                "farm_name": "Test Farm",
                "farm_size": "2 hectares",
                "main_crop": "Maize",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        user = get_user_model().objects.get(email="google-user@example.com")
        self.assertTrue(user.is_verified)
        self.assertEqual(user.profile.cell, "Biryogo")
        self.assertEqual(user.profile.village, "Kagarama")
        self.assertEqual(user.profile.farmer_profile.main_crop, "Maize")


class RegistrationProfileTests(TestCase):
    def test_buyer_registration_saves_profile_and_company_details(self):
        response = self.client.post(
            "/api/auth/register/buyer/",
            {
                "email": "buyer@example.com",
                "username": "buyer",
                "password": "StrongPass123",
                "password2": "StrongPass123",
                "company_name": "Kigali Hotel",
                "buyer_type": "business",
                "province": "Kigali City",
                "district": "Gasabo",
                "sector": "Bumbogo",
                "cell": "Kinyaga",
                "village": "Village 1",
                "supply_needs": "Vegetables",
                "monthly_volume": "100-500 kg/month",
                "delivery_frequency": "Weekly",
                "buyer_registration_number": "RDB-123",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        profile = Profile.objects.get(user__email="buyer@example.com")
        self.assertEqual(profile.cell, "Kinyaga")
        self.assertEqual(profile.buyer_profile.company_name, "Kigali Hotel")
        self.assertEqual(profile.buyer_profile.supply_needs, "Vegetables")
        self.assertEqual(profile.buyer_profile.registration_number, "RDB-123")

    def test_ngo_registration_saves_application_details(self):
        response = self.client.post(
            "/api/auth/register/ngo/",
            {
                "email": "ngo@example.com",
                "username": "ngo",
                "password": "StrongPass123",
                "password2": "StrongPass123",
                "organization_name": "Hope Rwanda",
                "organization_type": "NGO",
                "beneficiaries_served": "100-500 beneficiaries",
                "mission": "Community food support",
                "focus_areas": "School feeding",
                "collection_capacity": "Up to 50 kg",
                "has_transport": "No",
                "food_types": "Fresh produce",
                "ngo_registration_number": "RCA-123",
                "website": "https://example.org",
                "province": "Southern Province",
                "district": "Huye",
                "sector": "Ngoma",
                "cell": "Butare",
                "village": "Village 1",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        profile = Profile.objects.get(user__email="ngo@example.com")
        self.assertEqual(profile.cell, "Butare")
        self.assertEqual(profile.ngo_profile.organization_name, "Hope Rwanda")
        self.assertEqual(profile.ngo_profile.focus_areas, "School feeding")


class BuyerDashboardTests(TestCase):
    def test_dashboard_returns_empty_user_scoped_metrics(self):
        buyer = get_user_model().objects.create_user(
            username="dashboard-buyer",
            email="dashboard-buyer@example.com",
            password="StrongPass123",
            role="buyer",
        )
        Order.objects.create(buyer=buyer, delivery_address="Kigali")
        client = APIClient()
        client.force_authenticate(user=buyer)

        response = client.get("/api/dashboard/buyer/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_orders"], 1)
        self.assertEqual(response.data["pending_orders"], 1)
        self.assertEqual(response.data["recent_orders"][0]["delivery_address"], "Kigali")
        self.assertEqual(len(response.data["monthly_spend"]), 6)

    def test_dashboard_aggregates_real_delivered_orders(self):
        buyer = get_user_model().objects.create_user(
            username="dashboard-buyer-with-orders",
            email="dashboard-buyer-with-orders@example.com",
            password="StrongPass123",
            role="buyer",
        )
        farmer = get_user_model().objects.create_user(
            username="dashboard-farmer",
            email="dashboard-farmer@example.com",
            password="StrongPass123",
            first_name="Test",
            last_name="Farmer",
            role="farmer",
        )
        FarmerProfile.objects.create(profile=farmer.profile, store_name="Green Farm")
        category = Category.objects.create(name="Vegetables")
        product = Product.objects.create(
            farmer=farmer,
            category=category,
            name="Tomatoes",
            description="Fresh tomatoes",
            quantity=100,
            price_per_unit=2500,
        )
        order = Order.objects.create(
            buyer=buyer,
            status="delivered",
            subtotal=5000,
            delivery_address="Kigali",
        )
        OrderItem.objects.create(
            order=order,
            product=product,
            farmer=farmer,
            product_name="Tomatoes",
            quantity=2,
            unit_price=2500,
            total_price=5000,
        )
        client = APIClient()
        client.force_authenticate(user=buyer)

        response = client.get("/api/dashboard/buyer/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Decimal(response.data["total_spent"]), Decimal("5000"))
        self.assertEqual(Decimal(response.data["monthly_spent"]), Decimal("5000"))
        self.assertEqual(Decimal(response.data["year_spent"]), Decimal("5000"))
        self.assertEqual(
            response.data["category_spend"][0]["category"],
            "Vegetables",
        )
        self.assertEqual(
            Decimal(response.data["category_spend"][0]["total"]),
            Decimal("5000"),
        )
        self.assertEqual(response.data["recent_orders"][0]["product_name"], "Tomatoes")
        self.assertEqual(response.data["top_suppliers"][0]["name"], "Green Farm")
