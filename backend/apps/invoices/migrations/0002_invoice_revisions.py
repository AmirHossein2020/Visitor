import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("invoices", "0001_initial"),
        ("orders", "0002_salesorder_version"),
    ]

    operations = [
        migrations.AddField(
            model_name="invoice",
            name="revision_number",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name="invoice",
            name="revision_of",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="revisions", to="invoices.invoice"),
        ),
        migrations.AddField(
            model_name="invoice",
            name="source_order_version",
            field=models.PositiveIntegerField(default=1),
        ),
    ]
