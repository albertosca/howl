import traceback
from datetime import datetime
from pathlib import Path

from ..i18n import set_language, t
from .paths import (
    config_path as _config_path,
)
from .paths import (
    ensure_config_dir,
)
from .paths import (
    log_path as _log_path,
)
from .prompts import (
    _is_no,
    _is_yes,
    _prompt_api_key,
    _prompt_language,
    _prompt_username,
    _prompt_vdf_path,
)

# --- config paths: see steam_hltb/config/paths.py ---


def _log_error(msg: str) -> None:
    """Appends an entry to setup.log. Logging must never break setup."""
    try:
        ensure_config_dir()
        with _log_path().open("a") as f:
            ts = datetime.now().isoformat(timespec="seconds")
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass


def _read_env_file(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                result[k.strip()] = v.strip()
    return result


def _write_env(env_vars: dict[str, str], confirm_overwrite: bool = True) -> Path:
    """Writes variables to ~/.config/howl/.env (dir 0700, file 0600).

    If confirm_overwrite and any key already has a different value,
    asks before overwriting; on refusal, keeps the existing values.
    """
    env_vars = dict(env_vars)
    env_path = _config_path()
    ensure_config_dir()
    existing = _read_env_file(env_path)

    if confirm_overwrite:
        clobbered = [k for k in env_vars if k in existing and existing[k] != env_vars[k]]
        if clobbered:
            print(t("setup.already_has", path=env_path, keys=", ".join(clobbered)))
            choice = input(t("setup.prompt_overwrite")).strip().lower()
            if not _is_yes(choice):
                for k in clobbered:
                    env_vars[k] = existing[k]
                print(t("setup.keeping_existing"))

    existing.update(env_vars)
    env_path.write_text("".join(f"{k}={v}\n" for k, v in existing.items()))
    env_path.chmod(0o600)
    return env_path


def _maybe_migrate_legacy_env() -> None:
    """If ./.env exists in cwd but ~/.config/howl/.env does not, offers to migrate."""
    legacy = Path.cwd() / ".env"
    target = _config_path()
    if not legacy.exists() or target.exists():
        return
    print(t("setup.legacy_found", path=legacy))
    print(t("setup.legacy_now_reads", path=target))
    choice = input(t("setup.prompt_migrate")).strip().lower()
    if _is_no(choice):
        return
    ensure_config_dir()
    target.write_text(legacy.read_text())
    target.chmod(0o600)
    print(t("setup.legacy_migrated", path=target))
    print(t("setup.legacy_remove_hint", path=legacy))


def _run_setup_inner(verbose: bool = False) -> None:
    language = _prompt_language()
    set_language(language)

    print(t("setup.header"))

    _maybe_migrate_legacy_env()

    api_key = _prompt_api_key(verbose=verbose)
    username = _prompt_username(api_key, verbose=verbose)
    vdf_path = _prompt_vdf_path()

    config: dict[str, str] = {
        "HOWL_LANG": language,
        "STEAM_API_KEY": api_key,
        "STEAM_USERNAME": username,
    }
    if vdf_path:
        config["STEAM_VDF_PATH"] = vdf_path

    print(t("setup.igdb_intro"))
    print(t("setup.igdb_step1"))
    print(t("setup.igdb_step2"))
    print(t("setup.igdb_step3"))
    setup_igdb = input(t("setup.prompt_igdb_now")).strip().lower()
    if _is_yes(setup_igdb):
        igdb_client_id = input(t("setup.prompt_igdb_id")).strip()
        igdb_client_secret = input(t("setup.prompt_igdb_secret")).strip()
        if igdb_client_id and igdb_client_secret:
            config["IGDB_CLIENT_ID"] = igdb_client_id
            config["IGDB_CLIENT_SECRET"] = igdb_client_secret

    print(t("setup.summary"))
    for k, v in config.items():
        display = f"***{v[-4:]}" if "KEY" in k else v
        print(f"  {k}={display}")

    env_path = _write_env(config)
    print(t("setup.saved", path=env_path))
    print(t("setup.complete"))


def run_setup(verbose: bool = False) -> None:
    try:
        _run_setup_inner(verbose=verbose)
    except (KeyboardInterrupt, EOFError):
        print(t("setup.cancelled"))
    except Exception as exc:
        _log_error(traceback.format_exc())
        print(t("setup.unexpected_error", error=exc))
        print(t("setup.error_logged", path=_log_path()))
        if verbose:
            traceback.print_exc()
