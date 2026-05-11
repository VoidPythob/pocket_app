from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QWidget

from pocket_app.components.toast import Toast, ToastType, Toaster


def _drain_events(qt_app, wait_ms: int = 0) -> None:
    qt_app.processEvents()
    if wait_ms > 0:
        QTest.qWait(wait_ms)
        qt_app.processEvents()


def test_toast_updates_type_property(qt_app) -> None:
    parent = QWidget()
    parent.resize(640, 480)
    parent.show()
    _drain_events(qt_app, 10)

    toast = Toast(parent, "hello", ToastType.INFO, visible=False)
    toast.set_type(ToastType.SUCCESS)

    assert toast.property("type") == ToastType.SUCCESS.value

    parent.close()


def test_stack_reuses_same_instance_for_same_parent(qt_app) -> None:
    parent = QWidget()
    parent.resize(640, 480)
    parent.show()
    _drain_events(qt_app, 10)

    first_stack = Toaster.stack(parent)
    second_stack = Toaster.stack(parent)

    assert first_stack is second_stack

    parent.close()


def test_show_adds_active_toast_for_explicit_parent(qt_app) -> None:
    parent = QWidget()
    parent.resize(640, 480)
    parent.show()
    _drain_events(qt_app, 10)

    Toaster.show("saved", ToastType.SUCCESS, parent=parent)
    _drain_events(qt_app, 10)

    stack = Toaster.stack(parent)

    assert len(stack._active_toasts) == 1
    assert stack._active_toasts[0].text() == "saved"
    assert stack._active_toasts[0].property("type") == ToastType.SUCCESS.value

    parent.close()
