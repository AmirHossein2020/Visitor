from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.invoices.models import Invoice, InvoiceItem
from apps.products.inventory import reverse_return, sync_return

from .models import SalesReturn, SalesReturnItem
from .return_serializers import (
    AddSalesReturnItemSerializer,
    CreateSalesReturnSerializer,
    SalesReturnItemSerializer,
    SalesReturnListSerializer,
    SalesReturnSerializer,
    UpdateSalesReturnItemSerializer,
)


def confirmed_returned_quantity(invoice_item, *, exclude_return=None):
    queryset = SalesReturnItem.objects.filter(
        invoice_item=invoice_item,
        sales_return__status=SalesReturn.Status.CONFIRMED,
    )
    if exclude_return:
        queryset = queryset.exclude(sales_return=exclude_return)
    return queryset.aggregate(total=Sum("quantity"))["total"] or 0


def validate_return_quantity(invoice_item, quantity, *, sales_return):
    already_returned = confirmed_returned_quantity(
        invoice_item, exclude_return=sales_return
    )
    if already_returned + quantity > invoice_item.quantity:
        remaining = invoice_item.quantity - already_returned
        raise ValidationError({
            "quantity": f"حداکثر مقدار قابل مرجوعی {remaining} است."
        })


class SalesReturnViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = ("get", "post", "patch", "delete", "head", "options")

    def get_queryset(self):
        queryset = SalesReturn.objects.filter(owner=self.request.user).select_related("invoice")
        invoice_id = self.request.query_params.get("invoice")
        if invoice_id:
            queryset = queryset.filter(invoice_id=invoice_id)
        if self.action == "retrieve":
            queryset = queryset.prefetch_related("items__invoice_item")
        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return CreateSalesReturnSerializer
        if self.action == "list":
            return SalesReturnListSerializer
        return SalesReturnSerializer

    def create(self, request, *args, **kwargs):
        serializer = CreateSalesReturnSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            invoice = get_object_or_404(
                Invoice.objects.select_for_update(),
                pk=serializer.validated_data["invoice"].pk,
                owner=request.user,
                status=Invoice.Status.ISSUED,
            )
            sales_return = SalesReturn.objects.create(
                owner=request.user, invoice=invoice, notes=serializer.validated_data["notes"]
            )
        return Response(SalesReturnSerializer(sales_return).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        with transaction.atomic():
            sales_return = get_object_or_404(
                SalesReturn.objects.select_for_update(), pk=kwargs["pk"], owner=request.user
            )
            if sales_return.status != SalesReturn.Status.DRAFT:
                raise ValidationError("مرجوعی تأییدشده یا لغوشده قابل ویرایش نیست.")
            requested_status = request.data.get("status")
            if requested_status not in (None, SalesReturn.Status.DRAFT, SalesReturn.Status.CONFIRMED):
                raise ValidationError({"status": "وضعیت مرجوعی معتبر نیست."})
            invoice = Invoice.objects.select_for_update().get(pk=sales_return.invoice_id)
            if invoice.status != Invoice.Status.ISSUED:
                raise ValidationError("فاکتور دیگر برای ثبت مرجوعی فعال نیست.")
            if "notes" in request.data:
                sales_return.notes = str(request.data["notes"])
            if requested_status == SalesReturn.Status.CONFIRMED:
                items = list(sales_return.items.select_related("invoice_item"))
                if not items:
                    raise ValidationError("مرجوعی بدون محصول قابل تأیید نیست.")
                locked_items = {
                    item.pk: item for item in InvoiceItem.objects.select_for_update().filter(
                        pk__in=[return_item.invoice_item_id for return_item in items]
                    )
                }
                for return_item in items:
                    validate_return_quantity(
                        locked_items[return_item.invoice_item_id],
                        return_item.quantity,
                        sales_return=sales_return,
                    )
                sales_return.status = SalesReturn.Status.CONFIRMED
            sales_return.save(update_fields=("notes", "status", "updated_at"))
            if sales_return.status == SalesReturn.Status.CONFIRMED:
                sync_return(sales_return)
        return Response(SalesReturnSerializer(sales_return).data)

    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            sales_return = get_object_or_404(
                SalesReturn.objects.select_for_update(), pk=kwargs["pk"], owner=request.user
            )
            if sales_return.status == SalesReturn.Status.CONFIRMED:
                reverse_return(sales_return)
            sales_return.status = SalesReturn.Status.CANCELLED
            sales_return.save(update_fields=("status", "updated_at"))
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=("post",), url_path="items")
    def add_item(self, request, pk=None):
        serializer = AddSalesReturnItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            sales_return = get_object_or_404(
                SalesReturn.objects.select_for_update(), pk=pk, owner=request.user
            )
            if sales_return.status != SalesReturn.Status.DRAFT:
                raise ValidationError("فقط مرجوعی پیش‌نویس قابل ویرایش است.")
            invoice = Invoice.objects.select_for_update().get(pk=sales_return.invoice_id)
            if invoice.status != Invoice.Status.ISSUED:
                raise ValidationError("فاکتور دیگر برای ثبت مرجوعی فعال نیست.")
            invoice_item = get_object_or_404(
                InvoiceItem.objects.select_for_update(),
                pk=serializer.validated_data["invoice_item"].pk,
                invoice=sales_return.invoice,
            )
            if sales_return.items.filter(invoice_item=invoice_item).exists():
                raise ValidationError({"invoice_item": "این محصول قبلاً به مرجوعی اضافه شده است."})
            quantity = serializer.validated_data["quantity"]
            validate_return_quantity(invoice_item, quantity, sales_return=sales_return)
            item = SalesReturnItem.objects.create(
                sales_return=sales_return,
                invoice_item=invoice_item,
                product_name_snapshot=invoice_item.product_name,
                brand_snapshot=invoice_item.brand,
                unit_snapshot=invoice_item.unit,
                quantity=quantity,
                unit_price=invoice_item.unit_price,
            )
            sales_return.recalculate_total()
        return Response(SalesReturnItemSerializer(item).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=("patch", "delete"), url_path=r"items/(?P<item_id>[^/.]+)")
    def item_detail(self, request, pk=None, item_id=None):
        with transaction.atomic():
            sales_return = get_object_or_404(
                SalesReturn.objects.select_for_update(), pk=pk, owner=request.user
            )
            if sales_return.status != SalesReturn.Status.DRAFT:
                raise ValidationError("فقط مرجوعی پیش‌نویس قابل ویرایش است.")
            invoice = Invoice.objects.select_for_update().get(pk=sales_return.invoice_id)
            if invoice.status != Invoice.Status.ISSUED:
                raise ValidationError("فاکتور دیگر برای ثبت مرجوعی فعال نیست.")
            item = get_object_or_404(
                SalesReturnItem.objects.select_related("invoice_item"),
                pk=item_id, sales_return=sales_return,
            )
            if request.method == "DELETE":
                item.delete()
                sales_return.recalculate_total()
                return Response(status=status.HTTP_204_NO_CONTENT)
            serializer = UpdateSalesReturnItemSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            invoice_item = InvoiceItem.objects.select_for_update().get(pk=item.invoice_item_id)
            quantity = serializer.validated_data["quantity"]
            validate_return_quantity(invoice_item, quantity, sales_return=sales_return)
            item.quantity = quantity
            item.save(update_fields=("quantity", "line_total", "updated_at"))
            sales_return.recalculate_total()
        return Response(SalesReturnItemSerializer(item).data)
