from decimal import Decimal
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def backfill_stock_movements(apps, schema_editor):
    StockMovement = apps.get_model("products", "StockMovement")
    PurchaseItem = apps.get_model("purchases", "PurchaseItem")
    SalesOrderItem = apps.get_model("orders", "SalesOrderItem")
    SalesReturnItem = apps.get_model("orders", "SalesReturnItem")

    movements = []
    for item in PurchaseItem.objects.filter(purchase__status="confirmed").select_related("purchase"):
        movements.append(StockMovement(owner_id=item.purchase.owner_id, product_id=item.product_id, movement_type="purchase_in", quantity=item.quantity, reference_type="purchase_item", reference_id=item.pk, notes=f"خرید شماره {item.purchase_id}"))
    for item in SalesOrderItem.objects.filter(order__status="confirmed").select_related("order"):
        movements.append(StockMovement(owner_id=item.order.owner_id, product_id=item.product_id, movement_type="sale_out", quantity=-item.quantity, reference_type="sales_order_item", reference_id=item.pk, notes=f"فروش سفارش {item.order_id}"))
    for item in SalesReturnItem.objects.filter(sales_return__status="confirmed").select_related("sales_return", "invoice_item"):
        if item.invoice_item.product_id:
            movements.append(StockMovement(owner_id=item.sales_return.owner_id, product_id=item.invoice_item.product_id, movement_type="return_in", quantity=item.quantity, reference_type="sales_return_item", reference_id=item.pk, notes=f"مرجوعی شماره {item.sales_return_id}"))
    StockMovement.objects.bulk_create(movements, ignore_conflicts=True)


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("products", "0001_initial"),
        ("purchases", "0001_initial"),
        ("orders", "0003_sales_returns"),
    ]

    operations = [
        migrations.CreateModel(
            name="StockMovement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("movement_type", models.CharField(choices=[("purchase_in", "ورود از خرید"), ("sale_out", "خروج از فروش"), ("return_in", "ورود از مرجوعی"), ("reversal", "برگشت اثر"), ("manual_adjustment", "اصلاح دستی")], max_length=24)),
                ("quantity", models.DecimalField(decimal_places=3, max_digits=14)),
                ("reference_type", models.CharField(max_length=30)),
                ("reference_id", models.PositiveBigIntegerField()),
                ("notes", models.CharField(blank=True, max_length=300)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="stock_movements", to=settings.AUTH_USER_MODEL)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="stock_movements", to="products.product")),
            ],
            options={"ordering": ("-created_at",), "indexes": [models.Index(fields=["owner", "product", "created_at"], name="products_st_owner_i_df2b41_idx"), models.Index(fields=["reference_type", "reference_id"], name="products_st_referen_03e101_idx")], "constraints": [models.UniqueConstraint(fields=("owner", "product", "movement_type", "reference_type", "reference_id"), name="unique_stock_movement_source")]},
        ),
        migrations.RunPython(backfill_stock_movements, migrations.RunPython.noop),
    ]
