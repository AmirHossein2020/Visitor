from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


MONEY_PLACES = Decimal("0.01")


class SalesOrder(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "پیش‌نویس"
        CONFIRMED = "confirmed", "تأییدشده"
        CANCELLED = "cancelled", "لغوشده"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sales_orders",
    )
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="sales_orders",
    )
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    notes = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("owner", "created_at")),
            models.Index(fields=("owner", "status")),
        ]

    def recalculate_total(self):
        total = sum(
            self.items.values_list("line_total", flat=True),
            start=Decimal("0.00"),
        )
        self.total_amount = total.quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)
        self.save(update_fields=("total_amount", "updated_at"))

    def __str__(self):
        return f"{self.customer} - {self.pk}"


class SalesOrderItem(models.Model):
    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="sales_order_items",
    )
    product_name_snapshot = models.CharField(max_length=200)
    brand_snapshot = models.CharField(max_length=120, blank=True)
    unit_snapshot = models.CharField(max_length=50)
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
    )
    unit_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    line_total = models.DecimalField(max_digits=18, decimal_places=2, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("created_at",)

    def save(self, *args, **kwargs):
        self.line_total = (self.quantity * self.unit_price).quantize(
            MONEY_PLACES,
            rounding=ROUND_HALF_UP,
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.product_name_snapshot
