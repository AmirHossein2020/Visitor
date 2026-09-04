from io import BytesIO
from statistics import median

from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError


class BackgroundIsolationError(ValueError):
    pass


def process_seller_asset(uploaded):
    try:
        image = Image.open(uploaded)
        image = ImageOps.exif_transpose(image).convert("RGBA")
    except (UnidentifiedImageError, OSError) as error:
        raise BackgroundIsolationError("فایل بارگذاری‌شده تصویر معتبر نیست.") from error
    width, height = image.size
    if width < 20 or height < 20 or width > 4000 or height > 4000:
        raise BackgroundIsolationError("ابعاد تصویر باید بین ۲۰ و ۴۰۰۰ پیکسل باشد.")

    original_alpha = image.getchannel("A")
    has_transparency = original_alpha.getextrema()[0] < 245
    if has_transparency:
        # A prepared transparent upload already contains the best edge mask.
        # Preserve it rather than trying to infer a background from invisible RGB data.
        output = image.copy()
    else:
        pixels = image.load()
        step = max(1, min(width, height) // 80)
        border = []
        for x in range(0, width, step):
            border.extend((pixels[x, 0][:3], pixels[x, height - 1][:3]))
        for y in range(0, height, step):
            border.extend((pixels[0, y][:3], pixels[width - 1, y][:3]))
        background = tuple(int(median(channel)) for channel in zip(*border))
        luminance = sum(background) / 3
        spread = median(
            max(abs(pixel[index] - background[index]) for index in range(3))
            for pixel in border
        )
        if luminance < 175 or spread > 35:
            raise BackgroundIsolationError("حذف خودکار پس‌زمینه این تصویر با کیفیت مطلوب انجام نشد. لطفاً تصویر واضح‌تر با پس‌زمینه روشن بارگذاری کنید.")

        output = Image.new("RGBA", image.size)
        source, target = image.load(), output.load()
        for y in range(height):
            for x in range(width):
                red, green, blue, source_alpha = source[x, y]
                distance = max(
                    abs(red - background[0]),
                    abs(green - background[1]),
                    abs(blue - background[2]),
                )
                soft_alpha = (
                    0 if distance <= 7 else
                    255 if distance >= 42 else
                    round((distance - 7) * 255 / 35)
                )
                target[x, y] = (red, green, blue, min(source_alpha, soft_alpha))

    alpha = output.getchannel("A")
    meaningful = alpha.point(lambda value: 255 if value >= 12 else 0)
    bounds = meaningful.getbbox()
    if not bounds:
        raise BackgroundIsolationError("اثر قابل تشخیصی در تصویر پیدا نشد. لطفاً تصویر واضح‌تری بارگذاری کنید.")
    left, top, right, bottom = bounds
    padding = max(2, round(max(right - left, bottom - top) * 0.025))
    bounds = (
        max(0, left - padding),
        max(0, top - padding),
        min(width, right + padding),
        min(height, bottom + padding),
    )
    output = output.crop(bounds)
    buffer = BytesIO()
    output.save(buffer, format="PNG", optimize=True)
    return ContentFile(buffer.getvalue(), name="processed.png")
