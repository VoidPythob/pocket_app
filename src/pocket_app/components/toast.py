import logging
import queue
import threading
import weakref
from enum import Enum
from typing import Any, Generic, List, Type, TypeVar

from PyQt6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QEvent,
    QObject,
    QParallelAnimationGroup,
    QPoint,
    QPropertyAnimation,
    QTimer,
    Qt,
    pyqtSignal,
)
from PyQt6.QtWidgets import QApplication, QGraphicsOpacityEffect, QLabel, QWidget

from pocket_app.resources import Qss, ThemeManager, load_qss


class ToastType(Enum):
    INFO = "info"
    WARN = "warn"
    SUCCESS = "success"
    ERROR = "error"


class Toast(QLabel):

    before_enter = pyqtSignal()
    after_enter = pyqtSignal()
    before_leave = pyqtSignal()
    after_leave = pyqtSignal()

    def __init__(
        self,
        parent: QWidget,
        msg: str,
        type_: ToastType,
        leave_time: int = 3000,
        start_y: int = 0,
        anim_duration: int = 300,
        visible: bool = True,
    ) -> None:
        super().__init__(parent)
        self._parent = parent
        self._msg = msg
        self._type = type_

        if parent is None:
            raise Exception("toast必须拥有父元素")

        self._leave_time = leave_time
        self._start_y = start_y
        self._anim_duration = anim_duration
        self._visible = visible
        ThemeManager.theme_changed.connect(self._on_theme_changed)
        self._setup_ui()
        self._setup_anim()

    def _setup_ui(self) -> None:
        self.set_start_y(self._start_y)
        self.set_type(self._type)
        self.setText(self._msg)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(0)
        self.setGraphicsEffect(self._opacity_effect)

        self.setVisible(self._visible)
        self.setStyleSheet(load_qss(Qss.s_toast))
        self.adjustSize()
        self.resize(self.sizeHint())

    def _setup_anim(self) -> None:
        self.move_in_anim = QPropertyAnimation(self, b"pos")
        self.move_in_anim.setEasingCurve(QEasingCurve.Type.InQuad)
        self.move_in_anim.setDuration(self._anim_duration)

        self.fade_in_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self.fade_in_anim.setStartValue(0)
        self.fade_in_anim.setEndValue(1.0)
        self.fade_in_anim.setDuration(self._anim_duration)

        self.enter_anim_group = QParallelAnimationGroup(self)
        self.enter_anim_group.addAnimation(self.move_in_anim)
        self.enter_anim_group.addAnimation(self.fade_in_anim)
        self.enter_anim_group.finished.connect(lambda: self.after_enter.emit())

        self.move_out_anim = QPropertyAnimation(self, b"pos")
        self.move_out_anim.setEasingCurve(QEasingCurve.Type.InQuad)
        self.move_out_anim.setDuration(self._anim_duration)

        self.fade_out_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self.fade_out_anim.setStartValue(1.0)
        self.fade_out_anim.setEndValue(0)
        self.fade_out_anim.setDuration(self._anim_duration)

        self.leave_anim_group = QParallelAnimationGroup(self)
        self.leave_anim_group.addAnimation(self.move_out_anim)
        self.leave_anim_group.addAnimation(self.fade_out_anim)
        self.leave_anim_group.finished.connect(lambda: self.after_leave.emit())
        self.leave_anim_group.finished.connect(lambda: self.setVisible(False))

        self.move_up_anim = QPropertyAnimation(self, b"pos")
        self.move_up_anim.setEasingCurve(QEasingCurve.Type.InQuad)
        self.move_up_anim.setDuration(self._anim_duration)

        self.leave_timer = QTimer(self)
        self.leave_timer.setSingleShot(True)
        self.leave_timer.timeout.connect(self.play_leave_anim)

    def play_enter_anim(self, end_x: int = 50) -> None:
        self.before_enter.emit()
        self.setVisible(True)
        self.move_up_anim.stop()
        self.move_in_anim.setStartValue(QPoint(0, self.y()))
        self.move_in_anim.setEndValue(QPoint(end_x, self.y()))
        self.fade_in_anim.setStartValue(self._opacity_effect.opacity())
        self.fade_in_anim.setEndValue(1.0)
        self.enter_anim_group.start()
        self.leave_timer.start(self._leave_time)

    def play_leave_anim(self) -> None:
        self.before_leave.emit()
        self.leave_timer.stop()
        if self.enter_anim_group.state() == QAbstractAnimation.State.Running:
            self.move_in_anim.stop()
            self.fade_in_anim.stop()
            self.move(self.move_in_anim.endValue())
            self._opacity_effect.setOpacity(1.0)
            self.after_enter.emit()
            self.enter_anim_group.stop()
        self.move_up_anim.stop()
        self.move_out_anim.setStartValue(QPoint(self.x(), self.y()))
        self.move_out_anim.setEndValue(QPoint(-100, self.y()))
        self.fade_out_anim.setStartValue(self._opacity_effect.opacity())
        self.leave_anim_group.start()

    def play_move_up_anim(self, end_x: int, end_y: int) -> None:
        if self.enter_anim_group.state() == QAbstractAnimation.State.Running:
            self.move_in_anim.stop()
            self.fade_in_anim.stop()
            self.move(self.move_in_anim.endValue())
            self._opacity_effect.setOpacity(1.0)
            self.after_enter.emit()
            self.enter_anim_group.stop()
        self.move_up_anim.setStartValue(QPoint(self.x(), self.y()))
        self.move_up_anim.setEndValue(QPoint(end_x, end_y))
        self.move_up_anim.start()

    def set_start_y(self, start_y: int) -> None:
        self._start_y = start_y
        self.move(0, self._start_y)

    def set_type(self, type_: ToastType) -> None:
        self._type = type_
        self.setProperty("type", type_.value)
        s = self.style()
        if not s is None:
            s.unpolish(self)
            s.polish(self)

    def set_msg(self, msg: str) -> None:
        self._msg = msg
        self.setText(msg)
        self.adjustSize()
        self.resize(self.sizeHint())

    def _on_theme_changed(self, _theme: str) -> None:
        self.setStyleSheet(load_qss(Qss.s_toast))


