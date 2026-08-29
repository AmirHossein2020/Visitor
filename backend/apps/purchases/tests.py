from datetime import date
from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.customers.models import Customer
from apps.products.models import Product

from .models import Purchase, PurchaseItem


class PurchaseAPITests(APITestCase):
    list_url = "/api/purchases/"

    def setUp(self):
        self.user = User.objects.create_user(email="owner@example.com", full_name="ویزیتور اول", password="StrongPass!2026")
        self.other_user = User.objects.create_user(email="other@example.com", full_name="ویزیتور دوم", password="StrongPass!2026")
        self.customer = Customer.objects.create(owner=self.user, name="تأمین‌کننده سپید")
        self.other_customer = Customer.objects.create(owner=self.other_user, name="تأمین‌کننده دیگر")
        self.product = Product.objects.create(owner=self.user, name="برنج", default_price=Decimal("100"), unit=Product.Unit.KILOGRAM)
        self.other_product = Product.objects.create(owner=self.other_user, name="چای", default_price=Decimal("80"), unit=Product.Unit.PACKAGE)

    def authenticate(self, user=None):
        self.client.force_authenticate(user or self.user)

    def create_purchase(self, owner=None, customer=None):
        return Purchase.objects.create(owner=owner or self.user, customer=customer or self.customer, purchase_date=date(2026, 8, 29))

    def add_item(self, purchase, product=None, quantity="2", unit_price="125"):
        return self.client.post(f"{self.list_url}{purchase.id}/items/", {"product": (product or self.product).id, "quantity": quantity, "unit_price": unit_price}, format="json")

    def test_create_purchase_for_own_customer(self):
        self.authenticate()
        response = self.client.post(self.list_url, {"customer": self.customer.id, "purchase_date": "2026-08-29"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Purchase.objects.get().owner, self.user)

    def test_cannot_use_another_users_customer(self):
        self.authenticate()
        response = self.client.post(self.list_url, {"customer": self.other_customer.id, "purchase_date": "2026-08-29"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_own_product_with_snapshot(self):
        purchase = self.create_purchase(); self.authenticate()
        response = self.add_item(purchase)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        item = PurchaseItem.objects.get()
        self.assertEqual(item.product_name_snapshot, self.product.name)

    def test_cannot_add_another_users_product(self):
        purchase = self.create_purchase(); self.authenticate()
        self.assertEqual(self.add_item(purchase, product=self.other_product).status_code, status.HTTP_400_BAD_REQUEST)

    def test_quantity_validation(self):
        purchase = self.create_purchase(); self.authenticate()
        for quantity in ("0", "-1"):
            with self.subTest(quantity=quantity):
                self.assertEqual(self.add_item(purchase, quantity=quantity).status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_purchase_price_rejected(self):
        purchase = self.create_purchase(); self.authenticate()
        self.assertEqual(self.add_item(purchase, unit_price="-1").status_code, status.HTTP_400_BAD_REQUEST)

    def test_line_total_calculated_by_backend(self):
        purchase = self.create_purchase(); self.authenticate()
        response = self.add_item(purchase, quantity="2.5", unit_price="120")
        self.assertEqual(Decimal(response.data["line_total"]), Decimal("300.00"))

    def test_purchase_total_calculated_by_backend(self):
        purchase = self.create_purchase(); self.authenticate()
        self.add_item(purchase, quantity="2", unit_price="100")
        self.add_item(purchase, quantity="3", unit_price="50")
        purchase.refresh_from_db()
        self.assertEqual(purchase.total_amount, Decimal("350.00"))

    def test_item_update_recalculates_total(self):
        purchase = self.create_purchase(); self.authenticate()
        item_id = self.add_item(purchase, quantity="2", unit_price="100").data["id"]
        response = self.client.patch(f"{self.list_url}{purchase.id}/items/{item_id}/", {"quantity": "3"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        purchase.refresh_from_db()
        self.assertEqual(purchase.total_amount, Decimal("300.00"))

    def test_item_removal_recalculates_total(self):
        purchase = self.create_purchase(); self.authenticate()
        item_id = self.add_item(purchase, quantity="2", unit_price="100").data["id"]
        self.add_item(purchase, quantity="1", unit_price="50")
        self.assertEqual(self.client.delete(f"{self.list_url}{purchase.id}/items/{item_id}/").status_code, status.HTTP_204_NO_CONTENT)
        purchase.refresh_from_db()
        self.assertEqual(purchase.total_amount, Decimal("50.00"))

    def test_cancelling_purchase(self):
        purchase = self.create_purchase(); self.authenticate()
        self.assertEqual(self.client.delete(f"{self.list_url}{purchase.id}/").status_code, status.HTTP_204_NO_CONTENT)
        purchase.refresh_from_db()
        self.assertEqual(purchase.status, Purchase.Status.CANCELLED)

    def test_unauthenticated_access_rejected(self):
        self.assertEqual(self.client.get(self.list_url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_access_another_users_purchase(self):
        purchase = self.create_purchase(owner=self.other_user, customer=self.other_customer)
        self.authenticate()
        url = f"{self.list_url}{purchase.id}/"
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.patch(url, {"notes": "تغییر"}, format="json").status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_404_NOT_FOUND)
