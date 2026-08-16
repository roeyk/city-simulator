from __future__ import annotations

import os
from pathlib import Path


def data_home() -> Path:
    return Path(os.environ.get("CITY_SIMULATOR_HOME", "~/.city-simulator")).expanduser()


def ensure_data_dirs() -> Path:
    home = data_home()
    for name in ("cities", "scenarios", "reports"):
        (home / name).mkdir(parents=True, exist_ok=True)
    return home


def saved_cities() -> list[Path]:
    cities_dir = data_home() / "cities"
    if not cities_dir.exists():
        return []
    return sorted(cities_dir.glob("*.json"))


def city_path(name_or_path: str | Path) -> Path:
    return _named_json_path(name_or_path, "cities")


def scenario_path(name_or_path: str | Path) -> Path:
    return _named_json_path(name_or_path, "scenarios")


def report_path(name_or_path: str | Path) -> Path:
    return _named_json_path(name_or_path, "reports")


def _named_json_path(name_or_path: str | Path, directory: str) -> Path:
    raw_path = Path(name_or_path).expanduser()
    if raw_path.is_absolute() or raw_path.parent != Path("."):
        return raw_path
    filename = raw_path.name if raw_path.suffix else f"{raw_path.name}.json"
    return data_home() / directory / filename
