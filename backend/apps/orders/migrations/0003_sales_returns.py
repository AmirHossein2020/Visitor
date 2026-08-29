import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("invoices", "0002_invoice_revisions"),
        ("orders", "0002_salesorder_version"),
    ]

    operations = [
        migrations.CreateModel(
            name="SalesReturn",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("draft", "پیش‌نویس"), ("confirmed", "تأییدشده"), ("cancelled", "لغوشده")], default="draft", max_length=12)),
                ("notes", models.TextField(blank=True)),
                ("total_amount", models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("invoice", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="sales_returns", to="invoices.invoice")),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sales_returns", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-created_at",), "indexes": [models.Index(fields=["owner", "created_at"], name="orders_sale_owner_i_77f38f_idx"), models.Index(fields=["invoice", "status"], name="orders_sale_invoice_52f14d_idx")]},
        ),
        migrations.CreateModel(
            name="SalesReturnItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("product_name_snapshot", models.CharField(max_length=200)),
                ("brand_snapshot", models.CharField(blank=True, max_length=120)),
                ("unit_snapshot", models.CharField(max_length=50)),
                ("quantity", models.DecimalField(decimal_places=3, max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal("0.001"))])),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=14, validators=[django.core.validators.MinValueValidator(0)])),
                ("line_total", models.DecimalField(decimal_places=2, editable=False, max_digits=18)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("invoice_item", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="sales_return_items", to="invoices.invoiceitem")),
                ("sales_return", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="orders.salesreturn")),
            ],
            options={"ordering": ("created_at",), "constraints": [models.UniqueConstraint(fields=("sales_return", "invoice_item"), name="unique_invoice_item_per_sales_return")]},
        ),
    ]
