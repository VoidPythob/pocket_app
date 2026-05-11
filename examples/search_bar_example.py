import sys

from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget

from pocket_app.components import SearchBar
from pocket_app.config import init_config


class SearchBarDemoWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Search Bar Demo")
        self.resize(540, 220)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        self._status_label = QLabel("Press Enter to search", self)
        self._search_bar = SearchBar(
            placeholder="Search Pokemon, moves, abilities...",
            tooltip="Type keywords and press Enter, or click the search button",
            parent=self,
            height=40,
        )
        self._search_bar.text_changed.connect(
            lambda text: self._status_label.setText(f"Typing: {text or '(empty)'}")
        )
        self._search_bar.search_requested.connect(
            lambda text: self._status_label.setText(f"Search requested: {text}")
        )

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        layout.addWidget(self._search_bar)
        layout.addWidget(self._status_label)
        layout.addStretch(1)


if __name__ == "__main__":
    init_config()
    app = QApplication(sys.argv)
    window = SearchBarDemoWindow()
    window.show()
    sys.exit(app.exec())
