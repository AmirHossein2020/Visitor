from django.contrib import admin

from .models import Product, StockMovement


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "brand", "owner", "default_price", "unit", "is_active")
    list_filter = ("is_active", "unit")
    search_fields = ("name", "brand", "owner__email")


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("product", "movement_type", "quantity", "reference_type", "reference_id", "created_at")
    list_filter = ("movement_type",)
    readonly_fields = ("created_at", "updated_at")
