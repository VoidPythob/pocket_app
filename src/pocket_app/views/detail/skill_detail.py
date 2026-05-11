from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PyQt6.QtWidgets import QLabel

from pocket_app.resources import tr

from ..view_helpers import BasePageView, first_text, make_body_text
from .common import add_detail_header


def render_skill_detail(
    view: BasePageView,
    detail: dict[str, Any],
    on_back: Callable[[], None],
) -> None:
    title = first_text(detail, "name", "introduction", default=tr("skills.fallback"))
    add_detail_header(view, title, "", on_back)

    summary_panel, summary_layout = view.build_panel("pageCard")
    title_label = QLabel(f"{title} | ID: {detail.get('id', '-')}", summary_panel)
    title_label.setObjectName("resourceTitle")
    summary_layout.addWidget(title_label)
    summary_layout.addWidget(
        make_body_text(first_text(detail, "detail", default="-"), summary_panel)
    )
    view.content_layout.addWidget(summary_panel)
    view.content_layout.addStretch(1)
