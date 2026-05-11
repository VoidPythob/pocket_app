from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout

from pocket_app.components import RoundedNetworkImage, StatRadar, Tag
from pocket_app.resources import tr

from ..view_helpers import BasePageView, extract_list, first_text, make_section_title
from .common import (
    add_detail_header,
    add_image_gallery,
    add_tag_panel,
    add_text_list_panel,
    collect_image_urls,
)


def render_pet_detail(
    view: BasePageView,
    data: dict[str, Any],
    on_back: Callable[[], None],
) -> None:
    detail = data.get("detail") if isinstance(data.get("detail"), dict) else {}
    features = data.get("features", [])
    capture_methods = data.get("capture_methods", [])

    title = first_text(detail, "name", "en_name", default=tr("common.pet"))
    subtitle = first_text(detail, "detail", "introduction", default=tr("pets.intro_desc"))
    add_detail_header(view, title, subtitle, on_back)
    en_name = first_text(detail, "en_name", "name", default=tr("common.unknown"))
    failed_text = en_name[:1].upper() if en_name and en_name != tr("common.unknown") else tr("image.empty")
    image_urls = collect_image_urls(detail)

    _add_basic_info_panel(view, detail, image_urls, failed_text)
    _add_rance_panels(view, detail)
    _add_clickable_skill_panel(view, detail.get("skills", []))
    _add_clickable_egg_group_panel(view, detail.get("egg_groups", []))
    add_tag_panel(view, tr("pets.detail.tags"), detail.get("tags", []))
    add_tag_panel(view, tr("pets.detail.features"), features or detail.get("features", []))

    add_text_list_panel(view, tr("pets.detail.capture_methods"), capture_methods)
    add_image_gallery(
        view,
        tr("pets.detail.images"),
        image_urls,
        failed_text=failed_text,
    )

    generations = extract_list(detail.get("generations"))
    if generations:
        add_text_list_panel(view, tr("pets.generation"), generations)

    view.content_layout.addStretch(1)


