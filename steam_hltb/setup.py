import traceback
from datetime import datetime
from pathlib import Path

from steam_hltb.paths import (
    config_path as _config_path,
)
from steam_hltb.paths import (
    ensure_config_dir,
)
from steam_hltb.paths import (
    log_path as _log_path,
)
from steam_hltb.setup_prompts import _prompt_api_key, _prompt_username, _prompt_vdf_path

# --- caminhos de configuração: ver steam_hltb/paths.py ---


def _log_error(msg: str) -> None:
    """Grava uma entrada no setup.log. Logging nunca deve quebrar o setup."""
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
    """Escreve as variáveis em ~/.config/howl/.env (dir 0700, arquivo 0600).

    Se confirm_overwrite e já houver valores diferentes para alguma chave,
    pergunta antes de sobrescrever; ao recusar, mantém os valores existentes.
    """
    env_vars = dict(env_vars)
    env_path = _config_path()
    ensure_config_dir()
    existing = _read_env_file(env_path)

    if confirm_overwrite:
        clobbered = [k for k in env_vars if k in existing and existing[k] != env_vars[k]]
        if clobbered:
            print(f"\n  {env_path} já tem valores para: {', '.join(clobbered)}")
            choice = input("  Sobrescrever esses valores? [s/N] ").strip().lower()
            if choice not in ("s", "sim", "y", "yes"):
                for k in clobbered:
                    env_vars[k] = existing[k]
                print("  Mantendo os valores existentes.")

    existing.update(env_vars)
    env_path.write_text("".join(f"{k}={v}\n" for k, v in existing.items()))
    env_path.chmod(0o600)
    return env_path


def _maybe_migrate_legacy_env() -> None:
    """Se houver ./.env no cwd mas ainda não ~/.config/howl/.env, oferece migrar."""
    legacy = Path.cwd() / ".env"
    target = _config_path()
    if not legacy.exists() or target.exists():
        return
    print(f"\n  Encontrei um .env legado em {legacy}")
    print(f"  A partir de agora o howl lê de {target}.")
    choice = input("  Migrar para lá agora? [S/n] ").strip().lower()
    if choice in ("n", "não", "nao"):
        return
    ensure_config_dir()
    target.write_text(legacy.read_text())
    target.chmod(0o600)
    print(f"  Migrado para {target}")
    print(f"  Pode remover o antigo quando quiser: rm {legacy}")


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

    print("\n  IGDB (opcional — scores para jogos delisted/sem Metacritic):")
    print("  1. Acesse https://dev.twitch.tv/console e crie um app")
    print("  2. Category: Website Integration, OAuth Redirect URL: http://localhost")
    print("  3. Copie o Client ID e gere um Client Secret")
    setup_igdb = input("  Configurar IGDB agora? [s/N] ").strip().lower()
    if setup_igdb in ("s", "sim", "y", "yes"):
        igdb_client_id = input("  IGDB Client ID: ").strip()
        igdb_client_secret = input("  IGDB Client Secret: ").strip()
        if igdb_client_id and igdb_client_secret:
            config["IGDB_CLIENT_ID"] = igdb_client_id
            config["IGDB_CLIENT_SECRET"] = igdb_client_secret

    print("\n--- Resumo ---")
    for k, v in config.items():
        display = f"***{v[-4:]}" if "KEY" in k else v
        print(f"  {k}={display}")

    env_path = _write_env(config)
    print(f"\n  Salvo em {env_path}")
    print("\nSetup concluído! Rode 'howl' para começar.\n")


def run_setup(verbose: bool = False) -> None:
    try:
        _run_setup_inner(verbose=verbose)
    except (KeyboardInterrupt, EOFError):
        print("\n\n  Setup cancelado.")
    except Exception as exc:
        _log_error(traceback.format_exc())
        print(f"\n  Erro inesperado durante o setup: {exc}")
        print(f"  Detalhes registrados em {_log_path()}")
        if verbose:
            traceback.print_exc()
