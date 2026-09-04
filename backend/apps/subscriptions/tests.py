from datetime import timedelta
from decimal import Decimal

from django.test import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.products.models import Product

from .models import PlatformAdminAuditLog, PlatformSettings, SubscriptionOrder, SubscriptionPayment, SubscriptionPlan, UserSubscription


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

    def test_eligible_user_activates_exactly_one_24_hour_trial_with_access_and_audit(self):
        self.authenticate()
        before = timezone.now()
        response = self.client.post("/api/subscriptions/trial/activate/")
        self.assertEqual(response.status_code, 201)
        subscription = UserSubscription.objects.get(user=self.user)
        self.assertEqual(subscription.source, UserSubscription.Source.FREE_TRIAL)
        self.assertEqual(subscription.expires_at - subscription.starts_at, timedelta(hours=24))
        self.assertGreaterEqual(subscription.starts_at, before)
        self.assertEqual(self.client.get("/api/products/").status_code, 200)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.trial_used_at)
        self.assertTrue(PlatformAdminAuditLog.objects.filter(action="free_trial_activated", target_id=str(subscription.id)).exists())
        self.assertFalse(SubscriptionOrder.objects.filter(user=self.user).exists())
        self.assertFalse(SubscriptionPayment.objects.filter(user=self.user).exists())
        self.assertEqual(self.client.post("/api/subscriptions/trial/activate/").status_code, 400)

    def test_expired_or_cancelled_trial_never_restores_eligibility(self):
        self.authenticate()
        self.client.post("/api/subscriptions/trial/activate/")
        subscription = UserSubscription.objects.get(user=self.user)
        subscription.status = UserSubscription.Status.CANCELLED
        subscription.save(update_fields=("status",))
        self.assertEqual(self.client.post("/api/subscriptions/trial/activate/").status_code, 400)
        self.assertFalse(self.client.get("/api/subscriptions/me/").data["trial_eligible"])

    def test_active_and_previously_paid_users_are_not_trial_eligible(self):
        self.activate()
        self.authenticate()
        self.assertEqual(self.client.post("/api/subscriptions/trial/activate/").status_code, 400)
        UserSubscription.objects.all().delete()
        SubscriptionOrder.objects.create(user=self.user, plan=self.monthly, amount_snapshot=self.monthly.price, status=SubscriptionOrder.Status.APPROVED)
        self.assertEqual(self.client.post("/api/subscriptions/trial/activate/").status_code, 400)
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


