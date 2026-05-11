import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pocket_app.components import PopupPanel, Tag, create_popup_panel
from pocket_app.config import init_config


class PopupPanelDemoWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Popup Panel Demo")
        self.resize(860, 520)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        self._title_label = QLabel("Popup Panel Example", self)
        self._title_label.setStyleSheet("font-size: 26px; font-weight: 700;")
        self._desc_label = QLabel(
            "Click a button to open the small popup panel. It is rendered inside the current main window, follows the anchor, and keeps the show and hide animation.",
            self,
        )
        self._desc_label.setWordWrap(True)

        self._default_button = QPushButton("Open Default Popup", self)
        self._wide_button = QPushButton("Open Width Matched Popup", self)
        self._status_label = QLabel("Status: waiting for interaction", self)

        self._default_popup = PopupPanel(offset_y=10)
        self._default_popup.set_content_widget(self._build_default_content())
        self._default_popup.bind_toggle(self._default_button)
        self._default_popup.opened.connect(
            lambda: self._status_label.setText("Status: default popup opened")
        )
        self._default_popup.closed.connect(
            lambda: self._status_label.setText("Status: default popup closed")
        )

        self._wide_popup = create_popup_panel(
            self._build_wide_content(),
            offset_y=10,
            match_anchor_width=True,
        )
        self._wide_button.clicked.connect(
            lambda: self._wide_popup.toggle_for(self._wide_button)
        )

        button_row = QHBoxLayout()
        button_row.setSpacing(12)
        button_row.addWidget(self._default_button, 0, Qt.AlignmentFlag.AlignLeft)
        button_row.addWidget(self._wide_button, 0, Qt.AlignmentFlag.AlignLeft)
        button_row.addStretch(1)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)
        layout.addWidget(self._title_label)
        layout.addWidget(self._desc_label)
        layout.addLayout(button_row)
        layout.addWidget(self._status_label)
        layout.addStretch(1)

    def _build_default_content(self) -> QWidget:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        title = QLabel("Pokemon Quick Actions", content)
        title.setObjectName("popupTitle")
        desc = QLabel("This popup is anchored below the button, fades and slides in, then closes with the reverse animation when you click outside.", content)
        desc.setObjectName("popupDescription")
        desc.setWordWrap(True)

        tag_row = QHBoxLayout()
        tag_row.setSpacing(8)
        for name, color in (
            ("Water", "#dcefff"),
            ("Fire", "#ffe6dc"),
            ("Grass", "#e4f4e4"),
        ):
            tag_row.addWidget(Tag(name, parent=content, background_color=color))
        tag_row.addStretch(1)

        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addLayout(tag_row)
        return content

    def _build_wide_content(self) -> QWidget:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        title = QLabel("Matched Width Popup", content)
        title.setObjectName("popupTitle")
        line1 = QLabel("This one keeps at least the same width as the trigger button.", content)
        line1.setObjectName("popupDescription")
        line1.setWordWrap(True)
        line2 = QLabel("You can also create the panel through create_popup_panel().", content)
        line2.setObjectName("popupDescription")
        line2.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(line1)
        layout.addWidget(line2)
        return content


if __name__ == "__main__":
    init_config()
    app = QApplication(sys.argv)
    window = PopupPanelDemoWindow()
    window.show()
    sys.exit(app.exec())
