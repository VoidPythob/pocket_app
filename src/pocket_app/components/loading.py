from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pocket_app.resources import I18nManager, Qss, ThemeManager, load_qss, tr


class LoadingPlaceholder(QFrame):
    retry_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._mode = "loading"
        self._setup_ui()
        ThemeManager.theme_changed.connect(self._apply_style)
        I18nManager.language_changed.connect(self._on_language_changed)
        self.set_loading()

    def _setup_ui(self) -> None:
        self.setObjectName("loadingPlaceholder")
        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(32, 32, 32, 32)
        self.layout_.setSpacing(12)
        self.layout_.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title_label = QLabel(self)
        self.title_label.setObjectName("loadingTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.desc_label = QLabel(self)
        self.desc_label.setObjectName("loadingDesc")
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.desc_label.setWordWrap(True)

        self.progress = QProgressBar(self)
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 0)
        self.progress.setFixedWidth(220)

        self.retry_button = QPushButton(tr("loading.retry"), self)
        self.retry_button.setObjectName("loadingRetryButton")
        self.retry_button.clicked.connect(self.retry_requested.emit)

        self.layout_.addWidget(self.title_label)
        self.layout_.addWidget(self.desc_label)
        self.layout_.addWidget(self.progress, 0, Qt.AlignmentFlag.AlignCenter)
        self.layout_.addWidget(self.retry_button, 0, Qt.AlignmentFlag.AlignCenter)

        self._apply_style()

    def set_loading(
        self,
        title: str | None = None,
        desc: str | None = None,
    ) -> None:
        self._mode = "loading"
        self.title_label.setText(title or tr("loading.title"))
        self.desc_label.setText(desc or tr("loading.desc"))
        self.progress.show()
        self.retry_button.hide()

    def set_error(
        self,
        title: str | None = None,
        desc: str | None = None,
    ) -> None:
        self._mode = "error"
        self.title_label.setText(title or tr("loading.error_title"))
        self.desc_label.setText(desc or tr("loading.error_desc"))
        self.progress.hide()
        self.retry_button.show()

    def _apply_style(self) -> None:
        self.setStyleSheet(load_qss(Qss.s_loading_placeholder))

    def _on_language_changed(self, _locale: str) -> None:
        self.retry_button.setText(tr("loading.retry"))
        if self._mode == "loading":
            self.set_loading()
        elif self._mode == "error":
            self.set_error(desc=self.desc_label.text())
