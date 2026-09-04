from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.db.models import Count, Q, Sum
from django.utils import timezone
from rest_framework import mixins, permissions, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PlatformAdminAuditLog, PlatformSettings, SubscriptionOrder, SubscriptionPayment, SubscriptionPlan, UserSubscription
from .serializers import SubscriptionPaymentSerializer


class IsPlatformAdmin(permissions.BasePermission):
    message = "دسترسی مدیریت سامانه لازم است."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser))


class AdminPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


def audit(actor, action, target, before=None, after=None, reason=""):
    PlatformAdminAuditLog.objects.create(actor=actor, action=action, target_type=target.__class__.__name__, target_id=str(target.pk), target_display=str(target), before_snapshot=before or {}, after_snapshot=after or {}, reason=reason)


def role_of(user):
    return "superuser" if user.is_superuser else "staff" if user.is_staff else "user"


class AdminPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ("id", "name", "slug", "billing_period", "duration_days", "price", "discount_percent", "final_price", "is_active", "is_featured", "description", "sort_order", "created_at", "updated_at")
        read_only_fields = ("created_at", "updated_at")

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("قیمت نمی‌تواند منفی باشد.")
        return value

    def validate_duration_days(self, value):
        if value < 1:
            raise serializers.ValidationError("مدت پلن باید حداقل یک روز باشد.")
        return value

    def validate_discount_percent(self, value):
        if not 0 <= value <= 99:
            raise serializers.ValidationError("درصد تخفیف باید بین صفر تا ۹۹ باشد.")
        return value


class AdminSubscriptionSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    plan_name = serializers.CharField(source="plan.name", read_only=True)
    effective_status = serializers.CharField(read_only=True)
    approved_by_email = serializers.EmailField(source="approved_by.email", read_only=True, allow_null=True)

    class Meta:
        model = UserSubscription
        fields = ("id", "user", "user_email", "plan", "plan_name", "status", "effective_status", "source", "starts_at", "expires_at", "approved_at", "approved_by_email", "created_at")
        read_only_fields = fields


class AdminOrderSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    plan_name = serializers.CharField(source="plan.name", read_only=True)
    approved_by_email = serializers.EmailField(source="approved_by.email", read_only=True, allow_null=True)
    latest_payment = serializers.SerializerMethodField()
    payment_attempts = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionOrder
        fields = ("id", "user", "user_email", "plan", "plan_name", "original_price_snapshot", "discount_percent_snapshot", "amount_snapshot", "status", "payment_reference", "notes", "approved_at", "approved_by_email", "created_at", "latest_payment", "payment_attempts")
        read_only_fields = fields

    def get_latest_payment(self, obj):
        payment = obj.payments.first()
        return AdminPaymentSerializer(payment, context=self.context).data if payment else None

    def get_payment_attempts(self, obj):
        return AdminPaymentSerializer(obj.payments.all(), many=True, context=self.context).data


class AdminUserListSerializer(serializers.ModelSerializer):
    subscription_status = serializers.SerializerMethodField()
    active_plan = serializers.SerializerMethodField()
    subscription_expires_at = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ("id", "email", "full_name", "date_joined", "last_login", "is_active", "is_staff", "is_superuser", "role", "subscription_status", "active_plan", "subscription_expires_at", "trial_used_at")
        read_only_fields = fields

    def _subscription(self, obj):
        subscriptions = getattr(obj, "admin_subscriptions", [])
        return subscriptions[0] if subscriptions else None

    def get_subscription_status(self, obj):
        subscription = self._subscription(obj)
        return subscription.effective_status if subscription else "inactive"

    def get_active_plan(self, obj):
        subscription = self._subscription(obj)
        return subscription.plan.name if subscription and subscription.is_effective else None

    def get_subscription_expires_at(self, obj):
        subscription = self._subscription(obj)
        return subscription.expires_at if subscription else None

    def get_role(self, obj):
        return role_of(obj)


