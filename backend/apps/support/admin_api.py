from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Prefetch, Q
from django.utils import timezone
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.subscriptions.platform_admin import AdminPagination, IsPlatformAdmin, audit
from apps.subscriptions.models import UserSubscription
from .models import SupportMessage, SupportTicket
from .serializers import AttachmentSerializer, ReplySerializer, TicketListSerializer
from .views import add_attachments


class AdminMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    attachments = AttachmentSerializer(many=True, read_only=True)
    class Meta:
        model = SupportMessage
        fields = ("id", "sender_name", "body", "is_staff_reply", "is_internal_note", "attachments", "created_at")
    def get_sender_name(self, obj): return obj.sender.full_name or obj.sender.email if obj.sender else "پشتیبانی"


class AdminTicketSerializer(TicketListSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    user_is_active = serializers.BooleanField(source="user.is_active", read_only=True)
    assigned_admin_email = serializers.EmailField(source="assigned_admin.email", read_only=True, allow_null=True)
    messages = AdminMessageSerializer(many=True, read_only=True)
    subscription_summary = serializers.SerializerMethodField()
    class Meta(TicketListSerializer.Meta):
        fields = TicketListSerializer.Meta.fields + ("user", "user_email", "user_name", "user_is_active", "assigned_admin", "assigned_admin_email", "context_type", "context_id", "context_label", "closed_at", "admin_unread", "subscription_summary", "messages")
    def get_subscription_summary(self, obj):
        subscriptions = getattr(obj.user, "active_support_subscriptions", ())
        sub = subscriptions[0] if subscriptions else None
        return {"plan": sub.plan.name, "status": sub.effective_status, "expires_at": sub.expires_at} if sub else None


class AdminTicketViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsPlatformAdmin,)
    pagination_class = AdminPagination
    serializer_class = AdminTicketSerializer

    def get_queryset(self):
        active_subscriptions = UserSubscription.objects.filter(status="active").select_related("plan").order_by("-created_at")
        qs = SupportTicket.objects.select_related("user", "assigned_admin").prefetch_related(
            "messages__sender",
            "messages__attachments",
            Prefetch("user__subscriptions", queryset=active_subscriptions, to_attr="active_support_subscriptions"),
        )
        params = self.request.query_params
        search = params.get("search", "").strip()
        if search: qs = qs.filter(Q(ticket_number__icontains=search) | Q(subject__icontains=search) | Q(user__email__icontains=search) | Q(user__full_name__icontains=search))
        for field in ("status", "category", "priority"):
            if params.get(field): qs = qs.filter(**{field: params[field]})
        if params.get("user"): qs = qs.filter(user_id=params["user"])
        if params.get("date_from"): qs = qs.filter(created_at__date__gte=params["date_from"])
        if params.get("date_to"): qs = qs.filter(created_at__date__lte=params["date_to"])
        return qs.order_by("-admin_unread", "-last_message_at")

    def retrieve(self, request, *args, **kwargs):
        ticket = self.get_object()
        if ticket.admin_unread: ticket.admin_unread = False; ticket.save(update_fields=("admin_unread", "updated_at"))
        return Response(self.get_serializer(ticket).data)

    @action(detail=True, methods=("post",))
    @transaction.atomic
    def reply(self, request, pk=None):
        ticket = SupportTicket.objects.select_for_update().get(pk=self.get_object().pk)
        serializer = ReplySerializer(data=request.data); serializer.is_valid(raise_exception=True)
        message = SupportMessage.objects.create(ticket=ticket, sender=request.user, body=serializer.validated_data["body"], is_staff_reply=True)
        add_attachments(message, serializer.validated_data.get("attachments", []))
        before = ticket.status; ticket.status = request.data.get("status", SupportTicket.Status.WAITING_CUSTOMER)
        if ticket.status not in SupportTicket.Status.values: ticket.status = SupportTicket.Status.WAITING_CUSTOMER
        ticket.last_message_at = timezone.now(); ticket.customer_unread = True; ticket.admin_unread = False
        if ticket.status == SupportTicket.Status.CLOSED: ticket.closed_at = timezone.now()
        ticket.save(update_fields=("status", "last_message_at", "customer_unread", "admin_unread", "closed_at", "updated_at"))
        audit(request.user, "support_reply", ticket, {"status": before}, {"status": ticket.status})
        return Response(self.get_serializer(ticket).data)

    @action(detail=True, methods=("post",), url_path="internal-note")
    def internal_note(self, request, pk=None):
        body = request.data.get("body", "").strip()
        if not body: raise serializers.ValidationError({"body": "متن یادداشت الزامی است."})
        SupportMessage.objects.create(ticket=self.get_object(), sender=request.user, body=body, is_staff_reply=True, is_internal_note=True)
        audit(request.user, "support_internal_note", self.get_object())
        return Response(self.get_serializer(self.get_object()).data)

    @action(detail=True, methods=("post",))
    def status(self, request, pk=None):
        ticket = self.get_object(); value = request.data.get("status")
        if value not in SupportTicket.Status.values: raise serializers.ValidationError({"status": "وضعیت معتبر نیست."})
        before = ticket.status; ticket.status = value; ticket.closed_at = timezone.now() if value == "closed" else None; ticket.customer_unread = True
        ticket.save(update_fields=("status", "closed_at", "customer_unread", "updated_at")); audit(request.user, "support_status_changed", ticket, {"status": before}, {"status": value})
        return Response(self.get_serializer(ticket).data)

    @action(detail=True, methods=("post",))
    def assign(self, request, pk=None):
        ticket = self.get_object(); admin_id = request.data.get("assigned_admin_id")
        admin = request.user if admin_id == "self" else None if not admin_id else get_user_model().objects.filter(pk=admin_id, is_staff=True, is_active=True).first()
        if admin_id and not admin: raise serializers.ValidationError({"assigned_admin_id": "مدیر معتبر انتخاب کنید."})
        before = ticket.assigned_admin_id; ticket.assigned_admin = admin; ticket.save(update_fields=("assigned_admin", "updated_at")); audit(request.user, "support_assigned", ticket, {"assigned_admin_id": before}, {"assigned_admin_id": admin_id})
        return Response(self.get_serializer(ticket).data)
