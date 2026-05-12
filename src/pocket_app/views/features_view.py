from __future__ import annotations

from PyQt6.QtWidgets import QLabel

from pocket_app import api
from pocket_app.resources import tr

from .detail import build_clickable_panel, render_feature_detail
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


class FeaturesView(BasePageView):
    page_title_key = "page.features.title"
    page_description_key = "page.features.description"
    search_placeholder_key = "page.features.search"

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._selected_feature_id: int | None = None
        self._current_page = 1
        self._total_pages = 1

    def set_search_text(self, text: str) -> None:
        normalized = text.strip()
        if normalized == self.search_text:
            return
        self._current_page = 1
        super().set_search_text(text)

    async def fetch_data(self):
        if self._selected_feature_id is not None:
            return await api.get_feature_detail(self._selected_feature_id)
        return await api.list_features(
            name=self._search_text,
            page=self._current_page,
            page_size=LIST_PAGE_SIZE,
        )

    def render_data(self, data) -> None:
        clear_layout(self.content_layout)
        if self._selected_feature_id is not None:
            render_feature_detail(self, data if isinstance(data, dict) else {}, self._close_detail)
            return
        rows = extract_list(data)
        self._update_paging(data)

        cards_panel, cards_layout = self.build_grid_panel("cardCollectionPanel")
        for index, row in enumerate(rows):
            feature_id = row.get("id")
            card, layout = build_clickable_panel(
                self,
                lambda current_id=feature_id: self._open_detail(current_id),
            )
            title = QLabel(first_text(row, "name", "introduction", default=tr("features.fallback")), card)
            title.setObjectName("resourceTitle")
            layout.addWidget(title)
            feature_meta_parts = [f"ID: {feature_id if feature_id is not None else '-'}"]
            jp_name = first_text(row, "jp_name", default="")
            en_name = first_text(row, "en_name", default="")
            if jp_name or en_name:
                feature_meta_parts.append(
                    tr(
                        "items.card.meta",
                        jp_name=jp_name or "-",
                        en_name=en_name or "-",
                    )
                )
            layout.addWidget(make_meta_text("  |  ".join(feature_meta_parts), card))
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

    def _open_detail(self, feature_id: int | None) -> None:
        if feature_id is None:
            return
        self._selected_feature_id = feature_id
        self.refresh()

    def _close_detail(self) -> None:
        self._selected_feature_id = None
        self.refresh()