class AdminUserDetailSerializer(serializers.ModelSerializer):
    subscriptions = AdminSubscriptionSerializer(many=True, read_only=True)
    subscription_orders = AdminOrderSerializer(many=True, read_only=True)
    payments = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ("id", "email", "full_name", "phone_number", "date_joined", "last_login", "is_active", "is_staff", "is_superuser", "role", "trial_used_at", "subscriptions", "subscription_orders", "payments")
        read_only_fields = fields

    def get_payments(self, obj):
        return AdminPaymentSerializer(obj.subscription_payments.all(), many=True, context=self.context).data

    def get_role(self, obj):
        return role_of(obj)


class PlatformSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformSettings
        fields = ("site_name", "short_description", "manual_payment_enabled", "account_holder", "card_number", "iban", "bank_name", "payment_instructions", "updated_at")
        read_only_fields = ("updated_at",)


class AuditLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True, allow_null=True)

    class Meta:
        model = PlatformAdminAuditLog
        fields = ("id", "actor_email", "action", "target_type", "target_id", "target_display", "before_snapshot", "after_snapshot", "reason", "created_at")
        read_only_fields = fields


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("is_active",)


class DashboardView(APIView):
    permission_classes = (IsPlatformAdmin,)

    def get(self, request):
        now = timezone.now()
        orders = SubscriptionOrder.objects.all()
        plans = SubscriptionPlan.objects.filter(is_active=True)
        return Response({
            "total_users": get_user_model().objects.count(),
            "new_users_30_days": get_user_model().objects.filter(date_joined__gte=now - timedelta(days=30)).count(),
            "active_subscriptions": UserSubscription.objects.filter(status="active", starts_at__lte=now, expires_at__gt=now).count(),
            "expired_subscriptions": UserSubscription.objects.filter(Q(status="expired") | Q(status="active", expires_at__lte=now)).count(),
            "pending_requests": orders.filter(status="pending").count(),
            "awaiting_customer_payment": orders.filter(status="pending", payments__isnull=True).count(),
            "pending_payment_reviews": SubscriptionPayment.objects.filter(status=SubscriptionPayment.Status.PENDING_REVIEW).count(),
            "monthly_requests": orders.filter(plan__billing_period="monthly").count(),
            "yearly_requests": orders.filter(plan__billing_period="yearly").count(),
            "approved_revenue": orders.filter(status="approved").aggregate(total=Sum("amount_snapshot"))["total"] or 0,
            "active_monthly_plans": plans.filter(billing_period="monthly").count(),
            "active_yearly_plans": plans.filter(billing_period="yearly").count(),
            "expiring_in_7_days": UserSubscription.objects.filter(status="active", expires_at__gt=now, expires_at__lte=now + timedelta(days=7)).count(),
        })


class PlatformSettingsView(APIView):
    permission_classes = (IsPlatformAdmin,)

    def get(self, request): return Response(PlatformSettingsSerializer(PlatformSettings.load()).data)

    @transaction.atomic
    def patch(self, request):
        settings_obj = PlatformSettings.objects.select_for_update().filter(pk=1).first() or PlatformSettings.load()
        serializer = PlatformSettingsSerializer(settings_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        before = PlatformSettingsSerializer(settings_obj).data
        updated = serializer.save()
        audit(request.user, "platform_settings_updated", updated, before, PlatformSettingsSerializer(updated).data)
        return Response(PlatformSettingsSerializer(updated).data)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsPlatformAdmin,)
    pagination_class = AdminPagination
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        queryset = PlatformAdminAuditLog.objects.select_related("actor")
        actor = self.request.query_params.get("actor", "").strip(); action_filter = self.request.query_params.get("action", "").strip()
        date_from = self.request.query_params.get("date_from", "").strip(); date_to = self.request.query_params.get("date_to", "").strip()
        if actor: queryset = queryset.filter(actor__email__icontains=actor)
        if action_filter: queryset = queryset.filter(action=action_filter)
        if date_from: queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to: queryset = queryset.filter(created_at__date__lte=date_to)
        return queryset


class AdminUserViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    permission_classes = (IsPlatformAdmin,)
    pagination_class = AdminPagination
    http_method_names = ("get", "patch", "post", "head", "options")

    def get_queryset(self):
        from django.db.models import Prefetch
        queryset = get_user_model().objects.order_by("-date_joined")
        search = self.request.query_params.get("search", "").strip()
        subscription_status = self.request.query_params.get("subscription_status", "").strip()
        role = self.request.query_params.get("role", "").strip()
        account_status = self.request.query_params.get("account_status", "").strip()
        if search:
            queryset = queryset.filter(Q(email__icontains=search) | Q(full_name__icontains=search))
        if subscription_status == "active":
            queryset = queryset.filter(subscriptions__status="active", subscriptions__starts_at__lte=timezone.now(), subscriptions__expires_at__gt=timezone.now())
        elif subscription_status in {"pending", "cancelled", "rejected", "expired"}:
            queryset = queryset.filter(subscriptions__status=subscription_status)
        elif subscription_status == "inactive":
            queryset = queryset.exclude(subscriptions__status="active", subscriptions__expires_at__gt=timezone.now())
        if role == "user": queryset = queryset.filter(is_staff=False, is_superuser=False)
        elif role == "staff": queryset = queryset.filter(is_staff=True, is_superuser=False)
        elif role == "superuser": queryset = queryset.filter(is_superuser=True)
        if account_status == "active": queryset = queryset.filter(is_active=True)
        elif account_status == "inactive": queryset = queryset.filter(is_active=False)
        return queryset.distinct().prefetch_related(Prefetch("subscriptions", queryset=UserSubscription.objects.select_related("plan", "approved_by").order_by("-created_at"), to_attr="admin_subscriptions"), "subscription_orders__plan", "subscription_orders__approved_by", "subscription_orders__payments__reviewed_by", "subscription_payments__subscription_order__plan", "subscription_payments__reviewed_by")

    def get_serializer_class(self):
        if self.action in ("partial_update", "update"):
            return AdminUserUpdateSerializer
        return AdminUserDetailSerializer if self.action == "retrieve" else AdminUserListSerializer

    def perform_update(self, serializer):
        target = self.get_object()
        if target.is_superuser and not self.request.user.is_superuser:
            raise serializers.ValidationError({"detail": "مدیر عادی اجازه تغییر حساب سوپر ادمین را ندارد."})
        if target.is_superuser and target.is_active and serializer.validated_data.get("is_active") is False and get_user_model().objects.filter(is_superuser=True, is_active=True).count() <= 1:
            raise serializers.ValidationError({"detail": "آخرین سوپر ادمین فعال قابل غیرفعال‌سازی نیست."})
        before = {"is_active": target.is_active}
        updated = serializer.save()
        audit(self.request.user, "account_status_changed", updated, before, {"is_active": updated.is_active})

    def _change_role(self, request, target, *, staff=None, superuser=None):
        actor = request.user
        before = {"is_staff": target.is_staff, "is_superuser": target.is_superuser}
        if not actor.is_superuser:
            if target.is_superuser or target.pk == actor.pk or superuser is not None:
                return Response({"detail": "فقط سوپر ادمین اجازه این تغییر نقش را دارد."}, status=403)
        if superuser is False and target.is_superuser and target.is_active and get_user_model().objects.filter(is_superuser=True, is_active=True).count() <= 1:
            return Response({"detail": "آخرین سوپر ادمین فعال قابل تنزل نیست."}, status=400)
        if staff is not None: target.is_staff = staff
        if superuser is not None:
            target.is_superuser = superuser
            if superuser: target.is_staff = True
        if target.is_superuser: target.is_staff = True
        target.save(update_fields=("is_staff", "is_superuser"))
        audit(actor, "role_changed", target, before, {"is_staff": target.is_staff, "is_superuser": target.is_superuser}, request.data.get("reason", ""))
        return Response(AdminUserDetailSerializer(target, context={"request": request}).data)

    @action(detail=True, methods=("post",), url_path="grant-staff")
    def grant_staff(self, request, pk=None): return self._change_role(request, self.get_object(), staff=True)

    @action(detail=True, methods=("post",), url_path="revoke-staff")
    def revoke_staff(self, request, pk=None):
        target = self.get_object()
        if target.is_superuser: return Response({"detail": "ابتدا دسترسی سوپر ادمین را حذف کنید."}, status=400)
        return self._change_role(request, target, staff=False)

    @action(detail=True, methods=("post",), url_path="grant-superuser")
    def grant_superuser(self, request, pk=None): return self._change_role(request, self.get_object(), superuser=True)

    @action(detail=True, methods=("post",), url_path="revoke-superuser")
    def revoke_superuser(self, request, pk=None): return self._change_role(request, self.get_object(), superuser=False)

    @action(detail=True, methods=("post",), url_path="subscriptions/activate")
    @transaction.atomic
    def activate_subscription(self, request, pk=None):
        user = self.get_object()
        try:
            plan = SubscriptionPlan.objects.get(pk=request.data.get("plan_id"), is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response({"detail": "پلن فعال معتبر انتخاب کنید."}, status=400)
        now = timezone.now()
        UserSubscription.objects.filter(user=user, status="active").update(status="cancelled")
        subscription = UserSubscription.objects.create(user=user, plan=plan, status="active", source=UserSubscription.Source.MANUAL, starts_at=now, expires_at=now + timedelta(days=plan.duration_days), approved_at=now, approved_by=request.user)
        audit(request.user, "subscription_activated", subscription, after={"plan_id": plan.id, "expires_at": subscription.expires_at.isoformat()})
        return Response(AdminSubscriptionSerializer(subscription).data, status=201)


class AdminOrderViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsPlatformAdmin,)
    pagination_class = AdminPagination
    serializer_class = AdminOrderSerializer

    def get_queryset(self):
        queryset = SubscriptionOrder.objects.select_related("user", "plan", "approved_by").prefetch_related("payments__reviewed_by").order_by("-created_at")
        status_filter = self.request.query_params.get("status", "")
        return queryset.filter(status=status_filter) if status_filter else queryset

    @action(detail=True, methods=("post",))
    def approve(self, request, pk=None):
        order = self.get_object()
        try:
            subscription = order.approve(request.user)
        except ValueError as error:
            return Response({"detail": str(error)}, status=400)
        return Response(AdminSubscriptionSerializer(subscription).data)

    @action(detail=True, methods=("post",))
    @transaction.atomic
    def reject(self, request, pk=None):
        order = SubscriptionOrder.objects.select_for_update().get(pk=self.get_object().pk)
        if order.status != "pending":
            return Response({"detail": "فقط درخواست در انتظار را می‌توان رد کرد."}, status=400)
        order.status = "rejected"; order.approved_at = timezone.now(); order.approved_by = request.user
        if request.data.get("notes"):
            order.notes = request.data["notes"]
        order.save(update_fields=("status", "approved_at", "approved_by", "notes", "updated_at"))
        return Response(AdminOrderSerializer(order).data)


class AdminSubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsPlatformAdmin,)
    pagination_class = AdminPagination
    serializer_class = AdminSubscriptionSerializer
    def get_queryset(self):
        queryset = UserSubscription.objects.select_related("user", "plan", "approved_by").order_by("-created_at")
        search = self.request.query_params.get("search", "").strip()
        status_filter = self.request.query_params.get("status", "").strip()
        plan = self.request.query_params.get("plan", "").strip()
        if search: queryset = queryset.filter(Q(user__email__icontains=search) | Q(user__full_name__icontains=search))
        if status_filter == "expired": queryset = queryset.filter(Q(status="expired") | Q(status="active", expires_at__lte=timezone.now()))
        elif status_filter: queryset = queryset.filter(status=status_filter)
        if plan: queryset = queryset.filter(plan_id=plan)
        return queryset

    @action(detail=True, methods=("post",))
    @transaction.atomic
    def extend(self, request, pk=None):
        subscription = UserSubscription.objects.select_for_update().get(pk=self.get_object().pk)
        try:
            plan = SubscriptionPlan.objects.get(pk=request.data.get("plan_id"), is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response({"detail": "پلن فعال معتبر انتخاب کنید."}, status=400)
        before = {"plan_id": subscription.plan_id, "expires_at": subscription.expires_at.isoformat() if subscription.expires_at else None, "status": subscription.status}
        now = timezone.now(); base = max(subscription.expires_at or now, now)
        subscription.plan = plan; subscription.status = "active"; subscription.starts_at = subscription.starts_at or now
        subscription.expires_at = base + timedelta(days=plan.duration_days); subscription.approved_at = now; subscription.approved_by = request.user
        UserSubscription.objects.filter(user=subscription.user, status="active").exclude(pk=subscription.pk).update(status="cancelled")
        subscription.save()
        audit(request.user, "subscription_extended", subscription, before, {"plan_id": plan.id, "expires_at": subscription.expires_at.isoformat(), "status": subscription.status})
        return Response(self.get_serializer(subscription).data)

    @action(detail=True, methods=("post",))
    def cancel(self, request, pk=None):
        subscription = self.get_object()
        if subscription.status != "active":
            return Response({"detail": "فقط اشتراک فعال قابل لغو است."}, status=400)
        before = {"status": subscription.status}; subscription.status = "cancelled"; subscription.save(update_fields=("status", "updated_at"))
        audit(request.user, "subscription_cancelled", subscription, before, {"status": subscription.status}, request.data.get("reason", ""))
        return Response(self.get_serializer(subscription).data)

    @action(detail=True, methods=("post",))
    @transaction.atomic
    def adjust(self, request, pk=None):
        if not request.user.is_superuser: return Response({"detail": "فقط سوپر ادمین اجازه تنظیم دستی روزها را دارد."}, status=403)
        subscription = UserSubscription.objects.select_for_update().get(pk=self.get_object().pk)
        try: days = int(request.data.get("days"))
        except (TypeError, ValueError): return Response({"detail": "تعداد روز معتبر وارد کنید."}, status=400)
        reason = request.data.get("reason", "").strip()
        if not reason or days == 0 or abs(days) > 3650: return Response({"detail": "دلیل و تعداد روز معتبر الزامی است."}, status=400)
        if not subscription.expires_at: return Response({"detail": "اشتراک فاقد تاریخ پایان است."}, status=400)
        new_expiry = subscription.expires_at + timedelta(days=days)
        if new_expiry <= (subscription.starts_at or timezone.now()): return Response({"detail": "تاریخ پایان نمی‌تواند قبل از شروع باشد."}, status=400)
        before = {"expires_at": subscription.expires_at.isoformat()}
        subscription.expires_at = new_expiry; subscription.save(update_fields=("expires_at", "updated_at"))
        audit(request.user, "subscription_adjusted", subscription, before, {"expires_at": new_expiry.isoformat(), "days": days}, reason)
        return Response(self.get_serializer(subscription).data)


class AdminPlanViewSet(viewsets.ModelViewSet):
    permission_classes = (IsPlatformAdmin,)
    pagination_class = AdminPagination
    serializer_class = AdminPlanSerializer
    queryset = SubscriptionPlan.objects.order_by("sort_order", "price")
    http_method_names = ("get", "post", "patch", "delete", "head", "options")

    def perform_create(self, serializer):
        plan = serializer.save(); audit(self.request.user, "plan_created", plan, after={"price": str(plan.price), "is_active": plan.is_active})

    def perform_update(self, serializer):
        plan = self.get_object(); before = {"price": str(plan.price), "discount_percent": plan.discount_percent, "is_active": plan.is_active, "duration_days": plan.duration_days}
        updated = serializer.save(); audit(self.request.user, "plan_updated", updated, before, {"price": str(updated.price), "discount_percent": updated.discount_percent, "is_active": updated.is_active, "duration_days": updated.duration_days})

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        plan = SubscriptionPlan.objects.select_for_update().get(pk=self.get_object().pk)
        referenced = plan.orders.exists() or plan.subscriptions.exists()
        if referenced:
            before = {"is_active": plan.is_active}
            plan.is_active = False
            plan.save(update_fields=("is_active", "updated_at"))
            audit(request.user, "plan_archived", plan, before, {"is_active": False}, "پلن دارای سابقه است و به‌جای حذف، آرشیو شد.")
            return Response({"detail": "پلن به دلیل داشتن سابقه آرشیو شد.", "archived": True}, status=200)
        try:
            display, plan_id = str(plan), plan.pk
            plan.delete()
        except ProtectedError:
            return Response({"detail": "این پلن دارای سابقه است و قابل حذف دائمی نیست."}, status=409)
        PlatformAdminAuditLog.objects.create(actor=request.user, action="plan_deleted", target_type="SubscriptionPlan", target_id=str(plan_id), target_display=display)
        return Response(status=204)


class AdminPaymentSerializer(SubscriptionPaymentSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    plan_name = serializers.CharField(source="subscription_order.plan.name", read_only=True)

    class Meta(SubscriptionPaymentSerializer.Meta):
        fields = SubscriptionPaymentSerializer.Meta.fields + ("user_email", "plan_name")
        read_only_fields = fields
        extra_kwargs = {"receipt_image": {"read_only": True}}


class AdminPaymentViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsPlatformAdmin,)
    pagination_class = AdminPagination
    serializer_class = AdminPaymentSerializer

    def get_queryset(self):
        queryset = SubscriptionPayment.objects.select_related("user", "subscription_order__plan", "reviewed_by").order_by("-created_at")
        status_filter = self.request.query_params.get("status", "")
        return queryset.filter(status=status_filter) if status_filter else queryset

    @action(detail=True, methods=("post",))
    @transaction.atomic
    def approve(self, request, pk=None):
        payment = SubscriptionPayment.objects.select_for_update().select_related("subscription_order").get(pk=self.get_object().pk)
        if payment.status != SubscriptionPayment.Status.PENDING_REVIEW:
            return Response({"detail": "فقط پرداخت در انتظار بررسی قابل تأیید است."}, status=400)
        try:
            payment.subscription_order.approve(request.user)
        except ValueError as error:
            return Response({"detail": str(error)}, status=400)
        payment.status = SubscriptionPayment.Status.APPROVED
        payment.reviewed_at = timezone.now()
        payment.reviewed_by = request.user
        payment.admin_note = request.data.get("admin_note", "")
        payment.save(update_fields=("status", "reviewed_at", "reviewed_by", "admin_note", "updated_at"))
        audit(request.user, "payment_approved", payment, {"status": SubscriptionPayment.Status.PENDING_REVIEW}, {"status": payment.status})
        return Response(self.get_serializer(payment).data)

    @action(detail=True, methods=("post",))
    @transaction.atomic
    def reject(self, request, pk=None):
        payment = SubscriptionPayment.objects.select_for_update().get(pk=self.get_object().pk)
        if payment.status != SubscriptionPayment.Status.PENDING_REVIEW:
            return Response({"detail": "فقط پرداخت در انتظار بررسی قابل رد است."}, status=400)
        note = request.data.get("admin_note", "").strip()
        if not note:
            return Response({"detail": "دلیل رد پرداخت را وارد کنید."}, status=400)
        payment.status = SubscriptionPayment.Status.REJECTED
        payment.reviewed_at = timezone.now()
        payment.reviewed_by = request.user
        payment.admin_note = note
        payment.save(update_fields=("status", "reviewed_at", "reviewed_by", "admin_note", "updated_at"))
        audit(request.user, "payment_rejected", payment, {"status": SubscriptionPayment.Status.PENDING_REVIEW}, {"status": payment.status}, note)
        return Response(self.get_serializer(payment).data)
