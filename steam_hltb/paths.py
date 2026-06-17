"""Caminhos de configuração do howl (~/.config/howl, respeitando XDG_CONFIG_HOME)."""

import os
from pathlib import Path


def config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME")
    base_dir = Path(base) if base else Path.home() / ".config"
    return base_dir / "howl"


def config_path() -> Path:
    return config_dir() / ".env"


def log_path() -> Path:
    return config_dir() / "setup.log"


def token_path() -> Path:
    return config_dir() / ".igdb_token.json"


def ensure_config_dir() -> Path:
    """Cria ~/.config/howl com permissões restritivas (0700) e retorna o path."""
    d = config_dir()
    d.mkdir(mode=0o700, parents=True, exist_ok=True)
    return d
