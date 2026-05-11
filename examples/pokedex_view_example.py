import sys

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from pocket_app.components import (
    IconButton,
    SearchBar,
    SideNavigation,
    SideNavigationItemModel,
    Tag,
    Toaster,
)
from pocket_app.config import init_config
from pocket_app.resources import Icons, Qss, ThemeManager

TYPE_COLORS = {
    "Normal": "#d9d9d9",
    "Fire": "#ef7e63",
    "Water": "#6eaed8",
    "Grass": "#65b98c",
    "Electric": "#f6c064",
    "Ice": "#8fd7ea",
    "Fighting": "#cc7f6b",
    "Poison": "#9b70d8",
    "Ground": "#c8a472",
    "Flying": "#8dc8f1",
    "Psychic": "#f59cc8",
    "Bug": "#8ea85a",
    "Rock": "#a48b76",
    "Ghost": "#6f637f",
    "Dragon": "#5b81e3",
    "Dark": "#5e5e5e",
    "Steel": "#8592a1",
    "Fairy": "#e8b4c5",
}

TYPE_LABELS = {
    "en": {
        "Normal": "Normal",
        "Fire": "Fire",
        "Water": "Water",
        "Grass": "Grass",
        "Electric": "Electric",
        "Ice": "Ice",
        "Fighting": "Fight",
        "Poison": "Poison",
        "Ground": "Ground",
        "Flying": "Flying",
        "Psychic": "Psychic",
        "Bug": "Bug",
        "Rock": "Rock",
        "Ghost": "Ghost",
        "Dragon": "Dragon",
        "Dark": "Dark",
        "Steel": "Steel",
        "Fairy": "Fairy",
    },
    "zh": {
        "Normal": "一般",
        "Fire": "火",
        "Water": "水",
        "Grass": "草",
        "Electric": "电",
        "Ice": "冰",
        "Fighting": "格斗",
        "Poison": "毒",
        "Ground": "地面",
        "Flying": "飞行",
        "Psychic": "超能力",
        "Bug": "虫",
        "Rock": "岩石",
        "Ghost": "幽灵",
        "Dragon": "龙",
        "Dark": "恶",
        "Steel": "钢",
        "Fairy": "妖精",
    },
}

UI_TEXTS = {
    "en": {
        "window_title": "Pokemon Encyclopedia",
        "header_title": "Pokemon Encyclopedia",
        "search_placeholder": "Search by number, name, alias, or type",
        "search_tooltip": "Enter keywords and press Enter or click the search icon",
        "theme_tooltip_light": "Switch to dark theme",
        "theme_tooltip_dark": "Switch to light theme",
        "lang_tooltip_en": "Switch to Chinese",
        "lang_tooltip_zh": "Switch to English",
        "directory": "Directory",
        "intro_title": "Pokemon List",
        "intro_1": "This page uses the current component set to build a clean encyclopedia view with card-based presentation.",
        "intro_2": "Use the left navigation to switch generations, search the list from the header, and click type tags to filter cards.",
        "filter_title": "Filter By Type",
        "reset": "Reset",
        "result_empty_filter": "No extra filters enabled.",
        "result_count": "{count} result(s). {filters}",
        "search_filter": "Search: {value}",
        "type_filter": "Type: {value}",
        "meta_generation": "Generation {value}",
        "meta_type_count": "Type Count: {value}",
        "tag_clicked": "Tag clicked: {value}",
        "nav_selected": "Navigation selected: {value}",
        "theme_toast": "Switched to {value} theme",
        "lang_toast": "Language switched to {value}",
        "lang_name": "English",
    },
    "zh": {
        "window_title": "神奇宝贝百科",
        "header_title": "神奇宝贝百科",
        "search_placeholder": "按编号、名称、别名或属性搜索",
        "search_tooltip": "输入关键词后按回车或点击搜索图标",
        "theme_tooltip_light": "切换到深色主题",
        "theme_tooltip_dark": "切换到浅色主题",
        "lang_tooltip_en": "切换到中文",
        "lang_tooltip_zh": "切换到英文",
        "directory": "目录",
        "intro_title": "宝可梦列表",
        "intro_1": "这个示例使用当前组件库构建了一个卡片式百科页面，用更直观的方式展示宝可梦条目。",
        "intro_2": "可以通过左侧目录切换世代，使用顶部搜索框筛选内容，也可以点击属性标签过滤卡片。",
        "filter_title": "按属性筛选",
        "reset": "重置",
        "result_empty_filter": "当前未启用额外筛选条件。",
        "result_count": "共 {count} 条结果。{filters}",
        "search_filter": "搜索：{value}",
        "type_filter": "属性：{value}",
        "meta_generation": "第 {value} 世代",
        "meta_type_count": "属性数量：{value}",
        "tag_clicked": "点击了属性标签：{value}",
        "nav_selected": "当前目录：{value}",
        "theme_toast": "已切换到 {value} 主题",
        "lang_toast": "语言已切换为 {value}",
        "lang_name": "中文",
    },
}