class ToastStack(QWidget):

    def __init__(self, parent: QWidget, max_size: int = 10) -> None:
        super().__init__(parent)
        self._parent = parent
        self._max_size = max_size
        self._left = 50
        self._spacing = 10
        self._bottom_margin = 56
        self._pool = ObjectPool(
            Toast,
            self._max_size,
            parent=parent,
            msg="",
            type_=ToastType.INFO,
            visible=False,
        )
        self._active_toasts: List[Toast] = []

        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._re_layout)
        self._parent.installEventFilter(self)
        self._re_layout()

    def info(self, msg: str) -> None:
        self._show(msg, ToastType.INFO)

    def warn(self, msg: str) -> None:
        self._show(msg, ToastType.WARN)

    def success(self, msg: str) -> None:
        self._show(msg, ToastType.SUCCESS)

    def error(self, msg: str) -> None:
        self._show(msg, ToastType.ERROR)

    def _show(self, msg: str, type_: ToastType) -> None:
        toast = self._pool.get()
        if toast is None:
            if not self._active_toasts:
                return
            toast = self._active_toasts.pop(0)

        try:
            toast.before_leave.disconnect()
        except TypeError:
            pass
        toast.enter_anim_group.stop()
        toast.leave_anim_group.stop()
        toast.move_up_anim.stop()
        toast.leave_timer.stop()
        toast._opacity_effect.setOpacity(0)
        toast.setVisible(False)
        toast.set_msg(msg)
        toast.set_type(type_)

        try:
            toast.after_leave.disconnect()
        except TypeError:
            pass

        self._active_toasts.append(toast)
        toast.before_leave.connect(lambda toast=toast: self._deactivate_toast(toast))
        toast.after_leave.connect(lambda toast=toast: self._recycle_toast(toast))
        self._re_layout(enter_toast=toast, animate=True)

    def _deactivate_toast(self, toast: Toast) -> None:
        if toast in self._active_toasts:
            self._active_toasts.remove(toast)
            self._re_layout(animate=True)

    def _recycle_toast(self, toast: Toast) -> None:
        toast.setVisible(False)
        self._pool.put(toast)

    def eventFilter(self, a0: QObject | None, a1: QEvent | None) -> bool:
        if a1 is not None and a0 is self._parent and a1.type() == QEvent.Type.Resize:
            self._resize_timer.stop()
            self._resize_timer.start(100)
        return super().eventFilter(a0, a1)

    def _re_layout(
        self,
        enter_toast: Toast | None = None,
        animate: bool = False,
    ) -> None:
        current_bottom = max(
            self._spacing,
            self._parent.height() - self._bottom_margin,
        )
        for toast in reversed(self._active_toasts):
            toast.adjustSize()
            toast.resize(toast.sizeHint())
            start_y = max(self._spacing, current_bottom - toast.height())
            if toast is enter_toast:
                toast.set_start_y(start_y)
                toast.play_enter_anim(self._left)
            elif animate:
                toast.play_move_up_anim(self._left, start_y)
            else:
                toast.move(self._left, start_y)
            current_bottom = start_y - self._spacing


