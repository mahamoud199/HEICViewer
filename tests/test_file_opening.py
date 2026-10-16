"""
tests/test_file_opening.py - اختبارات تكامل ويندوز وفتح الملفات عبر المعاملات
"""
import os
import sys
from pathlib import Path

# إضافة مسار المشروع للبحث
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from services.file_association import is_heic_associated, get_target_executable_path


def test_get_target_executable_path():
    """التحقق من إمكانية استنتاج مسار الملف التنفيذي بشكل سليم"""
    path = get_target_executable_path()
    assert path is not None
    assert len(path) > 0


def test_file_association_check():
    """التحقق من قراءة حالة ارتباط ملفات HEIC في سجل ويندوز"""
    # يجب أن تعود الدالة بقيمة منطقية (True أو False) دون إثارة استثناءات
    status = is_heic_associated()
    assert isinstance(status, bool)
