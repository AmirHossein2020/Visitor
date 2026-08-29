from django.contrib import admin

from .models import Purchase, PurchaseItem


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 0
    readonly_fields = ("line_total",)


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "owner", "purchase_date", "status", "total_amount")
    list_filter = ("status", "purchase_date")
    inlines = (PurchaseItemInline,)
