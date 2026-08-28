from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User

from .models import Product


class ProductAPITests(APITestCase):
    list_url = "/api/products/"
    payload = {
        "name": "برنج ایرانی",
        "brand": "گلستان",
        "default_price": "250000.00",
        "unit": "kilogram",
        "description": "",
    }

    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@example.com",
            full_name="مالک محصول",
            password="StrongPass!2026",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            full_name="کاربر دیگر",
            password="StrongPass!2026",
        )

    def authenticate(self, user=None):
        self.client.force_authenticate(user or self.user)

    def create_product(self, owner=None, **overrides):
        data = {
            "name": "برنج ایرانی",
            "brand": "گلستان",
            "default_price": Decimal("250000.00"),
            "unit": Product.Unit.KILOGRAM,
            **overrides,
        }
        return Product.objects.create(owner=owner or self.user, **data)

    def test_create_product(self):
        self.authenticate()
        response = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        product = Product.objects.get()
        self.assertEqual(product.owner, self.user)
        self.assertEqual(product.default_price, Decimal("250000.00"))

    def test_list_only_own_products(self):
        own_product = self.create_product()
        self.create_product(owner=self.other_user, name="محصول کاربر دیگر")
        self.authenticate()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [own_product.id])

    def test_update_own_product(self):
        product = self.create_product()
        self.authenticate()
        response = self.client.patch(
            f"{self.list_url}{product.id}/", {"name": "برنج ممتاز"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product.refresh_from_db()
        self.assertEqual(product.name, "برنج ممتاز")

    def test_deactivate_own_product(self):
        product = self.create_product()
        self.authenticate()
        response = self.client.delete(f"{self.list_url}{product.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        product.refresh_from_db()
        self.assertFalse(product.is_active)

    def test_unauthenticated_access_rejected(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_access_another_users_product(self):
        product = self.create_product(owner=self.other_user)
        self.authenticate()
        detail_url = f"{self.list_url}{product.id}/"
        self.assertEqual(self.client.get(detail_url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            self.client.patch(detail_url, {"name": "تغییر"}, format="json").status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(self.client.delete(detail_url).status_code, status.HTTP_404_NOT_FOUND)

    def test_negative_price_rejected(self):
        self.authenticate()
        response = self.client.post(
            self.list_url, {**self.payload, "default_price": "-1"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Product.objects.exists())

    def test_required_product_fields_are_validated(self):
        self.authenticate()
        invalid_payloads = (
            {**self.payload, "name": "   "},
            {**self.payload, "default_price": "قیمت نامعتبر"},
            {key: value for key, value in self.payload.items() if key != "unit"},
        )
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                response = self.client.post(self.list_url, payload, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Product.objects.exists())

    def test_search_by_name_and_brand(self):
        rice = self.create_product()
        tea = self.create_product(name="چای سیاه", brand="رفاه")
        self.authenticate()
        name_response = self.client.get(self.list_url, {"search": "برنج"})
        brand_response = self.client.get(self.list_url, {"search": "رفاه"})
        self.assertEqual([item["id"] for item in name_response.data], [rice.id])
        self.assertEqual([item["id"] for item in brand_response.data], [tea.id])
