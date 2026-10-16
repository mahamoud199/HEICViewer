"""
app/filmstrip.py - شريط المصغرات السفلي التفاعلي السريع للتنقل بين صور المجلد
معالجة الخيوط المتزامنة بنظام الإشارات الآمن في كيوت (Safe QThread & Signals)
"""
import os
from pathlib import Path
from typing import List, Optional
from PIL import Image

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QListWidget, QListWidgetItem
)
from PySide6.QtGui import QIcon, QPixmap, QImage, QColor
from PySide6.QtCore import Qt, QSize, Signal, QThread


class ThumbnailWorker(QThread):
    """خيط خلفي آمن في كيوت لتوليد المصغرات دون تجميد الواجهة ودون مساس بكائنات الرسم GUI"""
    thumbnail_ready = Signal(int, QImage)

    def __init__(self, images: List[Path], start_idx: int, end_idx: int, parent=None):
        super().__init__(parent)
        self.images = list(images)
        self.start_idx = start_idx
        self.end_idx = end_idx
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        from services.image_loader import load_image
        total = len(self.images)
        for i in range(self.start_idx, self.end_idx):
            if self._cancelled or i >= total:
                break
            p = str(self.images[i])
            try:
                pil_img, _, _ = load_image(p)
                if self._cancelled:
                    break
                if pil_img is not None:
                    # توليد مصغرة مربعة 64x64 بسرعة عالية
                    thumb = pil_img.copy()
                    thumb.thumbnail((64, 64), Image.Resampling.LANCZOS)
                    if thumb.mode not in ("RGB", "RGBA"):
                        thumb = thumb.convert("RGBA")

                    if thumb.mode == "RGBA":
                        raw_data = thumb.tobytes("raw", "RGBA")
                        qimg = QImage(raw_data, thumb.width, thumb.height, QImage.Format.Format_RGBA8888).copy()
                    else:
                        raw_data = thumb.tobytes("raw", "RGB")
                        qimg = QImage(raw_data, thumb.width, thumb.height, thumb.width * 3, QImage.Format.Format_RGB888).copy()

                    if not self._cancelled:
                        self.thumbnail_ready.emit(i, qimg)
            except Exception:
                pass


class ThumbnailFilmstrip(QWidget):
    """شريط مصغرات أفقي أنيق قابل للإظهار والإخفاء للتنقل السريع بين صور المجلد"""
    image_selected = Signal(int)  # يرسل الفهرس المختار

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(94)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(6)

        self.list_widget = QListWidget(self)
        self.list_widget.setViewMode(QListWidget.ViewMode.IconMode)
        self.list_widget.setIconSize(QSize(64, 64))
        self.list_widget.setMovement(QListWidget.Movement.Static)
        self.list_widget.setFlow(QListWidget.Flow.LeftToRight)
        self.list_widget.setWrapping(False)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.setSpacing(6)
        self.list_widget.currentRowChanged.connect(self._on_row_changed)

        layout.addWidget(self.list_widget)

        self._images: List[Path] = []
        self._block_signals = False
        self._worker: Optional[ThumbnailWorker] = None

    def set_images(self, image_paths: List[Path], current_index: int = 0):
        """تحديث قائمة الصور وتوليد المصغرات التمهيدية"""
        # إيقاف أي عامل سابق بأمان
        if self._worker is not None and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(100)

        self._images = list(image_paths)
        self._block_signals = True
        self.list_widget.clear()

        # placeholder icon
        placeholder = QPixmap(64, 64)
        placeholder.fill(QColor("#334155"))

        for idx, img_path in enumerate(self._images):
            item = QListWidgetItem(self.list_widget)
            item.setSizeHint(QSize(72, 72))
            item.setToolTip(f"{img_path.name} ({idx + 1}/{len(self._images)})")
            item.setIcon(QIcon(placeholder))
            self.list_widget.addItem(item)

        self._block_signals = False
        self.set_current_index(current_index)
        self._load_visible_thumbnails()

    def set_current_index(self, index: int):
        """تحديد الصورة الحالية والتمرير إليها في الشريط"""
        if 0 <= index < self.list_widget.count():
            self._block_signals = True
            self.list_widget.setCurrentRow(index)
            item = self.list_widget.item(index)
            if item:
                self.list_widget.scrollToItem(item, QListWidget.ScrollHint.PositionAtCenter)
            self._block_signals = False

    def update_single_thumbnail(self, index: int, qimage: QImage):
        """تحديث مصغرة صورة محددة بعد استلامها بأمان عبر الإشارة في الخيط الرئيسي"""
        if 0 <= index < self.list_widget.count():
            item = self.list_widget.item(index)
            if item and not qimage.isNull():
                pixmap = QPixmap.fromImage(qimage)
                scaled = pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                x = max(0, (scaled.width() - 64) // 2)
                y = max(0, (scaled.height() - 64) // 2)
                cropped = scaled.copy(x, y, 64, 64)
                item.setIcon(QIcon(cropped))

    def _load_visible_thumbnails(self):
        """تحميل مصغرات الصور المجاورة بأمان كامل عبر QThread"""
        if not self._images:
            return

        if self._worker is not None and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(100)

        curr = self.list_widget.currentRow()
        start = max(0, curr - 15)
        end = min(len(self._images), curr + 16)

        self._worker = ThumbnailWorker(self._images, start, end, self)
        self._worker.thumbnail_ready.connect(self.update_single_thumbnail)
        self._worker.start()

    def stop_worker(self):
        """إيقاف عامل توليد المصغرات وانتظار إنهائه بأمان"""
        if self._worker is not None and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(300)

    def closeEvent(self, event):
        self.stop_worker()
        super().closeEvent(event)

    def _on_row_changed(self, row: int):
        if not self._block_signals and 0 <= row < len(self._images):
            self.image_selected.emit(row)

