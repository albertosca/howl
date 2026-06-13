import glob
import os
import platform

import requests


def _detect_vdf_paths() -> list[str]:
    system = platform.system()
    if system == "Darwin":
        pattern = os.path.expanduser(
            "~/Library/Application Support/Steam/userdata/*/7/remote/sharedconfig.vdf"
        )
    elif system == "Linux":
        pattern = os.path.expanduser(
            "~/.steam/steam/userdata/*/7/remote/sharedconfig.vdf"
        )
    elif system == "Windows":
        pattern = "C:/Program Files (x86)/Steam/userdata/*/7/remote/sharedconfig.vdf"
    else:
        return []
    return sorted(glob.glob(pattern))


def _validate_api_key(key: str) -> bool:
    try:
        resp = requests.get(
            "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/",
            params={"key": key, "vanityurl": "valve"},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def _validate_username(key: str, username: str) -> str | None:
    try:
        resp = requests.get(
            "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/",
            params={"key": key, "vanityurl": username},
            timeout=5,
        )
        data = resp.json().get("response", {})
        if data.get("success") == 1:
            return data["steamid"]
        return None
    except Exception:
        return None


def _write_env(env_vars: dict[str, str]) -> str:
    env_path = os.path.join(os.getcwd(), ".env")
    existing: dict[str, str] = {}
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, _, v = line.partition("=")
                    existing[k.strip()] = v.strip()
    existing.update(env_vars)
    with open(env_path, "w") as f:
        for k, v in existing.items():
            f.write(f"{k}={v}\n")
    return env_path


def _prompt_api_key() -> str:
    existing = os.environ.get("STEAM_API_KEY", "")
    if existing:
        print(f"  STEAM_API_KEY já definida (***{existing[-4:]})")
        choice = input("  Usar a existente? [S/n] ").strip().lower()
        if choice not in ("n", "não", "nao"):
            return existing

    print("\n  STEAM_API_KEY:")
    print("  1. Acesse https://steamcommunity.com/dev/apikey")
    print("  2. Faça login com sua conta Steam")
    print("  3. Preencha 'Domain Name' com qualquer valor (ex: localhost)")
    print("  4. Copie a chave gerada")
    while True:
        key = input("\n  Cole sua chave: ").strip()
        if not key:
            print("  Chave obrigatória.")
            continue
        print("  Validando...", end=" ", flush=True)
        if _validate_api_key(key):
            print("OK")
            return key
        print("inválida ou sem internet.")
        retry = input("  Tentar de novo? [S/n] ").strip().lower()
        if retry in ("n", "não", "nao"):
            return key


def _prompt_username(api_key: str) -> str:
    existing = os.environ.get("STEAM_USERNAME", "")
    if existing:
        print(f"\n  STEAM_USERNAME já definida: {existing}")
        choice = input("  Usar a existente? [S/n] ").strip().lower()
        if choice not in ("n", "não", "nao"):
            return existing

    print("\n  STEAM_USERNAME:")
    print("  É a vanity URL do seu perfil Steam.")
    print("  Ex: steamcommunity.com/id/gabelogannewell → username é gabelogannewell")
    while True:
        username = input("\n  Seu username: ").strip()
        if not username:
            print("  Username obrigatório.")
            continue
        print("  Validando...", end=" ", flush=True)
        steamid = _validate_username(api_key, username)
        if steamid:
            print(f"OK (SteamID: {steamid})")
            return username
        print("não encontrado.")
        retry = input("  Tentar de novo? [S/n] ").strip().lower()
        if retry in ("n", "não", "nao"):
            return username


def _prompt_vdf_path() -> str | None:
    existing = os.environ.get("STEAM_VDF_PATH", "")
    if existing:
        print(f"\n  STEAM_VDF_PATH já definida: {existing}")
        choice = input("  Usar a existente? [S/n] ").strip().lower()
        if choice not in ("n", "não", "nao"):
            return existing

    print("\n  STEAM_VDF_PATH (opcional — necessário para filtros de coleção):")
    detected = _detect_vdf_paths()
    if detected:
        print(f"  Encontrado(s) {len(detected)} arquivo(s) VDF:")
        for i, path in enumerate(detected, 1):
            print(f"  {i}. {path}")
        choice = input(f"  Escolha [1-{len(detected)}] ou Enter para pular: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(detected):
            return detected[int(choice) - 1]
        return None

    print("  Nenhum VDF detectado automaticamente.")
    manual = input("  Cole o caminho manualmente (ou Enter para pular): ").strip()
    return manual if manual else None


def run_setup() -> None:
    print("\n=== howl setup ===\n")

    api_key  = _prompt_api_key()
    username = _prompt_username(api_key)
    vdf_path = _prompt_vdf_path()

    config: dict[str, str] = {
        "STEAM_API_KEY":  api_key,
        "STEAM_USERNAME": username,
    }
    if vdf_path:
        config["STEAM_VDF_PATH"] = vdf_path

    print("\n--- Resumo ---")
    for k, v in config.items():
        display = f"***{v[-4:]}" if "KEY" in k else v
        print(f"  {k}={display}")

    print("\nOnde salvar?")
    print("  1. .env local (carregado automaticamente pelo howl)")
    print("  2. Mostrar bloco pra colar no ~/.zshenv (persistente no sistema)")
    print("  3. Ambos")
    dest = input("  Escolha [1/2/3]: ").strip()

    if dest in ("1", "3"):
        env_path = _write_env(config)
        print(f"  Salvo em {env_path}")

    if dest in ("2", "3"):
        print("\n  Cole no seu ~/.zshenv ou ~/.zprofile e rode 'source ~/.zshenv':")
        print("  " + "-" * 50)
        for k, v in config.items():
            print(f"  export {k}={v}")
        print("  " + "-" * 50)

    if dest not in ("1", "2", "3"):
        print("  Nenhum destino selecionado — nada foi salvo.")
        print("  Rode 'howl --setup' de novo para configurar.\n")
        return

    print("\nSetup concluído! Rode 'howl' para começar.\n")
