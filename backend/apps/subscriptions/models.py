from datetime import timedelta
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone


class SubscriptionPlan(models.Model):
    class BillingPeriod(models.TextChoices):
        MONTHLY = "monthly", "ماهانه"
        YEARLY = "yearly", "سالانه"

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    billing_period = models.CharField(max_length=10, choices=BillingPeriod.choices)
    duration_days = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=18, decimal_places=2)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    description = models.CharField(max_length=300, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("sort_order", "price")

    def __str__(self):
        return self.name


class UserSubscription(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "در انتظار تأیید"
        ACTIVE = "active", "فعال"
        EXPIRED = "expired", "منقضی شده"
        CANCELLED = "cancelled", "لغو شده"
        REJECTED = "rejected", "رد شده"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    starts_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_subscriptions")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [models.UniqueConstraint(fields=("user",), condition=Q(status="active"), name="one_active_subscription_per_user")]

    @property
    def is_effective(self):
        now = timezone.now()
        return self.status == self.Status.ACTIVE and self.starts_at and self.expires_at and self.starts_at <= now < self.expires_at

    @property
    def effective_status(self):
        if self.status == self.Status.ACTIVE and self.expires_at and timezone.now() >= self.expires_at:
            return self.Status.EXPIRED
        return self.status

    def __str__(self):
        return f"{self.user} - {self.plan}"


class SubscriptionOrder(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "در انتظار تأیید"
        APPROVED = "approved", "تأیید شده"
        REJECTED = "rejected", "رد شده"
        CANCELLED = "cancelled", "لغو شده"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscription_orders")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="orders")
    amount_snapshot = models.DecimalField(max_digits=18, decimal_places=2)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_subscription_orders")
    payment_reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    @transaction.atomic
    def approve(self, approved_by):
        locked = SubscriptionOrder.objects.select_for_update().select_related("plan", "user").get(pk=self.pk)
        if locked.status != self.Status.PENDING:
            raise ValueError("فقط درخواست در انتظار را می‌توان تأیید کرد.")
        now = timezone.now()
        UserSubscription.objects.filter(user=locked.user, status=UserSubscription.Status.ACTIVE).update(status=UserSubscription.Status.CANCELLED)
        subscription = UserSubscription.objects.create(
            user=locked.user, plan=locked.plan, status=UserSubscription.Status.ACTIVE,
            starts_at=now, expires_at=now + timedelta(days=locked.plan.duration_days),
            approved_at=now, approved_by=approved_by,
        )
        locked.status = self.Status.APPROVED
        locked.approved_at = now
        locked.approved_by = approved_by
        locked.save(update_fields=("status", "approved_at", "approved_by", "updated_at"))
        return subscription

    def __str__(self):
        return f"{self.user} - {self.plan} - {self.status}"


def receipt_upload_path(instance, filename):
    suffix = Path(filename).suffix.lower()
    return f"subscription-receipts/{instance.user_id}/{uuid4().hex}{suffix}"


class SubscriptionPayment(models.Model):
    class Method(models.TextChoices):
        MANUAL_BANK_TRANSFER = "manual_bank_transfer", "واریز بانکی دستی"
        BANK_GATEWAY = "bank_gateway", "درگاه بانکی"

    class Status(models.TextChoices):
        PENDING_SUBMISSION = "pending_submission", "در انتظار ثبت اطلاعات"
        PENDING_REVIEW = "pending_review", "در انتظار بررسی پرداخت"
        APPROVED = "approved", "پرداخت تأیید شده"
        REJECTED = "rejected", "پرداخت رد شده"
        CANCELLED = "cancelled", "لغو شده"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscription_payments")
    subscription_order = models.ForeignKey(SubscriptionOrder, on_delete=models.PROTECT, related_name="payments")
    method = models.CharField(max_length=30, choices=Method.choices, default=Method.MANUAL_BANK_TRANSFER)
    amount_snapshot = models.DecimalField(max_digits=18, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING_REVIEW)
    payer_name = models.CharField(max_length=150, blank=True)
    payer_card_last4 = models.CharField(max_length=4, blank=True)
    tracking_code = models.CharField(max_length=100, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    receipt_image = models.FileField(upload_to=receipt_upload_path, blank=True)
    user_note = models.TextField(blank=True)
    admin_note = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_subscription_payments")
    gateway = models.CharField(max_length=50, blank=True)
    gateway_authority = models.CharField(max_length=150, blank=True)
    gateway_transaction_id = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=("status", "created_at")), models.Index(fields=("user", "created_at"))]

    def __str__(self):
        return f"{self.subscription_order_id} - {self.status}"


class PlatformSettings(models.Model):
    site_name = models.CharField(max_length=100, default="ویزیت‌یار")
    short_description = models.CharField(max_length=300, blank=True)
    manual_payment_enabled = models.BooleanField(default=True)
    account_holder = models.CharField(max_length=150, blank=True)
    card_number = models.CharField(max_length=30, blank=True)
    iban = models.CharField(max_length=34, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    payment_instructions = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "platform settings"

    @classmethod
    def load(cls):
        payment = getattr(settings, "MANUAL_PAYMENT_PUBLIC_INFO", {})
        return cls.objects.get_or_create(pk=1, defaults={
            "account_holder": payment.get("account_holder", ""), "card_number": payment.get("card_number", ""),
            "iban": payment.get("iban", ""), "bank_name": payment.get("bank_name", ""),
            "payment_instructions": payment.get("instructions", ""),
        })[0]


class PlatformAdminAuditLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="platform_admin_audit_logs")
    action = models.CharField(max_length=60, db_index=True)
    target_type = models.CharField(max_length=60)
    target_id = models.CharField(max_length=64, blank=True)
    target_display = models.CharField(max_length=200, blank=True)
    before_snapshot = models.JSONField(default=dict, blank=True)
    after_snapshot = models.JSONField(default=dict, blank=True)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)
