from pathlib import Path

from django.conf import settings
from django.utils import timezone
from rest_framework import serializers

from .models import SubscriptionOrder, SubscriptionPayment, SubscriptionPlan, UserSubscription


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    billing_period_display = serializers.CharField(source="get_billing_period_display", read_only=True)
    final_price = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)

    class Meta:
        model = SubscriptionPlan
        fields = ("id", "name", "slug", "billing_period", "billing_period_display", "duration_days", "price", "discount_percent", "final_price", "is_featured", "description")


class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    effective_status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    days_remaining = serializers.SerializerMethodField()
    hours_remaining = serializers.SerializerMethodField()

    class Meta:
        model = UserSubscription
        fields = ("id", "plan", "status", "effective_status", "status_display", "source", "starts_at", "expires_at", "days_remaining", "hours_remaining")

    def get_days_remaining(self, obj):
        if not obj.is_effective:
            return 0
        return max(0, (obj.expires_at - timezone.now()).days)

    def get_hours_remaining(self, obj):
        if not obj.is_effective:
            return 0
        return max(0, int((obj.expires_at - timezone.now()).total_seconds() // 3600))


class SubscriptionOrderSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    plan_id = serializers.PrimaryKeyRelatedField(source="plan", queryset=SubscriptionPlan.objects.filter(is_active=True), write_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    latest_payment = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionOrder
        fields = ("id", "plan", "plan_id", "original_price_snapshot", "discount_percent_snapshot", "amount_snapshot", "status", "status_display", "payment_reference", "notes", "approved_at", "created_at", "latest_payment")
        read_only_fields = ("original_price_snapshot", "discount_percent_snapshot", "amount_snapshot", "status", "payment_reference", "approved_at")

    def create(self, validated_data):
        plan = validated_data["plan"]
        return SubscriptionOrder.objects.create(
            user=self.context["request"].user, plan=plan,
            original_price_snapshot=plan.price,
            discount_percent_snapshot=plan.discount_percent,
            amount_snapshot=plan.final_price,
            notes=validated_data.get("notes", ""),
        )

    def get_latest_payment(self, obj):
        payment = obj.payments.first()
        return SubscriptionPaymentSerializer(payment, context=self.context).data if payment else None


class SubscriptionPaymentSerializer(serializers.ModelSerializer):
    receipt_url = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    reviewed_by_email = serializers.EmailField(source="reviewed_by.email", read_only=True, allow_null=True)

    class Meta:
        model = SubscriptionPayment
        fields = ("id", "subscription_order", "method", "amount_snapshot", "status", "status_display", "payer_name", "payer_card_last4", "tracking_code", "paid_at", "receipt_image", "receipt_url", "user_note", "admin_note", "reviewed_at", "reviewed_by_email", "created_at")
        read_only_fields = ("subscription_order", "method", "amount_snapshot", "status", "admin_note", "reviewed_at", "reviewed_by_email", "receipt_url")
        extra_kwargs = {"receipt_image": {"write_only": True, "required": False}}

    def validate_payer_card_last4(self, value):
        if value and (len(value) != 4 or not value.isdigit()):
            raise serializers.ValidationError("چهار رقم آخر کارت باید دقیقاً چهار رقم باشد.")
        return value

    def validate_receipt_image(self, uploaded):
        if uploaded.size > settings.MAX_RECEIPT_UPLOAD_BYTES:
            raise serializers.ValidationError("حجم تصویر رسید نباید بیشتر از ۵ مگابایت باشد.")
        suffix = Path(uploaded.name).suffix.lower()
        if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
            raise serializers.ValidationError("فقط فایل JPG، PNG یا WebP پذیرفته می‌شود.")
        header = uploaded.read(16)
        uploaded.seek(0)
        valid = header.startswith(b"\xff\xd8\xff") or header.startswith(b"\x89PNG\r\n\x1a\n") or (header.startswith(b"RIFF") and header[8:12] == b"WEBP")
        if not valid:
            raise serializers.ValidationError("فقط تصویر معتبر JPG، PNG یا WebP پذیرفته می‌شود.")
        return uploaded

    def validate(self, attrs):
        if not attrs.get("tracking_code", "").strip() and not attrs.get("receipt_image"):
            raise serializers.ValidationError("کد پیگیری یا تصویر رسید را وارد کنید.")
        return attrs

    def get_receipt_url(self, obj):
        return f"/api/subscriptions/payments/{obj.pk}/receipt/" if obj.receipt_image else None
