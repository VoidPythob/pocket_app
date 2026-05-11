from __future__ import annotations

from PyQt6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QEvent,
    QObject,
    QPoint,
    QParallelAnimationGroup,
    QPropertyAnimation,
    Qt,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QColor,
    QHideEvent,
    QKeyEvent,
    QPaintEvent,
    QPainter,
    QPen,
    QShowEvent,
)
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsOpacityEffect,
    QVBoxLayout,
    QWidget,
)

from pocket_app.resources import Qss, ThemeManager, load_qss


class PopupPanel(QFrame):
    opened = pyqtSignal()
    closed = pyqtSignal()

    def __init__(
        self,
        *,
        offset_x: int = 0,
        offset_y: int = 8,
        match_anchor_width: bool = False,
    ) -> None:
        super().__init__(parent=None)
        self._anchor: QWidget | None = None
        self._host_widget: QWidget | None = None
        self._content_widget: QWidget | None = None
        self._offset = QPoint(offset_x, offset_y)
        self._match_anchor_width = match_anchor_width
        self._is_open = False
        self._is_hiding = False
        self._force_hide = False
        self._app_filter_bound = False
        self._final_pos = QPoint()
        self._hidden_pos = QPoint()
        self._anim_distance = 10
        self._content_padding = 12
        self._panel_background = QColor("#ffffff")
        self._panel_border = QColor("#dce5f0")

        self.setObjectName("popupPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.hide()

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(
            self._content_padding,
            self._content_padding,
            self._content_padding,
            self._content_padding,
        )
        self._layout.setSpacing(0)

        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_effect)

        self._opacity_anim = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        self._opacity_anim.setDuration(180)
        self._opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._pos_anim = QPropertyAnimation(self, b"pos", self)
        self._pos_anim.setDuration(180)
        self._pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._anim_group = QParallelAnimationGroup(self)
        self._anim_group.addAnimation(self._opacity_anim)
        self._anim_group.addAnimation(self._pos_anim)
        self._anim_group.finished.connect(self._on_animation_finished)

        ThemeManager.theme_changed.connect(self._on_theme_changed)
        self._apply_style()
        self._apply_palette()

    def set_content_widget(self, widget: QWidget | None) -> None:
        if self._content_widget is widget:
            return
        if self._content_widget is not None:
            self._layout.removeWidget(self._content_widget)
            self._content_widget.setParent(None)
        self._content_widget = widget
        if widget is not None:
            widget.setParent(self)
            self._layout.addWidget(widget)
        self.adjustSize()

    def content_widget(self) -> QWidget | None:
        return self._content_widget

    def set_offset(self, x: int, y: int) -> None:
        self._offset = QPoint(x, y)
        if self.isVisible():
            self._resolve_positions()
            self.move(self._hidden_pos if self._is_hiding else self._final_pos)

    def set_match_anchor_width(self, enabled: bool) -> None:
        self._match_anchor_width = enabled
        if self.isVisible():
            self._resolve_positions()
            self.move(self._hidden_pos if self._is_hiding else self._final_pos)

    def show_for(self, anchor: QWidget) -> None:
        if anchor is None:
            return
        self._bind_anchor(anchor)
        self.adjustSize()
        self._resolve_positions()
        self._stop_animation()
        self._is_hiding = False

        if not self.isVisible():
            self._opacity_effect.setOpacity(0.0)
            self.move(self._hidden_pos)
            self.show()
        else:
            self.move(self.pos())

        self.raise_()
        self._play_show_animation()

    def toggle_for(self, anchor: QWidget) -> None:
        if self.isVisible() and self._anchor is anchor:
            self.hide()
            return
        self.show_for(anchor)

    def bind_toggle(self, trigger: QWidget) -> None:
        clicked = getattr(trigger, "clicked", None)
        if clicked is None:
            return
        clicked.connect(lambda: self.toggle_for(trigger))

    def hide(self) -> None:  # type: ignore[override]
        if self._force_hide:
            super().hide()
            return
        self._request_hide()

    def hide_immediately(self) -> None:
        self._stop_animation()
        self._is_hiding = False
        self._finish_hide()

    def focusOutEvent(self, event) -> None:  # type: ignore[override]
        super().focusOutEvent(event)
        if not self.isVisible():
            return
        next_focus = QApplication.focusWidget()
        if isinstance(next_focus, QWidget) and self._owns_widget(next_focus):
            return

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self._request_hide()
            event.accept()
            return
        super().keyPressEvent(event)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self._bind_app_filter()
        if not self._is_open:
            self._is_open = True
            self.opened.emit()

    def hideEvent(self, event: QHideEvent) -> None:
        super().hideEvent(event)
        self._unbind_app_filter()
        self._opacity_effect.setOpacity(1.0)
        if self._is_open:
            self._is_open = False
            self.closed.emit()
        self._is_hiding = False
        self._unbind_anchor()

    def paintEvent(self, event: QPaintEvent) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)

        panel_rect = self.rect().adjusted(
            1,
            1,
            -2,
            -2,
        )

        painter.setBrush(self._panel_background)
        painter.setPen(QPen(self._panel_border, 1.0))
        painter.drawRect(panel_rect)

    def eventFilter(self, watched: QObject | None, event: QEvent | None) -> bool:  # type: ignore[override]
        if event is None:
            return super().eventFilter(watched, event)
        if self.isVisible():
            event_type = event.type()
            if event_type in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonDblClick):
                if self._should_hide_for_pointer_event(watched, event):
                    self._request_hide()
            elif event_type == QEvent.Type.ApplicationDeactivate:
                self._request_hide()
        if watched in (self._anchor, self._host_widget):
            event_type = event.type()
            if event_type in (QEvent.Type.Move, QEvent.Type.Resize):
                if self.isVisible():
                    self._resolve_positions()
                    if self._is_hiding:
                        self.move(self._hidden_pos)
                    else:
                        self.move(self._final_pos)
            elif event_type in (
                QEvent.Type.Hide,
                QEvent.Type.Close,
                QEvent.Type.WindowStateChange,
            ):
                self._request_hide()
        return super().eventFilter(watched, event)

    def _bind_anchor(self, anchor: QWidget) -> None:
        host_widget = anchor.window()
        if host_widget is None:
            return
        if self._anchor is anchor and self._host_widget is host_widget:
            return
        self._unbind_anchor()
        self._anchor = anchor
        self._host_widget = host_widget
        if self.parentWidget() is not host_widget:
            self.setParent(host_widget)
        self._anchor.installEventFilter(self)
        if self._host_widget is not self._anchor:
            self._host_widget.installEventFilter(self)

    def _unbind_anchor(self) -> None:
        if self._anchor is not None:
            try:
                self._anchor.removeEventFilter(self)
            except RuntimeError:
                pass
        if self._host_widget is not None and self._host_widget is not self._anchor:
            try:
                self._host_widget.removeEventFilter(self)
            except RuntimeError:
                pass
        self._anchor = None
        self._host_widget = None

    def _bind_app_filter(self) -> None:
        if self._app_filter_bound:
            return
        app = QApplication.instance()
        if app is None:
            return
        app.installEventFilter(self)
        self._app_filter_bound = True

    def _unbind_app_filter(self) -> None:
        if not self._app_filter_bound:
            return
        app = QApplication.instance()
        if app is None:
            self._app_filter_bound = False
            return
        try:
            app.removeEventFilter(self)
        except RuntimeError:
            pass
        self._app_filter_bound = False

    def _owns_widget(self, widget: QWidget | None) -> bool:
        current = widget
        while current is not None:
            if current is self or current is self._anchor:
                return True
            current = current.parentWidget()
        return False

    def _should_hide_for_pointer_event(self, watched: QObject | None, event: QEvent) -> bool:
        widget = watched if isinstance(watched, QWidget) else None
        if widget is not None and self._owns_widget(widget):
            return False
        global_position_getter = getattr(event, "globalPosition", None)
        if callable(global_position_getter):
            global_pos = global_position_getter().toPoint()
            local_pos = self.mapFromGlobal(global_pos)
            if self.rect().contains(local_pos):
                return False
            if self._anchor is not None:
                anchor_rect = self._anchor.rect()
                anchor_pos = self._anchor.mapFromGlobal(global_pos)
                if anchor_rect.contains(anchor_pos):
                    return False
        return True

    def _resolve_positions(self) -> None:
        anchor = self._anchor
        host_widget = self._host_widget
        if anchor is None or host_widget is None:
            return

        anchor_top_left = anchor.mapTo(host_widget, QPoint(0, 0))
        anchor_bottom_left = anchor.mapTo(host_widget, anchor.rect().bottomLeft())
        self.adjustSize()

        width = self.sizeHint().width()
        height = self.sizeHint().height()
        if self._match_anchor_width:
            width = max(width, anchor.width())

        x = anchor_top_left.x() + self._offset.x()
        y = anchor_bottom_left.y() + 1 + self._offset.y()

        available = host_widget.rect()
        max_width = max(120, available.width() - 16)
        width = min(width, max_width)

        min_x = available.left() + 8
        max_x = available.right() - width - 7
        x = min(max(x, min_x), max_x)

        bottom_limit = available.bottom() - height - 7
        if y > bottom_limit:
            y = anchor_top_left.y() - height - self._offset.y()
        min_y = available.top() + 8
        max_y = available.bottom() - height - 7
        y = min(max(y, min_y), max_y)

        final_pos = QPoint(x, y)
        show_above_anchor = y < anchor_top_left.y()
        hidden_pos = QPoint(
            x,
            y + self._anim_distance if show_above_anchor else y - self._anim_distance,
        )

        self.resize(width, height)
        self._final_pos = final_pos
        self._hidden_pos = hidden_pos

    def _play_show_animation(self) -> None:
        self._opacity_anim.setStartValue(float(self._opacity_effect.opacity()))
        self._opacity_anim.setEndValue(1.0)
        self._pos_anim.setStartValue(self.pos())
        self._pos_anim.setEndValue(self._final_pos)
        self._anim_group.start()

    def _request_hide(self) -> None:
        if not self.isVisible():
            self._finish_hide()
            return
        if self._is_hiding:
            return
        self._is_hiding = True
        self._resolve_positions()
        self._stop_animation()
        self._opacity_anim.setStartValue(float(self._opacity_effect.opacity()))
        self._opacity_anim.setEndValue(0.0)
        self._pos_anim.setStartValue(self.pos())
        self._pos_anim.setEndValue(self._hidden_pos)
        self._anim_group.start()

    def _stop_animation(self) -> None:
        if self._anim_group.state() == QAbstractAnimation.State.Stopped:
            return
        self._anim_group.stop()

    def _finish_hide(self) -> None:
        self._force_hide = True
        try:
            super().hide()
        finally:
            self._force_hide = False

    def _on_animation_finished(self) -> None:
        if self._is_hiding:
            self._finish_hide()
            return
        self.move(self._final_pos)
        self._opacity_effect.setOpacity(1.0)

    def _apply_style(self) -> None:
        self.setStyleSheet(load_qss(Qss.s_popup_panel))

    def _apply_palette(self) -> None:
        self._panel_background = self._theme_color("panel_background", "#ffffff")
        self._panel_border = self._theme_color("panel_border", "#dce5f0")
        self.update()

    def _theme_color(self, key: str, fallback: str) -> QColor:
        color = QColor(Qss.variables.get(key, fallback))
        if color.isValid():
            return color
        return QColor(fallback)

    def _on_theme_changed(self, _theme: str) -> None:
        self._apply_style()
        self._apply_palette()


def create_popup_panel(
    content: QWidget | None = None,
    *,
    offset_x: int = 0,
    offset_y: int = 8,
    match_anchor_width: bool = False,
) -> PopupPanel:
    panel = PopupPanel(
        offset_x=offset_x,
        offset_y=offset_y,
        match_anchor_width=match_anchor_width,
    )
    if content is not None:
        panel.set_content_widget(content)
    return panel
