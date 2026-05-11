from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QFontMetrics
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from pocket_app.resources import (
    I18n,
    _I18n,
    I18nManager,
    Icons,
    Qss,
    ThemeManager,
    load_qss,
    tr,
)

from .icon_button import IconButton
from .popup_panel import PopupPanel
from .toast import Toaster


class LanguageSelector(QWidget):
    locale_selected = pyqtSignal(str)

    _option_label_keys = {
        I18n.Locales.ZH_CN: "language.chinese",
        I18n.Locales.EN_US: "language.english",
        I18n.Locales.JA_JP: "language.japanese",
    }

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        button_size: int = 36,
        icon_size: int = 18,
        tooltip: str = "",
    ) -> None:
        super().__init__(parent)
        self._tooltip = tooltip
        self._button_size = button_size
        self._icon_size = icon_size
        self._popup = PopupPanel(offset_y=10, match_anchor_width=False)
        self._content_widget: QWidget | None = None
        self._option_buttons: dict[_I18n.Locales, QPushButton] = {}

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.button = IconButton(
            Icons.i18n_toggle,
            tooltip=tooltip,
            parent=self,
            button_size=button_size,
            icon_size=icon_size,
        )
        layout.addWidget(self.button, 0, Qt.AlignmentFlag.AlignCenter)

        self._popup.bind_toggle(self.button)
        self._rebuild_popup_content()

        ThemeManager.theme_changed.connect(self._apply_popup_style)
        I18nManager.language_changed.connect(self._on_language_changed)
        self.destroyed.connect(self._dispose_popup)

    def set_tooltip(self, tooltip: str) -> None:
        self._tooltip = tooltip
        self.button.set_tooltip(tooltip)
        self._rebuild_popup_content()

    def current_locale(self) -> _I18n.Locales:
        return I18nManager.current_locale

    def _rebuild_popup_content(self) -> None:
        previous_content = self._content_widget
        content = QWidget()
        content.setObjectName("languageSelectorContent")
        content_width = self._popup_content_width()
        content.setMinimumWidth(content_width)
        content.setMaximumWidth(content_width)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        title = QLabel(tr("header.language_tooltip"), content)
        title.setObjectName("resourceTitle")
        layout.addWidget(title)

        self._option_buttons = {}
        button_width = self._option_button_width()
        for locale in I18nManager.available_locales():
            button = QPushButton(tr(self._option_label_keys[locale]), content)
            button.setObjectName("languageOptionButton")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            button.setMinimumWidth(button_width)
            button.setMaximumWidth(button_width)
            button.setProperty("selected", locale == I18nManager.current_locale)
            button.clicked.connect(
                lambda checked=False, current=locale: self._select_locale(current)
            )
            layout.addWidget(button, 0, Qt.AlignmentFlag.AlignHCenter)
            self._option_buttons[locale] = button

        self._content_widget = content
        self._apply_popup_style()
        self._popup.set_content_widget(content)
        if previous_content is not None and previous_content is not content:
            previous_content.deleteLater()

    def _select_locale(self, locale: _I18n.Locales) -> None:
        self._popup.hide_immediately()
        if locale == I18nManager.current_locale:
            return
        I18nManager.set_locale(locale)
        Toaster.success(
            tr("toast.language_switched", language=tr(self._option_label_keys[locale])),
            parent=self.window(),
        )
        self.locale_selected.emit(locale.value)

    def _apply_popup_style(self) -> None:
        if self._content_widget is None:
            return
        self._content_widget.setStyleSheet(load_qss(Qss.s_language_selector))

    def _option_button_width(self) -> int:
        button_font = QFont(self.font())
        button_font.setPixelSize(13)
        button_font.setWeight(600)
        metrics = QFontMetrics(button_font)
        padding = 28
        max_width = 0
        for display_locale in I18nManager.available_locales():
            messages = I18n._messages.get(display_locale.value, {})
            for key in self._option_label_keys.values():
                text = str(messages.get(key, key))
                max_width = max(max_width, metrics.horizontalAdvance(text))
        return max(104, max_width + padding)

    def _popup_content_width(self) -> int:
        title_font = QFont(self.font())
        title_font.setPixelSize(16)
        title_font.setBold(True)
        metrics = QFontMetrics(title_font)
        padding = 16
        max_width = self._option_button_width()
        for display_locale in I18nManager.available_locales():
            messages = I18n._messages.get(display_locale.value, {})
            title = str(
                messages.get("header.language_tooltip", "header.language_tooltip")
            )
            max_width = max(max_width, metrics.horizontalAdvance(title) + padding)
        return max_width

    def _on_language_changed(self, _locale: str) -> None:
        self._popup.hide_immediately()
        self._rebuild_popup_content()

    def _dispose_popup(self, _obj: object | None = None) -> None:
        try:
            self._popup.deleteLater()
        except RuntimeError:
            pass


def create_language_selector(
    parent: QWidget | None = None,
    *,
    button_size: int = 36,
    icon_size: int = 18,
    tooltip: str = "",
) -> LanguageSelector:
    return LanguageSelector(
        parent=parent,
        button_size=button_size,
        icon_size=icon_size,
        tooltip=tooltip,
    )
