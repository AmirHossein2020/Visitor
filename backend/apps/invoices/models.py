from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Invoice(models.Model):
    class Status(models.TextChoices):
        ISSUED = "issued", "صادرشده"
        CANCELLED = "cancelled", "لغوشده"
        SUPERSEDED = "superseded", "جایگزین‌شده"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="invoices")
    sales_order = models.ForeignKey("orders.SalesOrder", on_delete=models.PROTECT, related_name="invoices")
    seller_profile = models.ForeignKey("companies.SellerProfile", on_delete=models.SET_NULL, null=True, related_name="invoices")
    invoice_number = models.CharField(max_length=30)
    revision_of = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True,
        related_name="revisions",
    )
    revision_number = models.PositiveIntegerField(default=1)
    source_order_version = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ISSUED)
    issued_at = models.DateTimeField(default=timezone.now)

    seller_name = models.CharField(max_length=200)
    seller_phone_number = models.CharField(max_length=25, blank=True)
    seller_address = models.CharField(max_length=500, blank=True)
    seller_economic_code = models.CharField(max_length=30, blank=True)
    seller_national_id = models.CharField(max_length=30, blank=True)
    seller_registration_number = models.CharField(max_length=30, blank=True)
    seller_postal_code = models.CharField(max_length=20, blank=True)

    buyer_name = models.CharField(max_length=200)
    buyer_company_name = models.CharField(max_length=200, blank=True)
    buyer_phone_number = models.CharField(max_length=25, blank=True)
    buyer_address = models.CharField(max_length=500, blank=True)
    buyer_economic_code = models.CharField(max_length=30, blank=True)
    buyer_postal_code = models.CharField(max_length=20, blank=True)

    subtotal = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0)])
    discount_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    tax_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    duties_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    final_amount = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0)])
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-issued_at",)
        constraints = [
            models.UniqueConstraint(fields=("owner", "invoice_number"), name="unique_owner_invoice_number"),
            models.UniqueConstraint(fields=("sales_order",), condition=Q(status="issued"), name="one_issued_invoice_per_order"),
        ]
        indexes = [models.Index(fields=("owner", "issued_at"))]

    def __str__(self):
        return self.invoice_number


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("products.Product", on_delete=models.SET_NULL, null=True, related_name="invoice_items")
    product_name = models.CharField(max_length=200)
    brand = models.CharField(max_length=120, blank=True)
    unit = models.CharField(max_length=50)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2)
    line_total = models.DecimalField(max_digits=18, decimal_places=2)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return self.product_name
