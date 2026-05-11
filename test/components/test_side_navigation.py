from PyQt6.QtTest import QTest

from pocket_app.components.side_navigation import SideNavigation, SideNavigationItemModel


def _drain_events(qt_app, wait_ms: int = 0) -> None:
    qt_app.processEvents()
    if wait_ms > 0:
        QTest.qWait(wait_ms)
        qt_app.processEvents()


def test_leaf_click_emits_selected_and_marks_item_active(qt_app) -> None:
    navigation = SideNavigation()
    navigation.resize(300, 400)
    navigation.show()
    _drain_events(qt_app, 10)

    selected_names: list[str] = []
    navigation.selected.connect(selected_names.append)

    root = SideNavigationItemModel(
        id_=1,
        name="root",
        tip="Root",
        children=[
            SideNavigationItemModel(id_=11, name="leaf_a", tip="Leaf A"),
            SideNavigationItemModel(id_=12, name="leaf_b", tip="Leaf B"),
        ],
    )
    navigation.add_item(root)
    _drain_events(qt_app, 10)

    root_item = navigation.main_layout.itemAt(0).widget()
    first_leaf = root_item._children[0]
    second_leaf = root_item._children[1]

    first_leaf.button.click()
    _drain_events(qt_app, 10)

    assert selected_names == ["leaf_a"]
    assert first_leaf.button.property("active") is True

    second_leaf.button.click()
    _drain_events(qt_app, 10)

    assert selected_names == ["leaf_a", "leaf_b"]
    assert first_leaf.button.property("active") is False
    assert second_leaf.button.property("active") is True

    navigation.close()


def test_parent_item_can_fold_and_unfold_children(qt_app) -> None:
    navigation = SideNavigation()
    navigation.resize(300, 400)
    navigation.show()
    _drain_events(qt_app, 10)

    root = SideNavigationItemModel(
        id_=1,
        name="root",
        tip="Root",
        children=[SideNavigationItemModel(id_=11, name="leaf_a", tip="Leaf A")],
    )
    navigation.add_item(root)
    _drain_events(qt_app, 10)

    root_item = navigation.main_layout.itemAt(0).widget()
    child_item = root_item._children[0]

    assert root_item.is_folded is False
    assert child_item.isHidden() is False

    root_item.fold()
    _drain_events(qt_app, 10)

    assert root_item.is_folded is True
    assert child_item.isHidden() is True
    assert root_item.button.property("active") is False

    root_item.unfold()
    _drain_events(qt_app, 10)

    assert root_item.is_folded is False
    assert child_item.isHidden() is False
    assert root_item.button.property("active") is True

    navigation.close()


def test_side_navigation_scrolls_when_content_exceeds_height(qt_app) -> None:
    navigation = SideNavigation()
    navigation.resize(220, 180)

    for index in range(20):
        navigation.add_item(
            SideNavigationItemModel(
                id_=index,
                name=f"item_{index}",
                tip=f"Item {index}",
            )
        )

    navigation.show()
    _drain_events(qt_app, 10)

    assert navigation.scroll_area.verticalScrollBar().maximum() > 0

    navigation.close()
