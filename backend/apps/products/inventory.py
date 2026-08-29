from decimal import Decimal

from django.db import transaction

from .models import Product, StockMovement


ZERO = Decimal("0.000")


def reconcile_item_movement(*, owner_id, product_id, movement_type, reference_type, reference_id, quantity, notes=""):
    """Create or update one stable source movement; product locking serializes reconciliation."""
    with transaction.atomic():
        product = Product.objects.select_for_update().get(pk=product_id, owner_id=owner_id)
        movement, _ = StockMovement.objects.update_or_create(
            owner_id=owner_id,
            product=product,
            movement_type=movement_type,
            reference_type=reference_type,
            reference_id=reference_id,
            defaults={"quantity": quantity, "notes": notes},
        )
        return movement


def sync_purchase_item(item, *, active=None):
    active = item.purchase.status == "confirmed" if active is None else active
    movement = reconcile_item_movement(
        owner_id=item.purchase.owner_id, product_id=item.product_id,
        movement_type=StockMovement.Type.PURCHASE_IN,
        reference_type="purchase_item", reference_id=item.pk,
        quantity=item.quantity if active else ZERO,
        notes=f"خرید شماره {item.purchase_id}" if active else "اثر خرید غیرفعال شد",
    )
    if active:
        StockMovement.objects.filter(
            owner_id=item.purchase.owner_id, product_id=item.product_id,
            movement_type=StockMovement.Type.REVERSAL,
            reference_type="purchase_cancel_item", reference_id=item.pk,
        ).update(quantity=ZERO, notes="لغو خرید خنثی شد")
    return movement


def sync_purchase(purchase):
    for item in purchase.items.select_related("purchase"):
        sync_purchase_item(item)


def reverse_purchase(purchase):
    for item in purchase.items.select_related("purchase"):
        reconcile_item_movement(
            owner_id=purchase.owner_id, product_id=item.product_id,
            movement_type=StockMovement.Type.REVERSAL,
            reference_type="purchase_cancel_item", reference_id=item.pk,
            quantity=-item.quantity,
            notes=f"لغو خرید شماره {purchase.pk}",
        )


def sync_order_item(item, *, active=None):
    active = item.order.status == "confirmed" if active is None else active
    movement = reconcile_item_movement(
        owner_id=item.order.owner_id, product_id=item.product_id,
        movement_type=StockMovement.Type.SALE_OUT,
        reference_type="sales_order_item", reference_id=item.pk,
        quantity=-item.quantity if active else ZERO,
        notes=f"فروش سفارش {item.order_id}" if active else "اثر فروش غیرفعال شد",
    )
    if active:
        StockMovement.objects.filter(
            owner_id=item.order.owner_id, product_id=item.product_id,
            movement_type=StockMovement.Type.REVERSAL,
            reference_type="sales_order_cancel_item", reference_id=item.pk,
        ).update(quantity=ZERO, notes="لغو سفارش خنثی شد")
    return movement


def sync_order(order):
    for item in order.items.select_related("order"):
        sync_order_item(item)


def reverse_order(order):
    for item in order.items.select_related("order"):
        reconcile_item_movement(
            owner_id=order.owner_id, product_id=item.product_id,
            movement_type=StockMovement.Type.REVERSAL,
            reference_type="sales_order_cancel_item", reference_id=item.pk,
            quantity=item.quantity,
            notes=f"لغو سفارش شماره {order.pk}",
        )


def sync_return_item(item):
    active = item.sales_return.status == "confirmed"
    return reconcile_item_movement(
        owner_id=item.sales_return.owner_id, product_id=item.invoice_item.product_id,
        movement_type=StockMovement.Type.RETURN_IN,
        reference_type="sales_return_item", reference_id=item.pk,
        quantity=item.quantity if active else ZERO,
        notes=f"مرجوعی فاکتور {item.sales_return.invoice.invoice_number}" if active else "مرجوعی پیش‌نویس",
    )


def sync_return(sales_return):
    for item in sales_return.items.select_related("invoice_item", "sales_return__invoice"):
        sync_return_item(item)


def reverse_return(sales_return):
    for item in sales_return.items.select_related("invoice_item"):
        reconcile_item_movement(
            owner_id=sales_return.owner_id, product_id=item.invoice_item.product_id,
            movement_type=StockMovement.Type.REVERSAL,
            reference_type="sales_return_cancel_item", reference_id=item.pk,
            quantity=-item.quantity,
            notes=f"لغو مرجوعی شماره {sales_return.pk}",
        )
