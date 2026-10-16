"""
app/image_view.py - لوحة عرض الصورة التفاعلية بدعم الملاءمة التلقائية الذكية والتكبير السلس
"""
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QFrame
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtCore import Qt, QRectF, QTimer


class SmoothImageView(QGraphicsView):
    """عنصر عرض الصورة التفاعلي بدعم التكبير والتدوير والملاءمة الذكية للنافذة"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.pixmap_item = QGraphicsPixmapItem()
        self.pixmap_item.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
        self.scene.addItem(self.pixmap_item)

        # تحسين جودة العرض والتنعيم
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.Shape.NoFrame)

        self._zoom_factor = 1.0
        self._rotation_angle = 0
        self._flip_h = False
        self._flip_v = False
        self._is_fit_mode = True

    def set_theme_background(self, theme_name: str):
        """تعديل خلفية لوحة العرض لتناسب الوضع الفاتح أو الداكن"""
        bg_color = "#121316" if theme_name == "dark" else "#f1f5f9"
        self.setStyleSheet(f"background-color: {bg_color};")

    def display_pixmap(self, pixmap: QPixmap):
        """عرض صورة جديدة وتفعيل الملاءمة للشاشة تلقائياً"""
        self.pixmap_item.setPixmap(pixmap)
        rect = QRectF(pixmap.rect())
        self.scene.setSceneRect(rect)
        self.reset_transform_state()
        self._is_fit_mode = True
        self.fit_to_window()

    def reset_transform_state(self):
        self._zoom_factor = 1.0
        self._rotation_angle = 0
        self._flip_h = False
        self._flip_v = False
        self.resetTransform()

    def fit_to_window(self):
        """ملاءمة أبعاد الصورة تماماً مع حجم النافذة الحالي"""
        if self.pixmap_item.pixmap().isNull():
            return

        rect = QRectF(self.pixmap_item.pixmap().rect())
        if rect.isEmpty():
            return

        vw = self.viewport().width()
        vh = self.viewport().height()
        if vw <= 20 or vh <= 20:
            # إذا لم يتم رسم النافذة بعد، تأجيل الملاءمة قليلاً
            QTimer.singleShot(30, self.fit_to_window)
            return

        self.resetTransform()
        # ملاءمة كامل الصورة داخل الإطار المرئي
        self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)

        # حساب مقياس التكبير الدقيق بعد الملاءمة
        self._zoom_factor = abs(self.transform().m11())
        self._is_fit_mode = True

        # تطبيق التدوير والقلب مع الحفاظ على التوسيط
        self._apply_transformations()
        self.centerOn(self.pixmap_item)
        self._notify_zoom_change()

    def zoom_actual_size(self):
        """عرض الصورة بالحجم الحقيقي 100%"""
        if self.pixmap_item.pixmap().isNull():
            return
        self._is_fit_mode = False
        self._zoom_factor = 1.0
        self._apply_transformations()
        self.centerOn(self.pixmap_item)
        self._notify_zoom_change()

    def zoom_by(self, factor: float):
        """تكبير أو تصغير بمقدار محدد"""
        if self.pixmap_item.pixmap().isNull():
            return
        self._is_fit_mode = False
        self.scale(factor, factor)
        self._zoom_factor *= factor
        self._notify_zoom_change()

    def rotate_image(self, degrees: int):
        """تدوير الصورة بمقدار 90 أو -90 درجة"""
        if self.pixmap_item.pixmap().isNull():
            return
        self._rotation_angle = (self._rotation_angle + degrees) % 360
        if self._is_fit_mode:
            self.fit_to_window()
        else:
            self._apply_transformations()
            self.centerOn(self.pixmap_item)

    def flip_horizontal(self):
        """قلب الصورة أفقياً"""
        if self.pixmap_item.pixmap().isNull():
            return
        self._flip_h = not self._flip_h
        self._apply_transformations()
        self.centerOn(self.pixmap_item)

    def flip_vertical(self):
        """قلب الصورة رأسياً"""
        if self.pixmap_item.pixmap().isNull():
            return
        self._flip_v = not self._flip_v
        self._apply_transformations()
        self.centerOn(self.pixmap_item)

    def _apply_transformations(self):
        """تطبيق التدوير والقلب والمقياس بدقة"""
        scale_x = -self._zoom_factor if self._flip_h else self._zoom_factor
        scale_y = -self._zoom_factor if self._flip_v else self._zoom_factor

        self.resetTransform()
        self.rotate(self._rotation_angle)
        self.scale(scale_x, scale_y)

    def _notify_zoom_change(self):
        if hasattr(self.parent(), "update_zoom_label"):
            self.parent().update_zoom_label(self._zoom_factor)

    def wheelEvent(self, event):
        """التكبير والتصغير باستخدام عجلة الماوس في موضع المؤشر"""
        if self.pixmap_item.pixmap().isNull():
            return
        delta = event.angleDelta().y()
        if delta > 0:
            self.zoom_by(1.18)
        elif delta < 0:
            self.zoom_by(1 / 1.18)
        event.accept()

    def resizeEvent(self, event):
        """إعادة ملاءمة الصورة تلقائياً عند تكبير أو تغيير حجم النافذة"""
        super().resizeEvent(event)
        if self._is_fit_mode and not self.pixmap_item.pixmap().isNull():
            self.fit_to_window()

    def mouseDoubleClickEvent(self, event):
        """النقر المزدوج على الصورة لتفعيل أو تعطيل ملء الشاشة"""
        if hasattr(self.parent(), "toggle_fullscreen"):
            self.parent().toggle_fullscreen()
        event.accept()
