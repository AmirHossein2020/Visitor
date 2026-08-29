from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.customers.models import Customer
from apps.invoices.models import Invoice, InvoiceItem
from apps.orders.models import SalesOrder, SalesOrderItem
from apps.purchases.models import Purchase, PurchaseItem
from apps.products.inventory import sync_order, sync_purchase
from django.db import IntegrityError, transaction
from django.db.models import Sum
from importlib import import_module

from .models import Product, StockMovement


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


class InventoryAPITests(APITestCase):
    inventory_url = "/api/inventory/"

    def setUp(self):
        self.user = User.objects.create_user(email="stock@example.com", full_name="مالک", password="StrongPass!2026")
        self.other_user = User.objects.create_user(email="other-stock@example.com", full_name="دیگری", password="StrongPass!2026")
        self.customer = Customer.objects.create(owner=self.user, name="طرف حساب")
        self.product = Product.objects.create(owner=self.user, name="برنج", brand="گلستان", default_price=Decimal("100"), unit=Product.Unit.KILOGRAM)
        self.other_product = Product.objects.create(owner=self.other_user, name="چای", default_price=Decimal("80"), unit=Product.Unit.PACKAGE)
        self.client.force_authenticate(self.user)

    def stock(self, product=None):
        product = product or self.product
        return StockMovement.objects.filter(product=product).aggregate(total=Sum("quantity"))["total"] or Decimal("0")

    def create_purchase(self, quantity="10", status_value="draft"):
        purchase = Purchase.objects.create(owner=self.user, customer=self.customer, status=status_value)
        item = PurchaseItem.objects.create(purchase=purchase, product=self.product, product_name_snapshot=self.product.name, brand_snapshot=self.product.brand, unit_snapshot=self.product.get_unit_display(), quantity=Decimal(quantity), unit_price=Decimal("50"))
        purchase.recalculate_total()
        return purchase, item

    def create_order(self, quantity="5", status_value="draft"):
        order = SalesOrder.objects.create(owner=self.user, customer=self.customer, status=status_value)
        item = SalesOrderItem.objects.create(order=order, product=self.product, product_name_snapshot=self.product.name, brand_snapshot=self.product.brand, unit_snapshot=self.product.get_unit_display(), quantity=Decimal(quantity), unit_price=Decimal("100"))
        order.recalculate_total()
        return order, item

    def test_confirmed_purchase_increases_draft_does_not_and_edit_reconciles(self):
        purchase, item = self.create_purchase()
        self.assertEqual(self.stock(), 0)
        self.client.patch(f"/api/purchases/{purchase.id}/", {"status": "confirmed"}, format="json")
        self.assertEqual(self.stock(), Decimal("10"))
        self.client.patch(f"/api/purchases/{purchase.id}/items/{item.id}/", {"quantity": "12"}, format="json")
        self.assertEqual(self.stock(), Decimal("12"))
        self.assertEqual(StockMovement.objects.filter(reference_type="purchase_item").count(), 1)

    def test_cancelled_purchase_has_zero_net_and_preserves_history(self):
        purchase, _ = self.create_purchase(status_value="confirmed")
        sync_purchase(purchase)
        self.client.delete(f"/api/purchases/{purchase.id}/")
        self.assertEqual(self.stock(), 0)
        self.assertEqual(StockMovement.objects.filter(product=self.product).count(), 2)

    def test_confirmed_sale_decreases_draft_does_not_and_quantity_reconciles(self):
        order, item = self.create_order()
        self.assertEqual(self.stock(), 0)
        self.client.patch(f"/api/orders/{order.id}/", {"status": "confirmed"}, format="json")
        self.assertEqual(self.stock(), Decimal("-5"))
        self.client.patch(f"/api/orders/{order.id}/items/{item.id}/", {"quantity": "7"}, format="json")
        self.assertEqual(self.stock(), Decimal("-7"))

    def test_invoice_revision_never_double_deducts(self):
        order, _ = self.create_order(status_value="confirmed")
        sync_order(order)
        first = Invoice.objects.create(owner=self.user, sales_order=order, invoice_number="INV-STOCK-1", seller_name="فروشنده", buyer_name="خریدار", subtotal=500, final_amount=500, source_order_version=order.version)
        first.status = Invoice.Status.SUPERSEDED; first.save(update_fields=("status",))
        Invoice.objects.create(owner=self.user, sales_order=order, invoice_number="INV-STOCK-2", seller_name="فروشنده", buyer_name="خریدار", subtotal=500, final_amount=500, revision_of=first, revision_number=2, source_order_version=order.version)
        self.assertEqual(self.stock(), Decimal("-5"))
        self.assertEqual(StockMovement.objects.filter(movement_type=StockMovement.Type.SALE_OUT).count(), 1)

    def test_confirmed_and_multiple_returns_increase_stock_and_cancel_reverses(self):
        order, order_item = self.create_order(quantity="10", status_value="confirmed")
        sync_order(order)
        invoice = Invoice.objects.create(owner=self.user, sales_order=order, invoice_number="INV-RET-STOCK", seller_name="فروشنده", buyer_name="خریدار", subtotal=1000, final_amount=1000)
        invoice_item = InvoiceItem.objects.create(invoice=invoice, product=self.product, product_name=self.product.name, unit=self.product.get_unit_display(), quantity=10, unit_price=100, line_total=1000)
        return_ids = []
        for quantity in ("2", "3"):
            sales_return = self.client.post("/api/returns/", {"invoice": invoice.id}, format="json").data
            self.client.post(f"/api/returns/{sales_return['id']}/items/", {"invoice_item": invoice_item.id, "quantity": quantity}, format="json")
            self.assertEqual(self.client.patch(f"/api/returns/{sales_return['id']}/", {"status": "confirmed"}, format="json").status_code, status.HTTP_200_OK)
            return_ids.append(sales_return["id"])
        self.assertEqual(self.stock(), Decimal("-5"))
        self.client.delete(f"/api/returns/{return_ids[0]}/")
        self.assertEqual(self.stock(), Decimal("-7"))
        self.assertGreaterEqual(StockMovement.objects.filter(product=self.product).count(), 4)

    def test_stock_may_be_negative_and_api_search_is_owner_scoped(self):
        order, _ = self.create_order(quantity="20", status_value="confirmed")
        sync_order(order)
        response = self.client.get(self.inventory_url, {"search": "برنج"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(Decimal(response.data[0]["current_stock"]), Decimal("-20"))
        self.assertNotEqual(response.data[0]["id"], self.other_product.id)
        self.assertEqual(self.client.get(f"{self.inventory_url}{self.other_product.id}/").status_code, status.HTTP_404_NOT_FOUND)

    def test_movement_is_idempotent_and_constraint_prevents_duplicate(self):
        purchase, _ = self.create_purchase(status_value="confirmed")
        sync_purchase(purchase); sync_purchase(purchase)
        movement = StockMovement.objects.get(reference_type="purchase_item")
        self.assertEqual(self.stock(), Decimal("10"))
        with self.assertRaises(IntegrityError), transaction.atomic():
            StockMovement.objects.create(owner=self.user, product=self.product, movement_type=movement.movement_type, quantity=10, reference_type=movement.reference_type, reference_id=movement.reference_id)

    def test_backfill_is_safe_when_run_twice(self):
        purchase, _ = self.create_purchase(status_value="confirmed")
        migration = import_module("apps.products.migrations.0002_stockmovement")
        from django.apps import apps
        migration.backfill_stock_movements(apps, None)
        migration.backfill_stock_movements(apps, None)
        self.assertEqual(StockMovement.objects.filter(reference_type="purchase_item").count(), 1)
        self.assertEqual(self.stock(), Decimal("10"))

    def test_inventory_requires_authentication(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(self.inventory_url).status_code, status.HTTP_401_UNAUTHORIZED)
