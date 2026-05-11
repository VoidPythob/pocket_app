from __future__ import annotations

import json
import logging
import os
from enum import Enum
from os.path import join as path_join
from pathlib import Path
import re

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtWidgets import QApplication

from pocket_app.utils import str_isempty


class ResourcesException(Exception):
    def __init__(self, msg: str) -> None:
        super().__init__(msg)


resources_dir = str(Path(__file__).resolve().parents[2] / "resources")
if not os.path.exists(resources_dir):
    raise ResourcesException(f"Resource path not found: {resources_dir}")


def link_root(root: str) -> str:
    return path_join(resources_dir, root)


QSS_VAR_PATTERN = re.compile(r"\{\{([a-z0-9_]+)\}\}")
QSS_FONT_FAMILY_PATTERN = re.compile(r"(font-family\s*:\s*)([a-zA-Z0-9_\-]+)(\s*;)")
QSS_FONT_SIZE_PATTERN = re.compile(r"(font-size\s*:\s*)(\d+(?:\.\d+)?)(px\s*;)")
_font_aliases: dict[str, str] = {}
_loaded_font_families: dict[str, str] = {}
_default_font_family = ""


def load_qss(path: str, extra_vars: dict[str, object] | None = None) -> str:
    try:
        with open(path, "r", encoding="utf-8") as file:
            raw = file.read()
    except FileNotFoundError:
        logging.warning("qss path does not exist: %s", path)
        return ""

    variables = dict(Qss.variables)
    if extra_vars:
        variables.update({str(key): str(value) for key, value in extra_vars.items()})

    resolved = QSS_VAR_PATTERN.sub(
        lambda match: variables.get(match.group(1), match.group(0)),
        raw,
    )
    resolved = QSS_FONT_FAMILY_PATTERN.sub(_replace_font_alias, resolved)
    return QSS_FONT_SIZE_PATTERN.sub(_replace_font_size, resolved)


def load_json_resource(path: str) -> dict[str, object]:
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        logging.warning("json resource path does not exist: %s", path)
        return {}
    except json.JSONDecodeError:
        logging.warning("json resource path is invalid: %s", path)
        return {}

    if not isinstance(data, dict):
        logging.warning("json resource root must be an object: %s", path)
        return {}
    return data


def register_font_alias(alias: str, family_name: str) -> None:
    normalized_alias = alias.strip().lower()
    normalized_family = family_name.strip()
    if not normalized_alias or not normalized_family:
        return
    _font_aliases[normalized_alias] = normalized_family


def _replace_font_alias(match: re.Match[str]) -> str:
    alias = match.group(2).strip().lower()
    family_name = _font_aliases.get(alias)
    if not family_name:
        return match.group(0)
    return f'{match.group(1)}"{family_name}"{match.group(3)}'


def _replace_font_size(match: re.Match[str]) -> str:
    scale = _font_size_scale_for_locale()
    if scale == 1.0:
        return match.group(0)
    size = float(match.group(2))
    scaled_size = max(1, round(size * scale))
    return f"{match.group(1)}{scaled_size}{match.group(3)}"


def _font_size_scale_for_locale() -> float:
    current_locale = getattr(globals().get("I18n"), "current_locale", None)
    if current_locale in (_I18n.Locales.EX_HY, _I18n.Locales.LZH_CN):
        return 1.14
    return 1.0


class Icons:
    _root = link_root("icons")
    back_arrow = path_join(_root, "back_arrow.svg")
    nav_egg_groups = path_join(_root, "nav_egg_groups.svg")
    nav_features = path_join(_root, "nav_features.svg")
    nav_game_docs = path_join(_root, "nav_game_docs.svg")
    nav_items = path_join(_root, "nav_items.svg")
    nav_pets = path_join(_root, "nav_pets.svg")
    nav_skills = path_join(_root, "nav_skills.svg")
    fold_chevron = path_join(_root, "fold_chevron.svg")
    i18n_toggle = path_join(_root, "i18n_toggle.svg")
    navigation_item = path_join(_root, "navigation_item.svg")
    refresh = path_join(_root, "refresh.svg")
    search = path_join(_root, "search.svg")
    theme_toggle = path_join(_root, "theme_toggle.svg")


class Fonts:
    _root = link_root("fonts")
    genshin = path_join(_root, "genshin.ttf")
    hymmnos = path_join(_root, "hymmnos.ttf")
    jinwen = path_join(_root, "jinwen.ttf")


class _Qss:
    _root = link_root("qss")
    _base_root = path_join(_root, "base")

    class Themes(Enum):
        DARK = "dark"
        LIGHT = "light"

    s_main_window = "main_window.qss"
    s_side_navigation = "side_navigation.qss"
    s_icon_button = "icon_button.qss"
    s_search_bar = "search_bar.qss"
    s_language_selector = "language_selector.qss"
    s_pagination = "pagination.qss"
    s_tag = "tag.qss"
    s_toast = "toast.qss"
    s_loading_placeholder = "loading_placeholder.qss"
    s_popup_panel = "popup_panel.qss"

    def __init__(self) -> None:
        self._theme = self.Themes.LIGHT
        self._styles: list[str] = []
        self._variables: dict[str, str] = {}
        self._runtime_variables: dict[str, str] = {}
        for name in dir(_Qss):
            if not name.startswith("s_"):
                continue
            self._styles.append(name)

        for name in self._styles:
            style_path = getattr(self, name)
            setattr(self, self._bak_name(name), style_path)
            self._update_style_path(name)
        self._load_theme_variables()

    def set_theme(self, theme: "Themes") -> None:
        self._theme = theme
        self._load_theme_variables()

    @property
    def variables(self) -> dict[str, str]:
        return {**self._variables, **self._runtime_variables}

    def set_runtime_variable(self, key: str, value: object) -> None:
        self._runtime_variables[str(key)] = str(value)

    def _update_style_path(self, style: str) -> None:
        style_path = getattr(self, self._bak_name(style))

        if not isinstance(style_path, str):
            raise TypeError(f"style path for {style} must be str, got {style_path!r}")
        if str_isempty(style_path):
            raise ResourcesException(f"style path for {style} is empty")

        base_style_path = os.path.join(self._base_root, style_path)
        setattr(self, style, base_style_path)

    def _load_theme_variables(self) -> None:
        path = os.path.join(self._root, self._theme.value, "variables.json")
        raw = load_json_resource(path)
        self._variables = {
            key: str(value)
            for key, value in raw.items()
            if value is not None
        }

    @staticmethod
    def _bak_name(style: str) -> str:
        return f"_bak_{style}"


