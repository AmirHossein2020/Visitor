from django.db import migrations, models
import django.core.validators


def populate_snapshots_and_repair(apps, schema_editor):
    Order = apps.get_model("subscriptions", "SubscriptionOrder")
    Payment = apps.get_model("subscriptions", "SubscriptionPayment")
    Subscription = apps.get_model("subscriptions", "UserSubscription")
    Order.objects.filter(original_price_snapshot=0).update(original_price_snapshot=models.F("amount_snapshot"))
    candidate_ids = Payment.objects.filter(
        status="approved", subscription_order__status="pending"
    ).values_list("subscription_order_id", flat=True)
    active_user_ids = Subscription.objects.filter(status="active").values_list("user_id", flat=True)
    repaired = Order.objects.filter(id__in=candidate_ids, user_id__in=active_user_ids, status="pending").update(status="approved")
    print(f"Subscription order repair: {repaired} record(s) repaired.")


class Migration(migrations.Migration):
    dependencies = [("subscriptions", "0004_platformsettings_platformadminauditlog")]
    operations = [
        migrations.AddField(
            model_name="subscriptionplan", name="discount_percent",
            field=models.PositiveSmallIntegerField(default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(99)]),
        ),
        migrations.AddField(
            model_name="subscriptionorder", name="discount_percent_snapshot",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="subscriptionorder", name="original_price_snapshot",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=18),
        ),
        migrations.RunPython(populate_snapshots_and_repair, migrations.RunPython.noop),
    ]
