from decimal import Decimal

from rest_framework import serializers

from apps.customers.models import Customer
from apps.products.models import Product

from .models import SalesOrder, SalesOrderItem


class SalesOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesOrderItem
        fields = (
            "id", "product", "product_name_snapshot", "brand_snapshot",
            "unit_snapshot", "quantity", "unit_price", "line_total",
            "created_at", "updated_at",
        )
        read_only_fields = fields


class SalesOrderListSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = SalesOrder
        fields = ("id", "customer", "customer_name", "status", "status_display", "total_amount", "version", "created_at", "updated_at")
        read_only_fields = ("id", "customer_name", "status_display", "total_amount", "version", "created_at", "updated_at")


class SalesOrderSerializer(SalesOrderListSerializer):
    items = SalesOrderItemSerializer(many=True, read_only=True)
    active_invoice = serializers.SerializerMethodField()
    invoice_needs_revision = serializers.SerializerMethodField()

    class Meta(SalesOrderListSerializer.Meta):
        fields = SalesOrderListSerializer.Meta.fields + ("notes", "items", "active_invoice", "invoice_needs_revision")

    def _active_invoice(self, obj):
        if not hasattr(self, "_invoice_cache"):
            self._invoice_cache = {}
        if obj.pk not in self._invoice_cache:
            self._invoice_cache[obj.pk] = obj.invoices.filter(status="issued").only(
                "id", "invoice_number", "source_order_version", "revision_number"
            ).first()
        return self._invoice_cache[obj.pk]

    def get_active_invoice(self, obj):
        invoice = self._active_invoice(obj)
        if not invoice:
            return None
        return {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "revision_number": invoice.revision_number,
            "source_order_version": invoice.source_order_version,
        }

    def get_invoice_needs_revision(self, obj):
        invoice = self._active_invoice(obj)
        return bool(invoice and obj.version > invoice.source_order_version)

    def validate_customer(self, customer):
        request = self.context["request"]
        if customer.owner_id != request.user.id or not customer.is_active:
            raise serializers.ValidationError("مشتری انتخاب‌شده معتبر نیست.")
        return customer


class AddOrderItemSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=Decimal("0.001"))
    unit_price = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0, required=False)

    def validate_product(self, product):
        request = self.context["request"]
        if product.owner_id != request.user.id or not product.is_active:
            raise serializers.ValidationError("محصول انتخاب‌شده معتبر نیست.")
        return product


class UpdateOrderItemSerializer(serializers.Serializer):
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=Decimal("0.001"), required=False)
    unit_price = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0, required=False)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("مقدار یا قیمت را وارد کنید.")
        return attrs