NAV_ITEMS = [
    ("all", {"en": "(Top)", "zh": "(顶部)"}),
    ("gen1", {"en": "Generation I", "zh": "第一世代"}),
    ("gen2", {"en": "Generation II", "zh": "第二世代"}),
    ("gen3", {"en": "Generation III", "zh": "第三世代"}),
    ("gen4", {"en": "Generation IV", "zh": "第四世代"}),
    ("gen5", {"en": "Generation V", "zh": "第五世代"}),
    ("gen6", {"en": "Generation VI", "zh": "第六世代"}),
    ("gen7", {"en": "Generation VII", "zh": "第七世代"}),
]

POKEMON_DATA = [
    {
        "no": "#0001",
        "en": "Bulbasaur",
        "zh": "妙蛙种子",
        "jp": "Fushigidane",
        "types": ["Grass", "Poison"],
        "gen": 1,
        "desc_en": "A calm seed Pokemon with a plant bulb on its back.",
        "desc_zh": "背上长着种子的草系宝可梦，性情安静温和。",
    },
    {
        "no": "#0002",
        "en": "Ivysaur",
        "zh": "妙蛙草",
        "jp": "Fushigisou",
        "types": ["Grass", "Poison"],
        "gen": 1,
        "desc_en": "The bulb grows heavier as it stores more sunlight energy.",
        "desc_zh": "随着吸收的阳光增多，背上的花苞也会逐渐变重。",
    },
    {
        "no": "#0003",
        "en": "Venusaur",
        "zh": "妙蛙花",
        "jp": "Fushigibana",
        "types": ["Grass", "Poison"],
        "gen": 1,
        "desc_en": "Its giant flower is said to gain vivid color from nutrition.",
        "desc_zh": "巨大的花朵会在吸收充分营养后绽放出鲜艳色彩。",
    },
    {
        "no": "#0004",
        "en": "Charmander",
        "zh": "小火龙",
        "jp": "Hitokage",
        "types": ["Fire"],
        "gen": 1,
        "desc_en": "The flame on its tail reflects its life force and emotions.",
        "desc_zh": "尾巴上的火焰会随着情绪和体力变化而摇曳。",
    },
    {
        "no": "#0005",
        "en": "Charmeleon",
        "zh": "火恐龙",
        "jp": "Lizardo",
        "types": ["Fire"],
        "gen": 1,
        "desc_en": "Known for its fierce temper and close-range fire attacks.",
        "desc_zh": "脾气暴躁，擅长在近距离发动猛烈火焰攻击。",
    },
    {
        "no": "#0006",
        "en": "Charizard",
        "zh": "喷火龙",
        "jp": "Lizardon",
        "types": ["Fire", "Flying"],
        "gen": 1,
        "desc_en": "A proud flying dragon-like Pokemon with blazing breath.",
        "desc_zh": "拥有飞行能力的强大火焰宝可梦，吐息炽热无比。",
    },
    {
        "no": "#0007",
        "en": "Squirtle",
        "zh": "杰尼龟",
        "jp": "Zenigame",
        "types": ["Water"],
        "gen": 1,
        "desc_en": "Its rounded shell offers both defense and streamlined speed.",
        "desc_zh": "圆润的龟壳既能防御，也能帮助它在水中快速移动。",
    },
    {
        "no": "#0008",
        "en": "Wartortle",
        "zh": "卡咪龟",
        "jp": "Kameil",
        "types": ["Water"],
        "gen": 1,
        "desc_en": "Its fluffy tail is a symbol of longevity and good luck.",
        "desc_zh": "蓬松的尾巴在传说中象征着长寿与好运。",
    },
    {
        "no": "#0025",
        "en": "Pikachu",
        "zh": "皮卡丘",
        "jp": "Pikachu",
        "types": ["Electric"],
        "gen": 1,
        "desc_en": "Stores electricity in its cheeks and releases it in bursts.",
        "desc_zh": "会把电能储存在脸颊中，需要时迅速释放出来。",
    },
    {
        "no": "#0133",
        "en": "Eevee",
        "zh": "伊布",
        "jp": "Eievui",
        "types": ["Normal"],
        "gen": 1,
        "desc_en": "Its unstable genes allow it to evolve into many forms.",
        "desc_zh": "基因极不稳定，因此拥有多种进化可能。",
    },
    {
        "no": "#0152",
        "en": "Chikorita",
        "zh": "菊草叶",
        "jp": "Chicorita",
        "types": ["Grass"],
        "gen": 2,
        "desc_en": "A gentle Pokemon that waves its leaf to detect warm places.",
        "desc_zh": "会摇动头上的叶片，感知附近温暖而舒适的地点。",
    },
    {
        "no": "#0155",
        "en": "Cyndaquil",
        "zh": "火球鼠",
        "jp": "Hinoarashi",
        "types": ["Fire"],
        "gen": 2,
        "desc_en": "It protects itself by flaring up the fire on its back.",
        "desc_zh": "遇到危险时会点燃背部火焰来保护自己。",
    },
    {
        "no": "#0158",
        "en": "Totodile",
        "zh": "小锯鳄",
        "jp": "Waninoko",
        "types": ["Water"],
        "gen": 2,
        "desc_en": "Small but energetic, it bites anything that moves nearby.",
        "desc_zh": "虽然体型不大，却精力十足，见到东西就想咬一口。",
    },
    {
        "no": "#0246",
        "en": "Larvitar",
        "zh": "幼基拉斯",
        "jp": "Yogiras",
        "types": ["Rock", "Ground"],
        "gen": 2,
        "desc_en": "Born underground, it comes to the surface after eating soil.",
        "desc_zh": "出生于地下，吃饱大量泥土后才会来到地表。",
    },
    {
        "no": "#0387",
        "en": "Turtwig",
        "zh": "草苗龟",
        "jp": "Naetle",
        "types": ["Grass"],
        "gen": 4,
        "desc_en": "The twig on its head draws energy and helps it grow strong.",
        "desc_zh": "头上的嫩枝会吸收能量，帮助它健康成长。",
    },
    {
        "no": "#0390",
        "en": "Chimchar",
        "zh": "小火焰猴",
        "jp": "Hikozaru",
        "types": ["Fire"],
        "gen": 4,
        "desc_en": "A nimble fire monkey whose rear flame never goes out.",
        "desc_zh": "动作敏捷，尾部火焰终年不熄。",
    },
    {
        "no": "#0393",
        "en": "Piplup",
        "zh": "波加曼",
        "jp": "Pochama",
        "types": ["Water"],
        "gen": 4,
        "desc_en": "A proud penguin Pokemon that dislikes accepting food from people.",
        "desc_zh": "性格高傲，不太愿意接受别人递来的食物。",
    },
    {
        "no": "#0448",
        "en": "Lucario",
        "zh": "路卡利欧",
        "jp": "Lucario",
        "types": ["Fighting", "Steel"],
        "gen": 4,
        "desc_en": "It reads aura to sense thoughts and locate distant targets.",
        "desc_zh": "可以通过波导感知他人的想法，并锁定远方目标。",
    },
]


class PokedexDemoWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._locale = "zh"
        self._selected_type = ""
        self._selected_generation = "all"
        self._type_tags: dict[str, Tag] = {}
        self._nav_widgets: dict[str, QWidget] = {}
        self._card_widgets: list[QFrame] = []

        self.resize(1580, 960)

        central = QWidget(self)
        self.setCentralWidget(central)
        self._opacity_effect = QGraphicsOpacityEffect(central)
        self._opacity_effect.setOpacity(1.0)
        central.setGraphicsEffect(self._opacity_effect)
        self._theme_anim = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        self._theme_anim.setDuration(220)
        self._theme_anim.setStartValue(0.78)
        self._theme_anim.setEndValue(1.0)
        self._theme_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self._build_header())
        root_layout.addWidget(self._build_body(), 1)

        ThemeManager.theme_changed.connect(self._on_theme_changed)
        self._apply_window_style()
        self._apply_locale()
        self._refresh_cards()

    def _build_header(self) -> QFrame:
        header = QFrame(self)
        header.setObjectName("headerBar")

        layout = QHBoxLayout(header)
        layout.setContentsMargins(28, 20, 28, 20)
        layout.setSpacing(20)

        left_col = QVBoxLayout()
        left_col.setSpacing(0)
        self.hero_title = QLabel(header)
        self.hero_title.setObjectName("heroTitle")
        left_col.addWidget(self.hero_title)
        left_col.addStretch(1)

        right_col = QHBoxLayout()
        right_col.setSpacing(10)
        right_col.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.search_bar = SearchBar(parent=header, height=38)
        self.search_bar.setFixedWidth(420)
        self.search_bar.search_requested.connect(self._refresh_cards)
        self.search_bar.text_changed.connect(lambda _text: self._refresh_cards())

        self.i18n_button = IconButton(
            Icons.i18n_toggle,
            parent=header,
            button_size=36,
            icon_size=18,
        )
        self.i18n_button.clicked.connect(self._toggle_locale)

        self.theme_button = IconButton(
            Icons.theme_toggle,
            parent=header,
            button_size=36,
            icon_size=18,
        )
        self.theme_button.clicked.connect(self._toggle_theme)

        right_col.addWidget(self.search_bar, 0, Qt.AlignmentFlag.AlignVCenter)
        right_col.addWidget(self.i18n_button, 0, Qt.AlignmentFlag.AlignVCenter)
        right_col.addWidget(self.theme_button, 0, Qt.AlignmentFlag.AlignVCenter)

        layout.addLayout(left_col, 1)
        layout.addLayout(right_col)
        return header

    def _build_body(self) -> QWidget:
        body = QWidget(self)
        layout = QHBoxLayout(body)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(18)
        layout.addWidget(self._build_sidebar())
        layout.addWidget(self._build_content_area(), 1)
        return body

    def _build_sidebar(self) -> QFrame:
        panel = QFrame(self)
        panel.setObjectName("sidebarPanel")
        panel.setFixedWidth(228)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 16, 14, 16)
        layout.setSpacing(12)

        self.directory_title = QLabel(panel)
        self.directory_title.setObjectName("pageTitle")

        self.navigation = SideNavigation(panel)
        for index, (name, localized) in enumerate(NAV_ITEMS, start=1):
            self.navigation.add_item(
                SideNavigationItemModel(id_=index, name=name, tip=localized[self._locale])
            )
            widget = self.navigation.main_layout.itemAt(index - 1).widget()
            if widget is not None:
                self._nav_widgets[name] = widget
        self.navigation.selected.connect(self._on_navigation_selected)

        layout.addWidget(self.directory_title)
        layout.addWidget(self.navigation, 1)

        first_item = self.navigation.main_layout.itemAt(0).widget()
        if first_item is not None:
            self.navigation._set_active_leaf_item(first_item)
        return panel

    def _build_content_area(self) -> QWidget:
        scroll = QScrollArea(self)
        scroll.setObjectName("contentScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget(scroll)
        container.setObjectName("contentScrollWidget")
        scroll.setWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 0, 0, 0)
        layout.setSpacing(18)

        self.page_title = QLabel(container)
        self.page_title.setObjectName("sectionTitle")
        self.page_title.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.result_hint = QLabel(container)
        self.result_hint.setObjectName("bodyText")

        layout.addWidget(self.page_title)
        layout.addWidget(self._build_intro_card(container))
        layout.addWidget(self._build_filter_card(container))
        layout.addWidget(self.result_hint)
        layout.addWidget(self._build_card_section(container))
        layout.addStretch(1)
        return scroll

    def _build_intro_card(self, parent: QWidget) -> QFrame:
        card = QFrame(parent)
        card.setObjectName("introCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)

        self.intro_label_1 = QLabel(card)
        self.intro_label_1.setObjectName("bodyText")
        self.intro_label_1.setWordWrap(True)
        self.intro_label_2 = QLabel(card)
        self.intro_label_2.setObjectName("bodyText")
        self.intro_label_2.setWordWrap(True)
        layout.addWidget(self.intro_label_1)
        layout.addWidget(self.intro_label_2)
        return card

    def _build_filter_card(self, parent: QWidget) -> QFrame:
        card = QFrame(parent)
        card.setObjectName("filterCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        top_row = QHBoxLayout()
        top_row.addStretch(1)
        self.filter_title = QLabel(card)
        self.filter_title.setObjectName("pageTitle")
        self.reset_button = QPushButton(card)
        self.reset_button.setObjectName("resetButton")
        self.reset_button.clicked.connect(self._reset_filters)
        top_row.addWidget(self.filter_title)
        top_row.addWidget(self.reset_button)
        top_row.addStretch(1)

        tag_grid = QGridLayout()
        tag_grid.setHorizontalSpacing(10)
        tag_grid.setVerticalSpacing(10)

        for index, (type_name, color) in enumerate(TYPE_COLORS.items()):
            tag = Tag(
                type_name,
                parent=card,
                background_color=color,
                height=30,
                tag_id=type_name,
            )
            tag.tag_clicked.connect(self._on_type_tag_clicked)
            self._type_tags[type_name] = tag
            tag_grid.addWidget(tag, index // 6, index % 6)

        layout.addLayout(top_row)
        layout.addLayout(tag_grid)
        return card

    def _build_card_section(self, parent: QWidget) -> QFrame:
        section = QFrame(parent)
        section.setObjectName("contentPanel")

        wrapper = QVBoxLayout(section)
        wrapper.setContentsMargins(18, 18, 18, 18)
        wrapper.setSpacing(16)

        self.card_title = QLabel(section)
        self.card_title.setObjectName("sectionTitle")

        self.cards_container = QWidget(section)
        self.cards_container.setObjectName("cardsContainer")
        self.cards_layout = QGridLayout(self.cards_container)
        self.cards_layout.setContentsMargins(8, 8, 8, 8)
        self.cards_layout.setHorizontalSpacing(16)
        self.cards_layout.setVerticalSpacing(16)
        for column in range(3):
            self.cards_layout.setColumnStretch(column, 1)

        wrapper.addWidget(self.card_title)
        wrapper.addWidget(self.cards_container)
        return section

    def _apply_window_style(self) -> None:
        is_dark = ThemeManager.current_theme == Qss.Themes.DARK
        if is_dark:
            background = "#10161f"
            header_bg = "#141b25"
            panel_bg = "#1a212d"
            border = "#2a3443"
            card_border = "#41536b"
            soft_text = "#9eacbe"
            card_hover = "#243142"
            title_color = "#edf3fb"
        else:
            background = "#f7f8fb"
            header_bg = "#fdfdfe"
            panel_bg = "#ffffff"
            border = "#e4e8ef"
            card_border = border
            soft_text = "#505d72"
            card_hover = "#fbfdff"
            title_color = "#22344c"

        self.setWindowTitle(self._text("window_title"))
        self.setStyleSheet(
            f"""
            QMainWindow, QWidget {{
                background: {background};
                color: #243549;
            }}
            QLabel {{
                background: transparent;
            }}
            QLabel#heroTitle {{
                font-size: 30px;
                font-weight: 800;
                color: {title_color};
            }}
            QLabel#pageTitle {{
                font-size: 18px;
                font-weight: 700;
                color: {title_color};
            }}
            QLabel#sectionTitle {{
                font-size: 20px;
                font-weight: 800;
                color: {title_color};
            }}
            QLabel#bodyText {{
                font-size: 13px;
                color: {soft_text};
            }}
            QLabel#cardNumber {{
                font-size: 12px;
                font-weight: 700;
                color: #6b7c90;
            }}
            QLabel#cardName {{
                font-size: 19px;
                font-weight: 800;
                color: {title_color};
            }}
            QLabel#cardAlias {{
                font-size: 13px;
                color: {soft_text};
            }}
            QLabel#cardDesc {{
                font-size: 13px;
                color: {soft_text};
            }}
            QLabel#cardBadge {{
                min-width: 52px;
                max-width: 52px;
                min-height: 52px;
                max-height: 52px;
                border-radius: 26px;
                background: transparent;
                color: #4e84cf;
                font-size: 18px;
                font-weight: 800;
            }}
            QFrame#headerBar {{
                background: {header_bg};
                border-bottom: 1px solid {border};
            }}
            QFrame#sidebarPanel,
            QFrame#contentPanel,
            QFrame#introCard,
            QFrame#filterCard {{
                background: {panel_bg};
                border: 1px solid {border};
            }}
            QFrame#pokemonCard {{
                background: {panel_bg};
                border: 1px solid {card_border};
            }}
            QFrame#pokemonCard {{
                border-radius: 18px;
            }}
            QFrame#pokemonCard:hover {{
                border-color: {"#6e89ae" if is_dark else "#cbd9ec"};
                background: {card_hover};
            }}
            QWidget#cardsContainer {{
                background: transparent;
                border: none;
            }}
            QScrollArea#contentScrollArea,
            QScrollArea#contentScrollArea > QWidget#qt_scrollarea_viewport,
            QWidget#contentScrollWidget {{
                background: transparent;
                border: none;
            }}
            QScrollArea#contentScrollArea QScrollBar:vertical {{
                background: transparent;
                width: 10px;
                margin: 8px 0 8px 8px;
            }}
            QScrollArea#contentScrollArea QScrollBar::handle:vertical {{
                background: {"#42536c" if is_dark else "#cad8ec"};
                min-height: 54px;
                border-radius: 5px;
            }}
            QScrollArea#contentScrollArea QScrollBar::handle:vertical:hover {{
                background: {"#586c89" if is_dark else "#aebfda"};
            }}
            QScrollArea#contentScrollArea QScrollBar::handle:vertical:pressed {{
                background: {"#6b82a4" if is_dark else "#95a9c9"};
            }}
            QScrollArea#contentScrollArea QScrollBar::add-line:vertical,
            QScrollArea#contentScrollArea QScrollBar::sub-line:vertical,
            QScrollArea#contentScrollArea QScrollBar::add-page:vertical,
            QScrollArea#contentScrollArea QScrollBar::sub-page:vertical {{
                background: transparent;
                border: none;
                height: 0;
            }}
            QScrollArea#contentScrollArea QScrollBar:horizontal {{
                background: transparent;
                height: 0;
                border: none;
            }}
            QPushButton#resetButton {{
                min-height: 32px;
                border: none;
                background: #f2b8c7;
                color: #ffffff;
                border-radius: 10px;
                padding: 0 18px;
                font-size: 13px;
                font-weight: 700;
            }}
            QPushButton#resetButton:hover {{
                background: #e7a5b7;
            }}
            """
        )

    def _apply_locale(self) -> None:
        self.setWindowTitle(self._text("window_title"))
        self.hero_title.setText(self._text("header_title"))
        self.directory_title.setText(self._text("directory"))
        self.intro_label_1.setText(self._text("intro_1"))
        self.intro_label_2.setText(self._text("intro_2"))
        self.filter_title.setText(self._text("filter_title"))
        self.reset_button.setText(self._text("reset"))
        self.search_bar.set_placeholder(self._text("search_placeholder"))
        self.search_bar.set_tooltip(self._text("search_tooltip"))
        self.i18n_button.set_tooltip(
            self._text("lang_tooltip_en")
            if self._locale == "en"
            else self._text("lang_tooltip_zh")
        )
        self.theme_button.set_tooltip(
            self._text("theme_tooltip_dark")
            if ThemeManager.current_theme == Qss.Themes.DARK
            else self._text("theme_tooltip_light")
        )

        for key, localized in NAV_ITEMS:
            widget = self._nav_widgets.get(key)
            if widget is not None:
                widget.button.setText(localized[self._locale])

        for type_name, tag in self._type_tags.items():
            tag.set_text(TYPE_LABELS[self._locale][type_name])
            tag.set_tooltip(
                f"{self._text('filter_title')}: {TYPE_LABELS[self._locale][type_name]}"
            )

        self._refresh_cards()

    def _toggle_locale(self) -> None:
        self._locale = "en" if self._locale == "zh" else "zh"
        self._apply_locale()
        Toaster.info(
            self._text("lang_toast").format(value=self._text("lang_name")),
            parent=self,
        )

    def _toggle_theme(self) -> None:
        theme = ThemeManager.toggle_theme()
        self._play_theme_transition()
        theme_label = "dark" if theme == Qss.Themes.DARK else "light"
        if self._locale == "zh":
            theme_label = "深色" if theme == Qss.Themes.DARK else "浅色"
        Toaster.success(
            self._text("theme_toast").format(value=theme_label),
            parent=self,
        )

    def _on_theme_changed(self, _theme: str) -> None:
        self._apply_window_style()
        self._apply_locale()

    def _play_theme_transition(self) -> None:
        self._theme_anim.stop()
        self._opacity_effect.setOpacity(0.78)
        self._theme_anim.start()

    def _on_navigation_selected(self, name: str) -> None:
        self._selected_generation = name
        self._refresh_cards()
        self.result_hint.setText(self._text("nav_selected").format(value=self._nav_label(name)))

    def _on_type_tag_clicked(self, type_name: str) -> None:
        self._selected_type = "" if self._selected_type == type_name else type_name
        for name, tag in self._type_tags.items():
            tag.set_selected(name == self._selected_type)
        self._refresh_cards()
        if self._selected_type:
            Toaster.info(
                self._text("tag_clicked").format(
                    value=TYPE_LABELS[self._locale][self._selected_type]
                ),
                parent=self,
            )

    def _reset_filters(self) -> None:
        self._selected_type = ""
        self.search_bar.clear()
        for tag in self._type_tags.values():
            tag.set_selected(False)
        self._refresh_cards()

    def _refresh_cards(self) -> None:
        rows = self._filtered_rows()
        self._update_titles(len(rows))
        self._clear_card_layout()

        for index, pokemon in enumerate(rows):
            card = self._build_pokemon_card(pokemon)
            self._card_widgets.append(card)
            self.cards_layout.addWidget(card, index // 3, index % 3)

    def _clear_card_layout(self) -> None:
        for card in self._card_widgets:
            self.cards_layout.removeWidget(card)
            card.deleteLater()
        self._card_widgets.clear()

    def _build_pokemon_card(self, pokemon: dict) -> QFrame:
        card = QFrame(self.cards_container)
        card.setObjectName("pokemonCard")
        card.setMinimumHeight(220)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        top_row = QHBoxLayout()
        badge = QLabel(pokemon["en"][:1].upper(), card)
        badge.setObjectName("cardBadge")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        number = QLabel(pokemon["no"], card)
        number.setObjectName("cardNumber")
        name = QLabel(pokemon["zh"] if self._locale == "zh" else pokemon["en"], card)
        name.setObjectName("cardName")
        alias = QLabel(
            f"JP: {pokemon['jp']}" if self._locale == "en" else f"日文：{pokemon['jp']}",
            card,
        )
        alias.setObjectName("cardAlias")
        title_col.addWidget(number)
        title_col.addWidget(name)
        title_col.addWidget(alias)

        top_row.addWidget(badge, 0, Qt.AlignmentFlag.AlignTop)
        top_row.addLayout(title_col, 1)

        types_row = QHBoxLayout()
        types_row.setSpacing(8)
        for type_name in pokemon["types"]:
            type_tag = Tag(
                TYPE_LABELS[self._locale][type_name],
                parent=card,
                background_color=TYPE_COLORS.get(type_name, "#d9d9d9"),
                height=26,
                tag_id=type_name,
            )
            type_tag.setEnabled(False)
            types_row.addWidget(type_tag)
        types_row.addStretch(1)

        desc = QLabel(
            pokemon["desc_zh"] if self._locale == "zh" else pokemon["desc_en"],
            card,
        )
        desc.setObjectName("cardDesc")
        desc.setWordWrap(True)

        meta = QLabel(
            f"{self._text('meta_generation').format(value=pokemon['gen'])}  |  "
            f"{self._text('meta_type_count').format(value=len(pokemon['types']))}",
            card,
        )
        meta.setObjectName("bodyText")

        layout.addLayout(top_row)
        layout.addLayout(types_row)
        layout.addWidget(desc)
        layout.addStretch(1)
        layout.addWidget(meta)
        return card

    def _filtered_rows(self) -> list[dict]:
        keyword = self.search_bar.text().strip().lower()
        generation = self._generation_from_key(self._selected_generation)

        rows = []
        for pokemon in POKEMON_DATA:
            if generation is not None and pokemon["gen"] != generation:
                continue
            if self._selected_type and self._selected_type not in pokemon["types"]:
                continue
            if keyword:
                searchable = " ".join(
                    [
                        pokemon["no"],
                        pokemon["en"],
                        pokemon["zh"],
                        pokemon["jp"],
                        " ".join(pokemon["types"]),
                        pokemon["desc_en"],
                        pokemon["desc_zh"],
                    ]
                ).lower()
                if keyword not in searchable:
                    continue
            rows.append(pokemon)
        return rows

    def _update_titles(self, result_count: int) -> None:
        generation_name = self._generation_title(self._selected_generation)
        self.page_title.setText(generation_name)
        self.card_title.setText(generation_name)

        filters: list[str] = []
        if self._selected_type:
            filters.append(
                self._text("type_filter").format(
                    value=TYPE_LABELS[self._locale][self._selected_type]
                )
            )
        keyword = self.search_bar.text().strip()
        if keyword:
            filters.append(self._text("search_filter").format(value=keyword))

        filter_text = " | ".join(filters) if filters else self._text("result_empty_filter")
        self.result_hint.setText(
            self._text("result_count").format(count=result_count, filters=filter_text)
        )

    def _text(self, key: str) -> str:
        return UI_TEXTS[self._locale][key]

    def _nav_label(self, key: str) -> str:
        for nav_key, localized in NAV_ITEMS:
            if nav_key == key:
                return localized[self._locale]
        return key

    def _generation_title(self, key: str) -> str:
        if key == "all":
            return self._text("intro_title")
        return self._nav_label(key)

    @staticmethod
    def _generation_from_key(key: str) -> int | None:
        if not key.startswith("gen"):
            return None
        return int(key.replace("gen", ""))


if __name__ == "__main__":
    init_config()
    app = QApplication(sys.argv)
    window = PokedexDemoWindow()
    window.show()
    sys.exit(app.exec())
