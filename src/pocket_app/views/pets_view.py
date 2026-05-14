from __future__ import annotations

import asyncio
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from pocket_app import api
from pocket_app.components import PetCard, PopupPanel, Tag
from pocket_app.resources import tr

from .detail import render_pet_detail
from .view_helpers import (
    LIST_PAGE_SIZE,
    BasePageView,
    add_pagination,
    clear_layout,
    extract_count,
    extract_list,
    first_text,
    make_section_title,
)


class PetsView(BasePageView):
    page_title_key = "page.pets.title"
    page_description_key = "page.pets.description"
    search_placeholder_key = "page.pets.search"

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._generation_id: int | None = None
        self._generation_label = ""
        self._feature_id: int | None = None
        self._tag_id: int | None = None
        self._detail_pet_id: int | None = None
        self._feature_popup = PopupPanel(offset_y=10, match_anchor_width=True)
        self._tag_popup = PopupPanel(offset_y=10, match_anchor_width=True)
        self._current_page = 1
        self._total_pages = 1

    def reset_filters(self) -> None:
        self._feature_id = None
        self._tag_id = None
        self._current_page = 1
        self.refresh()

    def set_generation_context(self, generation_id: int | None, generation_label: str = "") -> bool:
        normalized_label = generation_label.strip()
        changed = (
            self._generation_id != generation_id
            or self._generation_label != normalized_label
        )
        self._generation_id = generation_id
        self._generation_label = normalized_label
        if changed:
            self._detail_pet_id = None
            self._tag_id = None
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
        if self._generation_id is None:
            return {
                "features": await api.list_features(page=1),
                "tags": await api.list_tags(),
                "pets": {"results": [], "count": 0},
            }
        features, tags, pets = await asyncio.gather(
            api.list_features(page=1),
            api.list_tags(),
            api.list_pets(
                generation_id=self._generation_id,
                feature_id=self._feature_id,
                tag_id=self._tag_id,
                name=self._search_text,
                page=self._current_page,
                page_size=LIST_PAGE_SIZE,
            ),
        )
        return {"features": features, "tags": tags, "pets": pets}

    def render_data(self, data: dict[str, Any]) -> None:
        self._feature_popup.hide()
        self._tag_popup.hide()
        clear_layout(self.content_layout)
        if self._detail_pet_id is not None:
            render_pet_detail(self, data if isinstance(data, dict) else {}, self._close_detail)
            return

        features = extract_list(data["features"])
        tags = extract_list(data.get("tags", []))
        pets_payload = data["pets"]
        pets = extract_list(pets_payload)
        self._update_paging(pets_payload)

        filter_panel, filter_layout = self.build_panel("pageCard")
        filter_layout.addWidget(make_section_title(tr("common.filters"), filter_panel))
        self._add_filter_row(filter_layout, filter_panel, features, tags)
        self.content_layout.addWidget(filter_panel)

        cards_panel, cards_layout = self.build_grid_panel("cardCollectionPanel")
        for column in range(3):
            cards_layout.setColumnStretch(column, 1)
        for index, pet in enumerate(pets):
            cards_layout.addWidget(self._build_pet_card(pet), index // 3, index % 3)
        self.content_layout.addWidget(cards_panel)
        self.content_layout.addStretch(1)
        add_pagination(
            self.content_layout,
            self.content_widget,
            current_page=self._current_page,
            total_pages=self._total_pages,
            on_page_changed=self._set_page,
        )

    def _add_feature_row(
        self,
        parent_layout: QVBoxLayout,
        parent: QWidget,
        features: list[dict[str, Any]],
    ) -> None:
        row = QHBoxLayout()
        row.setSpacing(8)
        title = QLabel(tr("pets.feature"), parent)
        title.setObjectName("cardSubTitle")
        row.addWidget(title)

        trigger = Tag(self._feature_filter_text(features), parent=parent, tag_id="feature_filter")
        trigger.set_selected(self._feature_id is not None)
        trigger.set_tooltip(tr("common.filters"))
        self._feature_popup.set_content_widget(self._build_feature_popup_content(features))
        self._feature_popup.bind_toggle(trigger)
        row.addWidget(trigger)
        row.addStretch(1)
        parent_layout.addLayout(row)

    def _add_filter_row(
        self,
        parent_layout: QVBoxLayout,
        parent: QWidget,
        features: list[dict[str, Any]],
        tags: list[dict[str, Any]],
    ) -> None:
        row = QHBoxLayout()
        row.setSpacing(16)

        feature_title = QLabel(tr("pets.feature"), parent)
        feature_title.setObjectName("cardSubTitle")
        row.addWidget(feature_title)

        feature_trigger = Tag(
            self._feature_filter_text(features),
            parent=parent,
            tag_id="feature_filter",
        )
        feature_trigger.set_selected(self._feature_id is not None)
        feature_trigger.set_tooltip(tr("common.filters"))
        self._feature_popup.set_content_widget(self._build_feature_popup_content(features))
        self._feature_popup.bind_toggle(feature_trigger)
        row.addWidget(feature_trigger)

        tag_title = QLabel(tr("pets.detail.tags"), parent)
        tag_title.setObjectName("cardSubTitle")
        row.addWidget(tag_title)

        tag_trigger = Tag(
            self._tag_filter_text(tags),
            parent=parent,
            tag_id="tag_filter",
        )
        tag_trigger.set_selected(self._tag_id is not None)
        tag_trigger.set_tooltip(tr("common.filters"))
        self._tag_popup.set_content_widget(self._build_tag_popup_content(tags))
        self._tag_popup.bind_toggle(tag_trigger)
        row.addWidget(tag_trigger)

        row.addStretch(1)
        parent_layout.addLayout(row)

    def _build_feature_popup_content(self, features: list[dict[str, Any]]) -> QWidget:
        content = QWidget()
        content.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        title = QLabel(tr("common.filters"), content)
        title.setObjectName("resourceTitle")
        layout.addWidget(title)

        desc = QLabel(tr("pets.feature"), content)
        desc.setObjectName("metaText")
        layout.addWidget(desc)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

        all_tag = Tag(tr("common.all"), parent=content, tag_id="all")
        all_tag.set_selected(self._feature_id is None)
        all_tag.tag_clicked.connect(lambda _tag_id: self._select_feature_from_popup(None))
        grid.addWidget(all_tag, 0, 0)

        for index, feature in enumerate(features, start=1):
            label = first_text(feature, "name", "introduction", default=tr("features.fallback"))
            tag = Tag(label[:14], parent=content, tag_id=str(feature.get("id", "")))
            tag.set_selected(self._feature_id == feature.get("id"))
            tag.set_tooltip(first_text(feature, "introduction", "detail", default=label))
            tag.tag_clicked.connect(
                lambda _tag_id, feature_id=feature.get("id"): self._select_feature_from_popup(feature_id)
            )
            grid.addWidget(tag, index // 3, index % 3)

        layout.addLayout(grid)
        return content

    def _add_tag_row(
        self,
        parent_layout: QVBoxLayout,
        parent: QWidget,
        tags: list[dict[str, Any]],
    ) -> None:
        row = QHBoxLayout()
        row.setSpacing(8)
        title = QLabel(tr("pets.detail.tags"), parent)
        title.setObjectName("cardSubTitle")
        row.addWidget(title)

        trigger = Tag(self._tag_filter_text(tags), parent=parent, tag_id="tag_filter")
        trigger.set_selected(self._tag_id is not None)
        trigger.set_tooltip(tr("common.filters"))
        self._tag_popup.set_content_widget(self._build_tag_popup_content(tags))
        self._tag_popup.bind_toggle(trigger)
        row.addWidget(trigger)
        row.addStretch(1)
        parent_layout.addLayout(row)

    def _build_tag_popup_content(self, tags: list[dict[str, Any]]) -> QWidget:
        content = QWidget()
        content.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        title = QLabel(tr("common.filters"), content)
        title.setObjectName("resourceTitle")
        layout.addWidget(title)

        desc = QLabel(tr("pets.detail.tags"), content)
        desc.setObjectName("metaText")
        layout.addWidget(desc)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

        all_tag = Tag(tr("common.all"), parent=content, tag_id="all")
        all_tag.set_selected(self._tag_id is None)
        all_tag.tag_clicked.connect(lambda _tag_id: self._select_tag_from_popup(None))
        grid.addWidget(all_tag, 0, 0)

        for index, raw_tag in enumerate(tags, start=1):
            tag_id = raw_tag.get("id")
            if not isinstance(tag_id, int):
                continue
            label = first_text(raw_tag, "name", default=tr("pets.detail.tags"))
            color = first_text(raw_tag, "color", default="")
            tag = Tag(
                label[:14],
                parent=content,
                background_color=color,
                tag_id=str(tag_id),
            )
            tag.set_selected(self._tag_id == tag_id)
            tag.tag_clicked.connect(
                lambda _tag_id, current_id=tag_id: self._select_tag_from_popup(current_id)
            )
            grid.addWidget(tag, index // 3, index % 3)

        layout.addLayout(grid)
        return content

    def _feature_filter_text(self, features: list[dict[str, Any]]) -> str:
        if self._feature_id is None:
            return tr("common.filters")
        for feature in features:
            if feature.get("id") == self._feature_id:
                return first_text(feature, "name", "introduction", default=tr("common.filters"))[:14]
        return tr("common.filters")

    def _select_feature_from_popup(self, feature_id: int | None) -> None:
        self._feature_popup.hide()
        self._set_feature(feature_id)

    def _select_tag_from_popup(self, tag_id: int | None) -> None:
        self._tag_popup.hide()
        self._set_tag(tag_id)

    def _tag_filter_text(self, tags: list[dict[str, Any]]) -> str:
        if self._tag_id is None:
            return tr("common.filters")
        for raw_tag in tags:
            if raw_tag.get("id") == self._tag_id:
                return first_text(raw_tag, "name", default=tr("common.filters"))[:14]
        return tr("common.filters")

    def _build_pet_card(self, pet: dict[str, Any]) -> QWidget:
        card = PetCard(pet, parent=self.content_widget, image_size=40, clickable=True)
        card.clicked.connect(self._open_detail)
        return card

    def _set_feature(self, feature_id: int | None) -> None:
        self._feature_id = feature_id
        self._current_page = 1
        self.refresh()

    def _set_tag(self, tag_id: int | None) -> None:
        self._tag_id = tag_id
        self._current_page = 1
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

    def _open_detail(self, pet_id: int | None) -> None:
        if pet_id is None:
            return
        self._detail_pet_id = pet_id
        self.refresh()

    def _close_detail(self) -> None:
        self._detail_pet_id = None
        self.refresh()
