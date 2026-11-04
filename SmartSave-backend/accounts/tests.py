from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import BuyerProfile, FarmerProfile, Profile


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
        self.assertEqual(user.profile.role, 'farmer')

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
        self.assertEqual(user.profile.role, 'buyer')

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

    @override_settings(GOOGLE_OAUTH_CLIENT_ID="")
    def test_google_login_reports_missing_server_configuration(self):
        response = self.client.post(
            self.endpoint,
            {"credential": "valid-google-token"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 503)
