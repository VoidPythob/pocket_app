from pocket_app.components import IconButton, SearchBar, SideNavigation, Tag
from pocket_app.resources import Icons, Qss, ThemeManager


def test_theme_manager_updates_qss_theme(qt_app) -> None:
    ThemeManager.set_theme(Qss.Themes.DARK)

    assert ThemeManager.current_theme == Qss.Themes.DARK
    assert "\\dark\\" in Qss.s_icon_button
    assert "\\dark\\" in Qss.s_search_bar


def test_components_refresh_styles_when_theme_changes(qt_app) -> None:
    button = IconButton(Icons.theme_toggle)
    search_bar = SearchBar()
    tag = Tag("Water", background_color="#ffffff")
    navigation = SideNavigation()

    ThemeManager.set_theme(Qss.Themes.DARK)

    assert "#202633" in button.styleSheet()
    assert "#1f2632" in search_bar.styleSheet()
    assert "#20324d" in tag.styleSheet().lower()
    assert "#253143" in navigation.styleSheet()
