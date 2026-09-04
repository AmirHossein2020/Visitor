from pathlib import Path

from django.db import transaction
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import SupportAttachment, SupportMessage, SupportTicket
from .serializers import ReplySerializer, TicketCreateSerializer, TicketDetailSerializer, TicketListSerializer, validate_attachment


class SupportPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50


def add_attachments(message, files):
    from .models import SupportAttachment
    for file in files:
        validate_attachment(file)
        SupportAttachment.objects.create(message=message, file=file, original_name=Path(file.name).name[:180], content_type=file.content_type, size=file.size)


class TicketViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = SupportPagination
    http_method_names = ("get", "post", "head", "options")

    def get_queryset(self):
        return SupportTicket.objects.filter(user=self.request.user).select_related("assigned_admin").prefetch_related("messages__sender", "messages__attachments")

    def get_serializer_class(self):
        if self.action == "create": return TicketCreateSerializer
        return TicketDetailSerializer if self.action == "retrieve" else TicketListSerializer

    def create(self, request, *args, **kwargs):
        serializer = TicketCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        ticket = serializer.save()
        return Response(TicketDetailSerializer(ticket, context={"request": request}).data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        ticket = self.get_object()
        if ticket.customer_unread:
            ticket.customer_unread = False
            ticket.save(update_fields=("customer_unread", "updated_at"))
        return Response(TicketDetailSerializer(ticket, context={"request": request}).data)

    @action(detail=True, methods=("post",))
    @transaction.atomic
    def messages(self, request, pk=None):
        ticket = SupportTicket.objects.select_for_update().get(pk=self.get_object().pk)
        if ticket.status == SupportTicket.Status.CLOSED:
            return Response({"detail": "درخواست بسته شده است؛ ابتدا از پشتیبانی بخواهید آن را باز کند."}, status=400)
        serializer = ReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = SupportMessage.objects.create(ticket=ticket, sender=request.user, body=serializer.validated_data["body"])
        add_attachments(message, serializer.validated_data.get("attachments", []))
        ticket.last_message_at = timezone.now(); ticket.admin_unread = True; ticket.customer_unread = False
        if ticket.status in (SupportTicket.Status.WAITING_CUSTOMER, SupportTicket.Status.RESOLVED): ticket.status = SupportTicket.Status.OPEN
        ticket.closed_at = None
        ticket.save(update_fields=("last_message_at", "admin_unread", "customer_unread", "status", "closed_at", "updated_at"))
        return Response(TicketDetailSerializer(ticket, context={"request": request}).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=("post",))
    def close(self, request, pk=None):
        ticket = self.get_object(); ticket.status = SupportTicket.Status.CLOSED; ticket.closed_at = timezone.now(); ticket.save(update_fields=("status", "closed_at", "updated_at"))
        return Response(TicketDetailSerializer(ticket, context={"request": request}).data)


@api_view(("GET",))
@permission_classes((permissions.IsAuthenticated,))
def attachment_download(request, pk):
    queryset = SupportAttachment.objects.select_related("message__ticket")
    if not (request.user.is_staff or request.user.is_superuser): queryset = queryset.filter(message__ticket__user=request.user, message__is_internal_note=False)
    attachment = get_object_or_404(queryset, pk=pk)
    response = FileResponse(attachment.file.open("rb"), content_type=attachment.content_type)
    response["Content-Disposition"] = f'inline; filename="attachment-{attachment.pk}{Path(attachment.original_name).suffix.lower()}"'
    response["X-Content-Type-Options"] = "nosniff"
    return response
