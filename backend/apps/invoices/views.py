from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import DecimalField, Prefetch, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.companies.models import SellerProfile
from apps.orders.models import SalesOrder

from .models import Invoice, InvoiceItem
from .pdf import build_invoice_pdf
from .serializers import (
    InvoiceDetailSerializer,
    InvoiceListSerializer,
    IssueInvoiceSerializer,
)


def invoice_items_with_return_totals():
    return InvoiceItem.objects.annotate(
        _confirmed_returned_quantity=Coalesce(
            Sum(
                "sales_return_items__quantity",
                filter=Q(sales_return_items__sales_return__status="confirmed"),
            ),
            Value(Decimal("0.000")),
            output_field=DecimalField(max_digits=12, decimal_places=3),
        )
    )


class InvoiceViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = ("get", "post", "delete", "head", "options")

    def get_queryset(self):
        queryset = Invoice.objects.filter(owner=self.request.user)
        if self.action in ("retrieve", "pdf"):
            queryset = queryset.prefetch_related(
                Prefetch("items", queryset=invoice_items_with_return_totals())
            )
        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return IssueInvoiceSerializer
        if self.action == "list":
            return InvoiceListSerializer
        return InvoiceDetailSerializer

    def create(self, request, *args, **kwargs):
        input_serializer = IssueInvoiceSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        data = input_serializer.validated_data
        try:
            with transaction.atomic():
                user_model = type(request.user)
                owner = user_model.objects.select_for_update().get(pk=request.user.pk)
                order = (
                    SalesOrder.objects.select_for_update()
                    .select_related("customer")
                    .prefetch_related("items")
                    .get(pk=data["sales_order"].pk)
                )
                seller = SellerProfile.objects.select_for_update().get(pk=data["seller_profile"].pk)

                if order.owner_id != owner.id:
                    raise ValidationError({"sales_order": "سفارش انتخاب‌شده معتبر نیست."})
                if order.status != SalesOrder.Status.CONFIRMED:
                    raise ValidationError({"sales_order": "فقط سفارش تأییدشده قابل صدور فاکتور است."})
                order_items = list(order.items.all())
                if not order_items:
                    raise ValidationError({"sales_order": "سفارش بدون محصول قابل صدور فاکتور نیست."})
                if seller.owner_id != owner.id or not seller.is_active:
                    raise ValidationError({"seller_profile": "فروشنده انتخاب‌شده معتبر نیست."})
                active_invoice = (
                    Invoice.objects.select_for_update()
                    .filter(sales_order=order, status=Invoice.Status.ISSUED)
                    .first()
                )
                if active_invoice and order.version <= active_invoice.source_order_version:
                    raise ValidationError({"sales_order": "سفارش پس از صدور فاکتور تغییری نکرده است؛ صدور نسخه تکراری مجاز نیست."})

                subtotal = sum((item.line_total for item in order_items), start=Decimal("0.00"))
                final_amount = subtotal - data["discount_amount"] + data["tax_amount"] + data["duties_amount"]
                if final_amount < 0:
                    raise ValidationError({"discount_amount": "تخفیف نمی‌تواند مبلغ نهایی را منفی کند."})

                last_invoice = Invoice.objects.filter(owner=owner).order_by("-id").first()
                sequence = int(last_invoice.invoice_number.split("-")[-1]) + 1 if last_invoice else 1
                invoice_number = f"INV-{sequence:06d}"
                customer = order.customer
                invoice = Invoice.objects.create(
                    owner=owner,
                    sales_order=order,
                    seller_profile=seller,
                    invoice_number=invoice_number,
                    status=Invoice.Status.SUPERSEDED if active_invoice else Invoice.Status.ISSUED,
                    revision_of=(active_invoice.revision_of or active_invoice) if active_invoice else None,
                    revision_number=active_invoice.revision_number + 1 if active_invoice else 1,
                    source_order_version=order.version,
                    seller_name=seller.name,
                    seller_phone_number=seller.phone_number,
                    seller_address=seller.address,
                    seller_economic_code=seller.economic_code,
                    seller_national_id=seller.national_id,
                    seller_registration_number=seller.registration_number,
                    seller_postal_code=seller.postal_code,
                    buyer_name=customer.name,
                    buyer_company_name=customer.company_name,
                    buyer_phone_number=customer.phone_number,
                    buyer_address=customer.address,
                    buyer_economic_code=customer.economic_code,
                    buyer_postal_code=customer.postal_code,
                    subtotal=subtotal,
                    discount_amount=data["discount_amount"],
                    tax_amount=data["tax_amount"],
                    duties_amount=data["duties_amount"],
                    final_amount=final_amount,
                    notes=data["notes"],
                )
                InvoiceItem.objects.bulk_create([
                    InvoiceItem(
                        invoice=invoice,
                        product=item.product,
                        product_name=item.product_name_snapshot,
                        brand=item.brand_snapshot,
                        unit=item.unit_snapshot,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                        line_total=item.line_total,
                    )
                    for item in order_items
                ])
                if active_invoice:
                    active_invoice.status = Invoice.Status.SUPERSEDED
                    active_invoice.save(update_fields=("status", "updated_at"))
                    invoice.status = Invoice.Status.ISSUED
                    invoice.save(update_fields=("status", "updated_at"))
        except (SalesOrder.DoesNotExist, SellerProfile.DoesNotExist):
            raise ValidationError("سفارش یا فروشنده انتخاب‌شده معتبر نیست.")
        except IntegrityError:
            raise ValidationError("صدور فاکتور تکراری مجاز نیست.")

        invoice = Invoice.objects.prefetch_related(
            Prefetch("items", queryset=invoice_items_with_return_totals())
        ).get(pk=invoice.pk)
        return Response(InvoiceDetailSerializer(invoice).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            invoice = get_object_or_404(
                Invoice.objects.select_for_update(), pk=kwargs["pk"], owner=request.user
            )
            invoice.status = Invoice.Status.CANCELLED
            invoice.save(update_fields=("status", "updated_at"))
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=("get",))
    def pdf(self, request, pk=None):
        invoice = self.get_object()
        content = build_invoice_pdf(invoice)
        response = HttpResponse(content, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="invoice-{invoice.invoice_number}.pdf"'
        )
        return response
