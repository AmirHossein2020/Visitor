from django.conf import settings
from rest_framework.permissions import BasePermission


def active_subscription_for(user):
    if not user or not user.is_authenticated:
        return None
    if user.is_superuser:
        return True
    return next((subscription for subscription in user.subscriptions.select_related("plan").filter(status="active") if subscription.is_effective), None)


class HasActiveSubscription(BasePermission):
    message = "برای استفاده از امکانات کسب‌وکار، اشتراک فعال نیاز دارید."

    def has_permission(self, request, view):
        if getattr(settings, "SUBSCRIPTION_TEST_BYPASS", False):
            return True
        return bool(active_subscription_for(request.user))
