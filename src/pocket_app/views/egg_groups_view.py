from __future__ import annotations

import asyncio
from typing import Any

from PyQt6.QtWidgets import QWidget

from pocket_app import api
from pocket_app.components import PetCard
from .detail import render_egg_group_detail, render_pet_detail
from .view_helpers import (
    LIST_PAGE_SIZE,
    BasePageView,
    add_pagination,
    clear_layout,
    extract_count,
    extract_list,
    paginate_rows,
)


class EggGroupsView(BasePageView):
    page_title_key = "page.egg_groups.title"
    page_description_key = "page.egg_groups.description"
    search_placeholder_key = "page.egg_groups.search"

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._group_id: int | None = None
        self._group_label = ""
        self._detail_group_id: int | None = None
        self._detail_pet_id: int | None = None
        self._current_page = 1
        self._total_pages = 1

    def reset_filters(self) -> None:
        self._detail_group_id = None
        self._detail_pet_id = None
        self._current_page = 1
        self.refresh()

    def set_group_context(self, group_id: int | None, group_label: str = "") -> bool:
        normalized_label = group_label.strip()
        changed = self._group_id != group_id or self._group_label != normalized_label
        self._group_id = group_id
        self._group_label = normalized_label
        if changed:
            self._detail_group_id = None
            self._detail_pet_id = None
            self._current_page = 1
        return changed

    def set_search_text(self, text: str) -> None:
        normalized = text.strip()
        if normalized == self.search_text:
            return
        self._current_page = 1
        super().set_search_text(text)

    async def fetch_data(self) -> dict[str, Any]:
        if self._detail_pet_id is not None:
            return await api.get_pet_detail_payload(self._detail_pet_id)
        if self._detail_group_id is not None:
            detail, pets = await asyncio.gather(
                api.get_egg_group_detail(self._detail_group_id),
                api.list_egg_group_pets(
                    self._detail_group_id,
                    page=1,
                    page_size=LIST_PAGE_SIZE,
                ),
            )
            return {"detail": detail, "pets": pets}
        if self._group_id is None:
            return {"detail": {}, "pets": {"results": [], "count": 0}}
        detail = await api.get_egg_group_detail(self._group_id)
        if self.search_text:
            pets = await self._fetch_all_group_pets_for_search()
            return {"detail": detail, "pets": pets, "search_mode": True}
        pets = await api.list_egg_group_pets(
            self._group_id,
            page=self._current_page,
            page_size=LIST_PAGE_SIZE,
        )
        return {"detail": detail, "pets": pets}

    def render_data(self, data: dict[str, Any]) -> None:
        clear_layout(self.content_layout)
        if self._detail_pet_id is not None:
            render_pet_detail(self, data if isinstance(data, dict) else {}, self._close_pet_detail)
            return
        if self._detail_group_id is not None:
            render_egg_group_detail(self, data if isinstance(data, dict) else {}, self._close_detail)
            return

        pets_payload = data["pets"]
        selected_pets = extract_list(pets_payload)
        filtered_rows = [
            row
            for row in selected_pets
            if not self._search_text or self._search_text.lower() in str(row).lower()
        ]
        if data.get("search_mode"):
            filtered_rows, self._current_page, self._total_pages = paginate_rows(
                filtered_rows,
                self._current_page,
            )
        else:
            self._update_paging(pets_payload)

        cards_panel, cards_layout = self.build_grid_panel("cardCollectionPanel")
        for index, row in enumerate(filtered_rows):
            cards_layout.addWidget(self._build_pet_card(row), index // 3, index % 3)
        self.content_layout.addWidget(cards_panel)
        self.content_layout.addStretch(1)
        add_pagination(
            self.content_layout,
            self.content_widget,
            current_page=self._current_page,
            total_pages=self._total_pages,
            on_page_changed=self._set_page,
        )

    async def _fetch_all_group_pets_for_search(self) -> dict[str, Any]:
        first_page = await api.list_egg_group_pets(
            self._group_id,
            page=1,
            page_size=LIST_PAGE_SIZE,
        )
        rows = extract_list(first_page)
        count = first_page.get("count") if isinstance(first_page, dict) else None
        all_rows = list(rows)
        if isinstance(count, int) and rows:
            page_size = len(rows)
            total_pages = max(1, (count + page_size - 1) // page_size)
            if total_pages > 1:
                payloads = await asyncio.gather(
                    *(
                        api.list_egg_group_pets(
                            self._group_id,
                            page=page,
                            page_size=LIST_PAGE_SIZE,
                        )
                        for page in range(2, total_pages + 1)
                    )
                )
                for payload in payloads:
                    all_rows.extend(extract_list(payload))
        keyword = self.search_text.lower()
        filtered_rows = [row for row in all_rows if keyword in str(row).lower()]
        return {"results": filtered_rows, "count": len(filtered_rows)}

    def _build_pet_card(self, row: dict[str, Any]) -> QWidget:
        card = PetCard(row, parent=self.content_widget, image_size=40, clickable=True)
        card.clicked.connect(self._open_pet_detail)
        return card

    def _open_pet_detail(self, pet_id: int | None) -> None:
        if pet_id is None:
            return
        self._detail_pet_id = pet_id
        self.refresh()

    def _close_pet_detail(self) -> None:
        self._detail_pet_id = None
        self.refresh()

    def _close_detail(self) -> None:
        self._detail_group_id = None
        self.refresh()

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
