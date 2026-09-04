from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from uuid import uuid4
from pathlib import Path


phone_validator = RegexValidator(
    regex=r"^[0-9+()\-\s]{7,25}$",
    message="شماره تماس واردشده معتبر نیست.",
)


def seller_asset_path(instance, filename):
    return f"seller-assets/{instance.owner_id}/{uuid4().hex}{Path(filename).suffix.lower()}"


class SellerProfile(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="seller_profiles",
    )
    name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=25, blank=True, validators=[phone_validator])
    address = models.CharField(max_length=500, blank=True)
    economic_code = models.CharField(max_length=30, blank=True)
    national_id = models.CharField(max_length=30, blank=True)
    registration_number = models.CharField(max_length=30, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    stamp_image = models.FileField(upload_to=seller_asset_path, blank=True)
    signature_image = models.FileField(upload_to=seller_asset_path, blank=True)
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
