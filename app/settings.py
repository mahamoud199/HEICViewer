"""
app/settings.py - إدارة إعدادات البرنامج وتصميم الواجهة الحديثة (Windows 11 Fluent)
"""
from PySide6.QtCore import QSettings


class AppSettings:
    """إدارة الإعدادات المحفوظة للتطبيق باستخدام QSettings"""
    def __init__(self):
        self.settings = QSettings("HEICViewer", "HEICViewerPro")

    def get_theme(self) -> str:
        return self.settings.value("theme", "dark")

    def set_theme(self, theme_name: str):
        self.settings.setValue("theme", theme_name)


DARK_THEME_QSS = """
QMainWindow {
    background-color: #121316;
}
QToolBar {
    background-color: #18191e;
    border-bottom: 1px solid #262830;
    spacing: 4px;
    padding: 4px 8px;
}
QToolBar::separator {
    background-color: #2e303a;
    width: 1px;
    margin: 4px 6px;
}
QToolButton {
    background-color: transparent;
    color: #f1f3f7;
    padding: 6px;
    border-radius: 6px;
    border: none;
}
QToolButton:hover {
    background-color: #272932;
}
QToolButton:pressed {
    background-color: #323540;
}
QStatusBar {
    background-color: #18191e;
    color: #9ba1b0;
    border-top: 1px solid #262830;
    padding: 2px;
}
QLabel {
    color: #9ba1b0;
    font-family: 'Segoe UI', Tahoma, Arial;
    font-size: 12px;
}
QToolTip {
    background-color: #22242c;
    color: #ffffff;
    border: 1px solid #373a46;
    border-radius: 4px;
    padding: 5px 8px;
    font-size: 12px;
}
QMessageBox, QDialog {
    background-color: #18191e;
    color: #f1f3f7;
}
QPushButton {
    background-color: #3b82f6;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 7px 18px;
    font-weight: 600;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #2563eb;
}
QTableWidget {
    background-color: #121316;
    color: #e2e8f0;
    border: 1px solid #262830;
    border-radius: 8px;
    gridline-color: #1f2128;
}
QHeaderView::section {
    background-color: #1e2027;
    color: #9ba1b0;
    padding: 6px;
    border: none;
    font-weight: bold;
}
QListWidget {
    background-color: #16171d;
    border: 1px solid #262830;
    border-radius: 8px;
    padding: 2px;
}
QListWidget::item {
    border: 2px solid transparent;
    border-radius: 6px;
    padding: 2px;
}
QListWidget::item:hover {
    background-color: #262833;
    border-color: #3b82f6;
}
QListWidget::item:selected {
    background-color: #1e3a8a;
    border-color: #60a5fa;
}
"""

LIGHT_THEME_QSS = """
QMainWindow {
    background-color: #f8fafc;
}
QToolBar {
    background-color: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    spacing: 4px;
    padding: 4px 8px;
}
QToolBar::separator {
    background-color: #e2e8f0;
    width: 1px;
    margin: 4px 6px;
}
QToolButton {
    background-color: transparent;
    color: #334155;
    padding: 6px;
    border-radius: 6px;
    border: none;
}
QToolButton:hover {
    background-color: #f1f5f9;
}
QToolButton:pressed {
    background-color: #e2e8f0;
}
QStatusBar {
    background-color: #ffffff;
    color: #64748b;
    border-top: 1px solid #e2e8f0;
    padding: 2px;
}
QLabel {
    color: #64748b;
    font-family: 'Segoe UI', Tahoma, Arial;
    font-size: 12px;
}
QToolTip {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 5px 8px;
    font-size: 12px;
}
QMessageBox, QDialog {
    background-color: #ffffff;
    color: #0f172a;
}
QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 7px 18px;
    font-weight: 600;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #1d4ed8;
}
QTableWidget {
    background-color: #ffffff;
    color: #1e293b;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    gridline-color: #f1f5f9;
}
QHeaderView::section {
    background-color: #f8fafc;
    color: #475569;
    padding: 6px;
    border: none;
    font-weight: bold;
}
QListWidget {
    background-color: #f1f5f9;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 2px;
}
QListWidget::item {
    border: 2px solid transparent;
    border-radius: 6px;
    padding: 2px;
}
QListWidget::item:hover {
    background-color: #e2e8f0;
    border-color: #2563eb;
}
QListWidget::item:selected {
    background-color: #bfdbfe;
    border-color: #1d4ed8;
}
"""