class Toaster:

    _stacks: "weakref.WeakKeyDictionary[QWidget, ToastStack]" = (
        weakref.WeakKeyDictionary()
    )

    @classmethod
    def _resolve_parent(cls, parent: QWidget | None = None) -> QWidget:
        if parent is not None:
            return parent

        app = QApplication.instance()
        if app is None:
            raise RuntimeError("QApplication is not initialized")

        active_window = QApplication.activeWindow()
        if active_window is not None:
            return active_window

        focus_widget = QApplication.focusWidget()
        if focus_widget is not None:
            focus_window = focus_widget.window()
            if focus_window is not None:
                return focus_window

        for widget in QApplication.topLevelWidgets():
            if widget.isVisible():
                return widget

        raise RuntimeError("No visible window found for toast")

    @classmethod
    def stack(cls, parent: QWidget | None = None, max_size: int = 10) -> ToastStack:
        parent = cls._resolve_parent(parent)
        stack = cls._stacks.get(parent)
        if stack is None:
            stack = ToastStack(parent, max_size=max_size)
            cls._stacks[parent] = stack
        return stack

    @classmethod
    def show(
        cls,
        msg: str,
        type_: ToastType = ToastType.INFO,
        parent: QWidget | None = None,
        max_size: int = 10,
    ) -> None:
        cls.stack(parent, max_size=max_size)._show(msg, type_)

    @classmethod
    def info(
        cls,
        msg: str,
        parent: QWidget | None = None,
        max_size: int = 10,
    ) -> None:
        cls.show(msg, ToastType.INFO, parent=parent, max_size=max_size)

    @classmethod
    def warn(
        cls,
        msg: str,
        parent: QWidget | None = None,
        max_size: int = 10,
    ) -> None:
        cls.show(msg, ToastType.WARN, parent=parent, max_size=max_size)

    @classmethod
    def success(
        cls,
        msg: str,
        parent: QWidget | None = None,
        max_size: int = 10,
    ) -> None:
        cls.show(msg, ToastType.SUCCESS, parent=parent, max_size=max_size)

    @classmethod
    def error(
        cls,
        msg: str,
        parent: QWidget | None = None,
        max_size: int = 10,
    ) -> None:
        cls.show(msg, ToastType.ERROR, parent=parent, max_size=max_size)


T = TypeVar("T")


class ObjectPool(Generic[T]):

    def __init__(self, obj_cls: Type[T], size: int, **kwargs: Any) -> None:
        self._obj_cls = obj_cls
        self._size = size
        self._kwargs = kwargs
        self._pool = queue.Queue(maxsize=size)
        self._lock = threading.Lock()
        self._initialize_pool()

    def _initialize_pool(self) -> None:
        with self._lock:
            for _ in range(self._size):
                obj = self._obj_cls(**self._kwargs)
                self._pool.put(obj)

    def put(self, obj: T) -> bool:
        try:
            self._pool.put(obj, block=False)
            return True
        except queue.Full:
            return False

    def __enter__(self) -> T | None:
        return self.get()

    def get(self, timeout: float | None = None) -> T | None:
        try:
            if timeout is None:
                return self._pool.get(block=False)
            return self._pool.get(timeout=timeout)
        except queue.Empty:
            return None

    @property
    def size(self) -> int:
        return self._size

    @property
    def available_num(self) -> int:
        return self._pool.qsize()
