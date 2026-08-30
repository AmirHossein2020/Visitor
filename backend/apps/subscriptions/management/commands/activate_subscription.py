from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.subscriptions.models import SubscriptionPlan, UserSubscription


class Command(BaseCommand):
    help = "Activate a finite development subscription for an existing user."

    def add_arguments(self, parser):
        parser.add_argument("email")
        parser.add_argument("--plan", default="monthly-development")

    @transaction.atomic
    def handle(self, email, plan, **options):
        try:
            user = get_user_model().objects.get(email__iexact=email)
            selected_plan = SubscriptionPlan.objects.get(slug=plan, is_active=True)
        except get_user_model().DoesNotExist as exc:
            raise CommandError("User not found.") from exc
        except SubscriptionPlan.DoesNotExist as exc:
            raise CommandError("Active plan not found.") from exc
        now = timezone.now()
        UserSubscription.objects.filter(user=user, status="active").update(status="cancelled")
        UserSubscription.objects.create(
            user=user, plan=selected_plan, status="active", starts_at=now,
            expires_at=now + timedelta(days=selected_plan.duration_days),
        )
        self.stdout.write(self.style.SUCCESS(f"Subscription activated for {user.email}."))