Qss = _Qss()


class _I18n:
    _root = link_root("i18n")

    class Locales(Enum):
        ZH_CN = "zh_CN"
        EN_US = "en_US"
        JA_JP = "ja_JP"
        LZH_CN = "lzh_CN"
        EX_HY = "ex_hy"

    def __init__(self) -> None:
        self._locale = self.Locales.ZH_CN
        self._messages: dict[str, dict[str, str]] = {}
        for locale in self.Locales:
            path = path_join(self._root, f"{locale.value}.json")
            raw = load_json_resource(path)
            self._messages[locale.value] = {
                key: str(value) for key, value in raw.items() if value is not None
            }

    @property
    def current_locale(self) -> "_I18n.Locales":
        return self._locale

    def set_locale(self, locale: "_I18n.Locales") -> None:
        self._locale = locale

    def text(self, key: str, **kwargs: object) -> str:
        current_messages = self._messages.get(self._locale.value, {})
        fallback_messages = self._messages.get(self.Locales.ZH_CN.value, {})
        template = current_messages.get(key) or fallback_messages.get(key) or key
        try:
            return template.format(**kwargs)
        except Exception:
            return template


I18n = _I18n()


class _ThemeManager(QObject):
    theme_changing = pyqtSignal(str)
    theme_changed = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()

    @property
    def current_theme(self) -> _Qss.Themes:
        return Qss._theme

    def set_theme(self, theme: _Qss.Themes) -> None:
        if Qss._theme == theme:
            return
        self.theme_changing.emit(theme.value)
        Qss.set_theme(theme)
        self.theme_changed.emit(theme.value)

    def toggle_theme(self) -> _Qss.Themes:
        target_theme = (
            Qss.Themes.DARK if Qss._theme == Qss.Themes.LIGHT else Qss.Themes.LIGHT
        )
        self.set_theme(target_theme)
        return target_theme


ThemeManager = _ThemeManager()


class _I18nManager(QObject):
    language_changed = pyqtSignal(str)

    @property
    def current_locale(self) -> _I18n.Locales:
        return I18n.current_locale

    def set_locale(self, locale: _I18n.Locales) -> None:
        if I18n.current_locale == locale:
            return
        font_family_for_locale(locale)
        apply_locale_font(locale)
        I18n.set_locale(locale)
        self.language_changed.emit(locale.value)
        ThemeManager.theme_changed.emit(ThemeManager.current_theme.value)

    def toggle_locale(self) -> _I18n.Locales:
        locales = self.available_locales()
        current_index = locales.index(I18n.current_locale)
        target_locale = locales[(current_index + 1) % len(locales)]
        self.set_locale(target_locale)
        return target_locale

    def text(self, key: str, **kwargs: object) -> str:
        return I18n.text(key, **kwargs)

    def available_locales(self) -> list[_I18n.Locales]:
        return list(I18n.Locales)


I18nManager = _I18nManager()


def tr(key: str, **kwargs: object) -> str:
    return I18nManager.text(key, **kwargs)


def _load_font_family(cache_key: str, path: str, fallback_family: str) -> str:
    family_name = _loaded_font_families.get(cache_key, "")
    if family_name:
        return family_name

    font_id = QFontDatabase.addApplicationFont(path)
    if font_id < 0:
        logging.warning("failed to load font resource: %s", path)
        family_name = fallback_family
    else:
        families = QFontDatabase.applicationFontFamilies(font_id)
        family_name = families[0] if families else fallback_family

    _loaded_font_families[cache_key] = family_name
    register_font_alias(cache_key, family_name)
    return family_name


def _resolve_default_font_family() -> str:
    global _default_font_family
    if _default_font_family:
        return _default_font_family

    system_font = QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont)
    _default_font_family = _load_font_family("genshin", Fonts.genshin, system_font.family())
    return _default_font_family


def font_family_for_locale(locale: _I18n.Locales | None = None) -> str:
    target_locale = locale or I18n.current_locale
    default_family = _resolve_default_font_family()
    if target_locale == _I18n.Locales.EX_HY:
        return _load_font_family("hymmnos", Fonts.hymmnos, default_family)
    if target_locale == _I18n.Locales.LZH_CN:
        return _load_font_family("jinwen", Fonts.jinwen, default_family)
    return default_family


def apply_locale_font(locale: _I18n.Locales | None = None) -> QFont:
    family_name = font_family_for_locale(locale)
    register_font_alias("genshin", family_name)
    app = QApplication.instance()
    font = QFont(family_name)
    if app is not None:
        app.setFont(font)
    return font


def preload_app_fonts() -> None:
    default_family = _resolve_default_font_family()
    _load_font_family("hymmnos", Fonts.hymmnos, default_family)
    _load_font_family("jinwen", Fonts.jinwen, default_family)


def load_app_font() -> QFont:
    return apply_locale_font(I18n.current_locale)
