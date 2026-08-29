from django.contrib import admin

from .models import SellerProfile


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "phone_number", "owner", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "phone_number", "economic_code", "national_id", "owner__email")
