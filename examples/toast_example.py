import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pocket_app.components import Toaster
from pocket_app.config import init_config


class ToastDemoWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Toast Demo")
        self.resize(800, 500)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.addStretch(1)

        button_row = QHBoxLayout()
        layout.addLayout(button_row)

        info_button = QPushButton("Info", self)
        info_button.clicked.connect(
            lambda: Toaster.info("This is an info toast", parent=self)
        )
        button_row.addWidget(info_button)

        warn_button = QPushButton("Warn", self)
        warn_button.clicked.connect(
            lambda: Toaster.warn("This is a warning toast", parent=self)
        )
        button_row.addWidget(warn_button)

        success_button = QPushButton("Success", self)
        success_button.clicked.connect(
            lambda: Toaster.success("This is a success toast", parent=self)
        )
        button_row.addWidget(success_button)

        error_button = QPushButton("Error", self)
        error_button.clicked.connect(
            lambda: Toaster.error("This is an error toast", parent=self)
        )
        button_row.addWidget(error_button)

        QTimer.singleShot(200, lambda: Toaster.success("first success toast", self))
        QTimer.singleShot(500, lambda: Toaster.warn("second warning toast", self))
        QTimer.singleShot(800, lambda: Toaster.error("third error toast", self))
        QTimer.singleShot(1100, lambda: Toaster.info("fourth info toast", self))


if __name__ == "__main__":
    init_config()
    app = QApplication(sys.argv)
    window = ToastDemoWindow()
    window.show()
    sys.exit(app.exec())
