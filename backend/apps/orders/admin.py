from django.contrib import admin

from .models import SalesOrder, SalesOrderItem, SalesReturn, SalesReturnItem


class SalesOrderItemInline(admin.TabularInline):
    model = SalesOrderItem
    extra = 0
    readonly_fields = ("line_total",)


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "owner", "status", "total_amount", "created_at")
    list_filter = ("status",)
    inlines = (SalesOrderItemInline,)


class SalesReturnItemInline(admin.TabularInline):
    model = SalesReturnItem
    extra = 0
    readonly_fields = ("line_total",)


@admin.register(SalesReturn)
class SalesReturnAdmin(admin.ModelAdmin):
    list_display = ("id", "invoice", "owner", "status", "total_amount", "created_at")
    list_filter = ("status",)
    inlines = (SalesReturnItemInline,)
