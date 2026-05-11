import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QHBoxLayout,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from pocket_app.components import Tag
from pocket_app.config import init_config


class TagDemoWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Tag Demo")
        self.resize(640, 320)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        self._status_label = QLabel("Click a tag", self)
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        default_title = QLabel("Default Tags", self)
        custom_title = QLabel("Custom Background Tags", self)

        default_tags = [
            Tag("Water", tooltip="Water tag", parent=self, tag_id="water"),
            Tag("Electric", tooltip="Electric tag", parent=self, tag_id="electric"),
            Tag("Legendary", tooltip="Legendary tag", parent=self, height=32, tag_id="legendary"),
        ]
        default_tags[2].set_selected(True)

        custom_tags = [
            Tag(
                "Fire",
                tooltip="Fire tag",
                parent=self,
                background_color="#ffefe5",
                tag_id="fire",
            ),
            Tag(
                "Grass",
                tooltip="Grass tag",
                parent=self,
                background_color="#e8f7e8",
                tag_id="grass",
            ),
            Tag(
                "Ice",
                tooltip="Ice tag",
                parent=self,
                height=32,
                background_color="#e7f6ff",
                tag_id="ice",
            ),
        ]

        for tag in [*default_tags, *custom_tags]:
            tag.tag_clicked.connect(self._on_tag_clicked)

        default_row = QHBoxLayout()
        default_row.setSpacing(12)
        default_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for tag in default_tags:
            default_row.addWidget(tag)

        custom_row = QHBoxLayout()
        custom_row.setSpacing(12)
        custom_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for tag in custom_tags:
            custom_row.addWidget(tag)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        layout.addWidget(default_title)
        layout.addLayout(default_row)
        layout.addWidget(custom_title)
        layout.addLayout(custom_row)
        layout.addWidget(self._status_label)
        layout.addStretch(1)

    def _on_tag_clicked(self, tag_id: str) -> None:
        self._status_label.setText(f"Selected tag id: {tag_id}")


if __name__ == "__main__":
    init_config()
    app = QApplication(sys.argv)
    window = TagDemoWindow()
    window.show()
    sys.exit(app.exec())
