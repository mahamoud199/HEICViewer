"""
services/file_association.py - إدارة تكامل سجل ويندوز (Windows Registry) وارتباط ملفات .heic
"""
import os
import sys
import winreg
import ctypes
from pathlib import Path
from typing import Tuple


def get_target_executable_path() -> str:
    """الحصول على المسار الدقيق لملف التشغيل التنفيذي"""
    if getattr(sys, 'frozen', False):
        return sys.executable
    
    # في حالة بيئة التطوير، نتحقق من وجود النسخة المجمعة في dist أولاً
    root_dir = Path(__file__).resolve().parent.parent
    dist_exe = root_dir / "dist" / "HEICViewer" / "HEICViewer.exe"
    if dist_exe.exists():
        return str(dist_exe)

    top_dist = root_dir.parent / "dist" / "HEICViewer" / "HEICViewer.exe"
    if top_dist.exists():
        return str(top_dist)

    # تشغيل عبر pythonw.exe لتجنب النافذة السوداء للكونسول
    py_exe = sys.executable
    pyw_exe = Path(py_exe).parent / "pythonw.exe"
    launcher = str(pyw_exe) if pyw_exe.exists() else py_exe
    main_py = str(root_dir / "main.py")
    return f'"{launcher}" "{main_py}"'


def notify_shell_change() -> bool:
    """إشعار مستكشف ويندوز (Windows Explorer) فوراً بتحديث ارتباطات الملفات والأيقونات"""
    try:
        SHCNE_ASSOCCHANGED = 0x08000000
        SHCNF_IDLIST = 0x0000
        ctypes.windll.shell32.SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, None, None)
        return True
    except Exception:
        return False


def register_association(custom_exe_path: str = None) -> Tuple[bool, str]:
    """
    تسجيل البرنامج كعارض افتراضي لملفات .heic و .heif في سجل ويندوز (HKCU)
    لا يحتاج صلاحيات مسؤول Run as Administrator لأن التسجيل يتم في نطاق المستخدم الحالي.
    """
    try:
        exe_cmd_target = custom_exe_path or get_target_executable_path()
        if not exe_cmd_target.startswith('"') and " " in exe_cmd_target:
            cmd = f'"{exe_cmd_target}" "%1"'
            icon_str = f'"{exe_cmd_target}",0'
        elif exe_cmd_target.startswith('"'):
            cmd = f'{exe_cmd_target} "%1"'
            # استخراج مسار الملف للأيقونة
            raw_path = exe_cmd_target.split('"')[1]
            icon_str = f'"{raw_path}",0'
        else:
            cmd = f'"{exe_cmd_target}" "%1"'
            icon_str = f'"{exe_cmd_target}",0'

        prog_id = "HEICViewer.Image"
        app_name = "HEIC Viewer"
        extensions = [".heic", ".heif", ".heifs", ".hif", ".avif"]

        hkcu = winreg.HKEY_CURRENT_USER
        base = r"Software\Classes"

        # 1. إنشاء معرف البرنامج ProgID
        prog_path = f"{base}\\{prog_id}"
        with winreg.CreateKey(hkcu, prog_path) as k:
            winreg.SetValue(k, "", winreg.REG_SZ, "HEIC Image File")
            winreg.SetValueEx(k, "FriendlyTypeName", 0, winreg.REG_SZ, "HEIC Image File")

        with winreg.CreateKey(hkcu, f"{prog_path}\\DefaultIcon") as k:
            winreg.SetValue(k, "", winreg.REG_SZ, icon_str)

        with winreg.CreateKey(hkcu, f"{prog_path}\\shell\\open\\command") as k:
            winreg.SetValue(k, "", winreg.REG_SZ, cmd)

        with winreg.CreateKey(hkcu, f"{prog_path}\\shell\\open") as k:
            winreg.SetValueEx(k, "FriendlyAppName", 0, winreg.REG_SZ, app_name)

        # 2. ربط الامتدادات
        for ext in extensions:
            ext_path = f"{base}\\{ext}"
            with winreg.CreateKey(hkcu, ext_path) as k:
                winreg.SetValue(k, "", winreg.REG_SZ, prog_id)
                winreg.SetValueEx(k, "Content Type", 0, winreg.REG_SZ, "image/heic")
                winreg.SetValueEx(k, "PerceivedType", 0, winreg.REG_SZ, "image")

            with winreg.CreateKey(hkcu, f"{ext_path}\\OpenWithProgids") as k:
                winreg.SetValueEx(k, prog_id, 0, winreg.REG_NONE, b"")

        # 3. تسجيل في Applications\HEICViewer.exe
        app_key = f"{base}\\Applications\\HEICViewer.exe"
        with winreg.CreateKey(hkcu, f"{app_key}\\shell\\open\\command") as k:
            winreg.SetValue(k, "", winreg.REG_SZ, cmd)
        with winreg.CreateKey(hkcu, f"{app_key}\\SupportedTypes") as k:
            for ext in extensions:
                winreg.SetValueEx(k, ext, 0, winreg.REG_SZ, "")

        # 4. تسجيل في FileExts للمستكشف Explorer في ويندوز 10/11
        for ext in extensions:
            p = f"Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\FileExts\\{ext}\\OpenWithProgids"
            try:
                with winreg.CreateKey(hkcu, p) as k:
                    winreg.SetValueEx(k, prog_id, 0, winreg.REG_NONE, b"")
            except Exception:
                pass

        # 5. تسجيل معالج الصور المصغرة ShellEx Thumbnail Provider في ويندوز
        thumb_clsid = "{C7657C4A-9F68-40fa-A4DF-96BC08EB3551}"
        extract_clsid = "{3F30C968-480A-4C6C-862D-EFC0897BB84B}"

        shellex_targets = [
            f"{base}\\{prog_id}",
            f"{base}\\.heic",
            f"{base}\\.heif",
            r"Software\Classes\SystemFileAssociations\.heic",
            r"Software\Classes\SystemFileAssociations\.heif",
        ]
        for target in shellex_targets:
            try:
                with winreg.CreateKey(hkcu, f"{target}\\ShellEx\\{{e357fccd-a995-4576-b01f-234630154e96}}") as k:
                    winreg.SetValue(k, "", winreg.REG_SZ, thumb_clsid)
                with winreg.CreateKey(hkcu, f"{target}\\ShellEx\\{{BB2E617C-0920-11d1-9A0B-00C04FC2D6C1}}") as k:
                    winreg.SetValue(k, "", winreg.REG_SZ, extract_clsid)
            except Exception:
                pass

        notify_shell_change()
        return True, "تم تسجيل البرنامج وتفعيل المعاينة المصغرة للصور بنجاح!"

    except Exception as e:
        return False, f"فشل تسجيل الارتباط في السجل: {str(e)}"


