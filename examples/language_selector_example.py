import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget

from pocket_app.components import LanguageSelector
from pocket_app.config import init_config
from pocket_app.resources import I18nManager, tr


class LanguageSelectorDemoWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Language Selector Demo")
        self.resize(420, 220)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        self._status_label = QLabel(self)
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._selector = LanguageSelector(
            parent=self,
            tooltip=tr("header.language_tooltip"),
        )
        self._selector.locale_selected.connect(self._on_locale_selected)
        I18nManager.language_changed.connect(self._sync_text)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        layout.addStretch(1)
        layout.addWidget(self._selector, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status_label)
        layout.addStretch(1)

        self._sync_text(I18nManager.current_locale.value)

    def _on_locale_selected(self, locale: str) -> None:
        self._status_label.setText(f"Locale selected: {locale}")

    def _sync_text(self, locale: str) -> None:
        self._selector.set_tooltip(tr("header.language_tooltip"))
        self._status_label.setText(f"Current locale: {locale}")


if __name__ == "__main__":
    init_config()
    app = QApplication(sys.argv)
    window = LanguageSelectorDemoWindow()
    window.show()
    sys.exit(app.exec())
