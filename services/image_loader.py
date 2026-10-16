"""
services/image_loader.py - مسؤول فك تشفير وقراءة الصور مع تسريع المعالجة والتحميل المسبق الذكي (Preloader & Cache)
"""
import os
import threading
from collections import OrderedDict
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, List
from PIL import Image, ImageOps, ExifTags

# تسجيل وضبط محرك فك تشفير HEIC
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    # استخدام 4 مسارات معالجة لضمان استقرار كامل للذاكرة وسرعة عالية
    pillow_heif.options.DECODE_THREADS = 4
    HEIF_AVAILABLE = True
except ImportError:
    HEIF_AVAILABLE = False

# قفل التزامن لمنع تصادم فك التشفير بين الخيوط الخلفية وحماية الذاكرة (Thread Safety)
_DECODE_LOCK = threading.Lock()


SUPPORTED_EXTENSIONS = {
    '.heic', '.heif', '.heifs', '.hif', '.avif',
    '.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif', '.gif', '.ico'
}


class LRUImageCache:
    """ذاكرة تخزين مؤقتة سريعة في الرام (RAM Cache) للصور المفكوكة لضمان فتح فوري (0 ms)"""
    def __init__(self, capacity: int = 16):
        self.capacity = capacity
        self.cache: OrderedDict[str, Tuple[Image.Image, Dict[str, str]]] = OrderedDict()
        self.lock = threading.Lock()

    def get(self, key: str) -> Optional[Tuple[Image.Image, Dict[str, str]]]:
        with self.lock:
            if key not in self.cache:
                return None
            self.cache.move_to_end(key)
            return self.cache[key]

    def put(self, key: str, value: Tuple[Image.Image, Dict[str, str]]):
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value
            if len(self.cache) > self.capacity:
                self.cache.popitem(last=False)

    def clear(self):
        with self.lock:
            self.cache.clear()


# مثيل الذاكرة المؤقتة العام للتطبيق
IMAGE_CACHE = LRUImageCache(capacity=16)


def is_supported_file(file_path: str) -> bool:
    """التحقق مما إذا كان الملف مدعوماً من قبل البرنامج"""
    ext = Path(file_path).suffix.lower()
    return ext in SUPPORTED_EXTENSIONS


def extract_metadata(pil_image: Image.Image, file_path: str) -> Dict[str, str]:
    """استخراج بيانات الصورة وتفاصيل الكاميرا والميتاداتا (EXIF)"""
    path = Path(file_path)
    stat = path.stat()
    file_size_mb = stat.st_size / (1024 * 1024)
    size_str = f"{file_size_mb:.2f} MB ({stat.st_size:,} بايت)" if file_size_mb >= 1.0 else f"{stat.st_size / 1024:.1f} KB ({stat.st_size:,} بايت)"

    meta = {
        "اسم الملف": path.name,
        "المسار": str(path),
        "الأبعاد": f"{pil_image.width} × {pil_image.height} بكسل",
        "نسبة العرض": f"{pil_image.width / max(1, pil_image.height):.2f}:1",
        "نمط الألوان": pil_image.mode,
        "حجم الملف": size_str,
        "الصيغة": getattr(pil_image, "format", path.suffix.upper().replace(".", "")),
    }

    try:
        exif = pil_image.getexif()
        if exif:
            for tag_id, value in exif.items():
                tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                tag_map = {
                    "Make": "الشركة المصنعة",
                    "Model": "طراز الكاميرا / الجهاز",
                    "DateTime": "تاريخ الالتقاط",
                    "Software": "البرنامج / النظام",
                    "LensModel": "العدسة",
                    "ExposureTime": "سرعة الغالق",
                    "FNumber": "فتحة العدسة",
                    "ISOSpeedRatings": "حساسية ISO",
                    "FocalLength": "البعد البؤري"
                }
                if tag_name in tag_map:
                    meta[tag_map[tag_name]] = str(value)
    except Exception:
        pass

    return meta


def _decode_file(path_str: str) -> Tuple[Optional[Image.Image], Dict[str, str], Optional[str]]:
    """فك تشفير الملف مباشرة من القرص"""
    path = Path(path_str).resolve()
    if not path.exists():
        return None, {}, f"الملف غير موجود:\n{path_str}"

    if not path.is_file():
        return None, {}, f"المسار المحدد ليس ملفاً صالحاً:\n{path_str}"

    if path.stat().st_size == 0:
        return None, {}, "الملف فارغ بحجم 0 بايت (ملف تالف)."

    try:
        with _DECODE_LOCK:
            img = Image.open(str(path))
            try:
                img = ImageOps.exif_transpose(img)
            except Exception:
                pass
            img.load()
            metadata = extract_metadata(img, str(path))
            return img, metadata, None
    except Exception as e:
        return None, {}, f"تعذر قراءة وفك تشفير ملف الصورة:\n{str(e)}"


def load_image(file_path: str) -> Tuple[Optional[Image.Image], Dict[str, str], Optional[str]]:
    """
    تحميل صورة بسرعة فائقة، باستخدام الكاش إذا كانت محملة مسبقاً (0 ms)
    """
    key = str(Path(file_path).resolve())
    cached = IMAGE_CACHE.get(key)
    if cached is not None:
        img, meta = cached
        return img, meta, None

    img, metadata, err = _decode_file(key)
    if img is not None:
        IMAGE_CACHE.put(key, (img, metadata))
    return img, metadata, err


def preload_images_background(paths: List[str]):
    """
    تشغيل خيط خلفي (Background Thread) لفك تشفير الصور المجاورة وحفظها في الكاش مسبقاً
    بحيث تفتح فوراً عند الضغط على التالي أو السابق دون أي انتظار
    """
    def _worker():
        for p in paths:
            k = str(Path(p).resolve())
            if IMAGE_CACHE.get(k) is None and Path(k).is_file():
                try:
                    img, meta, err = _decode_file(k)
                    if img is not None:
                        IMAGE_CACHE.put(k, (img, meta))
                except Exception:
                    pass

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
