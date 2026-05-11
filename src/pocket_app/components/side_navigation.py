from dataclasses import dataclass, field

from PyQt6.QtGui import QFontMetrics, QIcon, QPaintEvent, QPainter, QTransform
from PyQt6.QtWidgets import (
    QFrame,
    QPushButton,
    QScrollArea,
    QStyle,
    QStyleOptionButton,
    QStylePainter,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal

from pocket_app.resources import Icons, Qss, ThemeManager, load_qss


@dataclass
class SideNavigationItemModel:
    id_: int
    name: str
    tip: str
    children: list["SideNavigationItemModel"] = field(default_factory=list)
    icon: str = ""
    expandable: bool = False


class SideNavigationItemButton(QPushButton):
    ICON_SIZE = 16
    HORIZONTAL_GAP = 8
    RIGHT_PADDING = 8
    LEFT_PADDING = 8

    def __init__(self, text: str = "", indent: int = 0, parent: QWidget | None = None):
        super().__init__(text, parent)
        self._indent = indent
        self._left_icon_path = Icons.navigation_item
        self._fold_icon_path = Icons.fold_chevron
        self._show_fold_icon = False
        self._is_folded = True

        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_indent(self, pixels: int) -> None:
        self._indent = pixels
        self.update()

    def set_left_icon(self, icon_path: str) -> None:
        self._left_icon_path = icon_path
        self.update()

    def set_fold_icon_visible(self, visible: bool) -> None:
        self._show_fold_icon = visible
        self.update()

    def set_folded(self, folded: bool) -> None:
        self._is_folded = folded
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # type: ignore
        option = QStyleOptionButton()
        self.initStyleOption(option)
        option.text = ""

        painter = QStylePainter(self)
        painter.drawControl(QStyle.ControlElement.CE_PushButton, option)

        painter.setPen(self.palette().buttonText().color())
        font_metrics = QFontMetrics(self.font())

        text_left = self._indent + self.LEFT_PADDING
        text_left = self._draw_left_icon(painter, text_left)
        right_padding = self.RIGHT_PADDING
        right_padding = self._draw_fold_icon(painter, right_padding)

        text_rect = self.rect().adjusted(text_left, 0, -right_padding, 0)
        text = font_metrics.elidedText(
            self.text(), Qt.TextElideMode.ElideRight, text_rect.width()
        )
        painter.drawText(
            text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text
        )
        event.accept()

    def _draw_left_icon(self, painter: QPainter, start_x: int) -> int:
        icon = QIcon(self._left_icon_path)
        if icon.isNull():
            return start_x

        icon_rect_top = max(0, (self.height() - self.ICON_SIZE) // 2)
        icon_rect = self.rect().adjusted(
            start_x,
            icon_rect_top,
            -(self.width() - start_x - self.ICON_SIZE),
            -(self.height() - icon_rect_top - self.ICON_SIZE),
        )
        icon.paint(painter, icon_rect, Qt.AlignmentFlag.AlignCenter)
        return start_x + self.ICON_SIZE + self.HORIZONTAL_GAP

    def _draw_fold_icon(self, painter: QPainter, right_padding: int) -> int:
        if not self._show_fold_icon:
            return right_padding

        icon = QIcon(self._fold_icon_path)
        if icon.isNull():
            return right_padding

        pixmap = icon.pixmap(self.ICON_SIZE, self.ICON_SIZE)
        if not self._is_folded:
            pixmap = pixmap.transformed(QTransform().rotate(90))

        icon_x = self.width() - right_padding - self.ICON_SIZE
        icon_y = max(0, (self.height() - self.ICON_SIZE) // 2)
        painter.drawPixmap(icon_x, icon_y, pixmap)
        return right_padding + self.ICON_SIZE + self.HORIZONTAL_GAP


class SideNavigationItem(QWidget):
    INDENT = 20

    def __init__(
        self,
        model: SideNavigationItemModel,
        depth: int = 0,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._model = model
        self._depth = depth
        self._children: list[SideNavigationItem] = []
        self._is_folded = bool(model.children) or model.expandable
        self._selected = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.button = SideNavigationItemButton(
            self._model.tip, indent=self._depth * self.INDENT + 8
        )
        if self._model.icon:
            self.button.set_left_icon(self._model.icon)
        self.button.set_fold_icon_visible(bool(self._model.children) or self._model.expandable)
        self.button.set_folded(self._is_folded)
        self._refresh_active_state()
        self.main_layout.addWidget(self.button)

        if self._model.children or self._model.expandable:
            self.button.clicked.connect(self.toggle_fold)

    def add_child(self, child_widget: "SideNavigationItem") -> None:
        self._children.append(child_widget)
        child_widget.setVisible(not self._is_folded)
        self.main_layout.addWidget(child_widget)

    def toggle_fold(self) -> None:
        self._is_folded = not self._is_folded
        self.button.set_folded(self._is_folded)
        self._refresh_active_state()
        self._update_fold_state()

    def fold(self) -> None:
        self._is_folded = True
        self.button.set_folded(self._is_folded)
        self._refresh_active_state()
        self._update_fold_state()

    def unfold(self) -> None:
        self._is_folded = False
        self.button.set_folded(self._is_folded)
        self._refresh_active_state()
        self._update_fold_state()

    def _update_fold_state(self) -> None:
        for child in self._children:
            child.setVisible(not self._is_folded)

    def _set_button_active(self, active: bool) -> None:
        self.button.setProperty("active", active)
        s = self.button.style()
        if not s is None:
            s.unpolish(self.button)
            s.polish(self.button)
        self.button.update()

    def set_active(self, active: bool) -> None:
        self._selected = active
        self._refresh_active_state()

    def _refresh_active_state(self) -> None:
        if self._model.children or self._model.expandable:
            self._set_button_active(False)
            return

        self._set_button_active(self._selected)

    @property
    def is_folded(self) -> bool:
        return self._is_folded

    @property
    def model(self) -> SideNavigationItemModel:
        return self._model


class SideNavigation(QFrame):
    selected = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._active_leaf_item: SideNavigationItem | None = None
        ThemeManager.theme_changed.connect(self._on_theme_changed)
        self._setup_ui()

    def _setup_ui(self) -> None:
        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._root_layout.setSpacing(0)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        self._content_widget = QWidget(self.scroll_area)
        self.main_layout = QVBoxLayout(self._content_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(self._content_widget)
        self._root_layout.addWidget(self.scroll_area, 1)

        self._bottom_widget = QWidget(self)
        self.bottom_layout = QVBoxLayout(self._bottom_widget)
        self.bottom_layout.setContentsMargins(0, 10, 0, 0)
        self.bottom_layout.setSpacing(0)
        self.bottom_layout.setAlignment(Qt.AlignmentFlag.AlignBottom)
        self._root_layout.addWidget(self._bottom_widget)

        self.setStyleSheet(load_qss(Qss.s_side_navigation))

    def add_item(
        self,
        item: SideNavigationItemModel,
        parent_item: SideNavigationItem | None = None,
        depth: int = 0,
        *,
        bottom: bool = False,
    ) -> SideNavigationItem:
        nav_item = SideNavigationItem(item, depth, self)

        if not item.children and not item.expandable:
            nav_item.button.clicked.connect(
                lambda clicked=False, current_item=nav_item: self._set_active_leaf_item(
                    current_item
                )
            )
            nav_item.button.clicked.connect(
                lambda clicked=False, name=item.name: self.selected.emit(name)
            )

        if parent_item is not None:
            parent_item.add_child(nav_item)
        elif bottom:
            self.bottom_layout.addWidget(nav_item)
        else:
            self.main_layout.addWidget(nav_item)

        for child in item.children:
            self.add_item(child, nav_item, depth + 1)

        return nav_item

    def add_item_by_json(self, json: str) -> None:
        pass

    def clear_items(self) -> None:
        self._active_leaf_item = None
        for layout in (self.main_layout, self.bottom_layout):
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

    def _set_active_leaf_item(self, item: SideNavigationItem) -> None:
        if self._active_leaf_item is item:
            item.set_active(True)
            return

        if self._active_leaf_item is not None:
            self._active_leaf_item.set_active(False)

        self._active_leaf_item = item
        self._active_leaf_item.set_active(True)

    def _on_theme_changed(self, _theme: str) -> None:
        self.setStyleSheet(load_qss(Qss.s_side_navigation))
