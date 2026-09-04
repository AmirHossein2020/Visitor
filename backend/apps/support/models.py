from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.db import models


def support_upload_path(instance, filename):
    return f"support-private/{instance.message.ticket.ticket_number}/{uuid4().hex}{Path(filename).suffix.lower()}"


class SupportTicket(models.Model):
    class Category(models.TextChoices):
        TECHNICAL = "technical", "مشکل فنی"
        USAGE = "usage", "سوال درباره استفاده از سامانه"
        ORDER_INVOICE = "order_invoice", "سفارش و فاکتور"
        DATA = "data", "اطلاعات و داده‌ها"
        SUBSCRIPTION = "subscription", "اشتراک و پرداخت"
        ACCOUNT = "account", "حساب کاربری"
        FEEDBACK = "feedback", "پیشنهاد و بازخورد"
        OTHER = "other", "سایر"

    class Priority(models.TextChoices):
        LOW = "low", "کم"
        NORMAL = "normal", "عادی"
        HIGH = "high", "مهم"

    class Status(models.TextChoices):
        OPEN = "open", "باز"
        IN_PROGRESS = "in_progress", "در حال بررسی"
        WAITING_CUSTOMER = "waiting_for_customer", "در انتظار پاسخ شما"
        RESOLVED = "resolved", "حل شده"
        CLOSED = "closed", "بسته شده"

    ticket_number = models.CharField(max_length=16, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="support_tickets")
    subject = models.CharField(max_length=180)
    category = models.CharField(max_length=24, choices=Category.choices)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.NORMAL)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.OPEN)
    assigned_admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_support_tickets", limit_choices_to={"is_staff": True})
    context_type = models.CharField(max_length=20, blank=True)
    context_id = models.CharField(max_length=64, blank=True)
    context_label = models.CharField(max_length=180, blank=True)
    customer_unread = models.BooleanField(default=False)
    admin_unread = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(auto_now_add=True, db_index=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-admin_unread", "-last_message_at")
        indexes = [models.Index(fields=("status", "last_message_at")), models.Index(fields=("user", "last_message_at"))]

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            while True:
                candidate = f"SUP-{uuid4().hex[:8].upper()}"
                if not type(self).objects.filter(ticket_number=candidate).exists():
                    self.ticket_number = candidate
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_number} - {self.subject}"


class SupportMessage(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="support_messages")
    body = models.TextField()
    is_staff_reply = models.BooleanField(default=False)
    is_internal_note = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)
        indexes = [models.Index(fields=("ticket", "created_at"))]


class SupportAttachment(models.Model):
    message = models.ForeignKey(SupportMessage, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to=support_upload_path)
    original_name = models.CharField(max_length=180)
    content_type = models.CharField(max_length=80)
    size = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
