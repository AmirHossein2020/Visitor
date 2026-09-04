from rest_framework import serializers
from pathlib import Path
from PIL import Image, UnidentifiedImageError
from .image_processing import BackgroundIsolationError, process_seller_asset

from .models import SellerProfile
from apps.accounts.normalization import normalize_phone


class SellerProfileSerializer(serializers.ModelSerializer):
    def to_internal_value(self, data):
        data = {key: data.get(key) for key in data}
        if "phone_number" in data:
            data["phone_number"] = normalize_phone(data["phone_number"])
        return super().to_internal_value(data)

    has_stamp = serializers.SerializerMethodField()
    has_signature = serializers.SerializerMethodField()
    stamp_url = serializers.SerializerMethodField()
    signature_url = serializers.SerializerMethodField()
    class Meta:
        model = SellerProfile
        fields = (
            "id", "name", "phone_number", "address", "economic_code",
            "national_id", "registration_number", "postal_code",
            "description", "stamp_image", "signature_image", "has_stamp", "has_signature",
            "stamp_url", "signature_url", "is_active", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")
        extra_kwargs = {
            "stamp_image": {"write_only": True, "required": False},
            "signature_image": {"write_only": True, "required": False},
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

    def get_has_stamp(self, obj): return bool(obj.stamp_image)
    def get_has_signature(self, obj): return bool(obj.signature_image)
    def get_stamp_url(self, obj): return f"/api/companies/{obj.pk}/stamp/" if obj.stamp_image else None
    def get_signature_url(self, obj): return f"/api/companies/{obj.pk}/signature/" if obj.signature_image else None

    def _validate_image(self, uploaded):
        if uploaded.size > 3 * 1024 * 1024:
            raise serializers.ValidationError("حجم تصویر نباید بیشتر از ۳ مگابایت باشد.")
        suffix = Path(uploaded.name).suffix.lower()
        if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
            raise serializers.ValidationError("فقط تصویر PNG، JPG یا WebP پذیرفته می‌شود.")
        if uploaded.content_type not in {"image/png", "image/jpeg", "image/webp"}:
            raise serializers.ValidationError("نوع فایل تصویر معتبر نیست.")
        try:
            image = Image.open(uploaded); image.verify(); uploaded.seek(0)
            image = Image.open(uploaded); width, height = image.size; image_format = image.format; uploaded.seek(0)
        except (UnidentifiedImageError, OSError):
            raise serializers.ValidationError("فایل بارگذاری‌شده تصویر معتبر نیست.")
        allowed = {"PNG", "JPEG", "WEBP"}
        if image_format not in allowed or width < 20 or height < 20 or width > 4000 or height > 4000:
            raise serializers.ValidationError("نوع یا ابعاد تصویر معتبر نیست؛ ابعاد باید بین ۲۰ و ۴۰۰۰ پیکسل باشد.")
        try:
            return process_seller_asset(uploaded)
        except BackgroundIsolationError as error:
            raise serializers.ValidationError(str(error))

    def validate_stamp_image(self, value): return self._validate_image(value)
    def validate_signature_image(self, value): return self._validate_image(value)

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("نام فروشنده یا شرکت الزامی است.")
        return value

    def validate_phone_number(self, value):
        return normalize_phone(value)
