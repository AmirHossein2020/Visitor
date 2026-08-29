from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("orders", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="salesorder",
            name="version",
            field=models.PositiveIntegerField(default=1),
        ),
    ]
