from rest_framework import serializers

from .models import Product, StockMovement


class InventoryProductSerializer(serializers.ModelSerializer):
    unit_display = serializers.CharField(source="get_unit_display", read_only=True)
    current_stock = serializers.DecimalField(max_digits=18, decimal_places=3, read_only=True)

    class Meta:
        model = Product
        fields = ("id", "name", "brand", "unit", "unit_display", "current_stock")
        read_only_fields = fields


class StockMovementSerializer(serializers.ModelSerializer):
    movement_type_display = serializers.CharField(source="get_movement_type_display", read_only=True)

    class Meta:
        model = StockMovement
        fields = (
            "id", "movement_type", "movement_type_display", "quantity",
            "reference_type", "reference_id", "notes", "created_at",
        )
        read_only_fields = fields
