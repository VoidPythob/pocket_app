import sys

from PyQt6.QtWidgets import QApplication, QGridLayout, QLabel, QMainWindow, QVBoxLayout, QWidget

from pocket_app.components import PetCard
from pocket_app.config import init_config


EXAMPLE_PETS = [
    {
        "id": 1,
        "name": "Bulbasaur",
        "jp_name": "Fushigidane",
        "en_name": "Bulbasaur",
        "first_image_url": "",
        "tags": [{"name": "Grass", "color": "#dff3df"}, {"name": "Poison", "color": "#efe3ff"}],
        "features": [{"name": "Overgrow"}, {"name": "Chlorophyll"}],
    },
    {
        "id": 4,
        "name": "Charmander",
        "jp_name": "Hitokage",
        "en_name": "Charmander",
        "first_image_url": "",
        "tags": [{"name": "Fire", "color": "#ffe6dc"}],
        "features": [{"name": "Blaze"}],
    },
    {
        "id": 7,
        "name": "Squirtle",
        "jp_name": "Zenigame",
        "en_name": "Squirtle",
        "first_image_url": "",
        "tags": [{"name": "Water", "color": "#dcefff"}],
        "features": [{"name": "Torrent"}],
    },
]


class PetCardDemoWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Pet Card Demo")
        self.resize(980, 620)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        title = QLabel("Reusable PetCard Component", self)
        title.setStyleSheet("font-size: 26px; font-weight: 700;")
        desc = QLabel(
            "This example shows the shared card used by the pets list and egg group pet list.",
            self,
        )
        desc.setWordWrap(True)

        self._status = QLabel("Click a card to emit its pet id.", self)

        grid_host = QWidget(self)
        grid = QGridLayout(grid_host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)

        for index, pet in enumerate(EXAMPLE_PETS):
            card = PetCard(pet, parent=grid_host, image_size=40, clickable=True)
            card.clicked.connect(self._on_card_clicked)
            grid.addWidget(card, index // 3, index % 3)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)
        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addWidget(self._status)
        layout.addWidget(grid_host)
        layout.addStretch(1)

    def _on_card_clicked(self, pet_id) -> None:
        self._status.setText(f"Clicked pet id: {pet_id}")


if __name__ == "__main__":
    init_config()
    app = QApplication(sys.argv)
    window = PetCardDemoWindow()
    window.show()
    sys.exit(app.exec())
