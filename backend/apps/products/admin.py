from django.contrib import admin

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "brand", "owner", "default_price", "unit", "is_active")
    list_filter = ("is_active", "unit")
    search_fields = ("name", "brand", "owner__email")
