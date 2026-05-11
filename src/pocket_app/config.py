from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = {"logging_level": "DEBUG", "api_base_url": "http://127.0.0.1:8080"}


class Config:
    logging_level = logging.DEBUG
    api_base_url = DEFAULT_CONFIG["api_base_url"]
    config_path: str | None = None


def load_config(config_path: str | None = None) -> dict[str, Any]:
    resolved_path = _resolve_config_path(config_path)
    if resolved_path is None or not resolved_path.exists():
        return DEFAULT_CONFIG.copy()

    with resolved_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise TypeError("config.json must contain a JSON object")

    merged = DEFAULT_CONFIG.copy()
    merged.update({key: value for key, value in data.items() if value is not None})
    return merged


def apply_config(config_data: dict[str, Any], config_path: str | None = None) -> None:
    resolved_path = _resolve_config_path(config_path)
    Config.logging_level = _resolve_logging_level(config_data.get("logging_level"))
    Config.api_base_url = str(
        config_data.get("api_base_url", DEFAULT_CONFIG["api_base_url"])
    ).rstrip("/")
    Config.config_path = str(resolved_path) if resolved_path is not None else None


def init_logging_config() -> None:
    logging.basicConfig(
        level=Config.logging_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )


def init_config(config_path: str | None = None) -> None:
    config_data = load_config(config_path)
    apply_config(config_data, config_path)
    init_logging_config()

    from pocket_app.api import set_base_url

    set_base_url(Config.api_base_url)


def _resolve_config_path(config_path: str | None) -> Path | None:
    if config_path:
        return Path(config_path).expanduser().resolve()

    default_path = Path.cwd() / "config.json"
    return default_path if default_path.exists() else None


def _resolve_logging_level(level: Any) -> int:
    if isinstance(level, int):
        return level

    if isinstance(level, str):
        normalized = level.strip().upper()
        if hasattr(logging, normalized):
            resolved = getattr(logging, normalized)
            if isinstance(resolved, int):
                return resolved

    return logging.DEBUG
