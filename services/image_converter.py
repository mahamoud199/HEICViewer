"""
services/image_converter.py - تصدير وتحويل صور HEIC إلى صيغ شائعة (JPG, PNG, WebP, BMP)
"""
import os
from pathlib import Path
from typing import List, Tuple, Callable, Optional
from PIL import Image


def convert_image(
    pil_image: Image.Image,
    output_path: str,
    target_format: Optional[str] = None,
    quality: int = 95
) -> Tuple[bool, Optional[str]]:
    """
    تحويل وتصدير صورة إلى ملف جديد بالصيغة المحددة.
    
    Args:
        pil_image: كائن صورة Pillow
        output_path: المسار المراد الحفظ فيه
        target_format: الصيغة (PNG, JPEG, WEBP, BMP) أو يتم استنتاجها من الامتداد
        quality: جودة الضغط (1-100)
        
    Returns:
        (نجاح العملية: bool, رسالة الخطأ إن وجدت: Optional[str])
    """
    try:
        path = Path(output_path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        ext = path.suffix.lower()
        fmt = (target_format or ext.replace(".", "")).upper()
        if fmt in ["JPG", "JPEG"]:
            fmt = "JPEG"

        img_to_save = pil_image

        if fmt == "JPEG":
            # صيغة JPEG لا تدعم قناة الشفافية Alpha (RGBA)
            if img_to_save.mode in ("RGBA", "LA", "P"):
                # إنشاء خلفية بيضاء نقية ودمج الصورة عليها
                background = Image.new("RGB", img_to_save.size, (255, 255, 255))
                if img_to_save.mode == "P":
                    img_to_save = img_to_save.convert("RGBA")
                background.paste(img_to_save, mask=img_to_save.split()[-1] if img_to_save.mode == "RGBA" else None)
                img_to_save = background
            elif img_to_save.mode != "RGB":
                img_to_save = img_to_save.convert("RGB")
            
            img_to_save.save(str(path), format="JPEG", quality=quality, optimize=True)

        elif fmt == "WEBP":
            img_to_save.save(str(path), format="WEBP", quality=quality)

        elif fmt == "BMP":
            if img_to_save.mode in ("RGBA", "P"):
                img_to_save = img_to_save.convert("RGB")
            img_to_save.save(str(path), format="BMP")

        else: # الافتراضي PNG
            img_to_save.save(str(path), format="PNG", optimize=True)

        return True, None
    except Exception as e:
        return False, str(e)


def batch_convert(
    input_files: List[str],
    output_directory: str,
    target_format: str = "PNG",
    quality: int = 95,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> Tuple[int, int, List[str]]:
    """
    تحويل دفعة من صور HEIC إلى الصيغة المطلوبة في مجلد محدد.
    
    Returns:
        (عدد الملفات الناجحة, عدد الملفات الفاشلة, قائمة الأخطاء)
    """
    out_dir = Path(output_directory).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0
    fail_count = 0
    errors = []

    ext = f".{target_format.lower()}"
    if ext == ".jpeg":
        ext = ".jpg"

    total = len(input_files)
    for idx, file_path in enumerate(input_files):
        src_path = Path(file_path)
        dest_path = out_dir / f"{src_path.stem}{ext}"

        try:
            from services.image_loader import load_image
            img, _, err = load_image(str(src_path))
            if err or not img:
                fail_count += 1
                errors.append(f"{src_path.name}: {err}")
                continue

            ok, save_err = convert_image(img, str(dest_path), target_format, quality)
            if ok:
                success_count += 1
            else:
                fail_count += 1
                errors.append(f"{src_path.name}: {save_err}")

        except Exception as e:
            fail_count += 1
            errors.append(f"{src_path.name}: {str(e)}")

        if progress_callback:
            progress_callback(idx + 1, total, src_path.name)

    return success_count, fail_count, errors
