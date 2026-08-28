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
