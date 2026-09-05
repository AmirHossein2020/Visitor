from pathlib import Path

from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import FileResponse
from django.utils import timezone
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import PlatformAdminAuditLog, PlatformSettings, SubscriptionOrder, SubscriptionPayment, SubscriptionPlan, UserSubscription
from .permissions import active_subscription_for
from .serializers import SubscriptionOrderSerializer, SubscriptionPaymentSerializer, SubscriptionPlanSerializer, UserSubscriptionSerializer


class PlanListView(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = SubscriptionPlanSerializer
    queryset = SubscriptionPlan.objects.filter(is_active=True)


class MySubscriptionView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        request.user.refresh_from_db(fields=("trial_used_at",))
        effective = active_subscription_for(request.user)
        if effective is True:
            return Response({"is_active": True, "is_staff": request.user.is_staff, "is_superuser": request.user.is_superuser, "subscription": None})
        latest = request.user.subscriptions.select_related("plan").first()
        previously_paid = request.user.subscription_orders.filter(status=SubscriptionOrder.Status.APPROVED).exists()
        return Response({
            "is_active": bool(effective), "is_staff": False, "is_superuser": False,
            "subscription": UserSubscriptionSerializer(latest).data if latest else None,
            "trial_used_at": request.user.trial_used_at,
            "trial_eligible": not request.user.trial_used_at and not effective and not previously_paid,
        })


class ActivateTrialView(generics.GenericAPIView):
    throttle_scope = "trial"
    permission_classes = (permissions.IsAuthenticated,)

    @transaction.atomic
    def post(self, request):
        user = get_user_model().objects.select_for_update().get(pk=request.user.pk)
        if user.trial_used_at:
            return Response({"detail": "آزمایش رایگان قبلاً استفاده شده است."}, status=400)
        if active_subscription_for(user):
            return Response({"detail": "در حال حاضر اشتراک فعال دارید."}, status=400)
        if user.subscription_orders.filter(status=SubscriptionOrder.Status.APPROVED).exists():
            return Response({"detail": "آزمایش رایگان فقط برای کاربران بدون سابقه اشتراک پولی ارائه می‌شود."}, status=400)

        now = timezone.now()
        trial_plan, _ = SubscriptionPlan.objects.get_or_create(
            slug="free-trial",
            defaults={
                "name": "آزمایش رایگان یک‌روزه", "billing_period": SubscriptionPlan.BillingPeriod.MONTHLY,
                "duration_days": 1, "price": 0, "is_active": False,
                "description": "دسترسی آزمایشی رایگان ۲۴ ساعته",
            },
        )
        user.trial_used_at = now
        user.save(update_fields=("trial_used_at",))
        subscription = UserSubscription.objects.create(
            user=user, plan=trial_plan, status=UserSubscription.Status.ACTIVE,
            source=UserSubscription.Source.FREE_TRIAL, starts_at=now,
            expires_at=now + timedelta(hours=24), approved_at=now,
        )
        PlatformAdminAuditLog.objects.create(
            actor=user, action="free_trial_activated", target_type="UserSubscription",
            target_id=str(subscription.pk), target_display=str(user),
            after_snapshot={"source": "free_trial", "activated_at": now.isoformat(), "expires_at": subscription.expires_at.isoformat()},
        )
        return Response(UserSubscriptionSerializer(subscription).data, status=status.HTTP_201_CREATED)


class SubscriptionOrderViewSet(viewsets.ModelViewSet):
    throttle_scope = "payment"
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = SubscriptionOrderSerializer
    http_method_names = ("get", "post", "head", "options")

    def get_queryset(self):
        return SubscriptionOrder.objects.filter(user=self.request.user).select_related("plan")

    @action(detail=True, methods=("get", "post"), url_path="payments")
    def payments(self, request, pk=None):
        order = self.get_object()
        if request.method == "GET":
            return Response(SubscriptionPaymentSerializer(order.payments.select_related("reviewed_by"), many=True).data)
        if order.status != SubscriptionOrder.Status.PENDING:
            return Response({"detail": "این درخواست امکان ثبت پرداخت جدید ندارد."}, status=400)
        if order.payments.filter(status=SubscriptionPayment.Status.PENDING_REVIEW).exists():
            return Response({"detail": "یک پرداخت در انتظار بررسی دارید."}, status=400)
        serializer = SubscriptionPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = serializer.save(user=request.user, subscription_order=order, amount_snapshot=order.amount_snapshot, method=SubscriptionPayment.Method.MANUAL_BANK_TRANSFER, status=SubscriptionPayment.Status.PENDING_REVIEW)
        return Response(SubscriptionPaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class PaymentInfoView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        configured = PlatformSettings.objects.filter(pk=1).first()
        if not configured:
            return Response({**settings.MANUAL_PAYMENT_PUBLIC_INFO, "manual_payment_enabled": True})
        return Response({"account_holder": configured.account_holder, "card_number": configured.card_number, "iban": configured.iban, "bank_name": configured.bank_name, "instructions": configured.payment_instructions, "manual_payment_enabled": configured.manual_payment_enabled})


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = SubscriptionPaymentSerializer

    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return SubscriptionPayment.objects.all().select_related("subscription_order__plan", "reviewed_by")
        return SubscriptionPayment.objects.filter(user=self.request.user).select_related("subscription_order__plan", "reviewed_by")

    @action(detail=True, methods=("get",))
    def receipt(self, request, pk=None):
        payment = self.get_object()
        if not payment.receipt_image:
            return Response({"detail": "تصویر رسید ثبت نشده است."}, status=404)
        content_types = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
        response = FileResponse(payment.receipt_image.open("rb"), content_type=content_types.get(Path(payment.receipt_image.name).suffix.lower(), "application/octet-stream"))
        response["Content-Disposition"] = f'inline; filename="receipt-{payment.pk}{Path(payment.receipt_image.name).suffix}"'
        response["X-Content-Type-Options"] = "nosniff"
        return response
