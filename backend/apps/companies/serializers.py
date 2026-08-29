from rest_framework import serializers

from .models import SellerProfile


class SellerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerProfile
        fields = (
            "id", "name", "phone_number", "address", "economic_code",
            "national_id", "registration_number", "postal_code",
            "description", "is_active", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")
        extra_kwargs = {
            "name": {
                "error_messages": {
                    "blank": "نام فروشنده یا شرکت الزامی است.",
                    "required": "نام فروشنده یا شرکت الزامی است.",
                    "max_length": "نام فروشنده یا شرکت بیش از حد طولانی است.",
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
            raise serializers.ValidationError("نام فروشنده یا شرکت الزامی است.")
        return value
