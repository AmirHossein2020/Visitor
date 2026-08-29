from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import SalesOrder, SalesOrderItem
from .serializers import (
    AddOrderItemSerializer,
    SalesOrderItemSerializer,
    SalesOrderListSerializer,
    SalesOrderSerializer,
    UpdateOrderItemSerializer,
)
from apps.products.inventory import reverse_order, sync_order, sync_order_item


class SalesOrderViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        queryset = SalesOrder.objects.filter(owner=self.request.user).select_related("customer")
        if self.action == "retrieve":
            queryset = queryset.prefetch_related("items")
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return SalesOrderListSerializer
        return SalesOrderSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            return super().update(request, *args, **kwargs)

    def perform_update(self, serializer):
        order = serializer.instance
        old_status = order.status
        meaningful_fields = {"customer", "notes"}
        changed = any(
            field in serializer.validated_data
            and getattr(order, f"{field}_id" if field == "customer" else field)
            != (serializer.validated_data[field].id if field == "customer" else serializer.validated_data[field])
            for field in meaningful_fields
        )
        order = serializer.save(version=order.version + 1 if changed else order.version)
        if order.status == SalesOrder.Status.CANCELLED and old_status == SalesOrder.Status.CONFIRMED:
            reverse_order(order)
        else:
            sync_order(order)

    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            order = get_object_or_404(
                SalesOrder.objects.select_for_update(), pk=kwargs["pk"], owner=request.user
            )
            if order.status == SalesOrder.Status.CONFIRMED:
                reverse_order(order)
            order.status = SalesOrder.Status.CANCELLED
            order.save(update_fields=("status", "updated_at"))
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=("post",), url_path="items")
    def add_item(self, request, pk=None):
        input_serializer = AddOrderItemSerializer(
            data=request.data,
            context={"request": request},
        )
        input_serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            order = get_object_or_404(
                SalesOrder.objects.select_for_update(),
                pk=pk,
                owner=request.user,
            )
            product = input_serializer.validated_data["product"]
            item = SalesOrderItem.objects.create(
                order=order,
                product=product,
                product_name_snapshot=product.name,
                brand_snapshot=product.brand,
                unit_snapshot=product.get_unit_display(),
                quantity=input_serializer.validated_data["quantity"],
                unit_price=input_serializer.validated_data.get(
                    "unit_price",
                    product.default_price,
                ),
            )
            order.recalculate_total(increment_version=True)
            if order.status == SalesOrder.Status.CONFIRMED:
                sync_order_item(item)
        return Response(SalesOrderItemSerializer(item).data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=("patch", "delete"),
        url_path=r"items/(?P<item_id>[^/.]+)",
    )
    def item_detail(self, request, pk=None, item_id=None):
        with transaction.atomic():
            order = get_object_or_404(
                SalesOrder.objects.select_for_update(),
                pk=pk,
                owner=request.user,
            )
            item = get_object_or_404(SalesOrderItem, pk=item_id, order=order)
            if request.method == "DELETE":
                if order.status == SalesOrder.Status.CONFIRMED:
                    sync_order_item(item, active=False)
                item.delete()
                order.recalculate_total(increment_version=True)
                return Response(status=status.HTTP_204_NO_CONTENT)

            input_serializer = UpdateOrderItemSerializer(data=request.data)
            input_serializer.is_valid(raise_exception=True)
            changed = any(
                getattr(item, field) != value
                for field, value in input_serializer.validated_data.items()
            )
            for field, value in input_serializer.validated_data.items():
                setattr(item, field, value)
            if changed:
                item.save()
                order.recalculate_total(increment_version=True)
                if order.status == SalesOrder.Status.CONFIRMED:
                    sync_order_item(item)
        return Response(SalesOrderItemSerializer(item).data)
