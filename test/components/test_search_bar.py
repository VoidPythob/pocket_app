from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from pocket_app.components import SearchBar


def _drain_events(qt_app, wait_ms: int = 0) -> None:
    qt_app.processEvents()
    if wait_ms > 0:
        QTest.qWait(wait_ms)
        qt_app.processEvents()


def test_search_bar_applies_placeholder_tooltip_and_text(qt_app) -> None:
    bar = SearchBar(
        placeholder="Search entries",
        tooltip="Search tooltip",
        height=40,
    )

    assert bar.line_edit.placeholderText() == "Search entries"
    assert bar.toolTip() == "Search tooltip"
    assert bar.line_edit.toolTip() == "Search tooltip"
    assert bar.search_button.toolTip() == "Search tooltip"
    assert bar.height() == 40
    assert not bar.search_button.icon().isNull()
    assert bar.search_button.cursor().shape() == Qt.CursorShape.PointingHandCursor

    bar.set_text("pikachu")

    assert bar.text() == "pikachu"


def test_search_bar_emits_search_requested_on_return(qt_app) -> None:
    bar = SearchBar()
    bar.show()
    _drain_events(qt_app, 10)

    requested: list[str] = []
    changed: list[str] = []
    bar.search_requested.connect(requested.append)
    bar.text_changed.connect(changed.append)

    bar.line_edit.setFocus()
    _drain_events(qt_app, 10)
    QTest.keyClicks(bar.line_edit, "bulbasaur")
    QTest.keyClick(bar.line_edit, Qt.Key.Key_Return)
    _drain_events(qt_app, 10)

    assert bar.property("focused") is True
    assert changed[-1] == "bulbasaur"
    assert requested == ["bulbasaur"]

    bar.close()


def test_search_bar_emits_search_requested_on_button_click(qt_app) -> None:
    bar = SearchBar()
    bar.show()
    _drain_events(qt_app, 10)

    requested: list[str] = []
    bar.search_requested.connect(requested.append)

    bar.set_text("charizard")
    bar.search_button.click()
    _drain_events(qt_app, 10)

    assert requested == ["charizard"]

    bar.close()
