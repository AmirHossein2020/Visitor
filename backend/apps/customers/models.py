from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models


phone_validator = RegexValidator(
    regex=r"^[0-9+()\-\s]{7,25}$",
    message="شماره تماس واردشده معتبر نیست.",
)


class Customer(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customers",
    )
    name = models.CharField(max_length=200)
    phone_number = models.CharField(
        max_length=25,
        blank=True,
        validators=[phone_validator],
    )
    company_name = models.CharField(max_length=200, blank=True)
    address = models.CharField(max_length=500, blank=True)
    economic_code = models.CharField(max_length=30, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
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
