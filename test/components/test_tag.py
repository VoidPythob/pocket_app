from pocket_app.resources import Qss, ThemeManager

from PyQt6.QtCore import Qt

from pocket_app.components import Tag


def test_tag_applies_text_tooltip_and_height(qt_app) -> None:
    tag = Tag("Water", tooltip="Water tag", height=32, tag_id="water")

    assert tag.text() == "Water"
    assert tag.tag_id() == "water"
    assert tag.toolTip() == "Water tag"
    assert tag.height() == 32
    assert tag.cursor().shape() == Qt.CursorShape.PointingHandCursor
    assert tag.property("selected") is False


def test_tag_click_emits_tag_id_signal(qt_app) -> None:
    tag = Tag("Electric", tag_id="electric")
    clicked: list[str] = []
    tag.tag_clicked.connect(clicked.append)

    tag.click()

    assert clicked == ["electric"]


def test_tag_click_falls_back_to_text_when_id_is_empty(qt_app) -> None:
    tag = Tag("Electric")
    clicked: list[str] = []
    tag.tag_clicked.connect(clicked.append)

    tag.click()

    assert clicked == ["Electric"]


def test_tag_selected_state_can_be_toggled(qt_app) -> None:
    tag = Tag("Legendary")

    tag.set_selected(True)
    assert tag.property("selected") is True

    tag.set_selected(False)
    assert tag.property("selected") is False


def test_tag_accepts_custom_background_color(qt_app) -> None:
    tag = Tag("Fire", background_color="#ffefe5")

    assert "#ffefe5" in tag.styleSheet().lower()

    tag.set_background_color("#ffe0e0")
    assert "#ffe0e0" in tag.styleSheet().lower()


def test_tag_uses_readable_text_for_light_background_in_dark_theme(qt_app) -> None:
    tag = Tag("Ice", background_color="#e7f6ff")

    ThemeManager.set_theme(Qss.Themes.DARK)

    assert "#20324d" in tag.styleSheet().lower()


def test_tag_id_can_be_updated_independently_from_text(qt_app) -> None:
    tag = Tag("Grass", tag_id="grass")

    tag.set_text("草")
    tag.set_tag_id("type_grass")

    assert tag.text() == "草"
    assert tag.tag_id() == "type_grass"
