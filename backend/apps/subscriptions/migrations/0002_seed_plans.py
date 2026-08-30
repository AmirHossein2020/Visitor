from decimal import Decimal

from django.db import migrations


def seed_plans(apps, schema_editor):
    Plan = apps.get_model("subscriptions", "SubscriptionPlan")
    Plan.objects.get_or_create(
        slug="monthly-development",
        defaults={
            "name": "اشتراک ماهانه",
            "billing_period": "monthly",
            "duration_days": 30,
            "price": Decimal("990000.00"),
            "description": "دسترسی یک‌ماهه به همه امکانات فعلی سامانه",
            "sort_order": 1,
        },
    )
    Plan.objects.get_or_create(
        slug="yearly-development",
        defaults={
            "name": "اشتراک سالانه",
            "billing_period": "yearly",
            "duration_days": 365,
            "price": Decimal("9900000.00"),
            "description": "دسترسی یک‌ساله به همه امکانات فعلی سامانه",
            "is_featured": True,
            "sort_order": 2,
        },
    )


class Migration(migrations.Migration):
    dependencies = [("subscriptions", "0001_initial")]
    operations = [migrations.RunPython(seed_plans, migrations.RunPython.noop)]
