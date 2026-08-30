from datetime import timedelta
from decimal import Decimal

from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.products.models import Product

from .models import SubscriptionOrder, SubscriptionPlan, UserSubscription


@override_settings(SUBSCRIPTION_TEST_BYPASS=False)
class SubscriptionAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="subscriber@example.com", full_name="کاربر اشتراک", password="StrongPass!2026")
        self.other = User.objects.create_user(email="other-sub@example.com", full_name="کاربر دیگر", password="StrongPass!2026")
        self.admin = User.objects.create_superuser(email="admin@example.com", full_name="مدیر", password="StrongPass!2026")
        self.monthly = SubscriptionPlan.objects.create(name="ماهانه تست", slug="monthly-test", billing_period="monthly", duration_days=30, price=Decimal("580000.00"), sort_order=10)
        self.yearly = SubscriptionPlan.objects.create(name="سالانه تست", slug="yearly-test", billing_period="yearly", duration_days=365, price=Decimal("5800000.00"), sort_order=11)

    def authenticate(self, user=None):
        self.client.force_authenticate(user or self.user)

    def activate(self, user=None, status="active", expires_delta=timedelta(days=30)):
        now = timezone.now()
        return UserSubscription.objects.create(user=user or self.user, plan=self.monthly, status=status, starts_at=now, expires_at=now + expires_delta)

    def test_public_plan_list_hides_inactive_and_price_is_decimal(self):
        SubscriptionPlan.objects.create(name="مخفی", slug="hidden-test", billing_period="monthly", duration_days=30, price=1, is_active=False)
        response = self.client.get("/api/subscriptions/plans/")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("hidden-test", [item["slug"] for item in response.data])
        self.assertIsInstance(self.monthly.price, Decimal)

    def test_order_uses_server_price_snapshot_and_cannot_be_self_approved(self):
        self.authenticate()
        response = self.client.post("/api/subscriptions/orders/", {"plan_id": self.monthly.id, "amount_snapshot": "1", "status": "approved"}, format="json")
        self.assertEqual(response.status_code, 201)
        order = SubscriptionOrder.objects.get(pk=response.data["id"])
        self.assertEqual(order.amount_snapshot, Decimal("580000.00"))
        self.assertEqual(order.status, "pending")
        self.assertEqual(self.client.patch(f"/api/subscriptions/orders/{order.id}/", {"status": "approved"}, format="json").status_code, 405)

    def test_order_and_subscription_are_owner_scoped(self):
        order = SubscriptionOrder.objects.create(user=self.other, plan=self.monthly, amount_snapshot=self.monthly.price)
        self.activate(user=self.other)
        self.authenticate()
        self.assertEqual(self.client.get(f"/api/subscriptions/orders/{order.id}/").status_code, 404)
        me = self.client.get("/api/subscriptions/me/")
        self.assertFalse(me.data["is_active"])

    def test_missing_pending_cancelled_and_expired_subscriptions_block_business_api(self):
        self.authenticate()
        self.assertEqual(self.client.get("/api/products/").status_code, 403)
        for status in ("pending", "cancelled"):
            subscription = self.activate(status=status)
            self.assertEqual(self.client.get("/api/products/").status_code, 403)
            subscription.delete()
        self.activate(expires_delta=timedelta(seconds=-1))
        self.assertEqual(self.client.get("/api/products/").status_code, 403)

    def test_active_and_renewed_subscription_restore_business_access(self):
        self.authenticate()
        expired = self.activate(expires_delta=timedelta(seconds=-1))
        self.assertEqual(self.client.get("/api/products/").status_code, 403)
        expired.status = "cancelled"; expired.save(update_fields=("status",))
        self.activate()
        self.assertEqual(self.client.get("/api/products/").status_code, 200)

    def test_admin_bypass_login_register_and_subscription_endpoints_remain_available(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get("/api/products/").status_code, 200)
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.post("/api/auth/login/", {"email": self.user.email, "password": "StrongPass!2026"}, format="json").status_code, 200)
        self.assertEqual(self.client.post("/api/auth/register/", {"email": "new@example.com", "full_name": "کاربر جدید", "password": "StrongPass!2026", "password_confirm": "StrongPass!2026"}, format="json").status_code, 201)
        self.authenticate()
        self.assertEqual(self.client.get("/api/subscriptions/me/").status_code, 200)
        self.assertEqual(self.client.get("/api/subscriptions/orders/").status_code, 200)

    def test_approval_activates_subscription_and_preserves_business_data_after_expiration(self):
        product = Product.objects.create(owner=self.user, name="محصول محفوظ", default_price=100, unit="item")
        order = SubscriptionOrder.objects.create(user=self.user, plan=self.monthly, amount_snapshot=self.monthly.price)
        subscription = order.approve(self.admin)
        self.authenticate()
        self.assertEqual(self.client.get("/api/products/").status_code, 200)
        subscription.expires_at = timezone.now() - timedelta(seconds=1)
        subscription.save(update_fields=("expires_at",))
        self.assertEqual(self.client.get("/api/products/").status_code, 403)
        self.assertTrue(Product.objects.filter(pk=product.pk).exists())
