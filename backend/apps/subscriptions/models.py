from datetime import timedelta

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
