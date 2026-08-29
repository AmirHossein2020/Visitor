from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Purchase, PurchaseItem
from .serializers import (
    AddPurchaseItemSerializer,
    PurchaseItemSerializer,
    PurchaseListSerializer,
    PurchaseSerializer,
    UpdatePurchaseItemSerializer,
)
from apps.products.inventory import reverse_purchase, sync_purchase, sync_purchase_item


class PurchaseViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        queryset = Purchase.objects.filter(owner=self.request.user).select_related("customer")
        if self.action == "retrieve":
            queryset = queryset.prefetch_related("items")
        return queryset

    def get_serializer_class(self):
        return PurchaseListSerializer if self.action == "list" else PurchaseSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            return super().update(request, *args, **kwargs)

    def perform_update(self, serializer):
        old_status = serializer.instance.status
        purchase = serializer.save()
        if purchase.status == Purchase.Status.CANCELLED and old_status == Purchase.Status.CONFIRMED:
            reverse_purchase(purchase)
        else:
            sync_purchase(purchase)

    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            purchase = get_object_or_404(
                Purchase.objects.select_for_update(), pk=kwargs["pk"], owner=request.user
            )
            if purchase.status == Purchase.Status.CONFIRMED:
                reverse_purchase(purchase)
            purchase.status = Purchase.Status.CANCELLED
            purchase.save(update_fields=("status", "updated_at"))
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=("post",), url_path="items")
    def add_item(self, request, pk=None):
        input_serializer = AddPurchaseItemSerializer(data=request.data, context={"request": request})
        input_serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            purchase = get_object_or_404(Purchase.objects.select_for_update(), pk=pk, owner=request.user)
            product = input_serializer.validated_data["product"]
            item = PurchaseItem.objects.create(
                purchase=purchase,
                product=product,
                product_name_snapshot=product.name,
                brand_snapshot=product.brand,
                unit_snapshot=product.get_unit_display(),
                quantity=input_serializer.validated_data["quantity"],
                unit_price=input_serializer.validated_data["unit_price"],
            )
            purchase.recalculate_total()
            if purchase.status == Purchase.Status.CONFIRMED:
                sync_purchase_item(item)
        return Response(PurchaseItemSerializer(item).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=("patch", "delete"), url_path=r"items/(?P<item_id>[^/.]+)")
    def item_detail(self, request, pk=None, item_id=None):
        with transaction.atomic():
            purchase = get_object_or_404(Purchase.objects.select_for_update(), pk=pk, owner=request.user)
            item = get_object_or_404(PurchaseItem, pk=item_id, purchase=purchase)
            if request.method == "DELETE":
                if purchase.status == Purchase.Status.CONFIRMED:
                    sync_purchase_item(item, active=False)
                item.delete()
                purchase.recalculate_total()
                return Response(status=status.HTTP_204_NO_CONTENT)
            input_serializer = UpdatePurchaseItemSerializer(data=request.data)
            input_serializer.is_valid(raise_exception=True)
            for field, value in input_serializer.validated_data.items():
                setattr(item, field, value)
            item.save()
            purchase.recalculate_total()
            if purchase.status == Purchase.Status.CONFIRMED:
                sync_purchase_item(item)
        return Response(PurchaseItemSerializer(item).data)
