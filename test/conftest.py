import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from PyQt6.QtWidgets import QApplication
from pocket_app.resources import Qss, ThemeManager


@pytest.fixture(scope="session")
def qt_app() -> QApplication:
    app = QApplication.instance()
    if app is not None:
        return app
    return QApplication([])


@pytest.fixture(autouse=True)
def reset_theme() -> None:
    ThemeManager.set_theme(Qss.Themes.LIGHT)
    yield
    ThemeManager.set_theme(Qss.Themes.LIGHT)
