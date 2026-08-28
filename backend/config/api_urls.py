from django.urls import include, path


urlpatterns = [
    path("auth/", include("apps.accounts.urls")),
    path("products/", include("apps.products.urls")),
    path("customers/", include("apps.customers.urls")),
    path("orders/", include("apps.orders.urls")),
]
