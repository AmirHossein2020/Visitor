from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Product(models.Model):
    class Unit(models.TextChoices):
        ITEM = "item", "عدد"
        PACKAGE = "package", "بسته"
        CARTON = "carton", "کارتن"
        KILOGRAM = "kilogram", "کیلوگرم"
        GRAM = "gram", "گرم"
        LITER = "liter", "لیتر"
        METER = "meter", "متر"
        OTHER = "other", "سایر"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="products",
    )
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=120, blank=True)
    default_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    unit = models.CharField(max_length=20, choices=Unit.choices)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)
        indexes = [
            models.Index(fields=("owner", "is_active")),
            models.Index(fields=("owner", "name")),
        ]

    def __str__(self):
        return self.name


class StockMovement(models.Model):
    class Type(models.TextChoices):
        PURCHASE_IN = "purchase_in", "ورود از خرید"
        SALE_OUT = "sale_out", "خروج از فروش"
        RETURN_IN = "return_in", "ورود از مرجوعی"
        REVERSAL = "reversal", "برگشت اثر"
        MANUAL_ADJUSTMENT = "manual_adjustment", "اصلاح دستی"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="stock_movements"
    )
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="stock_movements")
    movement_type = models.CharField(max_length=24, choices=Type.choices)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    reference_type = models.CharField(max_length=30)
    reference_id = models.PositiveBigIntegerField()
    notes = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("owner", "product", "movement_type", "reference_type", "reference_id"),
                name="unique_stock_movement_source",
            ),
        ]
        indexes = [
            models.Index(fields=("owner", "product", "created_at")),
            models.Index(fields=("reference_type", "reference_id")),
        ]

    def __str__(self):
        return f"{self.product} {self.quantity}"
