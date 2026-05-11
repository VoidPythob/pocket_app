from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pocket_app.resources import tr

from ..view_helpers import BasePageView, first_text, make_body_text, make_meta_text
from .common import add_detail_header


def render_feature_detail(
    view: BasePageView,
    detail: dict[str, Any],
    on_back: Callable[[], None],
) -> None:
    title = first_text(detail, "name", "introduction", default=tr("features.fallback"))
    add_detail_header(view, title, "", on_back)

    name_panel, name_layout = view.build_panel("pageCard")
    name_layout.addWidget(make_meta_text(f"ID: {detail.get('id', '-')}", name_panel))
    jp_name = first_text(detail, "jp_name", default="")
    en_name = first_text(detail, "en_name", default="")
    if jp_name:
        name_layout.addWidget(make_meta_text(f"JP: {jp_name}", name_panel))
    if en_name:
        name_layout.addWidget(make_meta_text(f"EN: {en_name}", name_panel))
    view.content_layout.addWidget(name_panel)

    content_panel, content_layout = view.build_panel("pageCard")
    introduction = first_text(detail, "introduction", default="-")
    detail_text = first_text(detail, "detail", default="")
    content_layout.addWidget(make_body_text(introduction, content_panel))
    if detail_text and detail_text != introduction:
        content_layout.addWidget(make_meta_text(detail_text, content_panel))
    view.content_layout.addWidget(content_panel)
    view.content_layout.addStretch(1)
