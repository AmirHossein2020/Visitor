from rest_framework import status
from rest_framework.test import APITestCase

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
