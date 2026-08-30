from django.contrib import admin, messages

from .models import SubscriptionOrder, SubscriptionPlan, UserSubscription


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "billing_period", "price", "is_active", "is_featured", "sort_order")
    list_editable = ("price", "is_active", "is_featured", "sort_order")


@admin.action(description="تأیید درخواست‌های انتخاب‌شده و فعال‌سازی اشتراک")
def approve_orders(modeladmin, request, queryset):
    approved = 0
    for order in queryset:
        try:
            order.approve(request.user)
            approved += 1
        except ValueError:
            continue
    modeladmin.message_user(request, f"{approved} درخواست تأیید شد.", messages.SUCCESS)


@admin.register(SubscriptionOrder)
class SubscriptionOrderAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "amount_snapshot", "status", "created_at")
    readonly_fields = ("user", "plan", "amount_snapshot", "status", "approved_at", "approved_by", "created_at", "updated_at")
    actions = (approve_orders,)


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "status", "starts_at", "expires_at")
    readonly_fields = ("approved_at", "approved_by", "created_at", "updated_at")
