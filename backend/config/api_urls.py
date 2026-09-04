from django.urls import include, path
from apps.orders.report_views import DashboardView


urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("reports/", include("apps.orders.report_urls")),
    path("auth/", include("apps.accounts.urls")),
    path("subscriptions/", include("apps.subscriptions.urls")),
    path("support/", include("apps.support.urls")),
    path("platform-admin/", include("apps.subscriptions.platform_admin_urls")),
    path("products/", include("apps.products.urls")),
    path("inventory/", include("apps.products.inventory_urls")),
    path("customers/", include("apps.customers.urls")),
    path("orders/", include("apps.orders.urls")),
    path("returns/", include("apps.orders.return_urls")),
    path("purchases/", include("apps.purchases.urls")),
    path("companies/", include("apps.companies.urls")),
    path("invoices/", include("apps.invoices.urls")),
]
