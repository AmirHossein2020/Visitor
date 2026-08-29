from decimal import Decimal

from rest_framework import serializers

from apps.companies.models import SellerProfile
from apps.orders.models import SalesOrder

from .models import Invoice, InvoiceItem


class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ("id", "product", "product_name", "brand", "unit", "quantity", "unit_price", "line_total", "description", "created_at")
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
            "final_amount", "notes", "items", "created_at", "updated_at",
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
