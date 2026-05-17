from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget

from pocket_app.resources import I18nManager, Icons, Qss, ThemeManager, load_qss, tr

from .icon_button import IconButton


class PaginationBar(QFrame):
    page_changed = pyqtSignal(int)

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        current_page: int = 1,
        total_pages: int = 1,
        max_visible: int = 7,
    ) -> None:
        super().__init__(parent)
        self._current_page = max(1, current_page)
        self._total_pages = max(1, total_pages)
        self._max_visible = max(5, max_visible)
        ThemeManager.theme_changed.connect(self._on_theme_changed)
        I18nManager.language_changed.connect(self._on_language_changed)
        self._setup_ui()
        self._refresh()

    def _setup_ui(self) -> None:
        self.setObjectName("paginationBar")
        self._apply_style()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._prev_button = IconButton(
            Icons.back_arrow,
            parent=self,
            tooltip=tr("pagination.previous"),
            button_size=32,
            icon_size=16,
        )
        self._prev_button.clicked.connect(self._go_prev)
        layout.addWidget(self._prev_button, 0, Qt.AlignmentFlag.AlignVCenter)

        self._pages_host = QWidget(self)
        self._pages_layout = QHBoxLayout(self._pages_host)
        self._pages_layout.setContentsMargins(0, 0, 0, 0)
        self._pages_layout.setSpacing(6)
        layout.addWidget(self._pages_host, 0, Qt.AlignmentFlag.AlignVCenter)

        self._next_button = IconButton(
            Icons.fold_chevron,
            parent=self,
            tooltip=tr("pagination.next"),
            button_size=32,
            icon_size=16,
        )
        self._next_button.clicked.connect(self._go_next)
        layout.addWidget(self._next_button, 0, Qt.AlignmentFlag.AlignVCenter)

        self._info_label = QLabel(self)
        self._info_label.setObjectName("paginationInfo")
        layout.addWidget(self._info_label, 0, Qt.AlignmentFlag.AlignVCenter)

    def set_state(self, current_page: int, total_pages: int) -> None:
        self._total_pages = max(1, total_pages)
        self._current_page = min(max(1, current_page), self._total_pages)
        self._refresh()

    def set_total_pages(self, total_pages: int) -> None:
        self.set_state(self._current_page, total_pages)

    def set_current_page(self, current_page: int) -> None:
        self.set_state(current_page, self._total_pages)

    def current_page(self) -> int:
        return self._current_page

    def total_pages(self) -> int:
        return self._total_pages

    def _go_prev(self) -> None:
        self._change_page(self._current_page - 1)

    def _go_next(self) -> None:
        self._change_page(self._current_page + 1)

    def _change_page(self, page: int) -> None:
        page = min(max(1, page), self._total_pages)
        if page == self._current_page:
            return
        self._current_page = page
        self._refresh()
        self.page_changed.emit(page)

    def _refresh(self) -> None:
        self._prev_button.setEnabled(self._current_page > 1)
        self._next_button.setEnabled(self._current_page < self._total_pages)
        self._prev_button.setToolTip(tr("pagination.previous"))
        self._next_button.setToolTip(tr("pagination.next"))
        self._info_label.setText(f"{self._current_page} / {self._total_pages}")
        self._rebuild_page_buttons()

    def _rebuild_page_buttons(self) -> None:
        while self._pages_layout.count():
            item = self._pages_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for item in self._visible_items():
            if isinstance(item, int):
                button = QPushButton(str(item), self._pages_host)
                button.setObjectName("paginationPageButton")
                button.setCursor(Qt.CursorShape.PointingHandCursor)
                button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                button.setFixedSize(34, 32)
                button.setProperty("selected", item == self._current_page)
                button.clicked.connect(
                    lambda checked=False, current=item: self._change_page(current)
                )
                self._pages_layout.addWidget(button)
                continue

            label = QLabel(str(item), self._pages_host)
            label.setObjectName("paginationEllipsis")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFixedWidth(18)
            self._pages_layout.addWidget(label)

    def _visible_items(self) -> list[int | str]:
        if self._total_pages <= self._max_visible:
            return list(range(1, self._total_pages + 1))

        if self._current_page <= 4:
            return [1, 2, 3, 4, 5, "...", self._total_pages]
        if self._current_page >= self._total_pages - 3:
            return [
                1,
                "...",
                self._total_pages - 4,
                self._total_pages - 3,
                self._total_pages - 2,
                self._total_pages - 1,
                self._total_pages,
            ]
        return [
            1,
            "...",
            self._current_page - 1,
            self._current_page,
            self._current_page + 1,
            "...",
            self._total_pages,
        ]

    def _apply_style(self) -> None:
        self.setStyleSheet(load_qss(Qss.s_pagination))

    def _on_theme_changed(self, _theme: str) -> None:
        self._apply_style()

    def _on_language_changed(self, _locale: str) -> None:
        self._refresh()


def create_pagination(
    *,
    current_page: int = 1,
    total_pages: int = 1,
    max_visible: int = 7,
    parent: QWidget | None = None,
) -> PaginationBar:
    return PaginationBar(
        parent=parent,
        current_page=current_page,
        total_pages=total_pages,
        max_visible=max_visible,
    )
