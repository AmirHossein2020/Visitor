from decimal import Decimal
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.companies.models import SellerProfile
from apps.customers.models import Customer
from apps.orders.models import SalesOrder, SalesOrderItem
from apps.products.models import Product

from .models import Invoice


class InvoiceAPITests(APITestCase):
    list_url = "/api/invoices/"

    def setUp(self):
        self.user = User.objects.create_user(email="owner@example.com", full_name="ویزیتور اول", password="StrongPass!2026")
        self.other_user = User.objects.create_user(email="other@example.com", full_name="ویزیتور دوم", password="StrongPass!2026")
        self.customer = Customer.objects.create(owner=self.user, name="خریدار سپید", company_name="سپید تجارت", phone_number="02188776655", address="تهران", economic_code="111", postal_code="1234567890")
        self.other_customer = Customer.objects.create(owner=self.other_user, name="خریدار دیگر")
        self.seller = SellerProfile.objects.create(owner=self.user, name="فروشنده سپید", phone_number="02111111111", address="تهران", economic_code="222", national_id="333", registration_number="444", postal_code="0987654321")
        self.other_seller = SellerProfile.objects.create(owner=self.other_user, name="فروشنده دیگر")
        self.product = Product.objects.create(owner=self.user, name="برنج", brand="گلستان", default_price=Decimal("100"), unit=Product.Unit.KILOGRAM)
        self.other_product = Product.objects.create(owner=self.other_user, name="چای", default_price=Decimal("80"), unit=Product.Unit.PACKAGE)
        self.order = self.create_order()

    def create_order(self, owner=None, customer=None, status_value=SalesOrder.Status.CONFIRMED, with_item=True):
        owner = owner or self.user
        customer = customer or self.customer
        order = SalesOrder.objects.create(owner=owner, customer=customer, status=status_value)
        if with_item:
            product = self.product if owner == self.user else self.other_product
            item = SalesOrderItem.objects.create(order=order, product=product, product_name_snapshot=product.name, brand_snapshot=product.brand, unit_snapshot=product.get_unit_display(), quantity=Decimal("2.000"), unit_price=Decimal("125.00"))
            order.recalculate_total()
        return order

    def authenticate(self):
        self.client.force_authenticate(self.user)

    def issue(self, order=None, seller=None, **overrides):
        payload = {"sales_order": (order or self.order).id, "seller_profile": (seller or self.seller).id, **overrides}
        return self.client.post(self.list_url, payload, format="json")

    def test_issue_invoice_from_own_confirmed_order(self):
        self.authenticate()
        response = self.issue()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Invoice.objects.get().owner, self.user)
        self.assertEqual(len(response.data["items"]), 1)

    def test_cannot_issue_from_another_users_order(self):
        order = self.create_order(owner=self.other_user, customer=self.other_customer)
        self.authenticate()
        self.assertEqual(self.issue(order=order).status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_use_another_users_seller_profile(self):
        self.authenticate()
        self.assertEqual(self.issue(seller=self.other_seller).status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_use_inactive_seller_profile(self):
        self.seller.is_active = False; self.seller.save(update_fields=("is_active",))
        self.authenticate()
        self.assertEqual(self.issue().status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_invoice_cancelled_order(self):
        order = self.create_order(status_value=SalesOrder.Status.CANCELLED)
        self.authenticate()
        self.assertEqual(self.issue(order=order).status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_invoice_empty_order(self):
        order = self.create_order(with_item=False)
        self.authenticate()
        self.assertEqual(self.issue(order=order).status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_active_invoice_prevented(self):
        self.authenticate()
        self.assertEqual(self.issue().status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.issue().status_code, status.HTTP_400_BAD_REQUEST)

    def test_replacement_requires_changed_order_and_preserves_old_snapshot(self):
        self.authenticate()
        first_response = self.issue()
        first = Invoice.objects.get(pk=first_response.data["id"])
        old_total = first.final_amount
        item = self.order.items.get()
        edit_response = self.client.patch(f"/api/orders/{self.order.id}/items/{item.id}/", {"quantity": "3"}, format="json")
        self.assertEqual(edit_response.status_code, status.HTTP_200_OK, edit_response.data)
        replacement_response = self.issue()
        self.assertEqual(replacement_response.status_code, status.HTTP_201_CREATED, replacement_response.data)
        first.refresh_from_db()
        replacement = Invoice.objects.get(pk=replacement_response.data["id"])
        self.assertEqual(first.status, Invoice.Status.SUPERSEDED)
        self.assertEqual(first.final_amount, old_total)
        self.assertEqual(first.items.get().quantity, Decimal("2.000"))
        self.assertEqual(replacement.status, Invoice.Status.ISSUED)
        self.assertEqual(replacement.items.get().quantity, Decimal("3.000"))
        self.assertEqual(replacement.revision_of, first)
        self.assertEqual(replacement.revision_number, 2)

    def test_third_revision_uses_same_root_and_increments_number(self):
        self.authenticate()
        root = Invoice.objects.get(pk=self.issue().data["id"])
        item = self.order.items.get()
        edit_response = self.client.patch(f"/api/orders/{self.order.id}/items/{item.id}/", {"quantity": "3"}, format="json")
        self.assertEqual(edit_response.status_code, status.HTTP_200_OK, edit_response.data)
        second = Invoice.objects.get(pk=self.issue().data["id"])
        self.client.patch(f"/api/orders/{self.order.id}/items/{item.id}/", {"unit_price": "150"}, format="json")
        third_response = self.issue()
        self.assertEqual(third_response.status_code, status.HTTP_201_CREATED)
        second.refresh_from_db()
        third = Invoice.objects.get(pk=third_response.data["id"])
        self.assertEqual(second.status, Invoice.Status.SUPERSEDED)
        self.assertEqual(third.revision_of, root)
        self.assertEqual(third.revision_number, 3)

    def test_failed_replacement_does_not_supersede_active_invoice(self):
        self.authenticate()
        active = Invoice.objects.get(pk=self.issue().data["id"])
        item = self.order.items.get()
        edit_response = self.client.patch(f"/api/orders/{self.order.id}/items/{item.id}/", {"quantity": "4"}, format="json")
        self.assertEqual(edit_response.status_code, status.HTTP_200_OK, edit_response.data)
        with patch("apps.invoices.views.InvoiceItem.objects.bulk_create", side_effect=RuntimeError("failure")):
            with self.assertRaises(RuntimeError):
                self.issue()
        active.refresh_from_db()
        self.assertEqual(active.status, Invoice.Status.ISSUED)
        self.assertEqual(Invoice.objects.filter(sales_order=self.order).count(), 1)

    def test_revision_links_are_owner_scoped(self):
        self.authenticate()
        first_id = self.issue().data["id"]
        item = self.order.items.get()
        edit_response = self.client.patch(f"/api/orders/{self.order.id}/items/{item.id}/", {"quantity": "3"}, format="json")
        self.assertEqual(edit_response.status_code, status.HTTP_200_OK, edit_response.data)
        second_id = self.issue().data["id"]
        detail = self.client.get(f"{self.list_url}{second_id}/")
        self.assertEqual(detail.data["previous_invoice"]["id"], first_id)
        self.client.force_authenticate(self.other_user)
        self.assertEqual(self.client.get(f"{self.list_url}{second_id}/").status_code, status.HTTP_404_NOT_FOUND)

    def test_old_and_replacement_pdfs_remain_downloadable(self):
        self.authenticate()
        first_id = self.issue().data["id"]
        item = self.order.items.get()
        edit_response = self.client.patch(f"/api/orders/{self.order.id}/items/{item.id}/", {"quantity": "3"}, format="json")
        self.assertEqual(edit_response.status_code, status.HTTP_200_OK, edit_response.data)
        second_id = self.issue().data["id"]
        for invoice_id in (first_id, second_id):
            response = self.client.get(f"{self.list_url}{invoice_id}/pdf/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.content.startswith(b"%PDF"))

    def test_unique_sequential_invoice_number_per_owner(self):
        second_order = self.create_order()
        self.authenticate()
        first = self.issue().data["invoice_number"]
        second = self.issue(order=second_order).data["invoice_number"]
        self.assertEqual((first, second), ("INV-000001", "INV-000002"))

    def test_seller_snapshot_preserved(self):
        self.authenticate(); invoice_id = self.issue().data["id"]
        self.seller.name = "نام تغییریافته"; self.seller.save(update_fields=("name",))
        self.assertEqual(Invoice.objects.get(pk=invoice_id).seller_name, "فروشنده سپید")

    def test_buyer_snapshot_preserved(self):
        self.authenticate(); invoice_id = self.issue().data["id"]
        self.customer.name = "خریدار تغییریافته"; self.customer.save(update_fields=("name",))
        self.assertEqual(Invoice.objects.get(pk=invoice_id).buyer_name, "خریدار سپید")

    def test_item_snapshot_preserved(self):
        self.authenticate(); invoice_id = self.issue().data["id"]
        self.product.name = "محصول تغییریافته"; self.product.save(update_fields=("name",))
        order_item = self.order.items.get(); order_item.product_name_snapshot = "نام سفارش تغییریافته"; order_item.save()
        self.assertEqual(Invoice.objects.get(pk=invoice_id).items.get().product_name, "برنج")

    def test_totals_calculated_by_backend(self):
        self.authenticate()
        response = self.issue(discount_amount="20", tax_amount="10", duties_amount="5")
        self.assertEqual(Decimal(response.data["subtotal"]), Decimal("250.00"))
        self.assertEqual(Decimal(response.data["final_amount"]), Decimal("245.00"))

    def test_discount_validation(self):
        self.authenticate()
        self.assertEqual(self.issue(discount_amount="-1").status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.issue(discount_amount="300").status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_access_rejected(self):
        self.assertEqual(self.client.get(self.list_url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_access_another_users_invoice(self):
        other_order = self.create_order(owner=self.other_user, customer=self.other_customer)
        self.client.force_authenticate(self.other_user)
        invoice_id = self.issue(order=other_order, seller=self.other_seller).data["id"]
        self.authenticate()
        url = f"{self.list_url}{invoice_id}/"
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_404_NOT_FOUND)

    def test_invoice_cancellation_preserves_record(self):
        self.authenticate(); invoice_id = self.issue().data["id"]
        self.assertEqual(self.client.delete(f"{self.list_url}{invoice_id}/").status_code, status.HTTP_204_NO_CONTENT)
        invoice = Invoice.objects.get(pk=invoice_id)
        self.assertEqual(invoice.status, Invoice.Status.CANCELLED)

    def test_owner_can_download_non_empty_pdf(self):
        self.authenticate(); invoice_id = self.issue().data["id"]
        response = self.client.get(f"{self.list_url}{invoice_id}/pdf/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))
        self.assertGreater(len(response.content), 1000)

    def test_unauthenticated_pdf_request_rejected(self):
        self.authenticate(); invoice_id = self.issue().data["id"]
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(f"{self.list_url}{invoice_id}/pdf/").status_code, status.HTTP_401_UNAUTHORIZED)

    def test_another_visitor_cannot_download_pdf(self):
        self.authenticate(); invoice_id = self.issue().data["id"]
        self.client.force_authenticate(self.other_user)
        self.assertEqual(self.client.get(f"{self.list_url}{invoice_id}/pdf/").status_code, status.HTTP_404_NOT_FOUND)

    def test_pdf_filename_contains_invoice_number(self):
        self.authenticate(); issue_response = self.issue()
        response = self.client.get(f"{self.list_url}{issue_response.data['id']}/pdf/")
        self.assertIn(issue_response.data["invoice_number"], response["Content-Disposition"])

    def test_pdf_generator_receives_preserved_snapshots(self):
        self.authenticate(); invoice_id = self.issue().data["id"]
        self.seller.name = "فروشنده جدید"; self.seller.save(update_fields=("name",))
        self.customer.name = "خریدار جدید"; self.customer.save(update_fields=("name",))

        def verify_snapshots(invoice):
            self.assertEqual(invoice.seller_name, "فروشنده سپید")
            self.assertEqual(invoice.buyer_name, "خریدار سپید")
            self.assertEqual(invoice.items.get().product_name, "برنج")
            return b"%PDF-snapshot-test"

        with patch("apps.invoices.views.build_invoice_pdf", side_effect=verify_snapshots):
            response = self.client.get(f"{self.list_url}{invoice_id}/pdf/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cancelled_invoice_pdf_remains_available(self):
        self.authenticate(); invoice_id = self.issue().data["id"]
        self.client.delete(f"{self.list_url}{invoice_id}/")
        response = self.client.get(f"{self.list_url}{invoice_id}/pdf/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.content), 1000)

    def test_pdf_handles_persian_snapshot_values(self):
        self.authenticate(); invoice_id = self.issue(notes="یادداشت فارسی برای فاکتور").data["id"]
        response = self.client.get(f"{self.list_url}{invoice_id}/pdf/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_multi_item_invoice_pdf_generation(self):
        second_product = Product.objects.create(owner=self.user, name="روغن آفتابگردان با نام طولانی", brand="بهار", default_price=Decimal("75"), unit=Product.Unit.ITEM)
        for index in range(25):
            SalesOrderItem.objects.create(order=self.order, product=second_product, product_name_snapshot=f"روغن آفتابگردان شماره {index + 1}", brand_snapshot="بهار", unit_snapshot=second_product.get_unit_display(), quantity=Decimal("1"), unit_price=Decimal("75"))
        self.order.recalculate_total()
        self.authenticate(); invoice_id = self.issue().data["id"]
        response = self.client.get(f"{self.list_url}{invoice_id}/pdf/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.content), 1000)
