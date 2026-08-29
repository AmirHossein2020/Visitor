from decimal import Decimal

from rest_framework import serializers

from apps.invoices.models import Invoice, InvoiceItem

from .models import SalesReturn, SalesReturnItem


class SalesReturnItemSerializer(serializers.ModelSerializer):
    sold_quantity = serializers.DecimalField(
        source="invoice_item.quantity", max_digits=12, decimal_places=3, read_only=True
    )

    class Meta:
        model = SalesReturnItem
        fields = (
            "id", "invoice_item", "product_name_snapshot", "brand_snapshot",
            "unit_snapshot", "sold_quantity", "quantity", "unit_price",
            "line_total", "created_at", "updated_at",
        )
        read_only_fields = fields


class SalesReturnListSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source="invoice.invoice_number", read_only=True)
    customer_name = serializers.CharField(source="invoice.buyer_name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = SalesReturn
        fields = (
            "id", "invoice", "invoice_number", "customer_name", "status",
            "status_display", "total_amount", "created_at", "updated_at",
        )
        read_only_fields = fields


class SalesReturnSerializer(SalesReturnListSerializer):
    items = SalesReturnItemSerializer(many=True, read_only=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    class Meta(SalesReturnListSerializer.Meta):
        fields = SalesReturnListSerializer.Meta.fields + ("notes", "items")
        read_only_fields = SalesReturnListSerializer.Meta.read_only_fields + ("items",)


class CreateSalesReturnSerializer(serializers.Serializer):
    invoice = serializers.PrimaryKeyRelatedField(queryset=Invoice.objects.all())
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_invoice(self, invoice):
        request = self.context["request"]
        if invoice.owner_id != request.user.id:
            raise serializers.ValidationError("فاکتور انتخاب‌شده معتبر نیست.")
        if invoice.status != Invoice.Status.ISSUED:
            raise serializers.ValidationError("فقط برای فاکتور فعال می‌توان مرجوعی ثبت کرد.")
        return invoice


class AddSalesReturnItemSerializer(serializers.Serializer):
    invoice_item = serializers.PrimaryKeyRelatedField(queryset=InvoiceItem.objects.all())
    quantity = serializers.DecimalField(
        max_digits=12, decimal_places=3, min_value=Decimal("0.001")
    )


class UpdateSalesReturnItemSerializer(serializers.Serializer):
    quantity = serializers.DecimalField(
        max_digits=12, decimal_places=3, min_value=Decimal("0.001")
    )
