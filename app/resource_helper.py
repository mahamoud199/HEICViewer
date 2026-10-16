"""
app/resource_helper.py - إدارة وتحديد مسارات الموارد والأيقونات بدقة في التطبيق وحزم التوزيع
"""
import sys
import os
from pathlib import Path
from PySide6.QtGui import QIcon

def get_resource_path(relative_path: str) -> Path:
    """
    إرجاع المسار المطلق للمورد سواء تم التشغيل ككود بايثون أو عبر حزمة PyInstaller المجمعة
    """
    if getattr(sys, "frozen", False):
        # وضع التجميع بواسطة PyInstaller
        base_path = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    else:
        # وضع التطوير المباشر
        base_path = Path(__file__).resolve().parent.parent

    # التحقق من المسار المباشر
    res = base_path / relative_path
    if res.exists():
        return res

    # التحقق من مسار المجلد التنفيذي إذا اختلف
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).parent
        alt_res = exe_dir / relative_path
        if alt_res.exists():
            return alt_res
        alt_int = exe_dir / "_internal" / relative_path
        if alt_int.exists():
            return alt_int

    return res


def get_app_icon() -> QIcon:
    """
    تحميل أيقونة التطبيق متعددة الأبعاد بأعلى جودة ممكنة
    """
    ico_path = get_resource_path("assets/app.ico")
    if ico_path.exists():
        return QIcon(str(ico_path))

    png_path = get_resource_path("assets/app_icon.png")
    if png_path.exists():
        return QIcon(str(png_path))

    return QIcon()
