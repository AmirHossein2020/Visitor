from decimal import Decimal

from django.db.models import DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from rest_framework import permissions
from apps.subscriptions.permissions import HasActiveSubscription
from rest_framework.response import Response
from rest_framework.views import APIView

from .inventory_serializers import InventoryProductSerializer, StockMovementSerializer
from .models import Product


stock_output = DecimalField(max_digits=18, decimal_places=3)


def inventory_queryset(user):
    return Product.objects.filter(owner=user).annotate(
        current_stock=Coalesce(
            Sum("stock_movements__quantity"),
            Value(Decimal("0.000")),
            output_field=stock_output,
        )
    )


class InventoryListView(APIView):
    permission_classes = (permissions.IsAuthenticated, HasActiveSubscription)

    def get(self, request):
        queryset = inventory_queryset(request.user).order_by("name")
        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(brand__icontains=search))
        return Response(InventoryProductSerializer(queryset, many=True).data)


class InventoryDetailView(APIView):
    permission_classes = (permissions.IsAuthenticated, HasActiveSubscription)

    def get(self, request, product_id):
        product = get_object_or_404(inventory_queryset(request.user), pk=product_id)
        movements = product.stock_movements.filter(owner=request.user).order_by("-created_at")[:50]
        return Response({
            "product": InventoryProductSerializer(product).data,
            "movements": StockMovementSerializer(movements, many=True).data,
        })
