import glob
import os
import pytest
from unittest.mock import patch, MagicMock

import steam_hltb.setup as setup


# --- _detect_vdf_paths ---

def test_detect_vdf_paths_macos(monkeypatch, tmp_path):
    vdf = tmp_path / "sharedconfig.vdf"
    vdf.touch()
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    with patch("glob.glob", return_value=[str(vdf)]) as mock_glob:
        result = setup._detect_vdf_paths()
    assert result == [str(vdf)]
    called_pattern = mock_glob.call_args[0][0]
    assert "Library/Application Support/Steam" in called_pattern


def test_detect_vdf_paths_linux(monkeypatch):
    monkeypatch.setattr("platform.system", lambda: "Linux")
    with patch("glob.glob", return_value=[]) as mock_glob:
        setup._detect_vdf_paths()
    called_pattern = mock_glob.call_args[0][0]
    assert ".steam/steam" in called_pattern


def test_detect_vdf_paths_unknown_system(monkeypatch):
    monkeypatch.setattr("platform.system", lambda: "FreeBSD")
    result = setup._detect_vdf_paths()
    assert result == []


# --- _validate_api_key ---

def test_validate_api_key_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with patch("requests.get", return_value=mock_resp):
        assert setup._validate_api_key("VALIDKEY") is True


def test_validate_api_key_failure():
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    with patch("requests.get", return_value=mock_resp):
        assert setup._validate_api_key("BADKEY") is False


def test_validate_api_key_network_error():
    with patch("requests.get", side_effect=Exception("timeout")):
        assert setup._validate_api_key("KEY") is False


# --- _validate_username ---

def test_validate_username_found():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": {"success": 1, "steamid": "76561198012345"}}
    with patch("requests.get", return_value=mock_resp):
        result = setup._validate_username("KEY", "gabelogannewell")
    assert result == "76561198012345"


def test_validate_username_not_found():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": {"success": 42, "message": "No match"}}
    with patch("requests.get", return_value=mock_resp):
        result = setup._validate_username("KEY", "nonexistent")
    assert result is None


def test_validate_username_network_error():
    with patch("requests.get", side_effect=Exception("timeout")):
        assert setup._validate_username("KEY", "user") is None


# --- _config_path ---

def test_config_path_respects_xdg(monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", "/tmp/xdg")
    assert setup._config_path() == "/tmp/xdg/howl/.env"
    assert setup._log_path() == "/tmp/xdg/howl/setup.log"


def test_config_path_default(monkeypatch):
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setattr("os.path.expanduser", lambda p: p.replace("~", "/home/u"))
    assert setup._config_path() == "/home/u/.config/howl/.env"


# --- _write_env ---

def test_write_env_creates_file(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    path = setup._write_env({"STEAM_API_KEY": "ABC123", "STEAM_USERNAME": "gabelogannewell"})
    assert path == str(tmp_path / "howl" / ".env")
    content = open(path).read()
    assert "STEAM_API_KEY=ABC123" in content
    assert "STEAM_USERNAME=gabelogannewell" in content


def test_write_env_sets_restrictive_permissions(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    path = setup._write_env({"STEAM_API_KEY": "ABC123"})
    assert (os.stat(path).st_mode & 0o777) == 0o600
    assert (os.stat(tmp_path / "howl").st_mode & 0o777) == 0o700


def test_write_env_merges_with_existing(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    cfg = tmp_path / "howl"
    cfg.mkdir()
    (cfg / ".env").write_text("EXISTING_VAR=old\nSTEAM_API_KEY=old_key\n")
    # confirm_overwrite=False evita o prompt; merge mantém EXISTING_VAR
    setup._write_env({"STEAM_API_KEY": "new_key"}, confirm_overwrite=False)
    content = open(cfg / ".env").read()
    assert "EXISTING_VAR=old" in content
    assert "STEAM_API_KEY=new_key" in content
    assert "old_key" not in content


def test_write_env_overwrite_confirmed(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    cfg = tmp_path / "howl"
    cfg.mkdir()
    (cfg / ".env").write_text("STEAM_API_KEY=old_key\n")
    with patch("builtins.input", return_value="s"):
        setup._write_env({"STEAM_API_KEY": "new_key"})
    assert "STEAM_API_KEY=new_key" in open(cfg / ".env").read()


def test_write_env_overwrite_declined_keeps_old(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    cfg = tmp_path / "howl"
    cfg.mkdir()
    (cfg / ".env").write_text("STEAM_API_KEY=old_key\n")
    with patch("builtins.input", return_value="n"):
        setup._write_env({"STEAM_API_KEY": "new_key"})
    content = open(cfg / ".env").read()
    assert "STEAM_API_KEY=old_key" in content
    assert "new_key" not in content


# --- _maybe_migrate_legacy_env ---

def test_migrate_legacy_env_copies_and_chmods(tmp_path, monkeypatch):
    home = tmp_path / "config"
    cwd = tmp_path / "repo"
    cwd.mkdir()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home))
    monkeypatch.chdir(cwd)
    (cwd / ".env").write_text("STEAM_API_KEY=legacy\n")
    with patch("builtins.input", return_value="s"):
        setup._maybe_migrate_legacy_env()
    target = home / "howl" / ".env"
    assert target.exists()
    assert "STEAM_API_KEY=legacy" in target.read_text()
    assert (os.stat(target).st_mode & 0o777) == 0o600


def test_migrate_legacy_env_skips_when_target_exists(tmp_path, monkeypatch):
    home = tmp_path / "config"
    cwd = tmp_path / "repo"
    cwd.mkdir()
    (home / "howl").mkdir(parents=True)
    (home / "howl" / ".env").write_text("STEAM_API_KEY=current\n")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home))
    monkeypatch.chdir(cwd)
    (cwd / ".env").write_text("STEAM_API_KEY=legacy\n")
    # não deve nem perguntar; se perguntasse, o input quebraria
    setup._maybe_migrate_legacy_env()
    assert "current" in (home / "howl" / ".env").read_text()


def test_migrate_legacy_env_declined(tmp_path, monkeypatch):
    home = tmp_path / "config"
    cwd = tmp_path / "repo"
    cwd.mkdir()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home))
    monkeypatch.chdir(cwd)
    (cwd / ".env").write_text("STEAM_API_KEY=legacy\n")
    with patch("builtins.input", return_value="n"):
        setup._maybe_migrate_legacy_env()
    assert not (home / "howl" / ".env").exists()


# --- run_setup: robustez ---

def test_run_setup_graceful_on_interrupt(capsys, monkeypatch):
    monkeypatch.setattr(setup, "_run_setup_inner", lambda verbose: (_ for _ in ()).throw(KeyboardInterrupt))
    setup.run_setup()  # não deve propagar
    assert "cancelado" in capsys.readouterr().out.lower()


def test_run_setup_logs_unexpected_error(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    def boom(verbose):
        raise RuntimeError("kaboom")
    monkeypatch.setattr(setup, "_run_setup_inner", boom)
    setup.run_setup()  # não deve propagar
    out = capsys.readouterr().out
    assert "kaboom" in out
    log = tmp_path / "howl" / "setup.log"
    assert log.exists()
    assert "kaboom" in log.read_text()
