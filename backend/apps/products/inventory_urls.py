from django.urls import path

from .inventory_views import InventoryDetailView, InventoryListView


urlpatterns = [
    path("", InventoryListView.as_view(), name="inventory-list"),
    path("<int:product_id>/", InventoryDetailView.as_view(), name="inventory-detail"),
]
