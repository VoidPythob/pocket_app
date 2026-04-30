import logging
import os
from enum import Enum
from os.path import join as path_join

from pocket_app.utils import str_isempty


class ResourcesException(Exception):

    def __init__(self, msg: str) -> None:
        super().__init__(msg)


resources_dir = path_join(os.getcwd(), "resources")
if not os.path.exists(resources_dir):
    raise ResourcesException("资源路径未找到")


def link_root(root: str) -> str:
    return path_join(resources_dir, root)


def load_qss(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logging.warning(f"qss路径：{path}不存在")
        return ""


class i8H:
    _root = link_root("i8H")


class Icons:
    _root = link_root("icons")
    fold_chevron = path_join(_root, "fold_chevron.svg")
    navigation_item = path_join(_root, "navigation_item.svg")


class _Qss:
    _root = link_root("qss")

    class Themes(Enum):
        DARK = "dark"
        LIGHT = "light"

    s_main_window = "main_window.qss"
    s_side_navigation = "side_navigation.qss"

    def __init__(self) -> None:
        self._theme = self.Themes.LIGHT
        self._styles = []
        for i in dir(_Qss):

            if not i[0:2] == "s_":
                continue

            # 找到所有style_path属性
            self._styles.append(i)

        for i in self._styles:
            style_path = getattr(self, i)
            # 备份style_path
            setattr(self, self._bak_name(i), style_path)

            self._update_theme_style(i)

    def set_theme(self, theme: "Themes") -> None:
        self._theme = theme
        for i in self._styles:
            self._update_theme_style(i)

    def _update_theme_style(self, style: str) -> None:
        style_path = getattr(self, self._bak_name(style))

        if not isinstance(style_path, str):
            raise TypeError(f"style：{style}的路径配置不是字符串类型，值为{style_path}")
        if str_isempty(style_path):
            raise ResourcesException(f"style：{style}的路径配置为空")

        theme_style_path = os.path.join(self._root, self._theme.value, style_path)
        setattr(self, style, theme_style_path)

    @staticmethod
    def _bak_name(style: str) -> str:
        return f"_bak_{style}"


Qss = _Qss()

if __name__ == "__main__":
    pass
