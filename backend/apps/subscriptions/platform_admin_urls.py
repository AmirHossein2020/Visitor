from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .platform_admin import AdminOrderViewSet, AdminPaymentViewSet, AdminPlanViewSet, AdminSubscriptionViewSet, AdminUserViewSet, AuditLogViewSet, DashboardView, PlatformSettingsView

router = DefaultRouter()
router.register("users", AdminUserViewSet, basename="platform-user")
router.register("subscription-orders", AdminOrderViewSet, basename="platform-order")
router.register("subscriptions", AdminSubscriptionViewSet, basename="platform-subscription")
router.register("plans", AdminPlanViewSet, basename="platform-plan")
router.register("payments", AdminPaymentViewSet, basename="platform-payment")
router.register("audit-log", AuditLogViewSet, basename="platform-audit-log")

urlpatterns = [path("dashboard/", DashboardView.as_view()), path("settings/", PlatformSettingsView.as_view()), path("", include(router.urls))]
