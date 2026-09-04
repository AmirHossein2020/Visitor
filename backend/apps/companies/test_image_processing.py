from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from PIL import Image, ImageDraw

from .image_processing import BackgroundIsolationError, process_seller_asset


def upload(background, ink, *, fmt="PNG", size=(320, 220), thin=False, transparent=False):
    mode = "RGBA" if transparent else "RGB"
    base = (255, 255, 255, 0) if transparent else background
    image = Image.new(mode, size, base)
    draw = ImageDraw.Draw(image)
    if thin:
        draw.line((80, 110, 240, 112), fill=ink, width=1)
    else:
        draw.ellipse((90, 55, 230, 175), outline=ink, width=7)
    output = BytesIO(); image.save(output, format=fmt)
    suffix = "jpg" if fmt == "JPEG" else fmt.lower()
    return SimpleUploadedFile(f"asset.{suffix}", output.getvalue(), content_type=f"image/{suffix}")


class SellerAssetProcessingTests(SimpleTestCase):
    def processed(self, *args, **kwargs):
        result = process_seller_asset(upload(*args, **kwargs))
        return Image.open(result).convert("RGBA")

    def test_white_jpeg_and_near_white_and_gray_backgrounds_become_transparent(self):
        for background, fmt in (((255,255,255),"JPEG"),((247,246,244),"PNG"),((220,220,220),"PNG")):
            with self.subTest(background=background):
                image = self.processed(background, (10,70,190), fmt=fmt)
                self.assertEqual(image.mode, "RGBA")
                self.assertLess(image.getchannel("A").getextrema()[0], 20)
                self.assertLess(image.width, 320); self.assertLess(image.height, 220)

    def test_blue_and_black_ink_and_thin_signatures_are_preserved(self):
        for ink in ((0,70,210),(5,5,5),(80,110,180)):
            for thin in (False, True):
                with self.subTest(ink=ink, thin=thin):
                    image = self.processed((250,250,250), ink, thin=thin)
                    opaque = [pixel for pixel in image.getdata() if pixel[3] > 100]
                    self.assertTrue(opaque)
                    if ink[2] > ink[0]: self.assertTrue(any(pixel[2] > pixel[0] for pixel in opaque))

    def test_transparent_png_remains_transparent_and_is_cropped(self):
        image = self.processed((255,255,255), (0,0,0,255), transparent=True)
        self.assertEqual(image.mode, "RGBA"); self.assertLess(image.width, 200); self.assertLess(image.height, 180)

    def test_transparent_png_with_black_invisible_rgb_preserves_black_ink(self):
        image = Image.new("RGBA", (300, 200), (0, 0, 0, 0))
        ImageDraw.Draw(image).line((70, 100, 230, 102), fill=(0, 0, 0, 255), width=1)
        output = BytesIO()
        image.save(output, format="PNG")
        result = process_seller_asset(SimpleUploadedFile("asset.png", output.getvalue(), content_type="image/png"))
        processed = Image.open(result).convert("RGBA")
        self.assertTrue(any(pixel[3] > 200 for pixel in processed.getdata()))

    def test_invalid_tiny_and_unconfident_dark_background_are_rejected(self):
        with self.assertRaises(BackgroundIsolationError): process_seller_asset(SimpleUploadedFile("bad.png", b"bad"))
        with self.assertRaises(BackgroundIsolationError): process_seller_asset(upload((255,255,255),(0,0,0),size=(10,10)))
        with self.assertRaises(BackgroundIsolationError): process_seller_asset(upload((30,30,30),(0,0,0)))
        with self.assertRaises(BackgroundIsolationError): process_seller_asset(upload((255,255,255),(0,0,0),size=(4001,100)))
