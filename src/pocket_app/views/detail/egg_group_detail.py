from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pocket_app.components import PetCard
from pocket_app.resources import tr

from ..view_helpers import BasePageView, extract_list, first_text
from .common import add_detail_header, add_field_panel


def render_egg_group_detail(
    view: BasePageView,
    data: dict[str, Any],
    on_back: Callable[[], None],
) -> None:
    detail = data.get("detail") if isinstance(data.get("detail"), dict) else {}
    pets = extract_list(data.get("pets"))

    title = first_text(detail, "name", default=tr("egg_groups.group_default"))
    subtitle = tr("egg_groups.loaded_pets", count=len(pets), group_id=detail.get("id", "-"))
    add_detail_header(view, title, subtitle, on_back)

    add_field_panel(
        view,
        tr("detail.summary"),
        [
            ("ID", detail.get("id")),
            (tr("detail.name"), first_text(detail, "name", default="")),
        ],
    )

    cards_panel, cards_layout = view.build_grid_panel("cardCollectionPanel")
    for index, pet in enumerate(pets):
        card = PetCard(pet, parent=view.content_widget, image_size=40, clickable=True)
        if hasattr(view, "_open_pet_detail"):
            card.clicked.connect(view._open_pet_detail)  # type: ignore[attr-defined]
        cards_layout.addWidget(card, index // 3, index % 3)
    view.content_layout.addWidget(cards_panel)
    view.content_layout.addStretch(1)
