from decimal import Decimal

from rest_framework import serializers
from django.db.models import Sum

from apps.companies.models import SellerProfile
from apps.orders.models import SalesOrder

from .models import Invoice, InvoiceItem


class InvoiceItemSerializer(serializers.ModelSerializer):
    returned_quantity = serializers.SerializerMethodField()
    remaining_returnable_quantity = serializers.SerializerMethodField()

    def get_returned_quantity(self, obj):
        if not hasattr(obj, "_confirmed_returned_quantity"):
            obj._confirmed_returned_quantity = obj.sales_return_items.filter(
                sales_return__status="confirmed"
            ).aggregate(total=Sum("quantity"))["total"] or Decimal("0.000")
        return obj._confirmed_returned_quantity

    def get_remaining_returnable_quantity(self, obj):
        return obj.quantity - self.get_returned_quantity(obj)

    class Meta:
        model = InvoiceItem
        fields = ("id", "product", "product_name", "brand", "unit", "quantity", "returned_quantity", "remaining_returnable_quantity", "unit_price", "line_total", "description", "created_at")
        read_only_fields = fields


class InvoiceListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Invoice
        fields = ("id", "invoice_number", "status", "status_display", "issued_at", "seller_name", "buyer_name", "final_amount", "revision_number")
        read_only_fields = fields


class InvoiceDetailSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    items = InvoiceItemSerializer(many=True, read_only=True)
    is_active = serializers.SerializerMethodField()
    previous_invoice = serializers.SerializerMethodField()
    replacement_invoice = serializers.SerializerMethodField()
    has_stamp = serializers.SerializerMethodField()
    has_signature = serializers.SerializerMethodField()

    @staticmethod
    def _link(invoice):
        return {"id": invoice.id, "invoice_number": invoice.invoice_number, "revision_number": invoice.revision_number} if invoice else None

    def get_is_active(self, obj):
        return obj.status == Invoice.Status.ISSUED

    def get_previous_invoice(self, obj):
        if obj.revision_number <= 1:
            return None
        root = obj.revision_of or obj
        previous = Invoice.objects.filter(
            owner=obj.owner, sales_order=obj.sales_order,
            revision_of=root, revision_number=obj.revision_number - 1,
        ).first()
        return self._link(previous or (root if obj.revision_number == 2 else None))

    def get_replacement_invoice(self, obj):
        root = obj.revision_of or obj
        return self._link(Invoice.objects.filter(
            owner=obj.owner, sales_order=obj.sales_order,
            revision_of=root, revision_number=obj.revision_number + 1,
        ).first())

    def get_has_stamp(self, obj): return bool(obj.stamp_snapshot)
    def get_has_signature(self, obj): return bool(obj.signature_snapshot)

    class Meta:
        model = Invoice
        fields = (
            "id", "invoice_number", "status", "status_display", "issued_at",
            "revision_number", "source_order_version", "is_active",
            "previous_invoice", "replacement_invoice",
            "seller_name", "seller_phone_number", "seller_address",
            "seller_economic_code", "seller_national_id",
            "seller_registration_number", "seller_postal_code",
            "buyer_name", "buyer_company_name", "buyer_phone_number",
            "buyer_address", "buyer_economic_code", "buyer_postal_code",
            "subtotal", "discount_amount", "tax_amount", "duties_amount",
            "final_amount", "notes", "has_stamp", "has_signature", "items", "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "invoice_number", "status", "status_display", "issued_at",
            "revision_number", "source_order_version", "is_active",
            "previous_invoice", "replacement_invoice",
            "seller_name", "seller_phone_number", "seller_address",
            "seller_economic_code", "seller_national_id",
            "seller_registration_number", "seller_postal_code",
            "buyer_name", "buyer_company_name", "buyer_phone_number",
            "buyer_address", "buyer_economic_code", "buyer_postal_code",
            "subtotal", "discount_amount", "tax_amount", "duties_amount",
            "final_amount", "items", "created_at", "updated_at",
        )


class IssueInvoiceSerializer(serializers.Serializer):
    sales_order = serializers.PrimaryKeyRelatedField(queryset=SalesOrder.objects.all())
    seller_profile = serializers.PrimaryKeyRelatedField(queryset=SellerProfile.objects.all())
    discount_amount = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal("0"), default=Decimal("0"))
    tax_amount = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal("0"), default=Decimal("0"))
    duties_amount = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal("0"), default=Decimal("0"))
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    include_stamp = serializers.BooleanField(required=False, default=False)
    include_signature = serializers.BooleanField(required=False, default=False)
