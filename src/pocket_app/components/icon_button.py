import logging
from pathlib import Path

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QPushButton, QWidget

from pocket_app.resources import Qss, ThemeManager, load_qss
from pocket_app.utils import str_isempty

logger = logging.getLogger(__name__)


class IconButton(QPushButton):
    def __init__(
        self,
        icon: str,
        tooltip: str = "",
        parent: QWidget | None = None,
        button_size: int = 32,
        icon_size: int = 16,
    ) -> None:
        super().__init__(parent)
        self._icon = icon
        self._tooltip = tooltip
        self._button_size = button_size
        self._icon_size = icon_size
        ThemeManager.theme_changed.connect(self._on_theme_changed)

        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFixedSize(self._button_size, self._button_size)
        self.setProperty("variant", "circle")
        self._apply_style()
        self.set_tooltip(self._tooltip)

        if str_isempty(self._icon):
            logger.warning("IconButton icon path is empty")
            return

        if not Path(self._icon).exists():
            logger.warning("IconButton icon path does not exist: %s", self._icon)
            return

        self.setIcon(QIcon(self._icon))
        self.setIconSize(QSize(self._icon_size, self._icon_size))

    def _apply_style(self) -> None:
        radius = max(0, self._button_size // 2)
        style = load_qss(
            Qss.s_icon_button,
            extra_vars={"border_radius": f"{radius}px"},
        )
        self.setStyleSheet(style)

    def set_tooltip(self, tooltip: str) -> None:
        self._tooltip = tooltip
        self.setToolTip("" if str_isempty(tooltip) else tooltip)

    def _on_theme_changed(self, _theme: str) -> None:
        self._apply_style()
