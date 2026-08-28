from rest_framework import serializers

from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    unit_display = serializers.CharField(source="get_unit_display", read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "brand",
            "default_price",
            "unit",
            "unit_display",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "unit_display", "created_at", "updated_at")
        extra_kwargs = {
            "name": {
                "error_messages": {
                    "blank": "نام محصول الزامی است.",
                    "required": "نام محصول الزامی است.",
                }
            },
            "default_price": {
                "error_messages": {
                    "invalid": "قیمت باید یک عدد معتبر باشد.",
                    "min_value": "قیمت نمی‌تواند منفی باشد.",
                    "required": "قیمت الزامی است.",
                }
            },
            "unit": {
                "error_messages": {
                    "blank": "واحد محصول الزامی است.",
                    "required": "واحد محصول الزامی است.",
                    "invalid_choice": "واحد انتخاب‌شده معتبر نیست.",
                }
            },
        }

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("نام محصول الزامی است.")
        return value
