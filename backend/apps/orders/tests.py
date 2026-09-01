from decimal import Decimal
from datetime import datetime, timedelta

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.customers.models import Customer
from apps.products.models import Product
from apps.invoices.models import Invoice, InvoiceItem
from apps.products.models import StockMovement
from apps.purchases.models import Purchase
from django.utils import timezone
from django.test import override_settings
from apps.subscriptions.models import SubscriptionOrder, SubscriptionPlan, UserSubscription

from .models import SalesOrder, SalesOrderItem, SalesReturn, SalesReturnItem


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

    def test_rial_prices_are_stored_and_calculated_without_scaling(self):
        order = self.create_order()
        self.authenticate()
        response = self.add_item(order, quantity="600", unit_price="580000")
        self.assertEqual(Decimal(response.data["unit_price"]), Decimal("580000"))
        self.assertEqual(Decimal(response.data["line_total"]), Decimal("348000000"))
        order.refresh_from_db()
        self.assertEqual(order.total_amount, Decimal("348000000"))

        second_order = self.create_order()
        response = self.add_item(second_order, quantity="900", unit_price="48600")
        self.assertEqual(Decimal(response.data["line_total"]), Decimal("43740000"))

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


class SalesReturnAPITests(APITestCase):
    list_url = "/api/returns/"

    def setUp(self):
        self.user = User.objects.create_user(email="returns@example.com", full_name="فروشنده", password="StrongPass!2026")
        self.other_user = User.objects.create_user(email="other-returns@example.com", full_name="دیگری", password="StrongPass!2026")
        self.customer = Customer.objects.create(owner=self.user, name="خریدار")
        self.product = Product.objects.create(owner=self.user, name="برنج", brand="گلستان", default_price=Decimal("100"), unit=Product.Unit.KILOGRAM)
        self.order = SalesOrder.objects.create(owner=self.user, customer=self.customer, status=SalesOrder.Status.CONFIRMED)
        self.invoice = Invoice.objects.create(
            owner=self.user, sales_order=self.order, seller_profile=None,
            invoice_number="INV-RETURN-1", seller_name="فروشنده", buyer_name="خریدار",
            subtotal=Decimal("1000"), final_amount=Decimal("1000"),
        )
        self.invoice_item = InvoiceItem.objects.create(
            invoice=self.invoice, product=self.product, product_name="برنج",
            brand="گلستان", unit="کیلوگرم", quantity=Decimal("10"),
            unit_price=Decimal("100"), line_total=Decimal("1000"),
        )

    def authenticate(self, user=None):
        self.client.force_authenticate(user or self.user)

    def create_return(self, invoice=None, notes=""):
        return self.client.post(self.list_url, {"invoice": (invoice or self.invoice).id, "notes": notes}, format="json")

    def add_item(self, return_id, quantity, invoice_item=None):
        return self.client.post(
            f"{self.list_url}{return_id}/items/",
            {"invoice_item": (invoice_item or self.invoice_item).id, "quantity": quantity},
            format="json",
        )

    def confirm(self, return_id):
        return self.client.patch(f"{self.list_url}{return_id}/", {"status": "confirmed"}, format="json")

    def make_confirmed_return(self, quantity):
        return_id = self.create_return().data["id"]
        self.add_item(return_id, quantity)
        self.assertEqual(self.confirm(return_id).status_code, status.HTTP_200_OK)
        return SalesReturn.objects.get(pk=return_id)

    def test_create_own_return_and_reject_other_owner_invoice(self):
        self.authenticate()
        self.assertEqual(self.create_return().status_code, status.HTTP_201_CREATED)
        other_customer = Customer.objects.create(owner=self.other_user, name="خریدار دیگر")
        other_order = SalesOrder.objects.create(owner=self.other_user, customer=other_customer)
        other_invoice = Invoice.objects.create(owner=self.other_user, sales_order=other_order, invoice_number="OTHER-1", seller_name="دیگری", buyer_name="دیگری", subtotal=0, final_amount=0)
        self.assertEqual(self.create_return(other_invoice).status_code, status.HTTP_400_BAD_REQUEST)

    def test_cancelled_and_superseded_invoices_rejected(self):
        self.authenticate()
        for invoice_status in (Invoice.Status.CANCELLED, Invoice.Status.SUPERSEDED):
            with self.subTest(invoice_status=invoice_status):
                self.invoice.status = invoice_status
                self.invoice.save(update_fields=("status",))
                self.assertEqual(self.create_return().status_code, status.HTTP_400_BAD_REQUEST)

    def test_partial_and_full_returns_use_invoice_snapshots(self):
        self.authenticate()
        first = self.make_confirmed_return("3")
        second = self.make_confirmed_return("7")
        first_item = first.items.get()
        self.assertEqual(first_item.product_name_snapshot, "برنج")
        self.assertEqual(first_item.brand_snapshot, "گلستان")
        self.assertEqual(first_item.unit_snapshot, "کیلوگرم")
        self.assertEqual(second.items.get().quantity, Decimal("7"))

    def test_invalid_and_excess_quantities_rejected(self):
        self.authenticate()
        return_id = self.create_return().data["id"]
        for quantity in ("0", "-1", "11"):
            with self.subTest(quantity=quantity):
                self.assertEqual(self.add_item(return_id, quantity).status_code, status.HTTP_400_BAD_REQUEST)

    def test_cumulative_over_return_rejected(self):
        self.authenticate()
        self.make_confirmed_return("6")
        return_id = self.create_return().data["id"]
        self.assertEqual(self.add_item(return_id, "5").status_code, status.HTTP_400_BAD_REQUEST)

    def test_backend_calculates_line_and_return_totals(self):
        self.authenticate()
        return_id = self.create_return().data["id"]
        response = self.add_item(return_id, "2.5")
        self.assertEqual(Decimal(response.data["line_total"]), Decimal("250"))
        self.assertEqual(SalesReturn.objects.get(pk=return_id).total_amount, Decimal("250"))

    def test_update_and_removal_recalculate_total(self):
        self.authenticate()
        return_id = self.create_return().data["id"]
        item_id = self.add_item(return_id, "2").data["id"]
        response = self.client.patch(f"{self.list_url}{return_id}/items/{item_id}/", {"quantity": "4"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(SalesReturn.objects.get(pk=return_id).total_amount, Decimal("400"))
        self.assertEqual(self.client.delete(f"{self.list_url}{return_id}/items/{item_id}/").status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(SalesReturn.objects.get(pk=return_id).total_amount, Decimal("0"))

    def test_confirmed_return_is_not_editable_and_cancellation_preserves_it(self):
        self.authenticate()
        sales_return = self.make_confirmed_return("2")
        item = sales_return.items.get()
        self.assertEqual(self.client.patch(f"{self.list_url}{sales_return.id}/items/{item.id}/", {"quantity": "1"}, format="json").status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.client.delete(f"{self.list_url}{sales_return.id}/").status_code, status.HTTP_204_NO_CONTENT)
        sales_return.refresh_from_db()
        self.assertEqual(sales_return.status, SalesReturn.Status.CANCELLED)
        self.assertTrue(sales_return.items.filter(pk=item.id).exists())

    def test_confirmation_rechecks_quantity_for_competing_drafts(self):
        self.authenticate()
        first_id = self.create_return().data["id"]
        second_id = self.create_return().data["id"]
        self.add_item(first_id, "6")
        self.add_item(second_id, "6")
        self.assertEqual(self.confirm(first_id).status_code, status.HTTP_200_OK)
        self.assertEqual(self.confirm(second_id).status_code, status.HTTP_400_BAD_REQUEST)

    def test_invoice_snapshot_and_pdf_remain_unchanged(self):
        self.authenticate()
        original_quantity = self.invoice_item.quantity
        self.make_confirmed_return("3")
        self.invoice_item.refresh_from_db()
        self.assertEqual(self.invoice_item.quantity, original_quantity)
        response = self.client.get(f"/api/invoices/{self.invoice.id}/pdf/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_authentication_and_owner_isolation(self):
        self.assertEqual(self.client.get(self.list_url).status_code, status.HTTP_401_UNAUTHORIZED)
        self.authenticate(); return_id = self.create_return().data["id"]
        self.authenticate(self.other_user)
        self.assertEqual(self.client.get(f"{self.list_url}{return_id}/").status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.patch(f"{self.list_url}{return_id}/", {"notes": "x"}, format="json").status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.delete(f"{self.list_url}{return_id}/").status_code, status.HTTP_404_NOT_FOUND)


class DashboardReportAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="reports@example.com", full_name="گزارش‌گیر", password="StrongPass!2026")
        self.other_user = User.objects.create_user(email="other-reports@example.com", full_name="دیگری", password="StrongPass!2026")
        self.customer = Customer.objects.create(owner=self.user, name="مشتری سپید", company_name="سپید")
        self.other_customer = Customer.objects.create(owner=self.other_user, name="مشتری دیگر")
        self.product = Product.objects.create(owner=self.user, name="برنج", brand="گلستان", default_price=100, unit=Product.Unit.KILOGRAM)
        self.zero_product = Product.objects.create(owner=self.user, name="روغن", default_price=50, unit=Product.Unit.ITEM)
        self.other_product = Product.objects.create(owner=self.other_user, name="چای", default_price=80, unit=Product.Unit.PACKAGE)
        self.client.force_authenticate(self.user)

    def invoice(self, *, owner=None, customer=None, number="INV-R-1", amount="1000", status_value=Invoice.Status.ISSUED, issued_at=None, quantity="2"):
        owner = owner or self.user
        customer = customer or self.customer
        order = SalesOrder.objects.create(owner=owner, customer=customer, status=SalesOrder.Status.CONFIRMED)
        invoice = Invoice.objects.create(owner=owner, sales_order=order, invoice_number=number, seller_name="فروشنده", buyer_name=customer.name, buyer_company_name=customer.company_name, subtotal=amount, final_amount=amount, status=status_value)
        product = self.product if owner == self.user else self.other_product
        InvoiceItem.objects.create(invoice=invoice, product=product, product_name="برنج تاریخی" if owner == self.user else "چای تاریخی", brand="برند تاریخی", unit="کارتن", quantity=quantity, unit_price=Decimal(amount) / Decimal(quantity), line_total=amount)
        if issued_at:
            Invoice.objects.filter(pk=invoice.pk).update(issued_at=issued_at)
            invoice.refresh_from_db()
        return invoice

    def test_dashboard_today_month_and_owner_isolation(self):
        self.invoice(amount="1200")
        self.invoice(owner=self.other_user, customer=self.other_customer, number="OTHER-R", amount="9000")
        response = self.client.get("/api/dashboard/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data["today"]["sales_total"]), Decimal("1200"))
        self.assertEqual(Decimal(response.data["current_month"]["sales_total"]), Decimal("1200"))
        self.assertEqual(response.data["today"]["invoices_count"], 1)

    @override_settings(SUBSCRIPTION_TEST_BYPASS=False)
    def test_current_month_metrics_ignore_old_sales_and_subscription_orders(self):
        plan = SubscriptionPlan.objects.create(name="Test", slug="dashboard-test", billing_period="monthly", duration_days=30, price=100)
        now = timezone.now()
        UserSubscription.objects.create(user=self.user, plan=plan, status="active", starts_at=now - timedelta(days=1), expires_at=now + timedelta(days=29))
        current = self.invoice(number="CURRENT", amount="1200")
        old = self.invoice(number="OLD", amount="5000")
        old_time = now - timedelta(days=35)
        SalesOrder.objects.filter(pk=old.sales_order_id).update(created_at=old_time)
        Invoice.objects.filter(pk=old.pk).update(issued_at=old_time)
        SubscriptionOrder.objects.create(user=self.user, plan=plan, amount_snapshot=plan.price)
        response = self.client.get("/api/dashboard/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        month = response.data["current_month"]
        self.assertEqual(Decimal(month["sales_total"]), Decimal("1200"))
        self.assertEqual(Decimal(month["net_sales"]), Decimal("1200"))
        self.assertEqual(month["orders_count"], 1)

    def test_superseded_and_cancelled_invoices_are_excluded(self):
        self.invoice(number="ACTIVE", amount="700")
        self.invoice(number="OLD", amount="1000", status_value=Invoice.Status.SUPERSEDED)
        self.invoice(number="CANCEL", amount="2000", status_value=Invoice.Status.CANCELLED)
        summary = self.client.get("/api/reports/summary/").data
        self.assertEqual(Decimal(summary["sales_total"]), Decimal("700"))
        self.assertEqual(summary["invoices_count"], 1)

    def test_purchase_and_return_status_filters_and_net_sales(self):
        self.invoice(amount="1000")
        for purchase_status, amount in ((Purchase.Status.CONFIRMED, "300"), (Purchase.Status.DRAFT, "400"), (Purchase.Status.CANCELLED, "500")):
            Purchase.objects.create(owner=self.user, customer=self.customer, status=purchase_status, total_amount=amount)
        invoice = Invoice.objects.filter(owner=self.user).first()
        for return_status, amount in ((SalesReturn.Status.CONFIRMED, "100"), (SalesReturn.Status.DRAFT, "200"), (SalesReturn.Status.CANCELLED, "300")):
            SalesReturn.objects.create(owner=self.user, invoice=invoice, status=return_status, total_amount=amount)
        summary = self.client.get("/api/reports/summary/").data
        self.assertEqual(Decimal(summary["purchase_total"]), Decimal("300"))
        self.assertEqual(Decimal(summary["return_total"]), Decimal("100"))
        self.assertEqual(Decimal(summary["net_sales"]), Decimal("900"))
        self.assertEqual((summary["purchases_count"], summary["returns_count"]), (1, 1))

    def test_custom_date_range(self):
        today = timezone.now()
        self.invoice(number="TODAY", amount="100")
        self.invoice(number="OLD-DATE", amount="500", issued_at=today - timedelta(days=40))
        date_value = timezone.localdate().isoformat()
        response = self.client.get("/api/reports/summary/", {"from": date_value, "to": date_value})
        self.assertEqual(Decimal(response.data["sales_total"]), Decimal("100"))
        self.assertEqual(self.client.get("/api/reports/summary/", {"from": "bad", "to": date_value}).status_code, status.HTTP_400_BAD_REQUEST)

    def test_dashboard_accepts_canonical_range_for_a_true_jalali_month(self):
        inside = self.invoice(number="SHAHRIVAR", amount="700")
        outside = self.invoice(number="MORDAD", amount="900")
        Invoice.objects.filter(pk=inside.pk).update(issued_at=timezone.make_aware(datetime(2026, 9, 1, 12)))
        SalesOrder.objects.filter(pk=inside.sales_order_id).update(created_at=timezone.make_aware(datetime(2026, 9, 1, 12)))
        Invoice.objects.filter(pk=outside.pk).update(issued_at=timezone.make_aware(datetime(2026, 8, 22, 12)))
        SalesOrder.objects.filter(pk=outside.sales_order_id).update(created_at=timezone.make_aware(datetime(2026, 8, 22, 12)))
        response = self.client.get("/api/dashboard/", {"from": "2026-08-23", "to": "2026-09-22"})
        self.assertEqual(Decimal(response.data["current_month"]["sales_total"]), Decimal("700"))
        self.assertEqual(response.data["current_month"]["orders_count"], 1)

    def test_top_products_use_invoice_snapshots(self):
        self.invoice(number="P1", amount="500", quantity="5")
        self.invoice(number="P2", amount="300", quantity="3")
        self.product.name = "نام فعلی متفاوت"; self.product.save(update_fields=("name",))
        response = self.client.get("/api/reports/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["product_name"], "برنج تاریخی")
        self.assertEqual(Decimal(response.data[0]["quantity_sold"]), Decimal("8"))
        self.assertEqual(Decimal(response.data[0]["total_sales"]), Decimal("800"))

    def test_customer_sales_aggregation(self):
        self.invoice(number="C1", amount="400")
        self.invoice(number="C2", amount="600")
        response = self.client.get("/api/reports/customers/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["buyer_name"], "مشتری سپید")
        self.assertEqual(response.data[0]["invoice_count"], 2)
        self.assertEqual(Decimal(response.data[0]["total_sales"]), Decimal("1000"))

    def test_inventory_warning_counts(self):
        StockMovement.objects.create(owner=self.user, product=self.product, movement_type=StockMovement.Type.SALE_OUT, quantity=-2, reference_type="test", reference_id=1)
        StockMovement.objects.create(owner=self.other_user, product=self.other_product, movement_type=StockMovement.Type.SALE_OUT, quantity=-5, reference_type="test", reference_id=2)
        inventory = self.client.get("/api/dashboard/").data["inventory"]
        self.assertEqual(inventory["total_products"], 2)
        self.assertEqual(inventory["negative_stock_count"], 1)
        self.assertEqual(inventory["zero_stock_count"], 1)

    def test_dashboard_and_reports_require_authentication(self):
        self.client.force_authenticate(user=None)
        for url in ("/api/dashboard/", "/api/reports/summary/", "/api/reports/products/", "/api/reports/customers/"):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, status.HTTP_401_UNAUTHORIZED)
