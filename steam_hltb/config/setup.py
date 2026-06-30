import traceback
from datetime import datetime
from pathlib import Path

from .paths import (
    config_path as _config_path,
)
from .paths import (
    ensure_config_dir,
)
from .paths import (
    log_path as _log_path,
)
from .prompts import _prompt_api_key, _prompt_username, _prompt_vdf_path

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
            print(f"\n  {env_path} already has values for: {', '.join(clobbered)}")
            choice = input("  Overwrite these values? [y/N] ").strip().lower()
            if choice not in ("s", "sim", "y", "yes"):
                for k in clobbered:
                    env_vars[k] = existing[k]
                print("  Keeping existing values.")

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
    print(f"\n  Found a legacy .env at {legacy}")
    print(f"  From now on howl reads from {target}.")
    choice = input("  Migrate there now? [Y/n] ").strip().lower()
    if choice in ("n", "não", "nao", "no"):
        return
    ensure_config_dir()
    target.write_text(legacy.read_text())
    target.chmod(0o600)
    print(f"  Migrated to {target}")
    print(f"  You can remove the old one whenever: rm {legacy}")


def _run_setup_inner(verbose: bool = False) -> None:
    print("\n=== howl setup ===\n")

    _maybe_migrate_legacy_env()

    api_key = _prompt_api_key(verbose=verbose)
    username = _prompt_username(api_key, verbose=verbose)
    vdf_path = _prompt_vdf_path()

    config: dict[str, str] = {
        "STEAM_API_KEY": api_key,
        "STEAM_USERNAME": username,
    }
    if vdf_path:
        config["STEAM_VDF_PATH"] = vdf_path

    print("\n  IGDB (optional — scores for delisted/Metacritic-less games):")
    print("  1. Go to https://dev.twitch.tv/console and create an app")
    print("  2. Category: Website Integration, OAuth Redirect URL: http://localhost")
    print("  3. Copy the Client ID and generate a Client Secret")
    setup_igdb = input("  Configure IGDB now? [y/N] ").strip().lower()
    if setup_igdb in ("s", "sim", "y", "yes"):
        igdb_client_id = input("  IGDB Client ID: ").strip()
        igdb_client_secret = input("  IGDB Client Secret: ").strip()
        if igdb_client_id and igdb_client_secret:
            config["IGDB_CLIENT_ID"] = igdb_client_id
            config["IGDB_CLIENT_SECRET"] = igdb_client_secret

    print("\n--- Summary ---")
    for k, v in config.items():
        display = f"***{v[-4:]}" if "KEY" in k else v
        print(f"  {k}={display}")

    env_path = _write_env(config)
    print(f"\n  Saved to {env_path}")
    print("\nSetup complete! Run 'howl' to get started.\n")


def run_setup(verbose: bool = False) -> None:
    try:
        _run_setup_inner(verbose=verbose)
    except (KeyboardInterrupt, EOFError):
        print("\n\n  Setup cancelled.")
    except Exception as exc:
        _log_error(traceback.format_exc())
        print(f"\n  Unexpected error during setup: {exc}")
        print(f"  Details logged to {_log_path()}")
        if verbose:
            traceback.print_exc()
