from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QPointF, QRectF, QSize, Qt, pyqtProperty
from PyQt6.QtGui import QColor, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import QSizePolicy, QWidget

from pocket_app.resources import Qss, ThemeManager


class StatRadar(QWidget):
    STAT_KEYS = (
        ("hp", "HP"),
        ("attack", "ATK"),
        ("defense", "DEF"),
        ("special_attack", "SPA"),
        ("special_defense", "SPD"),
        ("speed", "SPE"),
    )

    def __init__(
        self,
        stats: Mapping[str, Any] | None = None,
        parent: QWidget | None = None,
        *,
        max_value: int = 255,
        animation_duration: int = 420,
        center_text_mode: str = "full",
    ) -> None:
        super().__init__(parent)
        self._max_value = max(1, max_value)
        self._progress = 0.0
        self._stats: dict[str, int | None] = {key: None for key, _label in self.STAT_KEYS}
        self._total: int | None = None
        self._name = ""
        self._center_text_mode = center_text_mode
        self._grid_color = QColor("#bccde0")
        self._axis_color = QColor("#61748b")
        self._line_color = QColor("#8fb3e8")
        self._fill_color = QColor("#8fb3e8")
        self._label_color = QColor("#21344d")
        self._center_color = QColor("#61748b")
        self._node_color = QColor("#6f9ddd")

        self._animation = QPropertyAnimation(self, b"progress", self)
        self._animation.setDuration(animation_duration)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.setMinimumSize(260, 260)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        ThemeManager.theme_changed.connect(self._on_theme_changed)
        self._apply_palette()
        if stats:
            self.set_stats(stats, animate=False)

    def sizeHint(self) -> QSize:  # type: ignore[override]
        return QSize(300, 300)

    def set_stats(self, stats: Mapping[str, Any], *, animate: bool = True) -> None:
        self._name = str(stats.get("name", "") or "").strip()
        for key, _label in self.STAT_KEYS:
            self._stats[key] = _to_int(stats.get(key))
        self._total = _to_int(stats.get("total"))
        if self._total is None:
            values = [value for value in self._stats.values() if value is not None]
            self._total = sum(values) if values else None
        if animate:
            self._animation.stop()
            self._progress = 0.0
            self._animation.setStartValue(0.0)
            self._animation.setEndValue(1.0)
            self._animation.start()
        else:
            self._progress = 1.0
        self.update()

    def set_center_text_mode(self, mode: str) -> None:
        self._center_text_mode = mode
        self.update()

    def total(self) -> int | None:
        return self._total

    def get_progress(self) -> float:
        return self._progress

    def set_progress(self, value: float) -> None:
        self._progress = max(0.0, min(1.0, float(value)))
        self.update()

    progress = pyqtProperty(float, fget=get_progress, fset=set_progress)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        rect = self.rect().adjusted(16, 16, -16, -16)
        chart_rect = rect.adjusted(48, 36, -48, -50)
        if chart_rect.width() <= 0 or chart_rect.height() <= 0:
            return

        center = QPointF(chart_rect.center())
        radius = min(chart_rect.width(), chart_rect.height()) * 0.5
        axis_points = [self._polar_point(center, radius, index) for index in range(len(self.STAT_KEYS))]

        painter.setPen(QPen(self._grid_color, 1))
        for level in range(1, 5):
            polygon = QPolygonF(
                [
                    self._polar_point(center, radius * (level / 4.0), index)
                    for index in range(len(self.STAT_KEYS))
                ]
            )
            painter.drawPolygon(polygon)

        painter.setPen(QPen(self._axis_color, 1))
        for point in axis_points:
            painter.drawLine(center, point)

        data_polygon = QPolygonF()
        for index, (key, _label) in enumerate(self.STAT_KEYS):
            value = self._stats.get(key) or 0
            ratio = min(max(value / self._max_value, 0.0), 1.0) * self._progress
            data_polygon.append(self._polar_point(center, radius * ratio, index))

        painter.setPen(QPen(self._line_color, 2))
        painter.setBrush(self._fill_color)
        painter.drawPolygon(data_polygon)

        painter.setBrush(self._node_color)
        painter.setPen(Qt.PenStyle.NoPen)
        for point in data_polygon:
            painter.drawEllipse(point, 4.0, 4.0)

        painter.setPen(self._label_color)
        for index, (_key, label) in enumerate(self.STAT_KEYS):
            value = self._stats[self.STAT_KEYS[index][0]]
            self._draw_axis_label(
                painter,
                self._polar_point(center, radius + 28, index),
                f"{label}\n{value if value is not None else '-'}",
            )

        center_text = self._center_text()
        if center_text:
            painter.setPen(self._center_color)
            painter.drawText(
                QRectF(center.x() - 56, center.y() - 28, 112, 56),
                Qt.AlignmentFlag.AlignCenter,
                center_text,
            )

    def _apply_palette(self) -> None:
        variables = Qss.variables
        self._grid_color = QColor(variables.get("panel_border", "#bccde0"))
        self._grid_color.setAlpha(130)
        self._axis_color = QColor(variables.get("body_text_color", "#61748b"))
        self._axis_color.setAlpha(150)
        self._line_color = QColor(variables.get("icon_button_hover_border", "#8fb3e8"))
        self._fill_color = QColor(self._line_color)
        self._fill_color.setAlpha(80)
        self._node_color = QColor(variables.get("icon_button_pressed_border", "#6f9ddd"))
        self._label_color = QColor(variables.get("section_title_color", "#21344d"))
        self._center_color = QColor(variables.get("body_text_color", "#61748b"))
        self.update()

    def _draw_axis_label(self, painter: QPainter, center: QPointF, text: str) -> None:
        painter.drawText(
            QRectF(center.x() - 34, center.y() - 20, 68, 40),
            Qt.AlignmentFlag.AlignCenter,
            text,
        )

    def _center_text(self) -> str:
        if self._center_text_mode == "none":
            return ""
        if self._center_text_mode == "total":
            return f"TOTAL\n{self._total if self._total is not None else '-'}"
        center_text = f"TOTAL\n{self._total if self._total is not None else '-'}"
        if self._name:
            center_text = f"{self._name}\n{center_text}"
        return center_text

    def _polar_point(self, center: QPointF, radius: float, index: int) -> QPointF:
        angle = math.radians(-90 + index * (360 / len(self.STAT_KEYS)))
        return QPointF(
            center.x() + math.cos(angle) * radius,
            center.y() + math.sin(angle) * radius,
        )

    def _on_theme_changed(self, _theme: str) -> None:
        self._apply_palette()


def create_stat_radar(
    stats: Mapping[str, Any] | None = None,
    *,
    parent: QWidget | None = None,
    max_value: int = 255,
    animation_duration: int = 420,
    center_text_mode: str = "full",
) -> StatRadar:
    return StatRadar(
        stats=stats,
        parent=parent,
        max_value=max_value,
        animation_duration=animation_duration,
        center_text_mode=center_text_mode,
    )


def _to_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if text.isdigit():
            return int(text)
    return None
