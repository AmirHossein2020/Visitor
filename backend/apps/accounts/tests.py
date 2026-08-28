from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class AuthenticationAPITests(APITestCase):
    register_url = "/api/auth/register/"
    login_url = "/api/auth/login/"
    me_url = "/api/auth/me/"
    valid_payload = {
        "full_name": "علی رضایی",
        "email": "ali@example.com",
        "phone_number": "09121234567",
        "password": "StrongPass!2026",
        "password_confirm": "StrongPass!2026",
    }

    def create_user(self):
        return User.objects.create_user(
            email="ali@example.com",
            full_name="علی رضایی",
            password="StrongPass!2026",
        )

    def test_successful_registration(self):
        response = self.client.post(self.register_url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", response.data)
        self.assertTrue(User.objects.get().check_password("StrongPass!2026"))

    def test_duplicate_email_rejected(self):
        self.create_user()
        response = self.client.post(self.register_url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_mismatch_rejected(self):
        payload = {**self.valid_payload, "password_confirm": "DifferentPass!2026"}
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.exists())

    def test_successful_login(self):
        self.create_user()
        response = self.client.post(
            self.login_url,
            {"email": "ali@example.com", "password": "StrongPass!2026"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_refresh_token(self):
        self.create_user()
        login_response = self.client.post(
            self.login_url,
            {"email": "ali@example.com", "password": "StrongPass!2026"},
            format="json",
        )
        response = self.client.post(
            "/api/auth/refresh/",
            {"refresh": login_response.data["refresh"]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_incorrect_login_rejected(self):
        self.create_user()
        response = self.client.post(
            self.login_url,
            {"email": "ali@example.com", "password": "wrong-password"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authenticated_me(self):
        user = self.create_user()
        self.client.force_authenticate(user)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], user.email)

    def test_unauthenticated_me_rejected(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
