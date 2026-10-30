from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


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
