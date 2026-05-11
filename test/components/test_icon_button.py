from pathlib import Path

from pocket_app.components import IconButton
from pocket_app.resources import Icons


def test_icon_button_applies_icon_tooltip_and_size(qt_app) -> None:
    button = IconButton(
        Icons.fold_chevron,
        tooltip="Fold section",
        button_size=40,
        icon_size=18,
    )

    assert button.toolTip() == "Fold section"
    assert button.width() == 40
    assert button.height() == 40
    assert button.iconSize().width() == 18
    assert button.iconSize().height() == 18
    assert button.property("variant") == "circle"
    assert not button.icon().isNull()


def test_icon_button_with_missing_icon_does_not_crash(qt_app) -> None:
    missing_icon = str(Path(Icons.fold_chevron).with_name("missing.svg"))
    button = IconButton(missing_icon)

    assert button.icon().isNull()
    assert button.property("variant") == "circle"
