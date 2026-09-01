from django.core.management.base import BaseCommand
from django.db import transaction

from apps.subscriptions.models import SubscriptionOrder, SubscriptionPayment, UserSubscription


class Command(BaseCommand):
    help = "Repair approved-payment orders that incorrectly remain pending."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        active_users = UserSubscription.objects.filter(status=UserSubscription.Status.ACTIVE).values("user_id")
        approved_orders = SubscriptionPayment.objects.filter(status=SubscriptionPayment.Status.APPROVED).values("subscription_order_id")
        queryset = SubscriptionOrder.objects.select_for_update().filter(
            status=SubscriptionOrder.Status.PENDING, user_id__in=active_users, id__in=approved_orders
        )
        count = queryset.count()
        if options["dry_run"]:
            transaction.set_rollback(True)
            self.stdout.write(f"{count} inconsistent record(s) found; no changes made.")
            return
        queryset.update(status=SubscriptionOrder.Status.APPROVED)
        self.stdout.write(self.style.SUCCESS(f"{count} record(s) repaired."))
