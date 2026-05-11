import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QLabel, QHBoxLayout, QMainWindow, QVBoxLayout, QWidget

from pocket_app.components import IconButton
from pocket_app.config import init_config
from pocket_app.resources import Icons


class IconButtonDemoWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Icon Button Demo")
        self.resize(480, 240)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        self._status_label = QLabel("Click a button", self)
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        primary_button = IconButton(
            Icons.fold_chevron,
            tooltip="Toggle section",
            parent=self,
            button_size=40,
            icon_size=18,
        )
        primary_button.clicked.connect(
            lambda: self._status_label.setText("Primary icon button clicked")
        )

        secondary_button = IconButton(
            Icons.navigation_item,
            tooltip="Open navigation item",
            parent=self,
            button_size=48,
            icon_size=20,
        )
        secondary_button.clicked.connect(
            lambda: self._status_label.setText("Secondary icon button clicked")
        )

        button_row = QHBoxLayout()
        button_row.setSpacing(16)
        button_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_row.addWidget(primary_button)
        button_row.addWidget(secondary_button)

        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.addStretch(1)
        layout.addLayout(button_row)
        layout.addWidget(self._status_label)
        layout.addStretch(1)


if __name__ == "__main__":
    init_config()
    app = QApplication(sys.argv)
    window = IconButtonDemoWindow()
    window.show()
    sys.exit(app.exec())