def _resolve_races(detail: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in extract_list(detail.get("rances")):
        if not isinstance(raw, dict):
            continue
        normalized = _normalize_race_stats(raw)
        if normalized:
            rows.append(normalized)
    if rows:
        return rows

    for key in ("rance", "race", "race_info", "stats"):
        value = detail.get(key)
        if isinstance(value, dict):
            normalized = _normalize_race_stats(value)
            return [normalized] if normalized else []

    normalized = _normalize_race_stats(detail)
    return [normalized] if normalized else []


def _normalize_race_stats(data: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        "name": first_text(data, "name", default=""),
        "hp": _first_number(data, "hp"),
        "attack": _first_number(data, "attack", "atk"),
        "defense": _first_number(data, "defense", "def"),
        "special_attack": _first_number(data, "special_attack", "sp_attack", "special_atk", "spa"),
        "special_defense": _first_number(data, "special_defense", "sp_defense", "special_def", "spd"),
        "speed": _first_number(data, "speed", "spe"),
        "total": _first_number(data, "total"),
    }
    if normalized["total"] is None:
        stat_values = [
            normalized["hp"],
            normalized["attack"],
            normalized["defense"],
            normalized["special_attack"],
            normalized["special_defense"],
            normalized["speed"],
        ]
        if any(value is not None for value in stat_values):
            normalized["total"] = sum(value or 0 for value in stat_values)
    if normalized["name"] or any(
        normalized[key] is not None
        for key in ("hp", "attack", "defense", "special_attack", "special_defense", "speed", "total")
    ):
        return normalized
    return {}


def _first_number(data: dict[str, Any], *keys: str) -> int | None:
    for key in keys:
        value = data.get(key)
        if isinstance(value, bool):
            continue
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            text = value.strip()
            if text.isdigit():
                return int(text)
    return None


def _format_gender_ratio(detail: dict[str, Any]) -> str:
    text = first_text(detail, "gender_ratio_display", default="")
    if not text:
        return ""
    return (
        text.replace("{woman}", tr("common.gender_woman"))
        .replace("{man}", tr("common.gender_man"))
        .strip()
    )


def _add_basic_info_panel(
    view: BasePageView,
    detail: dict[str, Any],
    image_urls: list[str],
    failed_text: str,
) -> None:
    panel, layout = view.build_panel("pageCard")
    title = tr("detail.basic_info")
    layout.addWidget(make_section_title(title if title != "detail.basic_info" else "基本信息", panel))

    row = QHBoxLayout()
    row.setSpacing(18)
    row.setAlignment(Qt.AlignmentFlag.AlignTop)

    hero_url = image_urls[0] if image_urls else ""
    hero_image = RoundedNetworkImage(
        hero_url,
        parent=panel,
        width=120,
        height=120,
        radius=24,
        failed_text=failed_text,
    )
    row.addWidget(hero_image, 0, Qt.AlignmentFlag.AlignTop)

    info_col = QVBoxLayout()
    info_col.setSpacing(8)
    for label, value in [
        ("ID", detail.get("id")),
        (tr("pets.generation"), detail.get("generation") or detail.get("generation_id")),
        (tr("common.gender_ratio"), _format_gender_ratio(detail)),
        ("JP", first_text(detail, "jp_name", default="")),
        ("EN", first_text(detail, "en_name", default="")),
    ]:
        text = str(value).strip() if value is not None else ""
        if not text:
            continue
        item = QLabel(f"{label}: {text}", panel)
        item.setObjectName("metaText")
        info_col.addWidget(item)
    info_col.addStretch(1)

    row.addLayout(info_col, 1)
    layout.addLayout(row)
    view.content_layout.addWidget(panel)


def _add_rance_panels(view: BasePageView, detail: dict[str, Any]) -> None:
    races = _resolve_races(detail)
    if not races:
        return

    for index, race in enumerate(races, start=1):
        panel, layout = view.build_panel("pageCard")
        layout.addWidget(make_section_title(tr("pets.detail.stats"), panel))

        radar = StatRadar(parent=panel, center_text_mode="none")
        layout.addWidget(radar, 0, Qt.AlignmentFlag.AlignCenter)
        radar.set_stats(race)
        total_label = QLabel(f"TOTAL: {radar.total() or '-'}", panel)
        total_label.setObjectName("resourceTitle")
        total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(total_label, 0, Qt.AlignmentFlag.AlignHCenter)
        view.content_layout.addWidget(panel)


def _add_clickable_egg_group_panel(view: BasePageView, values: Any) -> None:
    egg_groups = extract_list(values)
    if not egg_groups:
        return

    panel, layout = view.build_panel("pageCard")
    layout.addWidget(make_section_title(tr("pets.detail.egg_groups"), panel))

    row = QHBoxLayout()
    row.setSpacing(6)
    for raw in egg_groups:
        if not isinstance(raw, dict):
            continue
        egg_group_id = raw.get("id")
        if egg_group_id is None:
            continue
        text = first_text(raw, "name", default=tr("egg_groups.group_value", value=egg_group_id))
        color = first_text(raw, "color", default="")
        tag = Tag(text, parent=panel, background_color=color, tag_id=str(egg_group_id))
        tag.tag_clicked.connect(
            lambda _tag_id, current_id=egg_group_id: _navigate_to_egg_group(view, current_id)
        )
        row.addWidget(tag)
    row.addStretch(1)
    layout.addLayout(row)
    view.content_layout.addWidget(panel)


def _add_clickable_skill_panel(view: BasePageView, values: Any) -> None:
    skills = extract_list(values)
    if not skills:
        return

    panel, layout = view.build_panel("pageCard")
    layout.addWidget(make_section_title(tr("pets.detail.skills"), panel))

    row = QHBoxLayout()
    row.setSpacing(6)
    for raw in skills:
        if not isinstance(raw, dict):
            continue
        skill_id = raw.get("id")
        if skill_id is None:
            continue
        text = first_text(raw, "name", "introduction", default=tr("skills.fallback"))
        color = first_text(raw, "color", default="")
        tag = Tag(text, parent=panel, background_color=color, tag_id=str(skill_id))
        tag.tag_clicked.connect(
            lambda _tag_id, current_id=skill_id: _navigate_to_skill(view, current_id)
        )
        row.addWidget(tag)
    row.addStretch(1)
    layout.addLayout(row)
    view.content_layout.addWidget(panel)


def _navigate_to_egg_group(view: BasePageView, egg_group_id: int) -> None:
    central = view.window().centralWidget()
    route_name = f"egg_groups/group/{egg_group_id}"
    if central is not None and hasattr(central, "_show_page"):
        central._show_page(route_name)  # type: ignore[attr-defined]


def _navigate_to_skill(view: BasePageView, skill_id: int) -> None:
    central = view.window().centralWidget()
    if central is None or not hasattr(central, "_show_page"):
        return
    central._show_page("skills")  # type: ignore[attr-defined]
    page = getattr(central, "_pages", {}).get("skills")
    if page is None:
        return
    open_detail = getattr(page, "_open_detail", None)
    if callable(open_detail):
        open_detail(skill_id)
