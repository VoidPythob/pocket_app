from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from pocket_app import api
from pocket_app.components.network_image import RoundedNetworkImage
from pocket_app.components.tag import Tag
from pocket_app.resources import tr


def _first_text(data: dict[str, Any], *keys: str, default: str = "-") -> str:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if value is not None and not isinstance(value, (dict, list)):
            return str(value)
    return default


def _extract_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("results", "items", "list", "rows", "records", "pets", "docs"):
            nested = value.get(key)
            if isinstance(nested, list):
                return nested
    return []


def _normalize_names(values: Iterable[Any]) -> list[str]:
    names: list[str] = []
    for item in values:
        if isinstance(item, str):
            if item.strip():
                names.append(item.strip())
        elif isinstance(item, dict):
            for key in ("name", "introduction", "title", "tip"):
                value = item.get(key)
                if isinstance(value, str) and value.strip():
                    names.append(value.strip())
                    break
        elif item is not None:
            names.append(str(item))
    return names


def _failed_image_text(data: dict[str, Any]) -> str:
    en_name = _first_text(data, "en_name", default="")
    for char in en_name.strip():
        if char.isascii() and char.isalnum():
            return char.upper()
    return tr("image.empty")


def _resolve_image_url(data: dict[str, Any]) -> str:
    raw_url = _first_text(data, "first_image_url", default="")
    if not raw_url:
        return ""
    normalized = raw_url.strip()
    if normalized.startswith(("http://", "https://", "data:")):
        return normalized
    return api.get_file_url(normalized)


class PetCard(QFrame):
    TAG_WIDTH = 72

    clicked = pyqtSignal(object)

    def __init__(
        self,
        pet: dict[str, Any] | None = None,
        *,
        parent: QWidget | None = None,
        image_size: int = 40,
        clickable: bool = False,
    ) -> None:
        super().__init__(parent)
        self._pet: dict[str, Any] = {}
        self._clickable = clickable
        self._image_size = image_size

        self.setObjectName("petCard")
        self._build_ui()
        if pet is not None:
            self.set_pet(pet)
        self._apply_clickable()

    def _build_ui(self) -> None:
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(18, 16, 18, 16)
        self._layout.setSpacing(10)

        self._name_row = QHBoxLayout()
        self._name_row.setSpacing(8)
        self._name_row.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._icon = RoundedNetworkImage(
            parent=self,
            width=self._image_size,
            height=self._image_size,
            circular=True,
        )
        self._name_row.addWidget(self._icon, 0, Qt.AlignmentFlag.AlignVCenter)

        self._title_col = QVBoxLayout()
        self._title_col.setSpacing(4)
        self._title_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self._title_label = QLabel(self)
        self._title_label.setObjectName("resourceTitle")
        self._title_col.addWidget(self._title_label, 0, Qt.AlignmentFlag.AlignVCenter)
        self._meta_label = QLabel(self)
        self._meta_label.setObjectName("metaText")
        self._meta_label.setWordWrap(True)
        self._title_col.addWidget(self._meta_label, 0, Qt.AlignmentFlag.AlignVCenter)
        self._name_row.addLayout(self._title_col, 1)
        self._layout.addLayout(self._name_row)

        self._tag_host = QWidget(self)
        self._tag_host.setObjectName("petCardTagHost")
        self._tag_host.setStyleSheet("background: transparent; border: none;")
        self._tag_row = QHBoxLayout(self._tag_host)
        self._tag_row.setContentsMargins(0, 0, 0, 0)
        self._tag_row.setSpacing(6)
        self._layout.addWidget(self._tag_host)

        self._features_label = QLabel(self)
        self._features_label.setObjectName("bodyText")
        self._features_label.setWordWrap(True)
        self._layout.addWidget(self._features_label)

    def set_pet(self, pet: dict[str, Any]) -> None:
        self._pet = dict(pet)

        failed_text = _failed_image_text(self._pet)
        self._icon.set_placeholder_text(failed_text)
        self._icon.set_failed_text(failed_text)
        self._icon.set_url(_resolve_image_url(self._pet))

        self._title_label.setText(_first_text(self._pet, "name", "en_name", default=tr("common.unknown")))
        self._meta_label.setText(self._language_line())

        self._rebuild_tags()

        feature_names = _normalize_names(_extract_list(self._pet.get("features", [])))
        self._features_label.setVisible(bool(feature_names))
        if feature_names:
            self._features_label.setText(tr("pets.card.features", names=" / ".join(feature_names)))
        else:
            self._features_label.clear()

    def pet(self) -> dict[str, Any]:
        return dict(self._pet)

    def set_clickable(self, clickable: bool) -> None:
        self._clickable = clickable
        self._apply_clickable()

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if self._clickable and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._pet.get("id"))
            event.accept()
            return
        super().mousePressEvent(event)

    def _apply_clickable(self) -> None:
        self.setCursor(
            Qt.CursorShape.PointingHandCursor
            if self._clickable
            else Qt.CursorShape.ArrowCursor
        )

    def _rebuild_tags(self) -> None:
        while self._tag_row.count():
            item = self._tag_row.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        raw_tags = _extract_list(self._pet.get("tags", []))
        has_tags = False
        for raw_tag in raw_tags:
            tag_name = raw_tag if isinstance(raw_tag, str) else _first_text(raw_tag, "name", default="")
            if not tag_name:
                continue
            color = ""
            if isinstance(raw_tag, dict):
                color = _first_text(raw_tag, "color", default="")
            tag = Tag(tag_name, parent=self._tag_host, background_color=color)
            tag.setEnabled(False)
            tag.setFixedWidth(self.TAG_WIDTH)
            self._tag_row.addWidget(tag)
            has_tags = True

        self._tag_row.addStretch(1)
        self._tag_host.setVisible(has_tags)

    def _language_line(self) -> str:
        jp_name = _first_text(self._pet, "jp_name", default="")
        en_name = _first_text(self._pet, "en_name", default="")
        names = [value for value in (jp_name, en_name) if value and value != "-"]
        if names:
            return " | ".join(names)
        return tr("common.unknown")


def create_pet_card(
    pet: dict[str, Any] | None = None,
    *,
    parent: QWidget | None = None,
    image_size: int = 40,
    clickable: bool = False,
) -> PetCard:
    return PetCard(
        pet,
        parent=parent,
        image_size=image_size,
        clickable=clickable,
    )
