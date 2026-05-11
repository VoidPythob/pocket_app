from __future__ import annotations

import asyncio
from typing import Callable

from PyQt6.QtCore import QAbstractAnimation, QEasingCurve, QPropertyAnimation, QTimer, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from pocket_app import api
from pocket_app.components import IconButton, LanguageSelector, SearchBar, SideNavigation, SideNavigationItemModel, Toaster
from pocket_app.resources import I18n, I18nManager, Icons, Qss, ThemeManager, load_qss, preload_app_fonts, tr

from .egg_groups_view import EggGroupsView
from .features_view import FeaturesView
from .game_docs_view import GameDocsView
from .items_view import ItemsView
from .pets_view import PetsView
from .skills_view import SkillsView
from .view_helpers import BasePageView, extract_list, first_text

PAGE_CONFIG = [
    ("features", "nav.features", Icons.nav_features),
    ("skills", "nav.skills", Icons.nav_skills),
    ("egg_groups", "nav.egg_groups", Icons.nav_egg_groups),
]


class MainWindowCentralWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.side_navigation = SideNavigation(self)
        self.title_label = QLabel(self)
        self.title_label.setObjectName("headerTitle")
        self.description_label = QLabel(self)
        self.description_label.setObjectName("headerDescription")
        self.search_bar = SearchBar(parent=self, height=38)
        self.refresh_button = IconButton(Icons.refresh, parent=self, button_size=36, icon_size=18)
        self.language_selector = LanguageSelector(parent=self, button_size=36, icon_size=18)
        self.theme_button = IconButton(Icons.theme_toggle, parent=self, button_size=36, icon_size=18)
        self.page_stack = QStackedWidget(self)
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._current_route_name = "pets"
        self._pages: dict[str, BasePageView] = {}
        self._nav_items: dict[str, QWidget] = {}
        self._generation_routes: list[dict[str, object]] = []
        self._item_routes: list[dict[str, object]] = []
        self._egg_group_routes: list[dict[str, object]] = []
        self._game_doc_routes: list[dict[str, object]] = []
        self._generations_loading = False
        self._generation_request_pending = False
        self._items_loading = False
        self._item_request_pending = False
        self._egg_groups_loading = False
        self._egg_group_request_pending = False
        self._game_docs_loading = False
        self._game_doc_request_pending = False
        self._theme_transition_overlay: QLabel | None = None
        self._theme_transition_effect: QGraphicsOpacityEffect | None = None
        self._theme_transition_anim: QPropertyAnimation | None = None
        self._page_factories: dict[str, Callable[[], BasePageView]] = {
            "pets": PetsView,
            "features": FeaturesView,
            "skills": SkillsView,
            "items": ItemsView,
            "egg_groups": EggGroupsView,
            "game_docs": GameDocsView,
        }

        ThemeManager.theme_changing.connect(self._prepare_theme_transition)
        ThemeManager.theme_changed.connect(self._on_theme_changed)
        I18nManager.language_changed.connect(self._on_language_changed)
        self._setup_ui()
        self._load_navigation()
        self._show_page("pets")

    def _setup_ui(self) -> None:
        self.side_navigation.setMinimumWidth(220)
        self.side_navigation.selected.connect(self._show_page)
        self.search_bar.setMinimumWidth(420)

        self.search_bar.search_requested.connect(self._apply_search_now)
        self.search_bar.text_changed.connect(self._schedule_search)
        self.refresh_button.clicked.connect(self._refresh_current_page)
        self.language_selector.locale_selected.connect(self._handle_language_selected)
        self.theme_button.clicked.connect(self._toggle_theme)

        self._search_timer.timeout.connect(self._apply_search_now)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        header = QFrame(self)
        header.setObjectName("mainHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 20, 24, 20)
        header_layout.setSpacing(16)

        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        title_col.addWidget(self.title_label)
        title_col.addWidget(self.description_label)

        right_row = QHBoxLayout()
        right_row.setSpacing(10)
        right_row.addWidget(self.search_bar, 0, Qt.AlignmentFlag.AlignVCenter)
        right_row.addWidget(self.refresh_button, 0, Qt.AlignmentFlag.AlignVCenter)
        right_row.addWidget(self.language_selector, 0, Qt.AlignmentFlag.AlignVCenter)
        right_row.addWidget(self.theme_button, 0, Qt.AlignmentFlag.AlignVCenter)

        header_layout.addLayout(title_col, 1)
        header_layout.addLayout(right_row)

        body = QWidget(self)
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(20, 20, 20, 20)
        body_layout.setSpacing(18)
        body_layout.addWidget(self.side_navigation)
        body_layout.addWidget(self.page_stack, 1)

        root_layout.addWidget(header)
        root_layout.addWidget(body, 1)
        self._apply_theme()

    def _load_navigation(self) -> None:
        self._rebuild_navigation()
        self._load_generations()
        self._load_item_routes()
        self._load_egg_group_routes()
        self._load_game_doc_routes()

    def _rebuild_navigation(self) -> None:
        self.side_navigation.clear_items()
        self._nav_items.clear()

        models: list[SideNavigationItemModel] = [
            SideNavigationItemModel(
                id_=1,
                name="pets",
                tip=tr("nav.pets"),
                icon=Icons.nav_pets,
                children=self._build_generation_children(),
                expandable=True,
            ),
            SideNavigationItemModel(
                id_=2,
                name="items",
                tip=tr("nav.items"),
                icon=Icons.nav_items,
                children=self._build_item_children(),
                expandable=True,
            ),
            SideNavigationItemModel(
                id_=3,
                name="egg_groups",
                tip=tr("nav.egg_groups"),
                icon=Icons.nav_egg_groups,
                children=self._build_egg_group_children(),
                expandable=True,
            ),
            SideNavigationItemModel(
                id_=4,
                name="game_docs",
                tip=tr("nav.game_docs"),
                icon=Icons.nav_game_docs,
                children=self._build_game_doc_children(),
                expandable=True,
            ),
        ]

        base_id = 100
        for offset, (name, label_key, icon_path) in enumerate(PAGE_CONFIG, start=0):
            if name == "egg_groups":
                continue
            models.append(
                SideNavigationItemModel(
                    id_=base_id + offset,
                    name=name,
                    tip=tr(label_key),
                    icon=icon_path,
                )
            )

        for model in models:
            item = self.side_navigation.add_item(model)
            self._index_nav_items(item)

        self._restore_active_route()

    def _build_generation_children(self) -> list[SideNavigationItemModel]:
        children: list[SideNavigationItemModel] = []
        for index, generation in enumerate(self._generation_routes, start=1):
            route_name = str(generation["route"])
            label = str(generation["label"])
            children.append(
                SideNavigationItemModel(
                    id_=200 + index,
                    name=route_name,
                    tip=label,
                    icon=Icons.nav_pets,
                )
            )
        return children

    def _build_egg_group_children(self) -> list[SideNavigationItemModel]:
        children: list[SideNavigationItemModel] = []
        for index, egg_group in enumerate(self._egg_group_routes, start=1):
            route_name = str(egg_group["route"])
            label = str(egg_group["label"])
            children.append(
                SideNavigationItemModel(
                    id_=300 + index,
                    name=route_name,
                    tip=label,
                    icon=Icons.nav_egg_groups,
                )
            )
        return children

    def _build_item_children(self) -> list[SideNavigationItemModel]:
        children: list[SideNavigationItemModel] = []
        for index, item in enumerate(self._item_routes, start=1):
            route_name = str(item["route"])
            label = str(item["label"])
            children.append(
                SideNavigationItemModel(
                    id_=250 + index,
                    name=route_name,
                    tip=label,
                    icon=Icons.nav_items,
                )
            )
        return children

    def _build_game_doc_children(self) -> list[SideNavigationItemModel]:
        children: list[SideNavigationItemModel] = []
        for index, game_doc in enumerate(self._game_doc_routes, start=1):
            route_name = str(game_doc["route"])
            label = str(game_doc["label"])
            children.append(
                SideNavigationItemModel(
                    id_=400 + index,
                    name=route_name,
                    tip=label,
                    icon=Icons.nav_game_docs,
                )
            )
        return children

    def _index_nav_items(self, item: QWidget) -> None:
        model = item.model
        self._nav_items[model.name] = item
        for child in getattr(item, "_children", []):
            self._index_nav_items(child)

    def _restore_active_route(self) -> None:
        target = self._nav_items.get(self._current_route_name) or self._nav_items.get("pets")
        if target is None:
            return
        self.side_navigation._set_active_leaf_item(target)
        if getattr(target, "_depth", 0) > 0:
            parent_route = self._resolve_parent_route_name(self._current_route_name)
            parent_item = self._nav_items.get(parent_route)
            if parent_item is not None:
                parent_item.unfold()

    def _resolve_parent_route_name(self, route_name: str) -> str:
        if "/" not in route_name:
            return route_name
        return route_name.split("/", 1)[0]

    def _load_generations(self) -> None:
        if self._generation_request_pending:
            return
        self._generations_loading = True
        self._generation_request_pending = True
        api.submit_api_task(
            self,
            lambda: api.list_generations(page=1),
            self._handle_generations_loaded,
            self._handle_generations_failed,
        )

    def _handle_generations_loaded(self, data) -> None:
        rows = extract_list(data)
        self._generation_routes = []
        for row in rows:
            generation_id = row.get("id")
            if generation_id is None:
                continue
            label = first_text(row, "name", default=tr("pets.generation_value", value=generation_id))
            self._generation_routes.append(
                {
                    "id": generation_id,
                    "label": label,
                    "route": f"pets/generation/{generation_id}",
                }
            )
        self._generations_loading = False
        self._rebuild_navigation()
        self._generation_request_pending = False
        if self._current_route_name == "pets" or self._current_route_name.startswith("pets/"):
            self._show_page(self._current_route_name)

    def _handle_generations_failed(self, message: str) -> None:
        self._generation_routes = []
        self._generations_loading = False
        self._rebuild_navigation()
        self._generation_request_pending = False
        Toaster.warn(message or tr("nav.generations_failed"))

    def _load_item_routes(self) -> None:
        if self._item_request_pending:
            return
        self._items_loading = True
        self._item_request_pending = True
        api.submit_api_task(
            self,
            self._fetch_item_routes,
            self._handle_item_routes_loaded,
            self._handle_item_routes_failed,
        )

    async def _fetch_item_routes(self):
        first_page = await api.list_items(page=1)
        rows = extract_list(first_page)
        count = first_page.get("count") if isinstance(first_page, dict) else None
        if isinstance(count, int) and rows:
            page_size = len(rows)
            total_pages = (count + page_size - 1) // page_size
            if total_pages > 1:
                other_pages = await asyncio.gather(
                    *(api.list_items(page=page) for page in range(2, total_pages + 1))
                )
                all_rows = list(rows)
                for payload in other_pages:
                    all_rows.extend(extract_list(payload))
                return all_rows
        return rows

    def _handle_item_routes_loaded(self, data) -> None:
        seen_ids: set[int] = set()
        self._item_routes = []
        for row in extract_list(data):
            for category in extract_list(row.get("categories")):
                if not isinstance(category, dict):
                    continue
                category_id = category.get("id")
                if not isinstance(category_id, int) or category_id in seen_ids:
                    continue
                seen_ids.add(category_id)
                label = first_text(category, "name", default=tr("items.detail.categories"))
                self._item_routes.append(
                    {
                        "id": category_id,
                        "label": label,
                        "route": f"items/category/{category_id}",
                    }
                )
        self._items_loading = False
        self._item_request_pending = False
        self._rebuild_navigation()
        if self._current_route_name == "items" or self._current_route_name.startswith("items/"):
            self._show_page(self._current_route_name)

    def _handle_item_routes_failed(self, message: str) -> None:
        self._item_routes = []
        self._items_loading = False
        self._item_request_pending = False
        self._rebuild_navigation()
        Toaster.warn(message or f"{tr('nav.items')} {tr('loading.error_title')}")

    def _load_egg_group_routes(self) -> None:
        if self._egg_group_request_pending:
            return
        self._egg_groups_loading = True
        self._egg_group_request_pending = True
        api.submit_api_task(
            self,
            api.list_egg_groups,
            self._handle_egg_group_routes_loaded,
            self._handle_egg_group_routes_failed,
        )

    def _handle_egg_group_routes_loaded(self, data) -> None:
        rows = extract_list(data)
        self._egg_group_routes = []
        for row in rows:
            egg_group_id = row.get("id")
            if egg_group_id is None:
                continue
            label = first_text(row, "name", default=tr("egg_groups.group_value", value=egg_group_id))
            self._egg_group_routes.append(
                {
                    "id": egg_group_id,
                    "label": label,
                    "route": f"egg_groups/group/{egg_group_id}",
                }
            )
        self._egg_groups_loading = False
        self._egg_group_request_pending = False
        self._rebuild_navigation()
        if self._current_route_name == "egg_groups" or self._current_route_name.startswith("egg_groups/"):
            self._show_page(self._current_route_name)

    def _handle_egg_group_routes_failed(self, message: str) -> None:
        self._egg_group_routes = []
        self._egg_groups_loading = False
        self._egg_group_request_pending = False
        self._rebuild_navigation()
        Toaster.warn(message or tr("nav.egg_groups_failed"))

    def _load_game_doc_routes(self) -> None:
        if self._game_doc_request_pending:
            return
        self._game_docs_loading = True
        self._game_doc_request_pending = True
        api.submit_api_task(
            self,
            api.list_game_doc_categories,
            self._handle_game_doc_routes_loaded,
            self._handle_game_doc_routes_failed,
        )

    def _handle_game_doc_routes_loaded(self, data) -> None:
        rows = extract_list(data, "categories", "groups")
        self._game_doc_routes = []
        seen_ids: set[int] = set()
        for row in rows:
            source = row
            if not isinstance(source, dict):
                continue
            game_doc_id = source.get("id")
            if game_doc_id is None:
                for key in ("group", "category", "parent"):
                    nested = source.get(key)
                    if isinstance(nested, dict):
                        source = nested
                        game_doc_id = nested.get("id")
                        break
            parent_id = source.get("p_id")
            if parent_id not in (None, "", 0):
                continue
            if not isinstance(game_doc_id, int) or game_doc_id in seen_ids:
                continue
            seen_ids.add(game_doc_id)
            label = first_text(source, "name", default=tr("game_docs.category_value", value=game_doc_id))
            self._game_doc_routes.append(
                {
                    "id": game_doc_id,
                    "label": label,
                    "route": f"game_docs/group/{game_doc_id}",
                }
            )
        self._game_docs_loading = False
        self._game_doc_request_pending = False
        self._rebuild_navigation()
        if self._current_route_name == "game_docs" or self._current_route_name.startswith("game_docs/"):
            self._show_page(self._current_route_name)

    def _handle_game_doc_routes_failed(self, message: str) -> None:
        self._game_doc_routes = []
        self._game_docs_loading = False
        self._game_doc_request_pending = False
        self._rebuild_navigation()
        Toaster.warn(message or f"{tr('nav.game_docs')} {tr('loading.error_title')}")

    def _get_or_create_page(self, page_name: str) -> BasePageView:
        page = self._pages.get(page_name)
        if page is not None:
            return page

        factory = self._page_factories[page_name]
        page = factory()
        self._pages[page_name] = page
        self.page_stack.addWidget(page)
        return page

    def _resolve_page_key(self, route_name: str) -> str:
        if route_name.startswith("pets/"):
            return "pets"
        if route_name.startswith("items/"):
            return "items"
        if route_name.startswith("egg_groups/"):
            return "egg_groups"
        if route_name.startswith("game_docs/"):
            return "game_docs"
        return route_name

    def _resolve_generation_context(self, route_name: str) -> tuple[int | None, str]:
        for generation in self._generation_routes:
            if generation["route"] == route_name:
                return int(generation["id"]), str(generation["label"])
        return None, ""

    def _resolve_egg_group_context(self, route_name: str) -> tuple[int | None, str]:
        for egg_group in self._egg_group_routes:
            if egg_group["route"] == route_name:
                return int(egg_group["id"]), str(egg_group["label"])
        return None, ""

    def _resolve_item_context(self, route_name: str) -> tuple[int | None, str]:
        for item in self._item_routes:
            if item["route"] == route_name:
                return int(item["id"]), str(item["label"])
        return None, ""

    def _resolve_game_doc_context(self, route_name: str) -> tuple[int | None, str]:
        normalized_route = route_name.replace("game_docs/category/", "game_docs/group/", 1)
        for game_doc in self._game_doc_routes:
            if game_doc["route"] == normalized_route:
                return int(game_doc["id"]), str(game_doc["label"])
        return None, ""

    def _show_page(self, route_name: str) -> None:
        if route_name.startswith("game_docs/category/"):
            route_name = route_name.replace("game_docs/category/", "game_docs/group/", 1)
        if route_name == "pets" and self._generation_routes:
            route_name = str(self._generation_routes[0]["route"])
        elif route_name.startswith("pets/") and self._generation_routes:
            generation_id, _generation_label = self._resolve_generation_context(route_name)
            if generation_id is None:
                route_name = str(self._generation_routes[0]["route"])
        elif route_name == "items" and self._item_routes:
            route_name = str(self._item_routes[0]["route"])
        elif route_name.startswith("items/") and self._item_routes:
            item_category_id, _item_category_label = self._resolve_item_context(route_name)
            if item_category_id is None:
                route_name = str(self._item_routes[0]["route"])
        elif route_name == "egg_groups" and self._egg_group_routes:
            route_name = str(self._egg_group_routes[0]["route"])
        elif route_name.startswith("egg_groups/") and self._egg_group_routes:
            egg_group_id, _egg_group_label = self._resolve_egg_group_context(route_name)
            if egg_group_id is None:
                route_name = str(self._egg_group_routes[0]["route"])
        elif route_name == "game_docs" and self._game_doc_routes:
            route_name = str(self._game_doc_routes[0]["route"])
        elif route_name.startswith("game_docs/") and self._game_doc_routes:
            game_doc_id, _game_doc_label = self._resolve_game_doc_context(route_name)
            if game_doc_id is None:
                route_name = str(self._game_doc_routes[0]["route"])

        page_name = self._resolve_page_key(route_name)
        if page_name not in self._page_factories:
            return
        self._current_route_name = route_name
        self._restore_active_route()
        page = self._get_or_create_page(page_name)
        search_text = self.search_bar.text().strip()

        route_changed = False
        if page_name == "pets" and isinstance(page, PetsView):
            generation_id, generation_label = self._resolve_generation_context(route_name)
            route_changed = page.set_generation_context(generation_id, generation_label)
        elif page_name == "items" and isinstance(page, ItemsView):
            item_category_id, item_category_label = self._resolve_item_context(route_name)
            route_changed = page.set_category_context(item_category_id, item_category_label)
        elif page_name == "egg_groups" and isinstance(page, EggGroupsView):
            egg_group_id, egg_group_label = self._resolve_egg_group_context(route_name)
            route_changed = page.set_group_context(egg_group_id, egg_group_label)
        elif page_name == "game_docs" and isinstance(page, GameDocsView):
            game_doc_id, game_doc_label = self._resolve_game_doc_context(route_name)
            route_changed = page.set_category_context(game_doc_id, game_doc_label)

        self.page_stack.setCurrentWidget(page)
        self.title_label.setText(page.page_title)
        self.description_label.setText(page.page_description)
        self.search_bar.set_placeholder(page.search_placeholder)
        if page.search_text != search_text:
            page.set_search_text(search_text)
        elif route_changed and page.has_loaded:
            page.refresh()
        if not page.has_loaded:
            page.refresh()
        self._apply_tooltips()

    def _schedule_search(self, _text: str) -> None:
        self._search_timer.start(280)

    def _apply_search_now(self, _text: str | None = None) -> None:
        page = self._pages.get(self._resolve_page_key(self._current_route_name))
        if page is None:
            return
        search_text = self.search_bar.text().strip()
        if page.search_text == search_text:
            page.refresh()
            return
        page.set_search_text(search_text)

    def _refresh_current_page(self) -> None:
        self._refresh_navigation()
        page = self._pages.get(self._resolve_page_key(self._current_route_name))
        if page is None:
            self._show_page(self._current_route_name)
            return
        page.refresh()

    def _refresh_navigation(self) -> None:
        self._load_generations()
        self._load_item_routes()
        self._load_egg_group_routes()
        self._load_game_doc_routes()

    def _toggle_theme(self) -> None:
        theme = ThemeManager.toggle_theme()
        Toaster.success(
            tr(
                "toast.theme_switched",
                theme=tr("theme.dark") if theme == Qss.Themes.DARK else tr("theme.light"),
            )
        )

    def _handle_language_selected(self, locale_value: str) -> None:
        I18n.Locales(locale_value)

    def _apply_theme(self) -> None:
        self.setStyleSheet(load_qss(Qss.s_main_window))
        self._apply_tooltips()

    def _apply_tooltips(self) -> None:
        self.refresh_button.set_tooltip(tr("header.refresh_tooltip"))
        self.language_selector.set_tooltip(tr("header.language_tooltip"))
        self.theme_button.set_tooltip(tr("header.theme_tooltip"))

    def _prepare_theme_transition(self, _next_theme: str) -> None:
        if not self.isVisible():
            return
        snapshot = self.grab()
        if snapshot.isNull():
            return
        self._clear_theme_transition_overlay()
        overlay = QLabel(self)
        overlay.setPixmap(snapshot)
        overlay.setScaledContents(True)
        overlay.setGeometry(self.rect())
        overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        overlay.show()
        overlay.raise_()

        effect = QGraphicsOpacityEffect(overlay)
        effect.setOpacity(1.0)
        overlay.setGraphicsEffect(effect)

        self._theme_transition_overlay = overlay
        self._theme_transition_effect = effect

    def _play_theme_transition(self) -> None:
        overlay = self._theme_transition_overlay
        effect = self._theme_transition_effect
        if overlay is None or effect is None:
            return
        if self._theme_transition_anim is not None:
            self._theme_transition_anim.stop()
            self._theme_transition_anim.deleteLater()
            self._theme_transition_anim = None
        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(220)
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.finished.connect(self._clear_theme_transition_overlay)
        self._theme_transition_anim = animation
        animation.start()

    def _clear_theme_transition_overlay(self) -> None:
        if self._theme_transition_anim is not None:
            if self._theme_transition_anim.state() != QAbstractAnimation.State.Stopped:
                self._theme_transition_anim.stop()
            self._theme_transition_anim.deleteLater()
            self._theme_transition_anim = None
        if self._theme_transition_overlay is not None:
            self._theme_transition_overlay.setGraphicsEffect(None)
            self._theme_transition_overlay.hide()
            self._theme_transition_overlay.deleteLater()
            self._theme_transition_overlay = None
        self._theme_transition_effect = None

    def _on_theme_changed(self, _theme: str) -> None:
        self._apply_theme()
        self._play_theme_transition()

    def _on_language_changed(self, _locale: str) -> None:
        self.window().setWindowTitle(tr("window.title"))
        self._rebuild_navigation()

        current_page = self._pages.get(self._resolve_page_key(self._current_route_name))
        if current_page is not None:
            self.title_label.setText(current_page.page_title)
            self.description_label.setText(current_page.page_description)
            self.search_bar.set_placeholder(current_page.search_placeholder)

        for page in self._pages.values():
            page.rerender_last()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        if self._theme_transition_overlay is not None:
            self._theme_transition_overlay.setGeometry(self.rect())


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        preload_app_fonts()
        self.setWindowTitle(tr("window.title"))
        self.setWindowIcon(QIcon(Icons.nav_pets))
        self.setCentralWidget(MainWindowCentralWidget())
        self.resize(1280, 860)
