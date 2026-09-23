import os
from pathlib import Path

from steam_hltb.config import paths


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


def test_cache_dir_respects_xdg(monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", "/tmp/xdg-cache")
    assert paths.cache_dir() == Path("/tmp/xdg-cache/howl")


def test_cache_dir_default(monkeypatch):
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    assert paths.cache_dir() == Path.home() / ".cache" / "howl"


def test_cache_dir_howl_override_wins_over_xdg(monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", "/tmp/xdg-cache")
    monkeypatch.setenv("HOWL_CACHE_DIR", "/tmp/custom")
    assert paths.cache_dir() == Path("/tmp/custom")


def test_games_cache_path(monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", "/tmp/xdg-cache")
    assert paths.games_cache_path() == Path("/tmp/xdg-cache/howl/games_cache.json")


def test_overrides_path(monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", "/tmp/xdg")
    assert paths.overrides_path() == Path("/tmp/xdg/howl/howl_overrides.json")


def test_migrate_legacy_file_copies_and_keeps_original(tmp_path, capsys):
    legacy = tmp_path / "old.json"
    legacy.write_text('{"a": 1}')
    target = tmp_path / "new" / "dir" / "file.json"
    paths.migrate_legacy_file(legacy, target)
    assert target.read_text() == '{"a": 1}'
    assert legacy.exists()
    out = capsys.readouterr().out
    assert str(legacy) in out
    assert str(target) in out


def test_migrate_legacy_file_never_overwrites_target(tmp_path, capsys):
    legacy = tmp_path / "old.json"
    legacy.write_text("old")
    target = tmp_path / "file.json"
    target.write_text("current")
    paths.migrate_legacy_file(legacy, target)
    assert target.read_text() == "current"
    assert capsys.readouterr().out == ""


def test_migrate_legacy_file_noop_without_legacy(tmp_path, capsys):
    target = tmp_path / "file.json"
    paths.migrate_legacy_file(tmp_path / "missing.json", target)
    assert not target.exists()
    assert capsys.readouterr().out == ""
