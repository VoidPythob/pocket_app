import logging
from pathlib import Path

from PyQt6.QtCore import QEvent, QObject, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLineEdit, QPushButton, QWidget

from pocket_app.resources import Icons, Qss, ThemeManager, load_qss
from pocket_app.utils import str_isempty

logger = logging.getLogger(__name__)


class SearchBar(QFrame):
    DEFAULT_HEIGHT = 36
    DEFAULT_ICON_SIZE = 16
    DEFAULT_BUTTON_SIZE = 24

    search_requested = pyqtSignal(str)
    text_changed = pyqtSignal(str)

    def __init__(
        self,
        placeholder: str = "Search",
        tooltip: str = "",
        parent: QWidget | None = None,
        height: int = DEFAULT_HEIGHT,
        icon_path: str = Icons.search,
    ) -> None:
        super().__init__(parent)
        self._placeholder = placeholder
        self._tooltip = tooltip
        self._height = height
        self._icon_path = icon_path
        ThemeManager.theme_changed.connect(self._on_theme_changed)
        self._setup_ui()
        self._bind_events()

    def _setup_ui(self) -> None:
        self.setObjectName("searchBar")
        self.setFixedHeight(self._height)
        self.setProperty("focused", False)
        self._apply_style()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        self.line_edit = QLineEdit(self)
        self.line_edit.setObjectName("searchInput")
        self.line_edit.setPlaceholderText(self._placeholder)
        self.line_edit.setFrame(False)
        self.line_edit.installEventFilter(self)
        layout.addWidget(self.line_edit, 1)

        self.search_button = QPushButton(self)
        self.search_button.setObjectName("searchButton")
        self.search_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.search_button.setFixedSize(
            self.DEFAULT_BUTTON_SIZE, self.DEFAULT_BUTTON_SIZE
        )
        self.search_button.setIconSize(self._button_icon_size())
        self._apply_icon()
        layout.addWidget(self.search_button, 0, Qt.AlignmentFlag.AlignVCenter)

        self.set_tooltip(self._tooltip)

    def _bind_events(self) -> None:
        self.line_edit.returnPressed.connect(self._emit_search_requested)
        self.line_edit.textChanged.connect(self.text_changed.emit)
        self.search_button.clicked.connect(self._emit_search_requested)

    def _apply_style(self) -> None:
        radius = max(0, self._height // 2)
        style = load_qss(
            Qss.s_search_bar,
            extra_vars={"border_radius": f"{radius}px"},
        )
        self.setStyleSheet(style)

    def _apply_icon(self) -> None:
        if str_isempty(self._icon_path):
            logger.warning("SearchBar icon path is empty")
            self.search_button.setIcon(QIcon())
            return

        if not Path(self._icon_path).exists():
            logger.warning("SearchBar icon path does not exist: %s", self._icon_path)
            self.search_button.setIcon(QIcon())
            return

        icon = QIcon(self._icon_path)
        if icon.isNull():
            logger.warning("SearchBar icon failed to load: %s", self._icon_path)
            self.search_button.setIcon(QIcon())
            return

        self.search_button.setIcon(icon)
        self.search_button.setIconSize(self._button_icon_size())

    def _button_icon_size(self) -> QSize:
        icon_size = min(self.DEFAULT_ICON_SIZE, self.DEFAULT_BUTTON_SIZE - 8)
        return QSize(icon_size, icon_size)

    def _emit_search_requested(self) -> None:
        self.search_requested.emit(self.text())

    def eventFilter(self, watched: QObject | None, event: QEvent | None) -> bool:  # type: ignore
        if watched is self.line_edit and event is not None:
            if event.type() == QEvent.Type.FocusIn:
                self._set_focused(True)
            elif event.type() == QEvent.Type.FocusOut:
                self._set_focused(False)
        return super().eventFilter(watched, event)

    def _set_focused(self, focused: bool) -> None:
        self.setProperty("focused", focused)
        style = self.style()
        if style is not None:
            style.unpolish(self)
            style.polish(self)

    def text(self) -> str:
        return self.line_edit.text()

    def set_text(self, text: str) -> None:
        self.line_edit.setText(text)

    def clear(self) -> None:
        self.line_edit.clear()

    def set_placeholder(self, placeholder: str) -> None:
        self._placeholder = placeholder
        self.line_edit.setPlaceholderText(placeholder)

    def set_tooltip(self, tooltip: str) -> None:
        self._tooltip = tooltip
        final_tooltip = "" if str_isempty(tooltip) else tooltip
        self.setToolTip(final_tooltip)
        self.line_edit.setToolTip(final_tooltip)
        self.search_button.setToolTip(final_tooltip)

    def _on_theme_changed(self, _theme: str) -> None:
        self._apply_style()
