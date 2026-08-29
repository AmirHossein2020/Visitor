from django.urls import include, path


urlpatterns = [
    path("auth/", include("apps.accounts.urls")),
    path("products/", include("apps.products.urls")),
    path("customers/", include("apps.customers.urls")),
    path("orders/", include("apps.orders.urls")),
    path("purchases/", include("apps.purchases.urls")),
    path("companies/", include("apps.companies.urls")),
    path("invoices/", include("apps.invoices.urls")),
]
