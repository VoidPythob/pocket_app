from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from pocket_app.api import cancel_api_tasks, submit_api_task
from pocket_app.components import LoadingPlaceholder, PaginationBar
from pocket_app.resources import tr

LIST_PAGE_SIZE = 9


def clear_layout(layout: QLayout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        child_layout = item.layout()
        child_widget = item.widget()
        if child_layout is not None:
            clear_layout(child_layout)
        if child_widget is not None:
            child_widget.deleteLater()


def extract_list(data: Any, *keys: str) -> list[Any]:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in keys:
            value = data.get(key)
            if isinstance(value, list):
                return value
        for key in ("results", "items", "list", "rows", "records", "pets", "docs"):
            value = data.get(key)
            if isinstance(value, list):
                return value
    return []


def extract_count(data: Any) -> int:
    if isinstance(data, dict):
        count = data.get("count")
        if isinstance(count, int):
            return count
    return len(extract_list(data))


def paginate_rows(
    rows: list[Any],
    current_page: int,
    *,
    page_size: int = LIST_PAGE_SIZE,
) -> tuple[list[Any], int, int]:
    if page_size <= 0:
        return rows, 1, 1
    total_count = len(rows)
    if total_count <= 0:
        return [], 1, 1
    total_pages = max(1, (total_count + page_size - 1) // page_size)
    normalized_page = min(max(1, current_page), total_pages)
    start = (normalized_page - 1) * page_size
    end = start + page_size
    return rows[start:end], normalized_page, total_pages


def normalize_names(values: Any) -> list[str]:
    items = extract_list(values)
    if not items and isinstance(values, list):
        items = values
    names: list[str] = []
    for item in items:
        if isinstance(item, str):
            names.append(item)
        elif isinstance(item, dict):
            for key in ("name", "introduction", "title", "tip"):
                value = item.get(key)
                if isinstance(value, str) and value.strip():
                    names.append(value.strip())
                    break
        elif item is not None:
            names.append(str(item))
    return names


def first_text(data: dict[str, Any], *keys: str, default: str = "-") -> str:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if value is not None and not isinstance(value, (dict, list)):
            return str(value)
    return default


def add_pagination(
    layout: QVBoxLayout,
    parent: QWidget,
    *,
    current_page: int,
    total_pages: int,
    on_page_changed: Callable[[int], None],
) -> PaginationBar:
    pagination = PaginationBar(
        parent=parent,
        current_page=current_page,
        total_pages=total_pages,
    )
    pagination.page_changed.connect(on_page_changed)
    layout.addWidget(pagination)
    layout.addSpacing(20)
    return pagination


class ClickableFrame(QFrame):
    clicked = pyqtSignal()

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            event.accept()
            return
        super().mousePressEvent(event)


class BasePageView(QScrollArea):
    page_title_key = "page.generic.title"
    page_description_key = "page.generic.description"
    search_placeholder_key = "search.default"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._search_text = ""
        self._request_tokens: dict[str, int] = {}
        self._has_loaded = False
        self._last_data: Any = None

        self.setObjectName("contentScrollArea")
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.content_widget = QWidget(self)
        self.content_widget.setObjectName("contentScrollWidget")
        self.setWidget(self.content_widget)

        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(16)

    def set_search_text(self, text: str) -> None:
        normalized = text.strip()
        if normalized == self._search_text:
            return
        self._search_text = normalized
        if self._has_loaded:
            self.refresh()

    def refresh(self) -> None:
        self._has_loaded = True
        self.show_loading()
        self._start_async_load("page", self.fetch_data, self.render_data)

    def rerender_last(self) -> None:
        if self._last_data is None:
            return
        self.render_data(self._last_data)

    def reset_filters(self) -> None:
        return

    async def fetch_data(self) -> Any:
        raise NotImplementedError

    def render_data(self, data: Any) -> None:
        raise NotImplementedError

    def show_loading(
        self,
        title: str | None = None,
        desc: str | None = None,
    ) -> None:
        clear_layout(self.content_layout)
        loading_placeholder = LoadingPlaceholder(self.content_widget)
        loading_placeholder.set_loading(
            title or tr("loading.title"),
            desc or tr("loading.desc"),
        )
        self.content_layout.addStretch(1)
        self.content_layout.addWidget(loading_placeholder)
        self.content_layout.addStretch(1)

    def show_error(self, message: str) -> None:
        clear_layout(self.content_layout)
        loading_placeholder = LoadingPlaceholder(self.content_widget)
        loading_placeholder.set_error(
            title=tr("loading.error_title"),
            desc=message or tr("loading.error_desc"),
        )
        loading_placeholder.retry_requested.connect(self.refresh)
        self.content_layout.addStretch(1)
        self.content_layout.addWidget(loading_placeholder)
        self.content_layout.addStretch(1)

    def build_panel(
        self,
        object_name: str = "pageCard",
        margins: tuple[int, int, int, int] = (20, 18, 20, 18),
        spacing: int = 12,
    ) -> tuple[QFrame, QVBoxLayout]:
        panel = QFrame(self.content_widget)
        panel.setObjectName(object_name)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(*margins)
        layout.setSpacing(spacing)
        return panel, layout

    def build_grid_panel(
        self,
        object_name: str = "pageCard",
        margins: tuple[int, int, int, int] = (20, 18, 20, 18),
        h_spacing: int = 14,
        v_spacing: int = 14,
    ) -> tuple[QFrame, QGridLayout]:
        panel = QFrame(self.content_widget)
        panel.setObjectName(object_name)
        layout = QGridLayout(panel)
        layout.setContentsMargins(*margins)
        layout.setHorizontalSpacing(h_spacing)
        layout.setVerticalSpacing(v_spacing)
        for column in range(3):
            layout.setColumnStretch(column, 1)
        return panel, layout

    def _start_async_load(
        self,
        channel: str,
        task_factory: Callable[[], Awaitable[Any]],
        on_success: Callable[[Any], None],
        on_failure: Callable[[str], None] | None = None,
    ) -> None:
        token = self._request_tokens.get(channel, 0) + 1
        self._request_tokens[channel] = token
        submit_api_task(
            self,
            task_factory,
            lambda data, current=token, current_channel=channel: self._handle_success(
                current_channel, current, data, on_success
            ),
            lambda message, current=token, current_channel=channel: self._handle_failure(
                current_channel, current, message, on_failure
            ),
        )

    def _handle_success(
        self,
        channel: str,
        token: int,
        data: Any,
        on_success: Callable[[Any], None],
    ) -> None:
        if token != self._request_tokens.get(channel):
            return
        if channel == "page":
            self._last_data = data
        on_success(data)

    def _handle_failure(
        self,
        channel: str,
        token: int,
        message: str,
        on_failure: Callable[[str], None] | None = None,
    ) -> None:
        if token != self._request_tokens.get(channel):
            return
        if on_failure is not None:
            on_failure(message or "Unable to fetch data.")
            return
        self.show_error(message or "Unable to fetch data.")

    @property
    def has_loaded(self) -> bool:
        return self._has_loaded

    @property
    def search_text(self) -> str:
        return self._search_text

    @property
    def page_title(self) -> str:
        return tr(self.page_title_key)

    @property
    def page_description(self) -> str:
        return tr(self.page_description_key)

    @property
    def search_placeholder(self) -> str:
        return tr(self.search_placeholder_key)

    def closeEvent(self, event: QCloseEvent) -> None:
        cancel_api_tasks(self)
        super().closeEvent(event)


def make_section_title(text: str, parent: QWidget) -> QLabel:
    label = QLabel(text, parent)
    label.setObjectName("sectionTitle")
    return label


def make_body_text(text: str, parent: QWidget) -> QLabel:
    label = QLabel(text, parent)
    label.setObjectName("bodyText")
    label.setWordWrap(True)
    return label


def make_meta_text(text: str, parent: QWidget) -> QLabel:
    label = QLabel(text, parent)
    label.setObjectName("metaText")
    label.setWordWrap(True)
    return label


def make_metric_card(title: str, value: str, desc: str, parent: QWidget) -> QFrame:
    card = QFrame(parent)
    card.setObjectName("metricCard")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(18, 16, 18, 16)
    layout.setSpacing(6)

    value_label = QLabel(value, card)
    value_label.setObjectName("metricValue")
    title_label = QLabel(title, card)
    title_label.setObjectName("metricTitle")
    desc_label = make_body_text(desc, card)

    layout.addWidget(value_label)
    layout.addWidget(title_label)
    layout.addWidget(desc_label)
    return card
