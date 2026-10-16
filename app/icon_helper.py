"""
app/icon_helper.py - تحميل وتلوين أيقونات SVG فيكتور بدقة متناهية
"""
from pathlib import Path
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtCore import Qt
from PySide6.QtSvg import QSvgRenderer

from app.resource_helper import get_resource_path


def get_svg_icon(name: str, color: str = "#e4e4e7", size: int = 20) -> QIcon:
    """
    تحميل ملف SVG وتحويله إلى QIcon ملون بدقة فيكتور عالية
    """
    svg_file = get_resource_path(f"assets/icons/{name}")
    if not svg_file.exists():
        return QIcon()

    renderer = QSvgRenderer(str(svg_file))
    # رسم بجودة مضاعفة (Retina/High-DPI 2x)
    render_size = size * 2
    pixmap = QPixmap(render_size, render_size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), QColor(color))
    painter.end()

    # إنشاء QIcon بأحجام متعددة للعرض الأملس
    icon = QIcon()
    icon.addPixmap(pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
    return icon
