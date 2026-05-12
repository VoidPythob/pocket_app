from __future__ import annotations

from PyQt6.QtWidgets import QLabel

from pocket_app import api
from pocket_app.resources import tr

from .detail import build_clickable_panel, render_item_detail
from .view_helpers import (
    LIST_PAGE_SIZE,
    BasePageView,
    add_pagination,
    clear_layout,
    extract_count,
    extract_list,
    first_text,
    make_body_text,
    make_meta_text,
)


class ItemsView(BasePageView):
    page_title_key = "page.items.title"
    page_description_key = "page.items.description"
    search_placeholder_key = "page.items.search"

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._category_id: int | None = None
        self._category_label = ""
        self._selected_item_id: int | None = None
        self._current_page = 1
        self._total_pages = 1

    def reset_filters(self) -> None:
        self._category_id = None
        self._category_label = ""
        self._current_page = 1
        self.refresh()

    def set_category_context(self, category_id: int | None, category_label: str = "") -> bool:
        normalized_label = category_label.strip()
        changed = self._category_id != category_id or self._category_label != normalized_label
        self._category_id = category_id
        self._category_label = normalized_label
        if changed:
            self._selected_item_id = None
            self._current_page = 1
        return changed

    def set_search_text(self, text: str) -> None:
        normalized = text.strip()
        if normalized == self.search_text:
            return
        self._current_page = 1
        super().set_search_text(text)

    async def fetch_data(self):
        if self._selected_item_id is not None:
            return await api.get_item_detail(self._selected_item_id)
        return await api.list_items(
            category_id=self._category_id,
            name=self._search_text,
            page=self._current_page,
            page_size=LIST_PAGE_SIZE,
        )

    def render_data(self, data) -> None:
        clear_layout(self.content_layout)
        if self._selected_item_id is not None:
            render_item_detail(self, data if isinstance(data, dict) else {}, self._close_detail)
            return
        rows = extract_list(data)
        self._update_paging(data)

        cards_panel, cards_layout = self.build_grid_panel("cardCollectionPanel")
        for index, row in enumerate(rows):
            item_id = row.get("id")
            card, layout = build_clickable_panel(
                self,
                lambda current_id=item_id: self._open_detail(current_id),
            )
            title = QLabel(first_text(row, "name", default=tr("items.fallback")), card)
            title.setObjectName("resourceTitle")
            layout.addWidget(title)
            layout.addWidget(
                make_meta_text(
                    tr(
                        "items.card.meta",
                        jp_name=first_text(row, "jp_name"),
                        en_name=first_text(row, "en_name"),
                    ),
                    card,
                )
            )
            layout.addWidget(make_body_text(first_text(row, "introduction"), card))
            layout.addWidget(make_meta_text(first_text(row, "detail"), card))

            cards_layout.addWidget(card, index // 3, index % 3)
        self.content_layout.addWidget(cards_panel)
        self.content_layout.addStretch(1)
        add_pagination(
            self.content_layout,
            self.content_widget,
            current_page=self._current_page,
            total_pages=self._total_pages,
            on_page_changed=self._set_page,
        )

    def _update_paging(self, data) -> None:
        total_count = extract_count(data)
        if total_count <= 0:
            self._total_pages = 1
            self._current_page = 1
            return
        self._total_pages = max(1, (total_count + LIST_PAGE_SIZE - 1) // LIST_PAGE_SIZE)
        self._current_page = min(max(1, self._current_page), self._total_pages)

    def _set_page(self, page: int) -> None:
        normalized = min(max(1, page), self._total_pages)
        if normalized == self._current_page:
            return
        self._current_page = normalized
        self.refresh()

    def _open_detail(self, item_id: int | None) -> None:
        if item_id is None:
            return
        self._selected_item_id = item_id
        self.refresh()

    def _close_detail(self) -> None:
        self._selected_item_id = None
        self.refresh()
