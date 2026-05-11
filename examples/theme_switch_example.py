import sys

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from pocket_app.components import IconButton, SearchBar, SideNavigation, SideNavigationItemModel, Tag, Toaster
from pocket_app.config import init_config
from pocket_app.resources import Icons, Qss, ThemeManager


class ThemeSwitchDemoWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Theme Switch Demo")
        self.resize(1040, 680)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        self._opacity_effect = QGraphicsOpacityEffect(central_widget)
        self._opacity_effect.setOpacity(1.0)
        central_widget.setGraphicsEffect(self._opacity_effect)
        self._theme_anim = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        self._theme_anim.setDuration(220)
        self._theme_anim.setStartValue(0.76)
        self._theme_anim.setEndValue(1.0)
        self._theme_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._title_label = QLabel("Pokemon Theme Demo", self)
        self._subtitle_label = QLabel(
            "Use the icon button on the top right to switch between light and dark QSS themes.",
            self,
        )
        self._subtitle_label.setWordWrap(True)

        self._theme_button = IconButton(
            Icons.theme_toggle,
            tooltip="Switch to dark theme",
            parent=self,
            button_size=36,
            icon_size=18,
        )
        self._theme_button.clicked.connect(self._toggle_theme)

        self._search_bar = SearchBar(
            placeholder="Search Pokemon, moves, abilities...",
            tooltip="Search demo content",
            parent=self,
            height=40,
        )
        self._search_bar.search_requested.connect(
            lambda text: Toaster.info(f"Searching: {text or 'all'}", parent=self)
        )

        self._navigation = SideNavigation(self)
        self._navigation.setMinimumWidth(240)
        for item in self._build_navigation_items():
            self._navigation.add_item(item)
        self._navigation.selected.connect(self._on_nav_selected)

        self._info_label = QLabel("Select a navigation item or click a tag.", self)
        self._info_label.setWordWrap(True)

        self._tags = [
            Tag("Water", background_color="#dcefff", tooltip="Water", parent=self, tag_id="water"),
            Tag("Fire", background_color="#ffe6dc", tooltip="Fire", parent=self, tag_id="fire"),
            Tag("Grass", background_color="#e4f4e4", tooltip="Grass", parent=self, tag_id="grass"),
            Tag("Electric", background_color="#fff2c9", tooltip="Electric", parent=self, tag_id="electric"),
        ]
        for tag in self._tags:
            tag.tag_clicked.connect(self._on_tag_clicked)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._navigation)

        content_widget = QWidget(self)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(28, 24, 28, 24)
        content_layout.setSpacing(18)

        header_row = QHBoxLayout()
        header_row.setSpacing(12)
        title_col = QVBoxLayout()
        title_col.setSpacing(6)
        title_col.addWidget(self._title_label)
        title_col.addWidget(self._subtitle_label)
        header_row.addLayout(title_col, 1)
        header_row.addWidget(self._theme_button, 0, Qt.AlignmentFlag.AlignTop)

        tag_row = QHBoxLayout()
        tag_row.setSpacing(10)
        for tag in self._tags:
            tag_row.addWidget(tag)
        tag_row.addStretch(1)

        content_layout.addLayout(header_row)
        content_layout.addWidget(self._search_bar)
        content_layout.addLayout(tag_row)
        content_layout.addWidget(self._info_label)
        content_layout.addStretch(1)

        root_layout.addWidget(content_widget, 1)

        ThemeManager.theme_changed.connect(self._on_theme_changed)
        self._apply_theme()

    def _build_navigation_items(self) -> list[SideNavigationItemModel]:
        return [
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
                        name="favorites",
                        tip="Favorites",
                        icon=Icons.navigation_item,
                    ),
                ],
            ),
            SideNavigationItemModel(
                id_=2,
                name="team_builder",
                tip="Team Builder",
                icon=Icons.navigation_item,
            ),
            SideNavigationItemModel(
                id_=3,
                name="battle_notes",
                tip="Battle Notes",
                icon=Icons.navigation_item,
            ),
        ]

    def _apply_theme(self) -> None:
        if ThemeManager.current_theme == Qss.Themes.DARK:
            self.setStyleSheet(
                """
                QMainWindow, QWidget {
                    background: #10161f;
                    color: #e7edf6;
                }
                QLabel {
                    color: #e7edf6;
                }
                """
            )
            self._title_label.setStyleSheet(
                "font-size: 28px; font-weight: 800; color: #f2f6ff;"
            )
            self._subtitle_label.setStyleSheet(
                "font-size: 14px; color: #9eacbe;"
            )
            self._info_label.setStyleSheet(
                "font-size: 15px; color: #bac7d7;"
            )
            self._theme_button.set_tooltip("Switch to light theme")
        else:
            self.setStyleSheet(
                """
                QMainWindow, QWidget {
                    background: #f7f9fc;
                    color: #23354a;
                }
                QLabel {
                    color: #23354a;
                }
                """
            )
            self._title_label.setStyleSheet(
                "font-size: 28px; font-weight: 800; color: #16324e;"
            )
            self._subtitle_label.setStyleSheet(
                "font-size: 14px; color: #5d7189;"
            )
            self._info_label.setStyleSheet(
                "font-size: 15px; color: #52657c;"
            )
            self._theme_button.set_tooltip("Switch to dark theme")

    def _toggle_theme(self) -> None:
        theme = ThemeManager.toggle_theme()
        self._play_theme_transition()
        Toaster.success(f"Switched to {theme.value} theme", parent=self)

    def _play_theme_transition(self) -> None:
        self._theme_anim.stop()
        self._opacity_effect.setOpacity(0.76)
        self._theme_anim.start()

    def _on_theme_changed(self, _theme: str) -> None:
        self._apply_theme()

    def _on_nav_selected(self, name: str) -> None:
        self._info_label.setText(f"Navigation selected: {name}")

    def _on_tag_clicked(self, tag_id: str) -> None:
        self._info_label.setText(f"Tag clicked: {tag_id}")


if __name__ == "__main__":
    init_config()
    app = QApplication(sys.argv)
    window = ThemeSwitchDemoWindow()
    window.show()
    sys.exit(app.exec())
