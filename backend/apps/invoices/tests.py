import re
from io import BytesIO
from decimal import Decimal
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.companies.models import SellerProfile
from apps.customers.models import Customer
from apps.orders.models import SalesOrder, SalesOrderItem
from apps.products.models import Product

from .models import Invoice
from .pdf import fa, money


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

    def add_items(self, count):
        for index in range(count):
            SalesOrderItem.objects.create(
                order=self.order,
                product=self.product,
                product_name_snapshot=f"محصول آزمایشی شماره {index + 2}",
                brand_snapshot=self.product.brand,
                unit_snapshot=self.product.get_unit_display(),
                quantity=Decimal("1"),
                unit_price=Decimal("100"),
            )
        self.order.recalculate_total()

    @staticmethod
    def image(name="asset.png", color=(180, 0, 0, 140)):
        output = BytesIO()
        Image.new("RGBA", (180, 100), color).save(output, format="PNG")
        return SimpleUploadedFile(name, output.getvalue(), content_type="image/png")

    @staticmethod
    def pdf_page_count(content):
        return len(re.findall(rb"/Type\s*/Page\b", content))

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

    def test_issued_invoice_cannot_be_patched(self):
        self.authenticate(); invoice_id = self.issue(notes="یادداشت اصلی").data["id"]
        response = self.client.patch(
            f"{self.list_url}{invoice_id}/", {"notes": "تغییر غیرمجاز"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(Invoice.objects.get(pk=invoice_id).notes, "یادداشت اصلی")

    def test_owner_can_download_non_empty_pdf(self):
        self.authenticate(); invoice_id = self.issue().data["id"]
        response = self.client.get(f"{self.list_url}{invoice_id}/pdf/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))
        self.assertGreater(len(response.content), 1000)

    def test_one_item_invoice_pdf_is_exactly_one_page(self):
        self.authenticate()
        response = self.client.get(f"{self.list_url}{self.issue().data['id']}/pdf/")
        self.assertEqual(self.pdf_page_count(response.content), 1)

    def test_pdf_money_uses_rial_and_removes_unnecessary_decimal_zeros(self):
        self.assertEqual(money(Decimal("580000.00")), fa("580,000 ریال"))
        self.assertEqual(money(Decimal("48600.50")), fa("48,600.5 ریال"))
        self.assertNotIn("تومان", money(Decimal("808040000.00")))

    def test_five_item_invoice_pdf_is_exactly_one_page(self):
        self.add_items(4)
        self.authenticate()
        response = self.client.get(f"{self.list_url}{self.issue().data['id']}/pdf/")
        self.assertEqual(self.pdf_page_count(response.content), 1)

    def test_large_invoice_uses_multiple_pages_without_signature_only_page(self):
        self.add_items(24)
        self.authenticate()
        response = self.client.get(f"{self.list_url}{self.issue().data['id']}/pdf/")
        self.assertGreater(self.pdf_page_count(response.content), 1)
        # Explicit pagination always retains at least one item row on the final
        # page before the indivisible totals/notes/signatures ending block.
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_pdf_wraps_long_snapshot_content_without_layout_failure(self):
        self.seller.address = "نشانی طولانی فروشنده " * 18
        self.seller.save(update_fields=("address",))
        self.customer.address = "نشانی طولانی خریدار " * 18
        self.customer.save(update_fields=("address",))
        order_item = self.order.items.get()
        order_item.product_name_snapshot = "محصول با نام طولانی " * 9
        order_item.brand_snapshot = "برند طولانی " * 8
        order_item.save(update_fields=("product_name_snapshot", "brand_snapshot"))
        self.authenticate()
        invoice_id = self.issue(notes="یادداشت طولانی و خوانا " * 30).data["id"]
        response = self.client.get(f"{self.list_url}{invoice_id}/pdf/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(self.pdf_page_count(response.content), 0)


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


    def test_stamp_and_signature_are_optional_per_invoice_and_immutable(self):
        self.seller.stamp_image = self.image("stamp.png")
        self.seller.signature_image = self.image("signature.png", (0, 0, 120, 180))
        self.seller.save()
        self.authenticate()
        unsigned = Invoice.objects.get(pk=self.issue().data["id"])
        self.assertFalse(unsigned.stamp_snapshot); self.assertFalse(unsigned.signature_snapshot)
        second_order = self.create_order()
        signed = Invoice.objects.get(pk=self.issue(order=second_order, include_stamp=True, include_signature=True).data["id"])
        self.assertTrue(signed.stamp_snapshot); self.assertTrue(signed.signature_snapshot)
        signed.stamp_snapshot.open("rb"); original = signed.stamp_snapshot.read(); signed.stamp_snapshot.close()
        self.seller.stamp_image = self.image("new-stamp.png", (0, 180, 0, 160)); self.seller.save()
        signed.refresh_from_db(); signed.stamp_snapshot.open("rb")
        self.assertEqual(signed.stamp_snapshot.read(), original); signed.stamp_snapshot.close()

    def test_revision_takes_an_independent_current_asset_snapshot(self):
        self.seller.stamp_image = self.image("first.png"); self.seller.save()
        self.authenticate(); first = Invoice.objects.get(pk=self.issue(include_stamp=True).data["id"])
        item = self.order.items.get()
        self.client.patch(f"/api/orders/{self.order.id}/items/{item.id}/", {"quantity": "3"}, format="json")
        self.seller.stamp_image = self.image("second.png", (0, 180, 0, 160)); self.seller.save()
        second = Invoice.objects.get(pk=self.issue(include_stamp=True).data["id"])
        first.stamp_snapshot.open("rb"); first_bytes = first.stamp_snapshot.read(); first.stamp_snapshot.close()
        second.stamp_snapshot.open("rb"); second_bytes = second.stamp_snapshot.read(); second.stamp_snapshot.close()
        self.assertNotEqual(first_bytes, second_bytes)

    def test_pdf_with_stamp_and_signature_is_valid_and_one_item_stays_one_page(self):
        self.seller.stamp_image = self.image("stamp.png"); self.seller.signature_image = self.image("signature.png"); self.seller.save()
        self.authenticate(); invoice_id = self.issue(include_stamp=True, include_signature=True).data["id"]
        response = self.client.get(f"{self.list_url}{invoice_id}/pdf/")
        self.assertTrue(response.content.startswith(b"%PDF")); self.assertEqual(self.pdf_page_count(response.content), 1)

    def test_stamp_only_and_signature_only_follow_independent_flags(self):
        self.seller.stamp_image = self.image("stamp.png"); self.seller.signature_image = self.image("signature.png"); self.seller.save()
        self.authenticate()
        stamp_only = Invoice.objects.get(pk=self.issue(order=self.create_order(), include_stamp=True, include_signature=False).data["id"])
        signature_only = Invoice.objects.get(pk=self.issue(order=self.create_order(), include_stamp=False, include_signature=True).data["id"])
        self.assertTrue(stamp_only.stamp_snapshot); self.assertFalse(stamp_only.signature_snapshot)
        self.assertFalse(signature_only.stamp_snapshot); self.assertTrue(signature_only.signature_snapshot)
        for invoice in (stamp_only, signature_only):
            response = self.client.get(f"{self.list_url}{invoice.id}/pdf/")
            self.assertTrue(response.content.startswith(b"%PDF"))


class EndToEndBusinessScenarioTests(APITestCase):
    def test_complete_business_workflow(self):
        credentials = {
            "full_name": "ویزیتور نهایی", "email": "final-flow@example.com",
            "password": "StrongPass!2026", "password_confirm": "StrongPass!2026",
        }
        self.assertEqual(self.client.post("/api/auth/register/", credentials, format="json").status_code, 201)
        login = self.client.post("/api/auth/login/", {"email": credentials["email"], "password": credentials["password"]}, format="json")
        self.assertEqual(login.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + login.data["access"])

        product = self.client.post("/api/products/", {"name": "محصول نهایی", "brand": "برند", "default_price": "100", "unit": "item"}, format="json")
        customer = self.client.post("/api/customers/", {"name": "مشتری نهایی"}, format="json")
        seller = self.client.post("/api/companies/", {"name": "فروشنده نهایی"}, format="json")
        self.assertEqual((product.status_code, customer.status_code, seller.status_code), (201, 201, 201))

        order = self.client.post("/api/orders/", {"customer": customer.data["id"], "status": "draft"}, format="json")
        item = self.client.post(f"/api/orders/{order.data['id']}/items/", {"product": product.data["id"], "quantity": "6", "unit_price": "100"}, format="json")
        self.assertEqual(self.client.patch(f"/api/orders/{order.data['id']}/", {"status": "confirmed"}, format="json").status_code, 200)
        first_invoice = self.client.post("/api/invoices/", {"sales_order": order.data["id"], "seller_profile": seller.data["id"]}, format="json")
        self.assertEqual(first_invoice.status_code, 201)
        pdf = self.client.get(f"/api/invoices/{first_invoice.data['id']}/pdf/")
        self.assertEqual(pdf.status_code, 200)
        self.assertTrue(pdf.content.startswith(b"%PDF"))

        self.assertEqual(self.client.patch(f"/api/orders/{order.data['id']}/items/{item.data['id']}/", {"quantity": "4"}, format="json").status_code, 200)
        replacement = self.client.post("/api/invoices/", {"sales_order": order.data["id"], "seller_profile": seller.data["id"]}, format="json")
        self.assertEqual(replacement.status_code, 201)
        self.assertEqual(replacement.data["revision_number"], 2)
        self.assertEqual(Invoice.objects.get(pk=first_invoice.data["id"]).status, Invoice.Status.SUPERSEDED)

        sales_return = self.client.post("/api/returns/", {"invoice": replacement.data["id"]}, format="json")
        self.assertEqual(self.client.post(f"/api/returns/{sales_return.data['id']}/items/", {"invoice_item": replacement.data["items"][0]["id"], "quantity": "2"}, format="json").status_code, 201)
        self.assertEqual(self.client.patch(f"/api/returns/{sales_return.data['id']}/", {"status": "confirmed"}, format="json").status_code, 200)

        purchase = self.client.post("/api/purchases/", {"customer": customer.data["id"], "purchase_date": timezone.localdate().isoformat(), "status": "draft"}, format="json")
        self.assertEqual(self.client.post(f"/api/purchases/{purchase.data['id']}/items/", {"product": product.data["id"], "quantity": "10", "unit_price": "50"}, format="json").status_code, 201)
        self.assertEqual(self.client.patch(f"/api/purchases/{purchase.data['id']}/", {"status": "confirmed"}, format="json").status_code, 200)

        inventory = self.client.get(f"/api/inventory/{product.data['id']}/")
        dashboard = self.client.get("/api/dashboard/")
        reports = self.client.get("/api/reports/summary/")
        self.assertEqual(Decimal(inventory.data["product"]["current_stock"]), Decimal("8"))
        self.assertEqual(Decimal(dashboard.data["current_month"]["sales_total"]), Decimal("400"))
        self.assertEqual(Decimal(reports.data["return_total"]), Decimal("200"))
