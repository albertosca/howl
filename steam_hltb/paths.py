"""Caminhos de configuração do howl (~/.config/howl, respeitando XDG_CONFIG_HOME)."""

import os


def config_dir() -> str:
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "howl")


def config_path() -> str:
    return os.path.join(config_dir(), ".env")


def log_path() -> str:
    return os.path.join(config_dir(), "setup.log")


def token_path() -> str:
    return os.path.join(config_dir(), ".igdb_token.json")


def ensure_config_dir() -> str:
    """Cria ~/.config/howl com permissões restritivas (0700) e retorna o path."""
    d = config_dir()
    os.makedirs(d, mode=0o700, exist_ok=True)
    return d
