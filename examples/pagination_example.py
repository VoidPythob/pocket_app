import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget

from pocket_app.components import PaginationBar
from pocket_app.config import init_config


class PaginationDemoWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Pagination Demo")
        self.resize(560, 220)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        self._status_label = QLabel("Current page: 3", self)
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._pagination = PaginationBar(
            parent=self,
            current_page=3,
            total_pages=18,
            max_visible=7,
        )
        self._pagination.page_changed.connect(self._on_page_changed)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)
        layout.addStretch(1)
        layout.addWidget(self._pagination, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status_label)
        layout.addStretch(1)

    def _on_page_changed(self, page: int) -> None:
        self._status_label.setText(f"Current page: {page}")


if __name__ == "__main__":
    init_config()
    app = QApplication(sys.argv)
    window = PaginationDemoWindow()
    window.show()
    sys.exit(app.exec())
