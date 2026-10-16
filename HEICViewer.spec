# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
from pathlib import Path

base_dir = Path(__file__).resolve().parent

datas = [(str(base_dir / 'assets'), 'assets')]
binaries = []
hiddenimports = ['PySide6.QtPrintSupport', 'PIL.Image', 'pillow_heif']
tmp_ret = collect_all('pillow_heif')

# استبعاد أي حزم أو مكتبات تابعة لـ numpy أو scipy تسبب تضارباً في إدارة الذاكرة
for d in tmp_ret[0]:
    if 'numpy' not in d[0].lower() and 'scipy' not in d[0].lower():
        datas.append(d)

for b in tmp_ret[1]:
    if 'numpy' not in b[0].lower() and 'scipy' not in b[0].lower():
        binaries.append(b)

for h in tmp_ret[2]:
    if not h.startswith('numpy') and not h.startswith('scipy'):
        hiddenimports.append(h)

excludes = ['numpy', 'scipy', 'matplotlib', 'tkinter', 'pandas', 'unittest', 'email', 'html', 'http']

a = Analysis(
    [str(base_dir / 'main.py')],
    pathex=[str(base_dir)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='HEICViewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[str(base_dir / 'assets' / 'app.ico')],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='HEICViewer',
)
