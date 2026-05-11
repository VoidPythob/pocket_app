import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget

from pocket_app.components import StatRadar
from pocket_app.config import init_config


EXAMPLE_RANCE = {
    "id": 1,
    "name": "Pikachu",
    "hp": 35,
    "attack": 55,
    "defense": 40,
    "special_attack": 50,
    "special_defense": 50,
    "speed": 90,
    "total": 320,
}


class StatRadarDemoWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Stat Radar Demo")
        self.resize(720, 620)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        title = QLabel("Reusable StatRadar Component", self)
        title.setStyleSheet("font-size: 26px; font-weight: 700;")
        desc = QLabel(
            "This example shows the animated polygon chart used for pet race stats.",
            self,
        )
        desc.setWordWrap(True)

        radar = StatRadar(parent=central_widget, center_text_mode="none")
        radar.set_stats(EXAMPLE_RANCE)

        total_label = QLabel(f"TOTAL: {radar.total() or '-'}", self)
        total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        total_label.setStyleSheet("font-size: 20px; font-weight: 700;")

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)
        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addWidget(radar)
        layout.addWidget(total_label, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch(1)


if __name__ == "__main__":
    init_config()
    app = QApplication(sys.argv)
    window = StatRadarDemoWindow()
    window.show()
    sys.exit(app.exec())
