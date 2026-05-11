from __future__ import annotations

from PyQt6.QtWidgets import QLabel

from pocket_app import api
from pocket_app.resources import tr

from .detail import build_clickable_panel, render_skill_detail
from .view_helpers import (
    BasePageView,
    add_pagination,
    clear_layout,
    extract_count,
    extract_list,
    first_text,
    make_body_text,
    make_meta_text,
    make_section_title,
)


class SkillsView(BasePageView):
    page_title_key = "page.skills.title"
    page_description_key = "page.skills.description"
    search_placeholder_key = "page.skills.search"

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._selected_skill_id: int | None = None
        self._current_page = 1
        self._total_pages = 1

    def set_search_text(self, text: str) -> None:
        normalized = text.strip()
        if normalized == self.search_text:
            return
        self._current_page = 1
        super().set_search_text(text)

    async def fetch_data(self):
        if self._selected_skill_id is not None:
            return await api.get_skill_detail(self._selected_skill_id)
        return await api.list_skills(page=self._current_page)

    def render_data(self, data) -> None:
        clear_layout(self.content_layout)
        if self._selected_skill_id is not None:
            render_skill_detail(self, data if isinstance(data, dict) else {}, self._close_detail)
            return

        rows = extract_list(data)
        filtered_rows = self._filter_rows(rows)
        self._update_paging(data, len(rows))

        intro_panel, intro_layout = self.build_panel("introCard")
        intro_layout.addWidget(make_section_title(tr("skills.intro_title"), intro_panel))
        intro_layout.addWidget(
            make_body_text(
                tr("skills.intro_desc"),
                intro_panel,
            )
        )
        self.content_layout.addWidget(intro_panel)

        hint_panel, hint_layout = self.build_panel("pageCard", spacing=8)
        hint_layout.addWidget(make_meta_text(tr("skills.loaded", count=len(filtered_rows)), hint_panel))
        hint_layout.addWidget(make_meta_text(tr("skills.page_hint", page=self._current_page, total=self._total_pages), hint_panel))
        self.content_layout.addWidget(hint_panel)

        cards_panel, cards_layout = self.build_grid_panel("cardCollectionPanel")
        for index, row in enumerate(filtered_rows):
            skill_id = row.get("id")
            card, layout = build_clickable_panel(
                self,
                lambda current_id=skill_id: self._open_detail(current_id),
            )
            title = QLabel(first_text(row, "name", "introduction", default=tr("skills.fallback")), card)
            title.setObjectName("resourceTitle")
            layout.addWidget(title)
            layout.addWidget(make_body_text(first_text(row, "introduction"), card))
            layout.addWidget(make_meta_text(first_text(row, "detail"), card))
            cards_layout.addWidget(card, index // 3, index % 3)
        self.content_layout.addWidget(cards_panel)
        add_pagination(
            self.content_layout,
            self.content_widget,
            current_page=self._current_page,
            total_pages=self._total_pages,
            on_page_changed=self._set_page,
        )

        self.content_layout.addStretch(1)

    def _filter_rows(self, rows: list[dict]) -> list[dict]:
        if not self.search_text:
            return rows
        keyword = self.search_text.lower()
        return [row for row in rows if keyword in str(row).lower()]

    def _update_paging(self, data, page_size: int) -> None:
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

    def _open_detail(self, skill_id: int | None) -> None:
        if skill_id is None:
            return
        self._selected_skill_id = skill_id
        self.refresh()

    def _close_detail(self) -> None:
        self._selected_skill_id = None
        self.refresh()
