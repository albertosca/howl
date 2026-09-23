"""User paths for howl: config in ~/.config/howl, cache in ~/.cache/howl (XDG-aware)."""

import os
import shutil
from pathlib import Path

from ..i18n import t


def config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME")
    base_dir = Path(base) if base else Path.home() / ".config"
    return base_dir / "howl"


def cache_dir() -> Path:
    override = os.environ.get("HOWL_CACHE_DIR")
    if override:
        return Path(override)
    base = os.environ.get("XDG_CACHE_HOME")
    base_dir = Path(base) if base else Path.home() / ".cache"
    return base_dir / "howl"


def games_cache_path() -> Path:
    return cache_dir() / "games_cache.json"


def overrides_path() -> Path:
    return config_dir() / "howl_overrides.json"


def config_path() -> Path:
    return config_dir() / ".env"


def log_path() -> Path:
    return config_dir() / "setup.log"


def token_path() -> Path:
    return config_dir() / ".igdb_token.json"


def ensure_config_dir() -> Path:
    """Creates ~/.config/howl with restrictive permissions (0700) and returns the path."""
    d = config_dir()
    d.mkdir(mode=0o700, parents=True, exist_ok=True)
    return d


def migrate_legacy_file(legacy: Path, target: Path) -> None:
    """Copies a cwd-relative file from older versions to its fixed location, once."""
    if target.exists() or not legacy.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(legacy, target)
    print(t("paths.legacy_copied", legacy=legacy, target=target))
