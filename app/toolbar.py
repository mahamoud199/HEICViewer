"""
app/toolbar.py - بناء شريط أدوات احترافي بأيقونات فيكتور حقيقية وبدون أي إيموجي
"""
from PySide6.QtWidgets import QToolBar, QWidget, QSizePolicy
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import Qt, QSize
from app.icon_helper import get_svg_icon


def setup_toolbar(window) -> QToolBar:
    """إنشاء وتهيئة شريط الأدوات بأيقونات SVG نقية وتصميم عصري"""
    tb = QToolBar("شريط الأدوات الرئيسي", window)
    tb.setIconSize(QSize(20, 20))
    tb.setMovable(False)

    color = "#f1f3f7" if window.current_theme == "dark" else "#334155"

    # 1. فتح ملف
    window.act_open = QAction(get_svg_icon("open.svg", color), "", window)
    window.act_open.setShortcut(QKeySequence.StandardKey.Open)
    window.act_open.setToolTip("فتح صورة (Ctrl + O)")
    window.act_open.triggered.connect(window.action_open_file)
    tb.addAction(window.act_open)

    # 2. حفظ وتصدير
    window.act_save = QAction(get_svg_icon("save.svg", color), "", window)
    window.act_save.setShortcut(QKeySequence.StandardKey.Save)
    window.act_save.setToolTip("تصدير أو حفظ باسم (Ctrl + S)")
    window.act_save.triggered.connect(window.action_export_image)
    tb.addAction(window.act_save)

    # 3. طباعة الصورة
    window.act_print = QAction(get_svg_icon("print.svg", color), "", window)
    window.act_print.setShortcut(QKeySequence.StandardKey.Print)
    window.act_print.setToolTip("طباعة الصورة (Ctrl + P)")
    window.act_print.triggered.connect(window.action_print_image)
    tb.addAction(window.act_print)

    # 4. نسخ إلى الحافظة
    window.act_copy = QAction(get_svg_icon("copy.svg", color), "", window)
    window.act_copy.setShortcut(QKeySequence.StandardKey.Copy)
    window.act_copy.setToolTip("نسخ إلى الحافظة (Ctrl + C)")
    window.act_copy.triggered.connect(window.action_copy_clipboard)
    tb.addAction(window.act_copy)

    # 5. فتح موقع الصورة في مستكشف الملفات
    window.act_open_folder = QAction(get_svg_icon("folder_open.svg", color), "", window)
    window.act_open_folder.setToolTip("فتح وتحديد موقع الملف في مستكشف ويندوز")
    window.act_open_folder.triggered.connect(window.action_open_containing_folder)
    tb.addAction(window.act_open_folder)

    # 6. حذف إلى سلة المحذوفات
    window.act_delete = QAction(get_svg_icon("delete.svg", color), "", window)
    window.act_delete.setShortcut(QKeySequence.StandardKey.Delete)
    window.act_delete.setToolTip("نقل الصورة إلى سلة المحذوفات (Delete)")
    window.act_delete.triggered.connect(window.action_delete_image)
    tb.addAction(window.act_delete)

    tb.addSeparator()

    # 7. التنقل السابق / التالي
    window.act_prev = QAction(get_svg_icon("prev.svg", color), "", window)
    window.act_prev.setShortcut(Qt.Key.Key_Left)
    window.act_prev.setToolTip("الصورة السابقة (السهم الأيسر)")
    window.act_prev.triggered.connect(window.show_previous_image)
    tb.addAction(window.act_prev)

    window.act_next = QAction(get_svg_icon("next.svg", color), "", window)
    window.act_next.setShortcut(Qt.Key.Key_Right)
    window.act_next.setToolTip("الصورة التالية (السهم الأيمن)")
    window.act_next.triggered.connect(window.show_next_image)
    tb.addAction(window.act_next)

    # 8. عرض الشرائح التلقائي
    window.act_slideshow = QAction(get_svg_icon("slideshow_play.svg", color), "", window)
    window.act_slideshow.setShortcut(Qt.Key.Key_F5)
    window.act_slideshow.setToolTip("بدء / إيقاف عرض الشرائح التلقائي (F5 أو المسافة)")
    window.act_slideshow.triggered.connect(window.toggle_slideshow)
    tb.addAction(window.act_slideshow)

    # 9. شريط المصغرات السفلي
    window.act_filmstrip = QAction(get_svg_icon("filmstrip.svg", color), "", window)
    window.act_filmstrip.setShortcut(Qt.Key.Key_T)
    window.act_filmstrip.setToolTip("إظهار / إخفاء شريط المصغرات السفلي (مفتاح T)")
    window.act_filmstrip.triggered.connect(window.toggle_filmstrip)
    tb.addAction(window.act_filmstrip)

    tb.addSeparator()

    # 10. التكبير والتصغير
    window.act_zoom_in = QAction(get_svg_icon("zoom_in.svg", color), "", window)
    window.act_zoom_in.setShortcut(QKeySequence.StandardKey.ZoomIn)
    window.act_zoom_in.setToolTip("تكبير الصورة (+)")
    window.act_zoom_in.triggered.connect(lambda: window.viewer.zoom_by(1.25))
    tb.addAction(window.act_zoom_in)

    window.act_zoom_out = QAction(get_svg_icon("zoom_out.svg", color), "", window)
    window.act_zoom_out.setShortcut(QKeySequence.StandardKey.ZoomOut)
    window.act_zoom_out.setToolTip("تصغير الصورة (-)")
    window.act_zoom_out.triggered.connect(lambda: window.viewer.zoom_by(0.8))
    tb.addAction(window.act_zoom_out)

    window.act_actual = QAction(get_svg_icon("zoom_actual.svg", color), "", window)
    window.act_actual.setShortcut(Qt.Key.Key_1)
    window.act_actual.setToolTip("الحجم الفعلي 100% (مفتاح 1)")
    window.act_actual.triggered.connect(window.viewer.zoom_actual_size)
    tb.addAction(window.act_actual)

    window.act_fit = QAction(get_svg_icon("zoom_fit.svg", color), "", window)
    window.act_fit.setShortcut(Qt.Key.Key_0)
    window.act_fit.setToolTip("ملاءمة الشاشة (مفتاح 0)")
    window.act_fit.triggered.connect(window.viewer.fit_to_window)
    tb.addAction(window.act_fit)

    tb.addSeparator()

    # 11. التدوير والقلب
    window.act_rot_left = QAction(get_svg_icon("rotate_left.svg", color), "", window)
    window.act_rot_left.setShortcut(Qt.Key.Key_L)
    window.act_rot_left.setToolTip("تدوير يسار 90° (L)")
    window.act_rot_left.triggered.connect(lambda: window.viewer.rotate_image(-90))
    tb.addAction(window.act_rot_left)

    window.act_rot_right = QAction(get_svg_icon("rotate_right.svg", color), "", window)
    window.act_rot_right.setShortcut(Qt.Key.Key_R)
    window.act_rot_right.setToolTip("تدوير يمين 90° (R)")
    window.act_rot_right.triggered.connect(lambda: window.viewer.rotate_image(90))
    tb.addAction(window.act_rot_right)

    window.act_flip_h = QAction(get_svg_icon("flip_h.svg", color), "", window)
    window.act_flip_h.setToolTip("قلب أفقي")
    window.act_flip_h.triggered.connect(window.viewer.flip_horizontal)
    tb.addAction(window.act_flip_h)

    tb.addSeparator()

    # 12. تعيين كخلفية لسطح المكتب
    window.act_wallpaper = QAction(get_svg_icon("wallpaper.svg", color), "", window)
    window.act_wallpaper.setToolTip("تعيين الصورة كخلفية لسطح مكتب ويندوز")
    window.act_wallpaper.triggered.connect(window.action_set_as_wallpaper)
    tb.addAction(window.act_wallpaper)

    # 13. معلومات الصورة والميتاداتا
    window.act_info = QAction(get_svg_icon("info.svg", color), "", window)
    window.act_info.setShortcut(Qt.Key.Key_I)
    window.act_info.setToolTip("معلومات الصورة وEXIF (Ctrl + I)")
    window.act_info.triggered.connect(window.action_show_info)
    tb.addAction(window.act_info)

    # 14. ملء الشاشة
    window.act_fs = QAction(get_svg_icon("fullscreen.svg", color), "", window)
    window.act_fs.setShortcut(Qt.Key.Key_F11)
    window.act_fs.setToolTip("ملء الشاشة (F11)")
    window.act_fs.triggered.connect(window.toggle_fullscreen)
    tb.addAction(window.act_fs)

    # فاصل مرن لدفع أزرار الإعدادات والنظام لليسار
    spacer = QWidget()
    spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    tb.addWidget(spacer)

    # 15. زر تبديل الوضع الفاتح والداكن
    theme_icon_name = "theme_sun.svg" if window.current_theme == "dark" else "theme_moon.svg"
    window.act_theme = QAction(get_svg_icon(theme_icon_name, color), "", window)
    window.act_theme.setToolTip("التبديل بين الوضع الفاتح والداكن")
    window.act_theme.triggered.connect(window.toggle_theme)
    tb.addAction(window.act_theme)

    # 16. زر توليد المعاينات المصغرة لمستكشف ويندوز
    window.act_refresh_thumbs = QAction(get_svg_icon("refresh_thumbs.svg", color), "", window)
    window.act_refresh_thumbs.setToolTip("تحديث وتوليد المعاينات المصغرة لجميع صور المجلد في مستكشف ويندوز")
    window.act_refresh_thumbs.triggered.connect(window.action_generate_folder_thumbnails)
    tb.addAction(window.act_refresh_thumbs)

    # 17. زر الارتباط الافتراضي
    window.act_associate = QAction(get_svg_icon("associate.svg", color), "", window)
    window.act_associate.setToolTip("تعيين HEIC Viewer كعارض افتراضي لملفات HEIC في ويندوز")
    window.act_associate.triggered.connect(window.action_associate_heic)
    tb.addAction(window.act_associate)

    return tb


