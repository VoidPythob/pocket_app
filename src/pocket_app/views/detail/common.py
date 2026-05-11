from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from pocket_app.components import IconButton, RoundedNetworkImage, Tag
from pocket_app.resources import Icons, tr

from ..view_helpers import (
    BasePageView,
    ClickableFrame,
    extract_list,
    first_text,
    make_body_text,
    make_meta_text,
    make_section_title,
    normalize_names,
)


def build_clickable_panel(
    view: BasePageView,
    on_click: Callable[[], None],
    *,
    object_name: str = "resourceCard",
    margins: tuple[int, int, int, int] = (18, 16, 18, 16),
    spacing: int = 10,
) -> tuple[ClickableFrame, QVBoxLayout]:
    card = ClickableFrame(view.content_widget)
    card.setObjectName(object_name)
    card.setCursor(Qt.CursorShape.PointingHandCursor)
    card.clicked.connect(on_click)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(*margins)
    layout.setSpacing(spacing)
    return card, layout


def add_detail_header(
    view: BasePageView,
    title: str,
    subtitle: str,
    on_back: Callable[[], None],
) -> None:
    panel, layout = view.build_panel("introCard")
    top_row = QHBoxLayout()
    top_row.setSpacing(10)

    back_button = IconButton(
        Icons.back_arrow,
        tooltip=tr("detail.back"),
        parent=panel,
        button_size=34,
        icon_size=16,
    )
    back_button.clicked.connect(on_back)
    top_row.addWidget(back_button, 0, Qt.AlignmentFlag.AlignLeft)
    top_row.addStretch(1)

    layout.addLayout(top_row)
    layout.addWidget(make_section_title(title, panel))
    if subtitle.strip():
        layout.addWidget(make_body_text(subtitle, panel))
    view.content_layout.addWidget(panel)


def add_field_panel(
    view: BasePageView,
    title: str,
    fields: Iterable[tuple[str, object]],
) -> None:
    normalized = []
    for label, value in fields:
        text = _stringify_value(value)
        if text:
            normalized.append((label, text))
    if not normalized:
        return

    panel, layout = view.build_panel("pageCard")
    layout.addWidget(make_section_title(title, panel))
    for label, text in normalized:
        layout.addWidget(make_meta_text(f"{label}: {text}", panel))
    view.content_layout.addWidget(panel)


def add_tag_panel(
    view: BasePageView,
    title: str,
    values: Any,
) -> None:
    items = _normalize_tag_items(values)
    if not items:
        return

    panel, layout = view.build_panel("pageCard")
    layout.addWidget(make_section_title(title, panel))
    row = QHBoxLayout()
    row.setSpacing(6)
    for text, color in items:
        tag = Tag(text, parent=panel, background_color=color)
        tag.setEnabled(False)
        row.addWidget(tag)
    row.addStretch(1)
    layout.addLayout(row)
    view.content_layout.addWidget(panel)


def add_text_list_panel(
    view: BasePageView,
    title: str,
    values: Any,
) -> None:
    lines = _normalize_text_list(values)
    if not lines:
        return

    panel, layout = view.build_panel("pageCard")
    layout.addWidget(make_section_title(title, panel))
    for line in lines:
        layout.addWidget(make_body_text(line, panel))
    view.content_layout.addWidget(panel)


def add_image_gallery(
    view: BasePageView,
    title: str,
    urls: list[str],
    *,
    failed_text: str,
    image_size: int = 120,
) -> None:
    normalized_urls = [url for url in urls if url.strip()]
    if not normalized_urls:
        return

    panel = ClickableFrame(view.content_widget)
    panel.setObjectName("pageCard")
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(20, 18, 20, 18)
    layout.setSpacing(12)
    layout.addWidget(make_section_title(title, panel))

    grid = QGridLayout()
    grid.setHorizontalSpacing(12)
    grid.setVerticalSpacing(12)
    for index, url in enumerate(normalized_urls):
        image = RoundedNetworkImage(
            url,
            parent=panel,
            width=image_size,
            height=image_size,
            radius=20,
            failed_text=failed_text,
        )
        grid.addWidget(image, index // 3, index % 3)
    layout.addLayout(grid)
    view.content_layout.addWidget(panel)


def collect_image_urls(data: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    first_url = first_text(data, "first_image_url", default="")
    if first_url:
        urls.append(first_url)

    for key in ("icon_urls", "image_urls", "images"):
        raw_values = data.get(key)
        for value in extract_list(raw_values):
            if isinstance(value, str) and value.strip():
                urls.append(value.strip())
            elif isinstance(value, dict):
                url = first_text(value, "url", "image_url", "src", default="")
                if url:
                    urls.append(url)

    unique_urls: list[str] = []
    seen: set[str] = set()
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        unique_urls.append(url)
    return unique_urls


def _normalize_tag_items(values: Any) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for raw in extract_list(values):
        if isinstance(raw, str):
            text = raw.strip()
            if text:
                items.append((text, ""))
            continue
        if isinstance(raw, dict):
            text = first_text(raw, "name", "title", "introduction", default="")
            if text:
                items.append((text, first_text(raw, "color", default="")))
    return items


def _normalize_text_list(values: Any) -> list[str]:
    rows = normalize_names(values)
    if rows:
        return rows
    text = _stringify_value(values)
    return [text] if text else []


def _stringify_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, dict):
        return first_text(value, "name", "title", "introduction", "detail", default="")
    if isinstance(value, list):
        return ", ".join(normalize_names(value))
    return str(value).strip()
