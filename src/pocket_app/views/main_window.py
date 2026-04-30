from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from pocket_app.components import SideNavigation, SideNavigationItemModel

NAVIGATION_CONFIG = [
    {
        "id_": 1,
        "name": "pokemon",
        "tip": "宝可梦图鉴",
        "children": [
            {
                "id_": 11,
                "name": "pokemon_all",
                "tip": "全部图鉴",
                "children": [],
            },
            {
                "id_": 12,
                "name": "pokemon_favorites",
                "tip": "收藏列表",
                "children": [],
            },
        ],
    },
]

CONTENT_CONFIG = {
    "dashboard": {
        "title": "概览",
        "description": "这里适合展示首页摘要、最近访问和全局数据入口。",
    },
    "pokemon_all": {
        "title": "全部图鉴",
        "description": "这里可以接入完整的宝可梦列表、搜索和筛选。",
    },
    "pokemon_favorites": {
        "title": "收藏列表",
        "description": "这里可以展示用户收藏的图鉴条目或常用筛选。",
    },
    "team_builder": {
        "title": "队伍构建",
        "description": "这里可以扩展成六只宝可梦的编队编辑区。",
    },
    "team_analysis": {
        "title": "属性分析",
        "description": "这里可以展示队伍弱点、抗性和属性覆盖情况。",
    },
}

DEFAULT_PAGE = "dashboard"


def build_navigation_models(items: list[dict]) -> list[SideNavigationItemModel]:
    return [
        SideNavigationItemModel(
            id_=item["id_"],
            name=item["name"],
            tip=item["tip"],
            icon=item.get("icon", ""),
            children=build_navigation_models(item.get("children", [])),
        )
        for item in items
    ]


class MainWindowCentralWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.side_navigation = SideNavigation(self)
        self.title_label = QLabel(self)
        self.description_label = QLabel(self)
        self._setup_ui()
        self._load_navigation()
        self._show_page(DEFAULT_PAGE)

    def _setup_ui(self) -> None:
        self.side_navigation.setMinimumWidth(200)
        self.side_navigation.selected.connect(self._show_page)

        self.title_label.setStyleSheet(
            "font-size: 28px; font-weight: 700; color: #17304c;"
        )
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("font-size: 14px; color: #52657c;")

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(12)
        self.main_layout.addWidget(self.title_label)
        self.main_layout.addWidget(self.description_label)
        self.main_layout.addStretch(1)

        content_widget = QWidget(self)
        content_widget.setLayout(self.main_layout)

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.addWidget(self.side_navigation)
        self.main_layout.addWidget(content_widget, stretch=1)

    def _load_navigation(self) -> None:
        for item in build_navigation_models(NAVIGATION_CONFIG):
            self.side_navigation.add_item(item)

    def _show_page(self, page_name: str) -> None:
        page = CONTENT_CONFIG.get(
            page_name,
            {
                "title": page_name,
                "description": "这个页面还没有配置说明内容。",
            },
        )
        self.title_label.setText(page["title"])
        self.description_label.setText(page["description"])


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("宝可梦app")
        self.setCentralWidget(MainWindowCentralWidget())
        self.resize(900, 640)
