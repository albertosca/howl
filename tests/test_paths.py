import os
from pathlib import Path

from steam_hltb import paths


def test_config_dir_respects_xdg(monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", "/tmp/xdg")
    assert paths.config_dir() == Path("/tmp/xdg/howl")


def test_config_dir_default(monkeypatch):
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    assert paths.config_dir() == Path.home() / ".config" / "howl"


def test_config_path(monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", "/tmp/xdg")
    assert paths.config_path() == Path("/tmp/xdg/howl/.env")


def test_log_path(monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", "/tmp/xdg")
    assert paths.log_path() == Path("/tmp/xdg/howl/setup.log")


def test_token_path(monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", "/tmp/xdg")
    assert paths.token_path() == Path("/tmp/xdg/howl/.igdb_token.json")


def test_ensure_config_dir_creates_with_restrictive_perms(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    paths.ensure_config_dir()
    created = tmp_path / "howl"
    assert created.is_dir()
    assert (os.stat(created).st_mode & 0o777) == 0o700
