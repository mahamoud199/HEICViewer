import sys
import os
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from app.resource_helper import get_app_icon, get_resource_path
from app.filmstrip import ThumbnailFilmstrip

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

def test_app_icon_validity(qapp):
    icon = get_app_icon()
    assert not icon.isNull(), "Application icon must not be null"
    ico_path = get_resource_path("assets/app.ico")
    assert ico_path.exists(), f"app.ico must exist at {ico_path}"

def test_filmstrip_initialization(qapp):
    filmstrip = ThumbnailFilmstrip()
    assert filmstrip is not None
    assert filmstrip.list_widget.count() == 0

    # Test setting mock images
    sample_images = [Path(f"test_{i}.heic") for i in range(5)]
    filmstrip.set_images(sample_images, 0)
    assert filmstrip.list_widget.count() == 5
    filmstrip.stop_worker()

