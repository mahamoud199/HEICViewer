"""
app/main_window.py - النافذة الرئيسية لتطبيق HEIC Viewer مع الملاءمة الكاملة والأزرار الطافية المتناسقة
"""
import os
import sys
from pathlib import Path
from typing import Optional, List

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QStatusBar,
    QFileDialog, QMessageBox, QDialog, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QPushButton
)
from PySide6.QtGui import (
    QPixmap, QImage, QIcon, QPainter, QColor, QFont
)
from PySide6.QtCore import Qt, QSize, QTimer

from app.image_view import SmoothImageView
from app.toolbar import setup_toolbar, refresh_toolbar_icons
from app.settings import AppSettings, DARK_THEME_QSS, LIGHT_THEME_QSS
from app.icon_helper import get_svg_icon
from app.resource_helper import get_app_icon
from app.filmstrip import ThumbnailFilmstrip
from services.image_loader import load_image, is_supported_file
from services.image_converter import convert_image
from services.file_association import register_association, is_heic_associated


class MetadataDialog(QDialog):
    """نافذة أنيقة لعرض تفاصيل الصورة وبيانات EXIF"""
    def __init__(self, metadata: dict, is_dark: bool = True, parent=None):
        super().__init__(parent)
        self.setWindowTitle("معلومات الصورة وتفاصيل الميتاداتا (EXIF)")
        self.resize(540, 480)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QVBoxLayout(self)
        table = QTableWidget(len(metadata), 2)
        table.setHorizontalHeaderLabels(["الخاصية", "القيمة"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        row = 0
        for key, val in metadata.items():
            k_item = QTableWidgetItem(str(key))
            v_item = QTableWidgetItem(str(val))
            if is_dark:
                k_item.setForeground(QColor("#93c5fd"))
                v_item.setForeground(QColor("#f8fafc"))
            else:
                k_item.setForeground(QColor("#2563eb"))
                v_item.setForeground(QColor("#0f172a"))
            table.setItem(row, 0, k_item)
            table.setItem(row, 1, v_item)
            row += 1

        layout.addWidget(table)
        btn_close = QPushButton("إغلاق")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignCenter)


class MainWindow(QMainWindow):
    """النافذة الأساسية للعارض مع واجهة احترافية متكاملة وملاءمة ذكية للأبعاد"""
    def __init__(self, initial_file: Optional[str] = None):
        super().__init__()
        self.setWindowTitle("HEIC Viewer")
        self.resize(1180, 780)
        self.setMinimumSize(640, 480)
        self.setAcceptDrops(True)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.settings = AppSettings()
        self.current_theme = self.settings.get_theme()
        self.is_associated = is_heic_associated()

        self.current_filepath: Optional[str] = None
        self.current_pil_image = None
        self.current_metadata = {}
        self.folder_images: List[Path] = []
        self.current_index: int = -1

        # أيقونة النافذة الرسمية متعددة المقاسات لشريط العنوان وشريط المهام
        app_icon = get_app_icon()
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)

        # إعداد مؤقت عرض الشرائح التلقائي
        self.slideshow_timer = QTimer(self)
        self.slideshow_timer.setInterval(3500)
        self.slideshow_timer.timeout.connect(self._slideshow_next_tick)
        self.is_slideshow_running = False

        self._init_ui()
        self._apply_current_theme()

        # فتح الملف الأولي إذا تم تمريره من سطر الأوامر أو النقر المزدوج في ويندوز
        if initial_file and os.path.exists(initial_file):
            self.load_image_file(initial_file)
        else:
            self._render_welcome_screen()

        self.update_association_ui()

    def _init_ui(self):
        """إنشاء التخطيط وشريط الأدوات وشريط الحالة وشريط المصغرات"""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # مساحة العرض التفاعلية
        self.viewer = SmoothImageView(self)
        layout.addWidget(self.viewer)

        # شريط المصغرات السفلي التفاعلي السريع
        self.filmstrip = ThumbnailFilmstrip(self)
        self.filmstrip.image_selected.connect(self._on_filmstrip_image_selected)
        layout.addWidget(self.filmstrip)

        # أزرار التنقل الطافية مثبتة مباشرة على viewport لوحة العرض
        self.btn_floating_prev = QPushButton(self.viewer.viewport())
        self.btn_floating_prev.setIcon(get_svg_icon("prev.svg", "#ffffff", size=22))
        self.btn_floating_prev.setIconSize(QSize(22, 22))
        self.btn_floating_prev.setToolTip("الصورة السابقة (السهم الأيسر)")
        self.btn_floating_prev.clicked.connect(self.show_previous_image)
        self.btn_floating_prev.setFixedSize(46, 46)

        self.btn_floating_next = QPushButton(self.viewer.viewport())
        self.btn_floating_next.setIcon(get_svg_icon("next.svg", "#ffffff", size=22))
        self.btn_floating_next.setIconSize(QSize(22, 22))
        self.btn_floating_next.setToolTip("الصورة التالية (السهم الأيمن)")
        self.btn_floating_next.clicked.connect(self.show_next_image)
        self.btn_floating_next.setFixedSize(46, 46)

        self._apply_floating_buttons_style()

        # شريط الأدوات العلوي
        self.toolbar = setup_toolbar(self)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)

        # شريط الحالة السفلي المطور
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        self.lbl_format_badge = QLabel("")
        self.lbl_filename = QLabel("في انتظار اختيار صورة...")
        self.lbl_dims = QLabel("")
        self.lbl_filesize = QLabel("")
        self.lbl_zoom = QLabel("100%")
        self.lbl_counter = QLabel("")

        for w in (self.lbl_format_badge, self.lbl_filename, self.lbl_dims, self.lbl_filesize, self.lbl_zoom, self.lbl_counter):
            self.status_bar.addPermanentWidget(w)

        self._apply_status_bar_style()

    def _apply_floating_buttons_style(self):
        """تنسيق أزرار التنقل الطافية الشفافة"""
        btn_style = """
        QPushButton {
            background-color: rgba(24, 25, 30, 0.75);
            border: 1px solid rgba(255, 255, 255, 0.20);
            border-radius: 23px;
        }
        QPushButton:hover {
            background-color: rgba(37, 99, 235, 0.90);
            border: 1px solid rgba(255, 255, 255, 0.40);
        }
        QPushButton:pressed {
            background-color: rgba(29, 78, 216, 1.0);
        }
        """
        self.btn_floating_prev.setStyleSheet(btn_style)
        self.btn_floating_next.setStyleSheet(btn_style)

    def _apply_status_bar_style(self):
        """تنسيق عناصر شريط الحالة كشارات وبطاقات أنيقة"""
        is_dark = (self.current_theme == "dark")
        badge_bg = "#2563eb" if is_dark else "#3b82f6"
        badge_fg = "#ffffff"
        pill_bg = "#262830" if is_dark else "#e2e8f0"
        pill_fg = "#cbd5e1" if is_dark else "#475569"

        self.lbl_format_badge.setStyleSheet(f"""
            background-color: {badge_bg};
            color: {badge_fg};
            border-radius: 4px;
            padding: 2px 8px;
            font-weight: bold;
            font-size: 11px;
        """)

        base_style = f"padding: 2px 10px; font-size: 12px; color: {pill_fg};"
        self.lbl_filename.setStyleSheet(base_style + " font-weight: 500;")
        self.lbl_dims.setStyleSheet(base_style)
        self.lbl_filesize.setStyleSheet(base_style)

        pill_style = f"""
            background-color: {pill_bg};
            color: {pill_fg};
            border-radius: 4px;
            padding: 2px 8px;
            font-size: 11px;
            font-weight: bold;
        """
        self.lbl_zoom.setStyleSheet(pill_style)
        self.lbl_counter.setStyleSheet(pill_style)

    def update_floating_buttons_pos(self):
        """تثبيت أزرار التنقل الطافية على الجانبين الأيمن والأيسر بدقة تامة"""
        vw = self.viewer.viewport().width()
        vh = self.viewer.viewport().height()
        if vw <= 50:
            return
        btn_size = 46
        btn_y = max(10, (vh - btn_size) // 2)

        # زر السابق على اليسار وزر التالي على اليمين
        self.btn_floating_prev.setGeometry(20, btn_y, btn_size, btn_size)
        self.btn_floating_next.setGeometry(max(70, vw - 20 - btn_size), btn_y, btn_size, btn_size)

    def showEvent(self, event):
        """عند إظهار النافذة نضمن ملاءمة الصورة لحجم الشاشة فوراً"""
        super().showEvent(event)
        QTimer.singleShot(50, self.viewer.fit_to_window)
        QTimer.singleShot(50, self.update_floating_buttons_pos)

    def resizeEvent(self, event):
        """ضبط مواقع الأزرار الطافية عند تغيير حجم النافذة"""
        super().resizeEvent(event)
        self.update_floating_buttons_pos()

    def closeEvent(self, event):
        """إيقاف كافة العمليات والمؤقتات والخيوط الخلفية قبل إغلاق النافذة بأمان"""
        if hasattr(self, "slideshow_timer"):
            self.slideshow_timer.stop()
        if hasattr(self, "filmstrip"):
            self.filmstrip.stop_worker()
        super().closeEvent(event)


    def _apply_current_theme(self):
        """تطبيق السمة المختارة وتحديث جميع الأيقونات الفيكتور"""
        is_dark = (self.current_theme == "dark")
        self.setStyleSheet(DARK_THEME_QSS if is_dark else LIGHT_THEME_QSS)
        self.viewer.set_theme_background(self.current_theme)

        # تحديث ألوان أيقونات شريط الأدوات بالكامل
        refresh_toolbar_icons(self)
        self._apply_status_bar_style()

    def toggle_theme(self):
        """التبديل بين الوضع الفاتح والداكن وحفظ التفضيل"""
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.settings.set_theme(self.current_theme)
        self._apply_current_theme()
        if not self.current_pil_image:
            self._render_welcome_screen()

    def update_association_ui(self):
        """تحديث أيقونة وحالة الارتباط الافتراضي"""
        self.is_associated = is_heic_associated()
        refresh_toolbar_icons(self)

    def _render_welcome_screen(self):
        """عرض شاشة ترحيبية نظيفة وأنيقة بدقة فيكتور"""
        is_dark = (self.current_theme == "dark")
        bg_col = QColor("#121316" if is_dark else "#f8fafc")
        title_col = QColor("#f1f5f9" if is_dark else "#0f172a")
        text_col = QColor("#64748b" if is_dark else "#94a3b8")

        pix = QPixmap(800, 420)
        pix.fill(bg_col)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        ico_path = Path(__file__).resolve().parent.parent / "assets" / "app_icon.png"
        if ico_path.exists():
            logo_pix = QPixmap(str(ico_path)).scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            painter.drawPixmap(360, 60, logo_pix)

        font = QFont("Segoe UI", 20, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(title_col)
        painter.drawText(pix.rect().adjusted(0, 160, 0, 0), Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, "HEIC Viewer")

        font = QFont("Segoe UI", 12)
        painter.setFont(font)
        painter.setPen(text_col)
        desc = "اسحب وأفلت أي صورة بصيغة HEIC / HEIF هنا لفتحها فوراً\nأو انقر مرتين على أي ملف .heic في مستكشف ويندوز"
        painter.drawText(pix.rect().adjusted(0, 210, 0, 0), Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, desc)

        painter.end()

        self.viewer.display_pixmap(pix)
        self.lbl_format_badge.setText("")
        self.lbl_filename.setText("في انتظار اختيار صورة...")
        self.lbl_dims.setText("")
        self.lbl_filesize.setText("")
        self.lbl_counter.setText("")
        self.btn_floating_prev.hide()
        self.btn_floating_next.hide()
        if hasattr(self, "filmstrip"):
            self.filmstrip.hide()

    def load_image_file(self, file_path: str) -> bool:
        """تحميل صورة HEIC وعرضها مع ملاءمة الحجم تماماً للنافذة"""
        if hasattr(self, "filmstrip"):
            self.filmstrip.show()
        img, metadata, err = load_image(file_path)
        if err or not img:
            QMessageBox.critical(self, "خطأ في قراءة الصورة", err or "تعذر تحميل الصورة.")
            return False

        qimg = self._pil_to_qimage(img)
        pix = QPixmap.fromImage(qimg)

        self.current_filepath = str(Path(file_path).resolve())
        self.current_pil_image = img
        self.current_metadata = metadata

        # عرض الصورة وتفعيل الملاءمة للشاشة
        self.viewer.display_pixmap(pix)
        QTimer.singleShot(40, self.viewer.fit_to_window)
        QTimer.singleShot(40, self.update_floating_buttons_pos)

        path = Path(file_path)
        ext = path.suffix.upper().replace(".", "")
        self.setWindowTitle(f"{path.name} — ({img.width} × {img.height}) — HEIC Viewer")

        # تحديث شريط الحالة الأنيق
        stat = path.stat()
        file_size_mb = stat.st_size / (1024 * 1024)
        size_str = f"{file_size_mb:.2f} MB" if file_size_mb >= 1.0 else f"{stat.st_size / 1024:.1f} KB"

        self.lbl_format_badge.setText(ext)
        self.lbl_filename.setText(path.name)
        self.lbl_dims.setText(f"{img.width} × {img.height}")
        self.lbl_filesize.setText(size_str)

        self._scan_folder_for_images(path)

        if len(self.folder_images) > 1:
            self.btn_floating_prev.show()
            self.btn_floating_next.show()
        else:
            self.btn_floating_prev.hide()
            self.btn_floating_next.hide()

        return True

    def _pil_to_qimage(self, pil_image) -> QImage:
        """تحويل سلس وسريع من صورة PIL إلى صورة QImage"""
        if pil_image.mode != "RGBA" and pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGBA")

        if pil_image.mode == "RGBA":
            data = pil_image.tobytes("raw", "RGBA")
            qimage = QImage(data, pil_image.width, pil_image.height, QImage.Format.Format_RGBA8888)
            return qimage.copy()
        else:
            data = pil_image.tobytes("raw", "RGB")
            qimage = QImage(data, pil_image.width, pil_image.height, pil_image.width * 3, QImage.Format.Format_RGB888)
            return qimage.copy()

    def _scan_folder_for_images(self, current_file: Path):
        """حصر جميع الصور في نفس المجلد لتمكين التنقل الفوري بالأسهم"""
        folder = current_file.parent
        self.folder_images = []
        try:
            for item in sorted(folder.iterdir(), key=lambda p: p.name.lower()):
                if item.is_file() and is_supported_file(str(item)):
                    self.folder_images.append(item)

            if current_file in self.folder_images:
                self.current_index = self.folder_images.index(current_file)
                self.lbl_counter.setText(f"{self.current_index + 1} / {len(self.folder_images)}")
                self.filmstrip.set_images(self.folder_images, self.current_index)
                self._trigger_preloading()
            else:
                self.lbl_counter.setText("")
        except Exception:
            self.folder_images = []
            self.lbl_counter.setText("")

    def _trigger_preloading(self):
        """التحميل المسبق الذكي في الخلفية للصور المجاورة لفتحها في 0 ثانية فوراً"""
        if not self.folder_images or self.current_index < 0:
            return
        total = len(self.folder_images)
        if total <= 1:
            return

        to_preload = []
        for offset in [1, -1, 2, -2]:
            idx = (self.current_index + offset) % total
            to_preload.append(str(self.folder_images[idx]))

        from services.image_loader import preload_images_background
        preload_images_background(to_preload)

    def show_previous_image(self):
        """الانتقال للصورة السابقة في نفس المجلد"""
        if not self.folder_images:
            return
        if self.current_index > 0:
            self.current_index -= 1
        else:
            self.current_index = len(self.folder_images) - 1
        self.load_image_file(str(self.folder_images[self.current_index]))

    def show_next_image(self):
        """الانتقال للصورة التالية في نفس المجلد"""
        if not self.folder_images:
            return
        if self.current_index < len(self.folder_images) - 1:
            self.current_index += 1
        else:
            self.current_index = 0
        self.load_image_file(str(self.folder_images[self.current_index]))

    def update_zoom_label(self, factor: float):
        """تحديث نسبة التكبير المعروضة في شريط الحالة"""
        percent = int(factor * 100)
        self.lbl_zoom.setText(f"{percent}%")

    def toggle_fullscreen(self):
        """التبديل بين وضع ملء الشاشة والوضع الطبيعي"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def action_open_file(self):
        """فتح صورة جديدة من المستكشف"""
        flt = "جميع الصور المدعومة (*.heic *.heif *.jpg *.jpeg *.png *.webp *.bmp *.tiff);;صور HEIC (*.heic *.heif);;جميع الملفات (*.*)"
        path, _ = QFileDialog.getOpenFileName(self, "فتح صورة", "", flt)
        if path:
            self.load_image_file(path)

    def action_export_image(self):
        """تصدير وتحويل الصورة الحالية لصيغة أخرى"""
        if not self.current_pil_image:
            QMessageBox.warning(self, "تنبيه", "لا توجد صورة محملة لتصديرها.")
            return

        stem = Path(self.current_filepath).stem if self.current_filepath else "exported"
        default_name = str(Path.home() / "Desktop" / f"{stem}.png")

        dest, _ = QFileDialog.getSaveFileName(
            self, "حفظ وتصدير الصورة", default_name,
            "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg);;WebP Image (*.webp);;BMP Image (*.bmp)"
        )
        if not dest:
            return

        ok, err = convert_image(self.current_pil_image, dest)
        if ok:
            QMessageBox.information(self, "تم الحفظ بنجاح", f"تم حفظ الصورة في:\n{dest}")
        else:
            QMessageBox.critical(self, "خطأ في التصدير", f"تعذر حفظ الصورة:\n{err}")

    def action_copy_clipboard(self):
        """نسخ الصورة الحالية للحافظة للتمكن من لصقها مباشرة في أي تطبيق"""
        if not self.viewer.pixmap_item.pixmap().isNull():
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setPixmap(self.viewer.pixmap_item.pixmap())
            self.status_bar.showMessage("✓ تم نسخ الصورة إلى الحافظة بنجاح!", 3500)
        else:
            QMessageBox.warning(self, "تنبيه", "لا توجد صورة لنسخها.")

    def action_show_info(self):
        """عرض نافذة تفاصيل الصورة وبيانات EXIF"""
        if not self.current_metadata:
            QMessageBox.warning(self, "تنبيه", "يرجى فتح صورة أولاً للاطلاع على تفاصيلها.")
            return
        is_dark = (self.current_theme == "dark")
        dlg = MetadataDialog(self.current_metadata, is_dark=is_dark, parent=self)
        dlg.exec()

    def _on_filmstrip_image_selected(self, index: int):
        """الاستجابة للنقر على مصغرة في شريط المصغرات السفلي"""
        if 0 <= index < len(self.folder_images) and index != self.current_index:
            self.load_image_file(str(self.folder_images[index]))

    def toggle_filmstrip(self):
        """إظهار أو إخفاء شريط المصغرات السفلي"""
        vis = not self.filmstrip.isVisible()
        self.filmstrip.setVisible(vis)
        self.status_bar.showMessage("تم إظهار شريط المصغرات" if vis else "تم إخفاء شريط المصغرات", 2000)

    def toggle_slideshow(self):
        """بدء أو إيقاف عرض الشرائح التلقائي"""
        if not self.folder_images or len(self.folder_images) <= 1:
            QMessageBox.information(self, "عرض الشرائح", "لا توجد صور كافية في المجلد لبدء عرض الشرائح.")
            return
        self.is_slideshow_running = not self.is_slideshow_running
        if self.is_slideshow_running:
            self.slideshow_timer.start()
            self.status_bar.showMessage("▶ تم بدء عرض الشرائح التلقائي (كل 3.5 ثانية)", 3500)
        else:
            self.slideshow_timer.stop()
            self.status_bar.showMessage("⏸ تم إيقاف عرض الشرائح التلقائي", 2500)
        refresh_toolbar_icons(self)

    def _slideshow_next_tick(self):
        if self.is_slideshow_running and self.folder_images:
            self.show_next_image()

    def action_set_as_wallpaper(self):
        """تعيين صورة HEIC الحالية كخلفية لسطح مكتب ويندوز مباشرة"""
        if not self.current_filepath or not self.current_pil_image:
            QMessageBox.warning(self, "تنبيه", "يرجى فتح صورة أولاً لتعيينها كخلفية.")
            return
        try:
            import ctypes
            app_data = os.environ.get("APPDATA", str(Path.home()))
            wall_dir = Path(app_data) / "HEICViewer"
            wall_dir.mkdir(parents=True, exist_ok=True)
            wall_path = wall_dir / "desktop_wallpaper.jpg"
            self.current_pil_image.convert("RGB").save(str(wall_path), "JPEG", quality=98)
            # SPI_SETDESKWALLPAPER = 20, SPIF_UPDATEINIFILE = 1, SPIF_SENDCHANGE = 2
            res = ctypes.windll.user32.SystemParametersInfoW(20, 0, str(wall_path), 3)
            if res:
                self.status_bar.showMessage("✓ تم تعيين الصورة الحالية كخلفية لسطح مكتب ويندوز بنجاح!", 4000)
            else:
                QMessageBox.warning(self, "تنبيه", "تعذر تعيين الخلفية من خلال نظام ويندوز.")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تعيين الخلفية:\n{e}")

    def action_open_containing_folder(self):
        """فتح مستكشف الملفات مع تحديد الصورة الحالية"""
        if not self.current_filepath or not os.path.exists(self.current_filepath):
            QMessageBox.warning(self, "تنبيه", "يرجى فتح صورة أولاً لعرض موقعها.")
            return
        import subprocess
        try:
            subprocess.Popen(f'explorer /select,"{self.current_filepath}"')
        except Exception as e:
            QMessageBox.warning(self, "تنبيه", f"تعذر فتح مستكشف الملفات:\n{e}")

    def action_delete_image(self):
        """حذف الصورة الحالية ونقلها بأمان إلى سلة المحذوفات"""
        if not self.current_filepath or not os.path.exists(self.current_filepath):
            return
        curr_path = Path(self.current_filepath)
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            f"هل تريد بالتأكيد نقل هذه الصورة إلى سلة المحذوفات؟\n\n{curr_path.name}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            import ctypes
            from ctypes import wintypes
            class SHFILEOPSTRUCTW(ctypes.Structure):
                _fields_ = [
                    ('hwnd', wintypes.HWND),
                    ('wFunc', wintypes.UINT),
                    ('pFrom', wintypes.LPCWSTR),
                    ('pTo', wintypes.LPCWSTR),
                    ('fFlags', wintypes.WORD),
                    ('fAnyOperationsAborted', wintypes.BOOL),
                    ('hNameMappings', wintypes.LPVOID),
                    ('lpszProgressTitle', wintypes.LPCWSTR)
                ]
            pfrom = str(curr_path) + '\0\0'
            op = SHFILEOPSTRUCTW()
            op.wFunc = 0x0003  # FO_DELETE
            op.pFrom = pfrom
            op.fFlags = 0x0040 | 0x0010  # FOF_ALLOWUNDO | FOF_NOCONFIRMATION
            res = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
            if res == 0 and not op.fAnyOperationsAborted:
                self.status_bar.showMessage(f"✓ تم نقل {curr_path.name} إلى سلة المحذوفات بنجاح.", 4000)
                old_idx = self.current_index
                if curr_path in self.folder_images:
                    self.folder_images.remove(curr_path)
                if self.folder_images:
                    next_idx = min(old_idx, len(self.folder_images) - 1)
                    self.load_image_file(str(self.folder_images[next_idx]))
                else:
                    self._render_welcome_screen()
            else:
                QMessageBox.warning(self, "خطأ", "تعذر حذف الصورة أو تم إلغاء العملية.")

    def action_print_image(self):
        """طباعة الصورة الحالية بدقة عالية"""
        if not self.current_pil_image or self.viewer.pixmap_item.pixmap().isNull():
            QMessageBox.warning(self, "تنبيه", "يرجى فتح صورة أولاً لطباعتها.")
            return
        from PySide6.QtPrintSupport import QPrinter, QPrintDialog
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dlg = QPrintDialog(printer, self)
        dlg.setWindowTitle("طباعة الصورة")
        if dlg.exec() == QPrintDialog.DialogCode.Accepted:
            painter = QPainter(printer)
            pix = self.viewer.pixmap_item.pixmap()
            rect = printer.pageRect(QPrinter.Unit.DevicePixel)
            scaled = pix.scaled(rect.size().toSize(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            x = int(rect.x() + (rect.width() - scaled.width()) / 2)
            y = int(rect.y() + (rect.height() - scaled.height()) / 2)
            painter.drawPixmap(x, y, scaled)
            painter.end()
            self.status_bar.showMessage("✓ تم إرسال الصورة إلى الطابعة بنجاح!", 4000)

    def action_generate_folder_thumbnails(self):
        """توليد وتحديث المعاينات المصغرة لجميع صور المجلد في مستكشف ويندوز"""
        if not self.folder_images:
            QMessageBox.warning(self, "تنبيه", "يرجى فتح صورة من المجلد أولاً لتوليد وتحديث المعاينات المصغرة لملفاته.")
            return

        folder = str(self.folder_images[0].parent)
        total_count = len(self.folder_images)
        self.status_bar.showMessage(f"جاري توليد وتحديث المعاينات المصغرة لـ {total_count} صورة في ويندوز...", 15000)

        import threading
        def worker():
            try:
                from services.thumbnail_cache_helper import cache_chunk
                from concurrent.futures import ThreadPoolExecutor
                import ctypes

                all_paths = [str(p) for p in self.folder_images if p.suffix.lower() in [".heic", ".heif"]]
                chunk_size = 20
                chunks = [all_paths[i:i+chunk_size] for i in range(0, len(all_paths), chunk_size)]

                with ThreadPoolExecutor(max_workers=6) as ex:
                    results = list(ex.map(cache_chunk, chunks))

                cached = sum(results)
                shell32 = ctypes.windll.shell32
                shell32.SHChangeNotify(0x00001000, 0x0005, folder, None)
                shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
                QTimer.singleShot(0, lambda: self.status_bar.showMessage(f"✓ تم بنجاح تحديث وتوليد المعاينات لـ {cached} صورة في مستكشف ويندوز!", 5000))
            except Exception as e:
                QTimer.singleShot(0, lambda: self.status_bar.showMessage(f"تنبيه أثناء توليد المعاينات: {e}", 5000))

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def action_associate_heic(self):
        """تسجيل البرنامج كعارض افتراضي لملفات HEIC في نظام ويندوز"""
        reply = QMessageBox.question(
            self,
            "الارتباط الافتراضي لملفات HEIC",
            "هل ترغب في تعيين HEIC Viewer كبرنامج افتراضي لفتح جميع صور HEIC / HEIF في ويندوز؟\n\nستفتح الصور تلقائياً بهذا البرنامج عند النقر المزدوج عليها في مستكشف الملفات.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply == QMessageBox.StandardButton.Yes:
            ok, msg = register_association()
            if ok:
                QMessageBox.information(
                    self, "تم الربط بنجاح",
                    f"{msg}\n\nإذا عرض ويندوز 11 شاشة تأكيد، اختر 'HEIC Viewer' واضغط 'دائماً'."
                )
                self.update_association_ui()
            else:
                QMessageBox.warning(self, "تنبيه", f"تعذر إتمام التسجيل:\n{msg}")

    def keyPressEvent(self, event):
        """دعم اختصارات لوحة المفاتيح الإضافية"""
        key = event.key()
        if key == Qt.Key.Key_Space:
            self.toggle_slideshow()
        elif key == Qt.Key.Key_Escape:
            if self.is_slideshow_running:
                self.toggle_slideshow()
            elif self.isFullScreen():
                self.showNormal()
        elif key == Qt.Key.Key_Delete:
            self.action_delete_image()
        elif key == Qt.Key.Key_T:
            self.toggle_filmstrip()
        else:
            super().keyPressEvent(event)

    # السحب والإفلات المباشر (Drag and Drop)
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            local_path = urls[0].toLocalFile()
            if local_path:
                self.load_image_file(local_path)
        event.acceptProposedAction()
