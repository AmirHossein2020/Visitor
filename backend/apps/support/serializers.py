from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .models import SupportAttachment, SupportMessage, SupportTicket

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
MAX_SIZE = getattr(settings, "MAX_SUPPORT_UPLOAD_BYTES", 5 * 1024 * 1024)
CONTEXT_TYPES = {"order", "invoice", "customer", "product", "purchase", "return"}
CONTEXT_MODELS = {
    "order": ("orders", "SalesOrder"),
    "invoice": ("invoices", "Invoice"),
    "customer": ("customers", "Customer"),
    "product": ("products", "Product"),
    "purchase": ("purchases", "Purchase"),
    "return": ("orders", "SalesReturn"),
}


def validate_attachment(file):
    if file.size > MAX_SIZE:
        raise serializers.ValidationError("حجم هر پیوست نباید بیشتر از ۵ مگابایت باشد.")
    if file.content_type not in ALLOWED_TYPES or Path(file.name).suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp", ".pdf"}:
        raise serializers.ValidationError("فقط فایل‌های JPG، PNG، WEBP و PDF مجاز هستند.")
    return file


class AttachmentSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = SupportAttachment
        fields = ("id", "original_name", "content_type", "size", "download_url", "created_at")

    def get_download_url(self, obj):
        return f"/api/support/attachments/{obj.pk}/download/"


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    sender_role = serializers.SerializerMethodField()
    attachments = AttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = SupportMessage
        fields = ("id", "sender_name", "sender_role", "body", "is_staff_reply", "attachments", "created_at")

    def get_sender_name(self, obj):
        return obj.sender.full_name or obj.sender.email if obj.sender else "پشتیبانی"

    def get_sender_role(self, obj):
        return "support" if obj.is_staff_reply else "customer"


class TicketListSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = SupportTicket
        fields = ("id", "ticket_number", "subject", "category", "category_display", "priority", "priority_display", "status", "status_display", "customer_unread", "created_at", "updated_at", "last_message_at")


class TicketDetailSerializer(TicketListSerializer):
    messages = serializers.SerializerMethodField()

    class Meta(TicketListSerializer.Meta):
        fields = TicketListSerializer.Meta.fields + ("context_type", "context_id", "context_label", "closed_at", "messages")

    def get_messages(self, obj):
        return MessageSerializer(obj.messages.filter(is_internal_note=False).prefetch_related("attachments"), many=True, context=self.context).data


class TicketCreateSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=180)
    category = serializers.ChoiceField(choices=SupportTicket.Category.choices)
    priority = serializers.ChoiceField(choices=SupportTicket.Priority.choices, default=SupportTicket.Priority.NORMAL)
    description = serializers.CharField(max_length=10000)
    context_type = serializers.CharField(max_length=20, required=False, allow_blank=True)
    context_id = serializers.CharField(max_length=64, required=False, allow_blank=True)
    context_label = serializers.CharField(max_length=180, required=False, allow_blank=True)
    attachments = serializers.ListField(child=serializers.FileField(), required=False, write_only=True)

    def validate(self, attrs):
        context_type = attrs.get("context_type", "")
        context_id = attrs.get("context_id", "")
        if context_type and context_type not in CONTEXT_TYPES:
            raise serializers.ValidationError({"context_type": "نوع ارتباط معتبر نیست."})
        if bool(context_type) != bool(context_id):
            raise serializers.ValidationError({"context_id": "نوع و شناسه ارتباط باید هم‌زمان ارسال شوند."})
        if context_type:
            app_label, model_name = CONTEXT_MODELS[context_type]
            model = apps.get_model(app_label, model_name)
            linked = model.objects.filter(pk=context_id, owner=self.context["request"].user).first()
            if not linked:
                raise serializers.ValidationError({"context_id": "رکورد مرتبط پیدا نشد."})
            attrs["context_label"] = attrs.get("context_label") or str(linked)[:180]
        for file in attrs.get("attachments", []): validate_attachment(file)
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        files = validated_data.pop("attachments", [])
        description = validated_data.pop("description")
        ticket = SupportTicket.objects.create(user=self.context["request"].user, **validated_data)
        message = SupportMessage.objects.create(ticket=ticket, sender=ticket.user, body=description)
        for file in files:
            SupportAttachment.objects.create(message=message, file=file, original_name=Path(file.name).name[:180], content_type=file.content_type, size=file.size)
        return ticket


class ReplySerializer(serializers.Serializer):
    body = serializers.CharField(max_length=10000)
    attachments = serializers.ListField(child=serializers.FileField(), required=False, write_only=True)

    def validate_attachments(self, files):
        for file in files: validate_attachment(file)
        return files
