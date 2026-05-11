from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextDocument
from PyQt6.QtWidgets import QLabel

from pocket_app.resources import tr

from ..view_helpers import BasePageView, first_text
from .common import add_detail_header


def render_game_doc_detail(
    view: BasePageView,
    detail: dict[str, Any],
    on_back: Callable[[], None],
) -> None:
    title = first_text(detail, "name", default=tr("game_docs.doc_default"))
    add_detail_header(view, title, "", on_back)

    content_panel, content_layout = view.build_panel("pageCard")
    content = first_text(detail, "content", "detail", "body", default="-")
    content_label = QLabel(content_panel)
    content_label.setObjectName("bodyText")
    content_label.setWordWrap(True)
    content_label.setTextFormat(Qt.TextFormat.RichText)
    content_label.setTextInteractionFlags(
        Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.LinksAccessibleByMouse
    )
    content_label.setText(_render_markdown(content))
    content_label.setOpenExternalLinks(True)
    content_layout.addWidget(content_label)
    view.content_layout.addWidget(content_panel)

    view.content_layout.addStretch(1)


def _render_markdown(content: str) -> str:
    if not content.strip():
        return "-"
    document = QTextDocument()
    document.setDocumentMargin(0)
    document.setMarkdown(content)
    return document.toHtml()
