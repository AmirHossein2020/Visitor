from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "company_name", "phone_number", "owner", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "company_name", "phone_number", "owner__email")
