from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..view_helpers import BasePageView, first_text, make_body_text, make_meta_text
from .common import add_detail_header


def render_item_detail(
    view: BasePageView,
    detail: dict[str, Any],
    on_back: Callable[[], None],
) -> None:
    title = first_text(detail, "name", default="Item")
    add_detail_header(view, title, "", on_back)

    name_panel, name_layout = view.build_panel("pageCard")
    name_layout.addWidget(make_meta_text(f"ID: {detail.get('id', '-')}", name_panel))
    name_layout.addWidget(make_meta_text(f"JP: {first_text(detail, 'jp_name', default='-')}", name_panel))
    name_layout.addWidget(make_meta_text(f"EN: {first_text(detail, 'en_name', default='-')}", name_panel))
    view.content_layout.addWidget(name_panel)

    description_panel, description_layout = view.build_panel("pageCard")
    introduction = first_text(detail, "introduction", default="-")
    detail_text = first_text(detail, "detail", default="")
    description_layout.addWidget(make_body_text(introduction, description_panel))
    if detail_text and detail_text != introduction:
        description_layout.addWidget(make_meta_text(detail_text, description_panel))
    view.content_layout.addWidget(description_panel)

    view.content_layout.addStretch(1)
