"""
tests/test_heic.py - اختبارات معالجة صور HEIC وفك التشفير والتحويل
"""
import os
import sys
from pathlib import Path
import pytest
from PIL import Image, ImageDraw

# إضافة مسار المشروع للبحث
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from services.image_loader import load_image, is_supported_file
from services.image_converter import convert_image


@pytest.fixture(scope="module")
def sample_heic_path(tmp_path_factory):
    """إنشاء صورة HEIC تجريبية للاختبارات"""
    tmp_dir = tmp_path_factory.mktemp("heic_test")
    file_path = tmp_dir / "test_image.heic"

    import pillow_heif
    pillow_heif.register_heif_opener()

    img = Image.new("RGB", (400, 300), color=(50, 120, 220))
    d = ImageDraw.Draw(img)
    d.text((100, 140), "Test HEIC File", fill=(255, 255, 255))
    img.save(str(file_path), format="HEIF")

    return str(file_path)


def test_is_supported_file():
    """اختبار التحقق من الصيغ المدعومة"""
    assert is_supported_file("photo.heic") is True
    assert is_supported_file("photo.HEIC") is True
    assert is_supported_file("image.heif") is True
    assert is_supported_file("image.jpg") is True
    assert is_supported_file("image.png") is True
    assert is_supported_file("file.pdf") is False
    assert is_supported_file("document.docx") is False


def test_load_heic_image(sample_heic_path):
    """اختبار تحميل وفك تشفير ملف HEIC سليم"""
    img, metadata, err = load_image(sample_heic_path)
    assert err is None
    assert img is not None
    assert img.width == 400
    assert img.height == 300
    assert "الأبعاد" in metadata
    assert "حجم الملف" in metadata


def test_load_non_existent_file():
    """اختبار معالجة محاولة فتح ملف غير موجود"""
    img, metadata, err = load_image("non_existent_image_12345.heic")
    assert img is None
    assert "غير موجود" in err


def test_load_corrupted_file(tmp_path):
    """اختبار معالجة الملفات التالفة دون انهيار البرنامج"""
    corrupt_file = tmp_path / "corrupt.heic"
    corrupt_file.write_bytes(b"This is not a real HEIC file header at all!")

    img, metadata, err = load_image(str(corrupt_file))
    assert img is None
    assert err is not None


def test_convert_heic_to_formats(sample_heic_path, tmp_path):
    """اختبار تصدير وتحويل صورة HEIC إلى PNG و JPEG و WebP"""
    img, _, _ = load_image(sample_heic_path)
    assert img is not None

    # 1. تحويل إلى PNG
    png_path = tmp_path / "converted.png"
    ok_png, err_png = convert_image(img, str(png_path), "PNG")
    assert ok_png is True
    assert png_path.exists()
    assert png_path.stat().st_size > 0

    # 2. تحويل إلى JPEG
    jpg_path = tmp_path / "converted.jpg"
    ok_jpg, err_jpg = convert_image(img, str(jpg_path), "JPEG", quality=90)
    assert ok_jpg is True
    assert jpg_path.exists()
    assert jpg_path.stat().st_size > 0

    # 3. تحويل إلى WebP
    webp_path = tmp_path / "converted.webp"
    ok_webp, err_webp = convert_image(img, str(webp_path), "WEBP")
    assert ok_webp is True
    assert webp_path.exists()
    assert webp_path.stat().st_size > 0
