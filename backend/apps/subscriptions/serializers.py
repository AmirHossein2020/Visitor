from django.utils import timezone
from rest_framework import serializers

from .models import SubscriptionOrder, SubscriptionPlan, UserSubscription


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    billing_period_display = serializers.CharField(source="get_billing_period_display", read_only=True)

    class Meta:
        model = SubscriptionPlan
        fields = ("id", "name", "slug", "billing_period", "billing_period_display", "duration_days", "price", "is_featured", "description")


class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    effective_status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    days_remaining = serializers.SerializerMethodField()

    class Meta:
        model = UserSubscription
        fields = ("id", "plan", "status", "effective_status", "status_display", "starts_at", "expires_at", "days_remaining")

    def get_days_remaining(self, obj):
        if not obj.is_effective:
            return 0
        return max(0, (obj.expires_at - timezone.now()).days)


class SubscriptionOrderSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    plan_id = serializers.PrimaryKeyRelatedField(source="plan", queryset=SubscriptionPlan.objects.filter(is_active=True), write_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = SubscriptionOrder
        fields = ("id", "plan", "plan_id", "amount_snapshot", "status", "status_display", "payment_reference", "notes", "approved_at", "created_at")
        read_only_fields = ("amount_snapshot", "status", "payment_reference", "approved_at")

    def create(self, validated_data):
        plan = validated_data["plan"]
        return SubscriptionOrder.objects.create(user=self.context["request"].user, plan=plan, amount_snapshot=plan.price, notes=validated_data.get("notes", ""))