def refresh_toolbar_icons(window):
    """تحديث ألوان الأيقونات عند تبديل السمة (فاتح / داكن)"""
    color = "#f1f3f7" if window.current_theme == "dark" else "#334155"

    window.act_open.setIcon(get_svg_icon("open.svg", color))
    window.act_save.setIcon(get_svg_icon("save.svg", color))
    window.act_print.setIcon(get_svg_icon("print.svg", color))
    window.act_copy.setIcon(get_svg_icon("copy.svg", color))
    window.act_open_folder.setIcon(get_svg_icon("folder_open.svg", color))
    window.act_delete.setIcon(get_svg_icon("delete.svg", color))

    window.act_prev.setIcon(get_svg_icon("prev.svg", color))
    window.act_next.setIcon(get_svg_icon("next.svg", color))

    slideshow_icon = "slideshow_pause.svg" if getattr(window, "is_slideshow_running", False) else "slideshow_play.svg"
    window.act_slideshow.setIcon(get_svg_icon(slideshow_icon, color))
    window.act_filmstrip.setIcon(get_svg_icon("filmstrip.svg", color))

    window.act_zoom_in.setIcon(get_svg_icon("zoom_in.svg", color))
    window.act_zoom_out.setIcon(get_svg_icon("zoom_out.svg", color))
    window.act_actual.setIcon(get_svg_icon("zoom_actual.svg", color))
    window.act_fit.setIcon(get_svg_icon("zoom_fit.svg", color))
    window.act_rot_left.setIcon(get_svg_icon("rotate_left.svg", color))
    window.act_rot_right.setIcon(get_svg_icon("rotate_right.svg", color))
    window.act_flip_h.setIcon(get_svg_icon("flip_h.svg", color))

    window.act_wallpaper.setIcon(get_svg_icon("wallpaper.svg", color))
    window.act_info.setIcon(get_svg_icon("info.svg", color))
    window.act_fs.setIcon(get_svg_icon("fullscreen.svg", color))
    window.act_refresh_thumbs.setIcon(get_svg_icon("refresh_thumbs.svg", color))

    theme_icon_name = "theme_sun.svg" if window.current_theme == "dark" else "theme_moon.svg"
    window.act_theme.setIcon(get_svg_icon(theme_icon_name, color))

    assoc_icon = "check.svg" if window.is_associated else "associate.svg"
    window.act_associate.setIcon(get_svg_icon(assoc_icon, "#10b981" if window.is_associated else color))
