from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QPushButton, QWidget

from pocket_app.resources import Qss, ThemeManager, load_qss
from pocket_app.utils import str_isempty


class Tag(QPushButton):
    DEFAULT_HEIGHT = 28
    DEFAULT_HORIZONTAL_PADDING = 12

    tag_clicked = pyqtSignal(str)

    def __init__(
        self,
        text: str,
        tooltip: str = "",
        parent: QWidget | None = None,
        height: int = DEFAULT_HEIGHT,
        background_color: str = "",
        tag_id: str = "",
    ) -> None:
        super().__init__(text, parent)
        self._tooltip = tooltip
        self._height = height
        self._background_color = background_color
        self._tag_id = tag_id
        ThemeManager.theme_changed.connect(self._on_theme_changed)
        self._setup_ui()
        self.clicked.connect(self._emit_tag_clicked)

    def _setup_ui(self) -> None:
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFixedHeight(self._height)
        self.setMinimumWidth(self.sizeHint().width() + self.DEFAULT_HORIZONTAL_PADDING)
        self.setProperty("selected", False)
        self._apply_style()
        self.set_tooltip(self._tooltip)

    def _apply_style(self) -> None:
        radius = max(0, self._height // 2)
        colors = self._resolve_colors()
        style = load_qss(
            Qss.s_tag,
            extra_vars={
                "border_radius": f"{radius}px",
                "background_color": colors["background"],
                "text_color": colors["text"],
                "border_color": colors["border"],
                "hover_background_color": colors["hover_background"],
                "hover_border_color": colors["hover_border"],
                "pressed_background_color": colors["pressed_background"],
                "pressed_border_color": colors["pressed_border"],
                "selected_background_color": colors["selected_background"],
                "selected_text_color": colors["selected_text"],
                "selected_border_color": colors["selected_border"],
                "tooltip_background_color": Qss.variables.get("panel_background", "#ffffff"),
                "tooltip_text_color": Qss.variables.get("body_text_color", "#20324d"),
                "tooltip_border_color": Qss.variables.get("panel_border", "#bccde0"),
            },
        )
        self.setStyleSheet(style)

    def _resolve_colors(self) -> dict[str, str]:
        if str_isempty(self._background_color):
            return self._theme_default_colors()

        base_color = QColor(self._background_color)
        if not base_color.isValid():
            return self._theme_default_colors()

        luminance = self._luminance(base_color)
        text_color = QColor("#20324d") if luminance >= 160 else QColor("#f5f8ff")
        border_color = self._shade(base_color, 0.82 if luminance >= 160 else 1.28)
        hover_background = self._shade(base_color, 0.94 if luminance >= 160 else 1.08)
        hover_border = self._shade(base_color, 0.76 if luminance >= 160 else 1.36)
        pressed_background = self._shade(
            base_color, 0.88 if luminance >= 160 else 1.16
        )
        pressed_border = self._shade(base_color, 0.68 if luminance >= 160 else 1.48)
        selected_background = self._shade(
            base_color, 0.84 if luminance >= 160 else 1.22
        )
        selected_text = text_color
        selected_border = self._shade(base_color, 0.60 if luminance >= 160 else 1.58)

        return {
            "background": base_color.name(),
            "text": text_color.name(),
            "border": border_color.name(),
            "hover_background": hover_background.name(),
            "hover_border": hover_border.name(),
            "pressed_background": pressed_background.name(),
            "pressed_border": pressed_border.name(),
            "selected_background": selected_background.name(),
            "selected_text": selected_text.name(),
            "selected_border": selected_border.name(),
        }

    def _theme_default_colors(self) -> dict[str, str]:
        if ThemeManager.current_theme == Qss.Themes.DARK:
            return {
                "background": "#202734",
                "text": "#e7edf8",
                "border": "#47546d",
                "hover_background": "#293244",
                "hover_border": "#7da0d5",
                "pressed_background": "#31405a",
                "pressed_border": "#94b4e5",
                "selected_background": "#334563",
                "selected_text": "#f2f6ff",
                "selected_border": "#90b2e7",
            }

        return {
            "background": "#ffffff",
            "text": "#2b3e57",
            "border": "#d5ddea",
            "hover_background": "#eef4ff",
            "hover_border": "#93b1df",
            "pressed_background": "#dde9ff",
            "pressed_border": "#789ed7",
            "selected_background": "#dce9ff",
            "selected_text": "#1e3a63",
            "selected_border": "#6d97d8",
        }

    @staticmethod
    def _luminance(color: QColor) -> float:
        return (
            0.2126 * color.red()
            + 0.7152 * color.green()
            + 0.0722 * color.blue()
        )

    @staticmethod
    def _shade(color: QColor, factor: float) -> QColor:
        target = QColor(color)
        if factor < 1:
            return target.darker(max(100, int(100 / factor)))
        return target.lighter(max(100, int(factor * 100)))

    def _emit_tag_clicked(self) -> None:
        self.tag_clicked.emit(self.tag_id())

    def set_text(self, text: str) -> None:
        self.setText(text)
        self.setMinimumWidth(self.sizeHint().width() + self.DEFAULT_HORIZONTAL_PADDING)

    def tag_id(self) -> str:
        return self._tag_id if not str_isempty(self._tag_id) else self.text()

    def set_tag_id(self, tag_id: str) -> None:
        self._tag_id = tag_id

    def set_tooltip(self, tooltip: str) -> None:
        self._tooltip = tooltip
        self.setToolTip("" if str_isempty(tooltip) else tooltip)

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", selected)
        style = self.style()
        if style is not None:
            style.unpolish(self)
            style.polish(self)

    def set_background_color(self, background_color: str) -> None:
        self._background_color = background_color
        self._apply_style()

    def _on_theme_changed(self, _theme: str) -> None:
        self._apply_style()
