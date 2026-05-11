import sys

from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from pocket_app.components import SideNavigation, SideNavigationItemModel
from pocket_app.config import init_config
from pocket_app.resources import Icons


def build_example_items() -> list[SideNavigationItemModel]:
    items: list[SideNavigationItemModel] = [
        SideNavigationItemModel(
            id_=1,
            name="pokedex",
            tip="Pokedex",
            icon=Icons.navigation_item,
            children=[
                SideNavigationItemModel(
                    id_=11,
                    name="pokemon_all",
                    tip="All Pokemon",
                    icon=Icons.navigation_item,
                ),
                SideNavigationItemModel(
                    id_=12,
                    name="pokemon_favorites",
                    tip="Favorites",
                    icon=Icons.navigation_item,
                ),
            ],
        )
    ]

    generations = [
        "Generation I",
        "Generation II",
        "Generation III",
        "Generation IV",
        "Generation V",
        "Generation VI",
        "Generation VII",
        "Generation VIII",
        "Generation IX",
    ]
    sections = [
        "Overview",
        "Pokemon List",
        "Moves",
        "Abilities",
        "Items",
        "Locations",
    ]

    for gen_index, generation in enumerate(generations, start=2):
        items.append(
            SideNavigationItemModel(
                id_=gen_index,
                name=f"gen_{gen_index}",
                tip=generation,
                icon=Icons.navigation_item,
                children=[
                    SideNavigationItemModel(
                        id_=gen_index * 100 + section_index,
                        name=f"{generation.lower().replace(' ', '_')}_{section_index}",
                        tip=section,
                        icon=Icons.navigation_item,
                    )
                    for section_index, section in enumerate(sections, start=1)
                ],
            )
        )

    return items


class SideNavigationDemoWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Side Navigation Demo")
        self.resize(760, 420)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        self._navigation = SideNavigation(self)
        self._navigation.setMinimumWidth(220)
        self._title_label = QLabel("Select a navigation item", self)
        self._description_label = QLabel(
            "This example intentionally contains many navigation items so the left panel will overflow and show a vertical scrollbar.",
            self,
        )
        self._description_label.setWordWrap(True)

        self._navigation.selected.connect(self._show_page)
        for item in build_example_items():
            self._navigation.add_item(item)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(12)
        content_layout.addWidget(self._title_label)
        content_layout.addWidget(self._description_label)
        content_layout.addStretch(1)

        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._navigation)

        content_widget = QWidget(self)
        content_widget.setLayout(content_layout)
        layout.addWidget(content_widget, stretch=1)

    def _show_page(self, page_name: str) -> None:
        self._title_label.setText(page_name)
        self._description_label.setText(f"Current page: {page_name}")


if __name__ == "__main__":
    init_config()
    app = QApplication(sys.argv)
    window = SideNavigationDemoWindow()
    window.show()
    sys.exit(app.exec())