@override_settings(SUBSCRIPTION_TEST_BYPASS=False)
class PlatformAdminAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(email="platform@example.com", full_name="مدیر پلتفرم", password="StrongPass!2026")
        self.user = User.objects.create_user(email="customer@example.com", full_name="مشتری", password="StrongPass!2026")
        self.other = User.objects.create_user(email="another@example.com", full_name="کاربر دیگر", password="StrongPass!2026")
        self.plan = SubscriptionPlan.objects.create(name="پلن مدیریت", slug="admin-plan", billing_period="monthly", duration_days=30, price=Decimal("990000"), sort_order=20)

    def auth_admin(self):
        self.client.force_authenticate(self.admin)

    def test_admin_allowed_normal_user_forbidden_and_anonymous_rejected(self):
        self.assertEqual(self.client.get("/api/platform-admin/dashboard/").status_code, 401)
        self.client.force_authenticate(self.user)
        for url in ("/api/platform-admin/users/", "/api/platform-admin/plans/"):
            self.assertEqual(self.client.get(url).status_code, 403)
        self.auth_admin()
        self.assertEqual(self.client.get("/api/platform-admin/dashboard/").status_code, 200)

    def test_staff_without_subscription_can_access_platform_admin(self):
        staff = User.objects.create_user(email="staff-only@example.com", full_name="مدیر کارکنان", password="StrongPass!2026", is_staff=True)
        self.client.force_authenticate(staff)
        self.assertFalse(UserSubscription.objects.filter(user=staff).exists())
        self.assertEqual(self.client.get("/api/platform-admin/dashboard/").status_code, 200)
        self.assertTrue(self.client.get("/api/subscriptions/me/").data["is_active"])

    def test_user_list_detail_search_filter_pagination_and_account_toggle(self):
        self.auth_admin()
        response = self.client.get("/api/platform-admin/users/?search=customer&page_size=1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertIn("count", response.data)
        detail = self.client.get(f"/api/platform-admin/users/{self.user.id}/")
        self.assertEqual(detail.data["email"], self.user.email)
        self.assertNotIn("password", detail.data)
        self.assertEqual(self.client.patch(f"/api/platform-admin/users/{self.user.id}/", {"is_active": False, "email": "hacker@example.com"}, format="json").status_code, 200)
        self.user.refresh_from_db(); self.assertFalse(self.user.is_active); self.assertEqual(self.user.email, "customer@example.com")
        self.client.patch(f"/api/platform-admin/users/{self.user.id}/", {"is_active": True}, format="json")
        self.user.refresh_from_db(); self.assertTrue(self.user.is_active)

    def test_pending_order_approval_is_audited_and_duplicate_rejected(self):
        order = SubscriptionOrder.objects.create(user=self.user, plan=self.plan, amount_snapshot=self.plan.price)
        self.auth_admin()
        listed = self.client.get("/api/platform-admin/subscription-orders/?status=pending")
        self.assertEqual([row["id"] for row in listed.data["results"]], [order.id])
        response = self.client.post(f"/api/platform-admin/subscription-orders/{order.id}/approve/")
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db(); self.assertEqual(order.approved_by, self.admin); self.assertIsNotNone(order.approved_at)
        self.assertEqual(self.client.post(f"/api/platform-admin/subscription-orders/{order.id}/approve/").status_code, 400)
        self.assertTrue(UserSubscription.objects.filter(user=self.user, status="active").exists())

    def test_rejection_records_reviewer_and_timestamp(self):
        order = SubscriptionOrder.objects.create(user=self.user, plan=self.plan, amount_snapshot=self.plan.price)
        self.auth_admin()
        self.assertEqual(self.client.post(f"/api/platform-admin/subscription-orders/{order.id}/reject/", {"notes": "پرداخت تأیید نشد"}, format="json").status_code, 200)
        order.refresh_from_db(); self.assertEqual(order.status, "rejected"); self.assertEqual(order.approved_by, self.admin); self.assertIsNotNone(order.approved_at)

    def test_manual_activation_extension_and_cancellation(self):
        self.auth_admin()
        activated = self.client.post(f"/api/platform-admin/users/{self.user.id}/subscriptions/activate/", {"plan_id": self.plan.id}, format="json")
        self.assertEqual(activated.status_code, 201)
        subscription = UserSubscription.objects.get(pk=activated.data["id"]); old_expiry = subscription.expires_at
        extended = self.client.post(f"/api/platform-admin/subscriptions/{subscription.id}/extend/", {"plan_id": self.plan.id}, format="json")
        self.assertEqual(extended.status_code, 200)
        subscription.refresh_from_db(); self.assertGreater(subscription.expires_at, old_expiry); self.assertEqual(subscription.approved_by, self.admin)
        self.assertEqual(self.client.post(f"/api/platform-admin/subscriptions/{subscription.id}/cancel/").status_code, 200)
        subscription.refresh_from_db(); self.assertEqual(subscription.status, "cancelled")

    def test_plan_create_update_deactivate_preserves_order_snapshot(self):
        order = SubscriptionOrder.objects.create(user=self.user, plan=self.plan, amount_snapshot=self.plan.price)
        self.auth_admin()
        created = self.client.post("/api/platform-admin/plans/", {"name": "سالانه جدید", "slug": "new-yearly", "billing_period": "yearly", "duration_days": 365, "price": "1200000", "description": "پلن جدید", "sort_order": 30}, format="json")
        self.assertEqual(created.status_code, 201)
        self.assertEqual(self.client.patch(f"/api/platform-admin/plans/{self.plan.id}/", {"price": "1200000", "is_active": False}, format="json").status_code, 200)
        order.refresh_from_db(); self.assertEqual(order.amount_snapshot, Decimal("990000"))
        self.plan.refresh_from_db(); self.assertFalse(self.plan.is_active)

    def test_customer_cannot_call_admin_actions(self):
        order = SubscriptionOrder.objects.create(user=self.user, plan=self.plan, amount_snapshot=self.plan.price)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post(f"/api/platform-admin/subscription-orders/{order.id}/approve/").status_code, 403)
        self.assertEqual(self.client.patch(f"/api/platform-admin/plans/{self.plan.id}/", {"is_active": False}, format="json").status_code, 403)
        self.assertEqual(self.client.patch(f"/api/platform-admin/users/{self.other.id}/", {"is_active": False}, format="json").status_code, 403)

    def submit_payment(self, order, **extra):
        payload = {"tracking_code": "TRACK-123", "amount_snapshot": "1", **extra}
        return self.client.post(f"/api/subscriptions/orders/{order.id}/payments/", payload, format="multipart")

    def test_manual_payment_snapshot_ownership_and_validation(self):
        order = SubscriptionOrder.objects.create(user=self.user, plan=self.plan, amount_snapshot=self.plan.price)
        other_order = SubscriptionOrder.objects.create(user=self.other, plan=self.plan, amount_snapshot=self.plan.price)
        self.client.force_authenticate(self.user)
        response = self.submit_payment(order)
        self.assertEqual(response.status_code, 201)
        payment = SubscriptionPayment.objects.get(pk=response.data["id"])
        self.assertEqual(payment.amount_snapshot, self.plan.price)
        self.assertEqual(payment.status, "pending_review")
        self.assertEqual(self.submit_payment(other_order).status_code, 404)
        empty_order = SubscriptionOrder.objects.create(user=self.user, plan=self.plan, amount_snapshot=self.plan.price)
        self.assertEqual(self.client.post(f"/api/subscriptions/orders/{empty_order.id}/payments/", {}, format="multipart").status_code, 400)

    def test_receipt_type_and_size_are_validated(self):
        self.client.force_authenticate(self.user)
        order = SubscriptionOrder.objects.create(user=self.user, plan=self.plan, amount_snapshot=self.plan.price)
        bad = SimpleUploadedFile("receipt.txt", b"not-an-image", content_type="text/plain")
        self.assertEqual(self.submit_payment(order, receipt_image=bad).status_code, 400)
        large_order = SubscriptionOrder.objects.create(user=self.user, plan=self.plan, amount_snapshot=self.plan.price)
        large = SimpleUploadedFile("receipt.png", b"\x89PNG\r\n\x1a\n" + b"0" * 30, content_type="image/png")
        with override_settings(MAX_RECEIPT_UPLOAD_BYTES=20):
            self.assertEqual(self.submit_payment(large_order, receipt_image=large).status_code, 400)

    def test_admin_payment_approval_activates_access_and_is_not_repeatable(self):
        order = SubscriptionOrder.objects.create(user=self.user, plan=self.plan, amount_snapshot=self.plan.price)
        self.client.force_authenticate(self.user)
        payment_id = self.submit_payment(order).data["id"]
        self.assertEqual(self.client.get("/api/products/").status_code, 403)
        self.auth_admin()
        self.assertEqual(self.client.get("/api/platform-admin/payments/?status=pending_review").status_code, 200)
        self.assertEqual(self.client.post(f"/api/platform-admin/payments/{payment_id}/approve/").status_code, 200)
        self.assertEqual(self.client.post(f"/api/platform-admin/payments/{payment_id}/approve/").status_code, 400)
        payment = SubscriptionPayment.objects.get(pk=payment_id)
        self.assertEqual(payment.reviewed_by, self.admin)
        self.assertIsNotNone(payment.reviewed_at)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get("/api/products/").status_code, 200)

    def test_rejection_keeps_history_and_allows_retry(self):
        order = SubscriptionOrder.objects.create(user=self.user, plan=self.plan, amount_snapshot=self.plan.price)
        self.client.force_authenticate(self.user)
        first = self.submit_payment(order).data["id"]
        self.auth_admin()
        self.assertEqual(self.client.post(f"/api/platform-admin/payments/{first}/reject/", {"admin_note": "رسید خوانا نیست"}, format="json").status_code, 200)
        self.client.force_authenticate(self.user)
        second = self.submit_payment(order, tracking_code="TRACK-456")
        self.assertEqual(second.status_code, 201)
        history = self.client.get(f"/api/subscriptions/orders/{order.id}/payments/")
        self.assertEqual(len(history.data), 2)
        self.assertEqual(SubscriptionPayment.objects.get(pk=first).admin_note, "رسید خوانا نیست")

    def test_payment_admin_security_and_private_receipt(self):
        order = SubscriptionOrder.objects.create(user=self.user, plan=self.plan, amount_snapshot=self.plan.price)
        receipt = SimpleUploadedFile("receipt.png", b"\x89PNG\r\n\x1a\ncontent", content_type="image/png")
        self.client.force_authenticate(self.user)
        payment_id = self.submit_payment(order, receipt_image=receipt).data["id"]
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(f"/api/subscriptions/payments/{payment_id}/receipt/").status_code, 404)
        self.assertEqual(self.client.post(f"/api/platform-admin/payments/{payment_id}/approve/").status_code, 403)
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(f"/api/subscriptions/payments/{payment_id}/receipt/").status_code, 401)
        self.auth_admin()
        self.assertEqual(self.client.get(f"/api/subscriptions/payments/{payment_id}/receipt/").status_code, 200)

    def test_custom_admin_action_center_payment_acceptance_flow(self):
        order = SubscriptionOrder.objects.create(user=self.user, plan=self.plan, amount_snapshot=self.plan.price)
        self.client.force_authenticate(self.user)
        payment = self.submit_payment(order)
        self.assertEqual(payment.status_code, 201)
        self.auth_admin()
        dashboard = self.client.get("/api/platform-admin/dashboard/")
        self.assertEqual(dashboard.data["pending_payment_reviews"], 1)
        pending = self.client.get("/api/platform-admin/payments/?status=pending_review")
        self.assertEqual([row["id"] for row in pending.data["results"]], [payment.data["id"]])
        detail = self.client.get(f"/api/platform-admin/subscription-orders/{order.id}/")
        self.assertEqual(detail.data["latest_payment"]["status"], "pending_review")
        self.assertEqual(self.client.post(f"/api/platform-admin/payments/{payment.data['id']}/approve/").status_code, 200)
        self.assertEqual(self.client.get("/api/platform-admin/dashboard/").data["pending_payment_reviews"], 0)
        order.refresh_from_db()
        self.assertEqual(order.status, "approved")
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get("/api/products/").status_code, 200)

    def test_superuser_role_management_and_audit(self):
        self.auth_admin()
        grant_staff = self.client.post(f"/api/platform-admin/users/{self.user.id}/grant-staff/")
        self.assertEqual(grant_staff.status_code, 200)
        self.user.refresh_from_db(); self.assertTrue(self.user.is_staff)
        self.assertEqual(self.client.post(f"/api/platform-admin/users/{self.user.id}/revoke-staff/").status_code, 200)
        self.assertEqual(self.client.post(f"/api/platform-admin/users/{self.user.id}/grant-superuser/", {"reason": "نیاز عملیاتی"}, format="json").status_code, 200)
        self.user.refresh_from_db(); self.assertTrue(self.user.is_superuser); self.assertTrue(self.user.is_staff)
        self.assertEqual(self.client.post(f"/api/platform-admin/users/{self.user.id}/revoke-superuser/").status_code, 200)
        self.assertGreaterEqual(PlatformAdminAuditLog.objects.filter(action="role_changed", target_id=str(self.user.id)).count(), 4)

    def test_staff_cannot_manage_superuser_or_escalate_self(self):
        staff = User.objects.create_user(email="operator@example.com", full_name="اپراتور", password="StrongPass!2026", is_staff=True)
        self.client.force_authenticate(staff)
        self.assertEqual(self.client.post(f"/api/platform-admin/users/{staff.id}/grant-superuser/").status_code, 403)
        self.assertEqual(self.client.post(f"/api/platform-admin/users/{self.admin.id}/revoke-superuser/").status_code, 403)
        self.assertEqual(self.client.patch(f"/api/platform-admin/users/{self.admin.id}/", {"is_active": False}, format="json").status_code, 400)

    def test_last_active_superuser_is_protected(self):
        self.auth_admin()
        self.assertEqual(self.client.post(f"/api/platform-admin/users/{self.admin.id}/revoke-superuser/").status_code, 400)
        self.assertEqual(self.client.patch(f"/api/platform-admin/users/{self.admin.id}/", {"is_active": False}, format="json").status_code, 400)
        self.admin.refresh_from_db(); self.assertTrue(self.admin.is_superuser); self.assertTrue(self.admin.is_active)

    def test_subscription_adjustment_permissions_validity_and_audit(self):
        now = timezone.now()
        subscription = UserSubscription.objects.create(user=self.user, plan=self.plan, status="active", starts_at=now, expires_at=now + timedelta(days=30))
        original = subscription.expires_at
        self.auth_admin()
        response = self.client.post(f"/api/platform-admin/subscriptions/{subscription.id}/adjust/", {"days": 7, "reason": "پشتیبانی"}, format="json")
        self.assertEqual(response.status_code, 200)
        subscription.refresh_from_db(); self.assertEqual(subscription.expires_at, original + timedelta(days=7))
        self.assertTrue(PlatformAdminAuditLog.objects.filter(action="subscription_adjusted", target_id=str(subscription.id)).exists())
        staff = User.objects.create_user(email="adjust-staff@example.com", full_name="مدیر", password="StrongPass!2026", is_staff=True)
        self.client.force_authenticate(staff)
        self.assertEqual(self.client.post(f"/api/platform-admin/subscriptions/{subscription.id}/adjust/", {"days": 7, "reason": "x"}, format="json").status_code, 403)

    def test_safe_platform_settings_and_secrets_not_exposed(self):
        self.auth_admin()
        response = self.client.patch("/api/platform-admin/settings/", {"site_name": "سامانه فروش", "card_number": "1234", "manual_payment_enabled": False, "SECRET_KEY": "leak"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["site_name"], "سامانه فروش")
        self.assertNotIn("SECRET_KEY", response.data); self.assertNotIn("database_password", response.data)
        self.assertTrue(PlatformSettings.objects.filter(pk=1).exists())
        self.assertTrue(PlatformAdminAuditLog.objects.filter(action="platform_settings_updated").exists())
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get("/api/platform-admin/settings/").status_code, 403)

    def test_plan_price_change_preserves_order_and_payment_snapshots(self):
        order = SubscriptionOrder.objects.create(user=self.user, plan=self.plan, amount_snapshot=self.plan.price)
        payment = SubscriptionPayment.objects.create(user=self.user, subscription_order=order, amount_snapshot=order.amount_snapshot, tracking_code="immutable")
        self.auth_admin()
        self.assertEqual(self.client.patch(f"/api/platform-admin/plans/{self.plan.id}/", {"price": "2500000", "duration_days": 45, "is_active": False}, format="json").status_code, 200)
        order.refresh_from_db(); payment.refresh_from_db()
        self.assertEqual(order.amount_snapshot, Decimal("990000")); self.assertEqual(payment.amount_snapshot, Decimal("990000"))
        self.assertTrue(PlatformAdminAuditLog.objects.filter(action="plan_updated", target_id=str(self.plan.id)).exists())

    def test_discount_is_authoritative_and_order_snapshots_are_immutable(self):
        self.plan.discount_percent = 20
        self.plan.save(update_fields=("discount_percent",))
        self.client.force_authenticate(self.user)
        response = self.client.post("/api/subscriptions/orders/", {"plan_id": self.plan.id}, format="json")
        self.assertEqual(response.status_code, 201)
        order = SubscriptionOrder.objects.get(pk=response.data["id"])
        self.assertEqual(order.original_price_snapshot, Decimal("990000"))
        self.assertEqual(order.discount_percent_snapshot, 20)
        self.assertEqual(order.amount_snapshot, Decimal("792000"))
        self.plan.price = Decimal("2000000")
        self.plan.discount_percent = 0
        self.plan.save(update_fields=("price", "discount_percent"))
        order.refresh_from_db()
        self.assertEqual(order.amount_snapshot, Decimal("792000"))

    def test_payment_approval_completes_related_order_transactionally(self):
        order = SubscriptionOrder.objects.create(user=self.user, plan=self.plan, amount_snapshot=self.plan.price)
        self.client.force_authenticate(self.user)
        payment_id = self.submit_payment(order).data["id"]
        self.auth_admin()
        self.assertEqual(self.client.post(f"/api/platform-admin/payments/{payment_id}/approve/").status_code, 200)
        order.refresh_from_db()
        payment = SubscriptionPayment.objects.get(pk=payment_id)
        self.assertEqual(payment.status, SubscriptionPayment.Status.APPROVED)
        self.assertEqual(order.status, SubscriptionOrder.Status.APPROVED)
        self.assertTrue(UserSubscription.objects.filter(user=self.user, status=UserSubscription.Status.ACTIVE).exists())

    def test_plan_safe_delete_hard_deletes_unused_and_archives_referenced(self):
        unused = SubscriptionPlan.objects.create(name="Unused", slug="unused", billing_period="monthly", duration_days=1, price=1)
        SubscriptionOrder.objects.create(user=self.user, plan=self.plan, amount_snapshot=self.plan.price)
        self.auth_admin()
        self.assertEqual(self.client.delete(f"/api/platform-admin/plans/{unused.id}/").status_code, 204)
        archived = self.client.delete(f"/api/platform-admin/plans/{self.plan.id}/")
        self.assertEqual(archived.status_code, 200)
        self.plan.refresh_from_db()
        self.assertFalse(self.plan.is_active)
        self.assertTrue(PlatformAdminAuditLog.objects.filter(action="plan_archived", target_id=str(self.plan.id)).exists())
