from rest_framework import status
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image, ImageDraw

from apps.accounts.models import User
from apps.customers.models import Customer
from apps.orders.models import SalesOrder, SalesOrderItem
from apps.products.models import Product
from apps.purchases.models import Purchase, PurchaseItem

from .models import SellerProfile


class SellerProfileAPITests(APITestCase):
    list_url = "/api/companies/"
    payload = {
        "name": "شرکت سپید",
        "phone_number": "021-88776655",
        "address": "تهران",
        "economic_code": "123456789",
        "national_id": "10101010101",
        "registration_number": "4567",
        "postal_code": "1234567890",
        "description": "",
    }

    def setUp(self):
        self.user = User.objects.create_user(email="owner@example.com", full_name="ویزیتور اول", password="StrongPass!2026")
        self.other_user = User.objects.create_user(email="other@example.com", full_name="ویزیتور دوم", password="StrongPass!2026")

    def authenticate(self):
        self.client.force_authenticate(self.user)

    def create_profile(self, owner=None, **overrides):
        data = {"name": "شرکت سپید", **overrides}
        return SellerProfile.objects.create(owner=owner or self.user, **data)

    @staticmethod
    def image(name="asset.png", size=(120, 80)):
        source = Image.new("RGB", size, "white")
        ImageDraw.Draw(source).ellipse((30, 15, 90, 65), outline=(0, 90, 180), width=4)
        output = BytesIO(); source.save(output, format="PNG")
        return SimpleUploadedFile(name, output.getvalue(), content_type="image/png")

    def test_create_own_seller_profile(self):
        self.authenticate()
        response = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SellerProfile.objects.get().owner, self.user)

    def test_create_profile_with_only_name(self):
        self.authenticate()
        response = self.client.post(self.list_url, {"name": "فروشنده مستقل"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["phone_number"], "")

    def test_persian_phone_digits_are_normalized(self):
        self.authenticate()
        response = self.client.post(self.list_url, {"name": "فروشنده", "phone_number": "۰۲۱-۸۸۷۷۶۶۵۵"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["phone_number"], "021-88776655")

    def test_list_only_own_profiles(self):
        own = self.create_profile()
        self.create_profile(owner=self.other_user)
        self.authenticate()
        response = self.client.get(self.list_url)
        self.assertEqual([item["id"] for item in response.data], [own.id])

    def test_retrieve_own_profile(self):
        profile = self.create_profile(); self.authenticate()
        response = self.client.get(f"{self.list_url}{profile.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_own_profile(self):
        profile = self.create_profile(); self.authenticate()
        response = self.client.patch(f"{self.list_url}{profile.id}/", {"name": "نام جدید"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profile.refresh_from_db()
        self.assertEqual(profile.name, "نام جدید")

    def test_deactivate_own_profile(self):
        profile = self.create_profile(); self.authenticate()
        self.assertEqual(self.client.delete(f"{self.list_url}{profile.id}/").status_code, status.HTTP_204_NO_CONTENT)
        profile.refresh_from_db()
        self.assertFalse(profile.is_active)

    def test_unauthenticated_access_rejected(self):
        self.assertEqual(self.client.get(self.list_url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_another_visitor_cannot_access_profile(self):
        profile = self.create_profile(owner=self.other_user); self.authenticate()
        url = f"{self.list_url}{profile.id}/"
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.patch(url, {"name": "تغییر"}, format="json").status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_404_NOT_FOUND)

    def test_search_works(self):
        expected = self.create_profile(economic_code="778899")
        self.create_profile(name="فروشنده دیگر", economic_code="112233")
        self.authenticate()
        response = self.client.get(self.list_url, {"search": "778899"})
        self.assertEqual([item["id"] for item in response.data], [expected.id])

    def test_no_business_entity_references_seller_profile(self):
        for model in (Product, Customer, SalesOrder, SalesOrderItem, Purchase, PurchaseItem):
            with self.subTest(model=model.__name__):
                references = [
                    field for field in model._meta.get_fields()
                    if getattr(getattr(field, "remote_field", None), "model", None) is SellerProfile
                ]
                self.assertEqual(references, [])

    def test_optional_stamp_signature_upload_preview_replace_and_remove(self):
        profile = self.create_profile(); self.authenticate()
        response = self.client.patch(f"{self.list_url}{profile.id}/", {"stamp_image": self.image(), "signature_image": self.image("signature.png")}, format="multipart")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["has_stamp"]); self.assertTrue(response.data["has_signature"])
        profile.refresh_from_db()
        self.assertTrue(profile.stamp_image.name.endswith(".png"))
        profile.stamp_image.open("rb")
        processed = Image.open(profile.stamp_image)
        self.assertEqual(processed.format, "PNG")
        self.assertEqual(processed.mode, "RGBA")
        self.assertLess(processed.width, 120)
        self.assertLess(processed.height, 80)
        profile.stamp_image.close()
        self.assertEqual(self.client.get(f"{self.list_url}{profile.id}/stamp/").status_code, 200)
        self.assertEqual(self.client.patch(f"{self.list_url}{profile.id}/", {"stamp_image": self.image("replacement.png")}, format="multipart").status_code, 200)
        self.assertEqual(self.client.delete(f"{self.list_url}{profile.id}/stamp/").status_code, 204)
        profile.refresh_from_db(); self.assertFalse(profile.stamp_image); self.assertTrue(profile.signature_image)

    def test_asset_validation_and_owner_isolation(self):
        profile = self.create_profile(); self.authenticate()
        invalid = SimpleUploadedFile("asset.svg", b"<svg><script/></svg>", content_type="image/svg+xml")
        self.assertEqual(self.client.patch(f"{self.list_url}{profile.id}/", {"stamp_image": invalid}, format="multipart").status_code, 400)
        oversized = SimpleUploadedFile("large.png", b"\x89PNG\r\n\x1a\n" + b"0" * (3 * 1024 * 1024 + 1), content_type="image/png")
        self.assertEqual(self.client.patch(f"{self.list_url}{profile.id}/", {"stamp_image": oversized}, format="multipart").status_code, 400)
        self.client.force_authenticate(self.other_user)
        self.assertEqual(self.client.get(f"{self.list_url}{profile.id}/signature/").status_code, 404)