def is_heic_associated() -> bool:
    """التحقق مما إذا كان البرنامج هو المرتبط بملفات .heic في النظام"""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\.heic") as k:
            val = winreg.QueryValue(k, "")
            return val == "HEICViewer.Image"
    except Exception:
        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r".heic") as k:
                val = winreg.QueryValue(k, "")
                return val == "HEICViewer.Image"
        except Exception:
            return False


def open_windows_default_apps_settings() -> bool:
    """فتح واجهة إعدادات التطبيقات الافتراضية في ويندوز 10/11"""
    try:
        os.system("start ms-settings:defaultapps")
        return True
    except Exception:
        return False


def create_desktop_shortcut(shortcut_name: str = "HEIC Viewer.lnk") -> Tuple[bool, str]:
    """إنشاء اختصار مباشر للبرنامج على سطح مكتب المستخدم"""
    try:
        desktop = Path.home() / "Desktop"
        link_path = desktop / shortcut_name
        target_exe = get_target_executable_path().replace('"', '')

        vbs = f"""
        Set oWS = WScript.CreateObject("WScript.Shell")
        sLinkFile = "{str(link_path)}"
        Set oLink = oWS.CreateShortcut(sLinkFile)
        oLink.TargetPath = "{target_exe}"
        oLink.WorkingDirectory = "{str(Path(target_exe).parent)}"
        oLink.Description = "HEIC Viewer - عارض صور HEIC الاحترافي"
        oLink.IconLocation = "{target_exe}, 0"
        oLink.Save
        """
        temp_vbs = Path.home() / "create_shortcut_temp.vbs"
        temp_vbs.write_text(vbs, encoding="utf-8")
        os.system(f'cscript //nologo "{str(temp_vbs)}"')
        if temp_vbs.exists():
            temp_vbs.unlink()
        return True, str(link_path)
    except Exception as e:
        return False, str(e)
