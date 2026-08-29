from django.contrib import admin

from .models import Invoice, InvoiceItem


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    readonly_fields = ("product_name", "brand", "unit", "quantity", "unit_price", "line_total")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "buyer_name", "seller_name", "owner", "status", "final_amount", "issued_at")
    list_filter = ("status",)
    search_fields = ("invoice_number", "buyer_name", "seller_name", "owner__email")
    inlines = (InvoiceItemInline,)
