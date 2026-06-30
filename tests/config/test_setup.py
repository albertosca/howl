import os
from pathlib import Path
from unittest.mock import patch

import steam_hltb.config.setup as setup

# --- _config_path ---


def test_config_path_respects_xdg(monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", "/tmp/xdg")
    assert setup._config_path() == Path("/tmp/xdg/howl/.env")
    assert setup._log_path() == Path("/tmp/xdg/howl/setup.log")


def test_config_path_default(monkeypatch):
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    assert setup._config_path() == Path.home() / ".config" / "howl" / ".env"


# --- _write_env ---


def test_write_env_creates_file(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    path = setup._write_env({"STEAM_API_KEY": "ABC123", "STEAM_USERNAME": "gabelogannewell"})
    assert path == tmp_path / "howl" / ".env"
    content = path.read_text()
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
    content = (cfg / ".env").read_text()
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
    assert "STEAM_API_KEY=new_key" in (cfg / ".env").read_text()


def test_write_env_overwrite_declined_keeps_old(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    cfg = tmp_path / "howl"
    cfg.mkdir()
    (cfg / ".env").write_text("STEAM_API_KEY=old_key\n")
    with patch("builtins.input", return_value="n"):
        setup._write_env({"STEAM_API_KEY": "new_key"})
    content = (cfg / ".env").read_text()
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
    monkeypatch.setattr(
        setup, "_run_setup_inner", lambda verbose: (_ for _ in ()).throw(KeyboardInterrupt)
    )
    setup.run_setup()  # não deve propagar
    assert "cancelled" in capsys.readouterr().out.lower()


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


def test_run_setup_verbose_prints_traceback(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    def boom(verbose):
        raise RuntimeError("kaboom")

    monkeypatch.setattr(setup, "_run_setup_inner", boom)
    setup.run_setup(verbose=True)  # verbose → também imprime traceback
    assert "kaboom" in capsys.readouterr().out


def test_log_error_swallows_exceptions(monkeypatch):
    def raise_oserror():
        raise OSError("boom")

    monkeypatch.setattr(setup, "ensure_config_dir", raise_oserror)
    setup._log_error("msg")  # não deve levantar


def test_read_env_file_ignores_comments_and_blanks(tmp_path):
    p = tmp_path / ".env"
    p.write_text("# comment\n\nKEY=val\nnoequals\n")
    assert setup._read_env_file(p) == {"KEY": "val"}


def test_run_setup_inner_full_flow(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)  # sem .env legado no cwd
    monkeypatch.setattr(setup, "_prompt_api_key", lambda verbose=False: "KEY123")
    monkeypatch.setattr(setup, "_prompt_username", lambda api, verbose=False: "bob")
    monkeypatch.setattr(setup, "_prompt_vdf_path", lambda: "/x.vdf")
    inputs = iter(["s", "cid", "csec"])  # IGDB sim + client id/secret
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    setup._run_setup_inner()
    env = (tmp_path / "howl" / ".env").read_text()
    assert "STEAM_API_KEY=KEY123" in env
    assert "STEAM_USERNAME=bob" in env
    assert "STEAM_VDF_PATH=/x.vdf" in env
    assert "IGDB_CLIENT_ID=cid" in env
    assert "IGDB_CLIENT_SECRET=csec" in env


def test_run_setup_inner_igdb_empty_credentials(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(setup, "_prompt_api_key", lambda verbose=False: "K")
    monkeypatch.setattr(setup, "_prompt_username", lambda api, verbose=False: "u")
    monkeypatch.setattr(setup, "_prompt_vdf_path", lambda: None)
    inputs = iter(["s", "", ""])  # IGDB sim mas id/secret vazios → não grava
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    setup._run_setup_inner()
    assert "IGDB_CLIENT_ID" not in (tmp_path / "howl" / ".env").read_text()


def test_run_setup_inner_skips_optional(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(setup, "_prompt_api_key", lambda verbose=False: "K")
    monkeypatch.setattr(setup, "_prompt_username", lambda api, verbose=False: "u")
    monkeypatch.setattr(setup, "_prompt_vdf_path", lambda: None)  # sem VDF
    monkeypatch.setattr("builtins.input", lambda _: "n")  # IGDB não
    setup._run_setup_inner()
    env = (tmp_path / "howl" / ".env").read_text()
    assert "STEAM_VDF_PATH" not in env
    assert "IGDB_CLIENT_ID" not in env
