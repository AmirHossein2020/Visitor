from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.customers.models import Customer
from apps.products.models import Product

from .models import SalesOrder, SalesOrderItem


class SalesOrderAPITests(APITestCase):
    list_url = "/api/orders/"

    def setUp(self):
        self.user = User.objects.create_user(email="owner@example.com", full_name="ویزیتور اول", password="StrongPass!2026")
        self.other_user = User.objects.create_user(email="other@example.com", full_name="ویزیتور دوم", password="StrongPass!2026")
        self.customer = Customer.objects.create(owner=self.user, name="فروشگاه سپید")
        self.other_customer = Customer.objects.create(owner=self.other_user, name="مشتری دیگر")
        self.product = Product.objects.create(owner=self.user, name="برنج", default_price=Decimal("100.00"), unit=Product.Unit.KILOGRAM)
        self.other_product = Product.objects.create(owner=self.other_user, name="چای", default_price=Decimal("80.00"), unit=Product.Unit.PACKAGE)

    def authenticate(self, user=None):
        self.client.force_authenticate(user or self.user)

    def create_order(self, owner=None, customer=None):
        return SalesOrder.objects.create(owner=owner or self.user, customer=customer or self.customer)

    def add_item(self, order, product=None, quantity="2.000", unit_price="125.00"):
        return self.client.post(
            f"{self.list_url}{order.id}/items/",
            {"product": (product or self.product).id, "quantity": quantity, "unit_price": unit_price},
            format="json",
        )

    def test_create_order_for_own_customer(self):
        self.authenticate()
        response = self.client.post(self.list_url, {"customer": self.customer.id, "notes": "سفارش آزمایشی"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SalesOrder.objects.get().owner, self.user)

    def test_cannot_create_order_for_another_users_customer(self):
        self.authenticate()
        response = self.client.post(self.list_url, {"customer": self.other_customer.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_own_product_with_snapshots(self):
        order = self.create_order()
        self.authenticate()
        response = self.add_item(order)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        item = SalesOrderItem.objects.get()
        self.assertEqual(item.product_name_snapshot, self.product.name)
        self.assertEqual(item.unit_snapshot, self.product.get_unit_display())

    def test_cannot_add_another_users_product(self):
        order = self.create_order()
        self.authenticate()
        response = self.add_item(order, product=self.other_product)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_quantity_validation(self):
        order = self.create_order()
        self.authenticate()
        for quantity in ("0", "-1"):
            with self.subTest(quantity=quantity):
                self.assertEqual(self.add_item(order, quantity=quantity).status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_price_rejected(self):
        order = self.create_order()
        self.authenticate()
        self.assertEqual(self.add_item(order, unit_price="-1").status_code, status.HTTP_400_BAD_REQUEST)

    def test_line_total_calculated_by_backend(self):
        order = self.create_order()
        self.authenticate()
        response = self.add_item(order, quantity="2.500", unit_price="120.00")
        self.assertEqual(Decimal(response.data["line_total"]), Decimal("300.00"))

    def test_order_total_calculated_by_backend(self):
        order = self.create_order()
        self.authenticate()
        self.add_item(order, quantity="2", unit_price="100")
        self.add_item(order, quantity="3", unit_price="50")
        order.refresh_from_db()
        self.assertEqual(order.total_amount, Decimal("350.00"))

    def test_item_update_recalculates_totals(self):
        order = self.create_order()
        self.authenticate()
        item_id = self.add_item(order, quantity="2", unit_price="100").data["id"]
        response = self.client.patch(f"{self.list_url}{order.id}/items/{item_id}/", {"quantity": "3"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.total_amount, Decimal("300.00"))

    def test_item_removal_recalculates_totals(self):
        order = self.create_order()
        self.authenticate()
        first_id = self.add_item(order, quantity="2", unit_price="100").data["id"]
        self.add_item(order, quantity="1", unit_price="50")
        response = self.client.delete(f"{self.list_url}{order.id}/items/{first_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        order.refresh_from_db()
        self.assertEqual(order.total_amount, Decimal("50.00"))

    def test_item_mutations_increment_order_version(self):
        order = self.create_order()
        self.authenticate()
        initial = order.version
        item_id = self.add_item(order).data["id"]
        order.refresh_from_db(); self.assertEqual(order.version, initial + 1)
        self.client.patch(f"{self.list_url}{order.id}/items/{item_id}/", {"quantity": "3"}, format="json")
        order.refresh_from_db(); self.assertEqual(order.version, initial + 2)
        self.client.delete(f"{self.list_url}{order.id}/items/{item_id}/")
        order.refresh_from_db(); self.assertEqual(order.version, initial + 3)

    def test_notes_change_increments_version_but_status_change_does_not(self):
        order = self.create_order()
        self.authenticate()
        self.client.patch(f"{self.list_url}{order.id}/", {"notes": "اصلاح سفارش"}, format="json")
        order.refresh_from_db(); self.assertEqual(order.version, 2)
        self.client.patch(f"{self.list_url}{order.id}/", {"status": "confirmed"}, format="json")
        order.refresh_from_db(); self.assertEqual(order.version, 2)

    def test_unauthenticated_access_rejected(self):
        self.assertEqual(self.client.get(self.list_url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_access_another_users_order(self):
        order = self.create_order(owner=self.other_user, customer=self.other_customer)
        self.authenticate()
        url = f"{self.list_url}{order.id}/"
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.patch(url, {"notes": "تغییر"}, format="json").status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_404_NOT_FOUND)
