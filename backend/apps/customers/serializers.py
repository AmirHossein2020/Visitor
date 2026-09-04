from rest_framework import serializers

from .models import Customer
from apps.accounts.normalization import normalize_phone


class CustomerSerializer(serializers.ModelSerializer):
    def to_internal_value(self, data):
        data = data.copy()
        if "phone_number" in data:
            data["phone_number"] = normalize_phone(data["phone_number"])
        return super().to_internal_value(data)

    class Meta:
        model = Customer
        fields = (
            "id",
            "name",
            "phone_number",
            "company_name",
            "address",
            "economic_code",
            "postal_code",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")
        extra_kwargs = {
            "name": {
                "error_messages": {
                    "blank": "نام مشتری الزامی است.",
                    "required": "نام مشتری الزامی است.",
                    "max_length": "نام مشتری بیش از حد طولانی است.",
                }
            },
            "phone_number": {
                "error_messages": {
                    "invalid": "شماره تماس واردشده معتبر نیست.",
                    "max_length": "شماره تماس بیش از حد طولانی است.",
                }
            },
        }

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("نام مشتری الزامی است.")
        return value

    def validate_phone_number(self, value):
        return normalize_phone(value)
