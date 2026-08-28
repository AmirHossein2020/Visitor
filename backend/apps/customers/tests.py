from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User

from .models import Customer


class CustomerAPITests(APITestCase):
    list_url = "/api/customers/"
    payload = {
        "name": "فروشگاه سپید",
        "phone_number": "021-88776655",
        "company_name": "سپید تجارت",
        "address": "تهران",
        "economic_code": "123456789",
        "postal_code": "1234567890",
        "description": "",
    }

    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@example.com",
            full_name="ویزیتور اول",
            password="StrongPass!2026",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            full_name="ویزیتور دوم",
            password="StrongPass!2026",
        )

    def authenticate(self, user=None):
        self.client.force_authenticate(user or self.user)

    def create_customer(self, owner=None, **overrides):
        data = {
            "name": "فروشگاه سپید",
            "phone_number": "021-88776655",
            "company_name": "سپید تجارت",
            **overrides,
        }
        return Customer.objects.create(owner=owner or self.user, **data)

    def test_create_customer(self):
        self.authenticate()
        response = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Customer.objects.get().owner, self.user)

    def test_list_only_own_customers(self):
        own_customer = self.create_customer()
        self.create_customer(owner=self.other_user, name="مشتری دیگر")
        self.authenticate()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [own_customer.id])

    def test_retrieve_own_customer(self):
        customer = self.create_customer()
        self.authenticate()
        response = self.client.get(f"{self.list_url}{customer.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], customer.name)

    def test_update_own_customer(self):
        customer = self.create_customer()
        self.authenticate()
        response = self.client.patch(
            f"{self.list_url}{customer.id}/", {"name": "فروشگاه تازه"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        customer.refresh_from_db()
        self.assertEqual(customer.name, "فروشگاه تازه")

    def test_deactivate_own_customer(self):
        customer = self.create_customer()
        self.authenticate()
        response = self.client.delete(f"{self.list_url}{customer.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        customer.refresh_from_db()
        self.assertFalse(customer.is_active)

    def test_unauthenticated_access_rejected(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_access_another_users_customer(self):
        customer = self.create_customer(owner=self.other_user)
        self.authenticate()
        url = f"{self.list_url}{customer.id}/"
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            self.client.patch(url, {"name": "تغییر"}, format="json").status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_404_NOT_FOUND)

    def test_search_by_name(self):
        expected = self.create_customer()
        self.create_customer(name="فروشگاه آفتاب", company_name="آفتاب")
        self.authenticate()
        response = self.client.get(self.list_url, {"search": "سپید"})
        self.assertEqual([item["id"] for item in response.data], [expected.id])

    def test_search_by_phone_and_company(self):
        expected = self.create_customer()
        self.create_customer(name="مشتری دیگر", phone_number="09120000000", company_name="آفتاب")
        self.authenticate()
        phone_response = self.client.get(self.list_url, {"search": "88776655"})
        company_response = self.client.get(self.list_url, {"search": "سپید تجارت"})
        self.assertEqual([item["id"] for item in phone_response.data], [expected.id])
        self.assertEqual([item["id"] for item in company_response.data], [expected.id])

    def test_name_and_phone_validation(self):
        self.authenticate()
        for payload in (
            {**self.payload, "name": "   "},
            {**self.payload, "phone_number": "نامعتبر"},
        ):
            with self.subTest(payload=payload):
                response = self.client.post(self.list_url, payload, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Customer.objects.exists())
