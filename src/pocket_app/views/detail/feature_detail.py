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

    summary_panel, summary_layout = view.build_panel("pageCard")
    summary_layout.addWidget(make_meta_text(f"ID: {detail.get('id', '-')}", summary_panel))
    view.content_layout.addWidget(summary_panel)

    content_panel, content_layout = view.build_panel("pageCard")
    content_layout.addWidget(make_body_text(first_text(detail, "detail", default="-"), content_panel))
    view.content_layout.addWidget(content_panel)
    view.content_layout.addStretch(1)
