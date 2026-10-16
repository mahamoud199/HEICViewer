"""
main.py - نقطة الدخول الرئيسية لبرنامج HEIC Viewer
"""
import sys
import os
import traceback
from pathlib import Path

# إعداد ملف تسجيل الأخطاء والاستثناءات لضمان عدم خروج البرنامج بصمت
log_dir = Path(os.environ.get("APPDATA", str(Path.home()))) / "HEICViewer"
log_dir.mkdir(parents=True, exist_ok=True)
log_file_path = log_dir / "app_runtime.log"

try:
    import faulthandler
    _log_fh = open(log_file_path, "a", encoding="utf-8")
    faulthandler.enable(file=_log_fh)
except Exception:
    pass

def global_excepthook(exc_type, exc_value, exc_traceback):
    err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    try:
        with open(log_file_path, "a", encoding="utf-8") as f:
            f.write(f"\n[UNCAUGHT EXCEPTION]:\n{err_msg}\n")
    except Exception:
        pass
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = global_excepthook

# إضافة مسار المشروع إلى مسارات البحث
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

import ctypes
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from app.resource_helper import get_app_icon
from app.main_window import MainWindow


def main():
    # تسجيل AppUserModelID لنظام ويندوز بأمان مع تحديد نوع المعامل LPCWSTR
    if os.name == "nt":
        try:
            myappid = "Mahmoud.HEICViewer.App.1"
            set_app_id = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID
            set_app_id.argtypes = [ctypes.c_wchar_p]
            set_app_id(myappid)
        except Exception:
            pass

    # دعم شاشات العرض الحديثة فائقة الدقة (High DPI Scaling)
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("HEIC Viewer")
    app.setOrganizationName("HEICViewer")

    # تحميل أيقونة التطبيق متعددة الأحجام
    app_icon = get_app_icon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)

    # التحقق من وجود مسار ملف مرر عبر النقر المزدوج في ويندوز
    initial_file = None
    if len(sys.argv) > 1:
        initial_file = sys.argv[1]

    window = MainWindow(initial_file=initial_file)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
