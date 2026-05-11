from __future__ import annotations

import asyncio
from typing import Any

from PyQt6.QtWidgets import QLabel

from pocket_app import api
from pocket_app.resources import tr

from .detail import build_clickable_panel, render_game_doc_detail
from .view_helpers import (
    BasePageView,
    add_pagination,
    clear_layout,
    extract_count,
    extract_list,
    first_text,
    make_meta_text,
)


class GameDocsView(BasePageView):
    page_title_key = "page.game_docs.title"
    page_description_key = "page.game_docs.description"
    search_placeholder_key = "page.game_docs.search"

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._group_id: int | None = None
        self._group_label = ""
        self._detail_doc_id: int | None = None
        self._current_page = 1
        self._total_pages = 1

    def reset_filters(self) -> None:
        self._group_id = None
        self._group_label = ""
        self._current_page = 1
        self.refresh()

    def set_search_text(self, text: str) -> None:
        normalized = text.strip()
        if normalized == self.search_text:
            return
        self._current_page = 1
        super().set_search_text(text)

    def set_category_context(self, category_id: int | None, category_label: str = "") -> bool:
        normalized_label = category_label.strip()
        changed = self._group_id != category_id or self._group_label != normalized_label
        self._group_id = category_id
        self._group_label = normalized_label
        if changed:
            self._detail_doc_id = None
            self._current_page = 1
        return changed

    async def fetch_data(self) -> dict[str, Any] | Any:
        if self._detail_doc_id is not None:
            return await api.get_game_doc_detail(self._detail_doc_id)
        if self._group_id is None:
            return {"docs": [], "count": 0}
        if self.search_text:
            docs = await self._fetch_all_docs_for_search()
            return {"docs": docs, "count": len(docs), "search_mode": True}
        return await api.list_game_docs(group_id=self._group_id, page=self._current_page)

    def render_data(self, data: dict[str, Any]) -> None:
        clear_layout(self.content_layout)
        if self._detail_doc_id is not None:
            render_game_doc_detail(self, data if isinstance(data, dict) else {}, self._close_detail)
            return

        rows = extract_list(data, "docs")
        filtered_rows = self._filter_rows(rows)
        self._update_paging(data, len(rows))

        cards_panel, cards_layout = self.build_grid_panel("cardCollectionPanel")
        for index, row in enumerate(filtered_rows):
            doc_id = row.get("id")
            card, layout = build_clickable_panel(
                self,
                lambda current_id=doc_id: self._open_detail(current_id),
            )
            title = QLabel(first_text(row, "name", default=tr("game_docs.doc_default")), card)
            title.setObjectName("resourceTitle")
            layout.addWidget(title)
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

    async def _fetch_all_docs_for_search(self) -> list[dict[str, Any]]:
        first_page = await api.list_game_docs(group_id=self._group_id, page=1)
        rows = extract_list(first_page, "docs")
        count = first_page.get("count") if isinstance(first_page, dict) else None
        if isinstance(count, int) and rows:
            page_size = len(rows)
            total_pages = max(1, (count + page_size - 1) // page_size)
            if total_pages > 1:
                payloads = await asyncio.gather(
                    *(api.list_game_docs(group_id=self._group_id, page=page) for page in range(2, total_pages + 1))
                )
                all_rows = list(rows)
                for payload in payloads:
                    all_rows.extend(extract_list(payload, "docs"))
                return all_rows
        return rows

    def _filter_rows(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not self.search_text:
            return rows
        keyword = self.search_text.lower()
        return [
            row
            for row in rows
            if keyword in first_text(row, "name", "path", default=str(row)).lower()
            or keyword in str(row.get("id", "")).lower()
        ]

    def _update_paging(self, data: Any, page_size: int) -> None:
        if self.search_text:
            self._current_page = 1
            self._total_pages = 1
            return
        total_count = extract_count(data)
        if total_count <= 0 or page_size <= 0:
            self._total_pages = 1
            self._current_page = 1
            return
        self._total_pages = max(1, (total_count + page_size - 1) // page_size)
        self._current_page = min(max(1, self._current_page), self._total_pages)

    def _set_page(self, page: int) -> None:
        normalized = min(max(1, page), self._total_pages)
        if normalized == self._current_page:
            return
        self._current_page = normalized
        self.refresh()

    def _open_detail(self, doc_id: int | None) -> None:
        if doc_id is None:
            return
        self._detail_doc_id = doc_id
        self.refresh()

    def _close_detail(self) -> None:
        self._detail_doc_id = None
        self.refresh()
