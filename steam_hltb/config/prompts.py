"""Camada interativa do wizard: detecção de VDF, validação na Steam API e prompts."""

import os
import platform
from pathlib import Path

import requests


def _detect_vdf_paths() -> list[str]:
    system = platform.system()
    if system == "Darwin":
        base = Path.home() / "Library/Application Support/Steam/userdata"
    elif system == "Linux":
        base = Path.home() / ".steam/steam/userdata"
    elif system == "Windows":
        base = Path("C:/Program Files (x86)/Steam/userdata")
    else:
        return []
    return sorted(str(p) for p in base.glob("*/7/remote/sharedconfig.vdf"))


def _validate_api_key(key: str, verbose: bool = False) -> bool:
    try:
        resp = requests.get(
            "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/",
            params={"key": key, "vanityurl": "valve"},
            timeout=5,
        )
        if verbose:
            print(f"\n  [debug] GET ResolveVanityURL (valve) → HTTP {resp.status_code}")
        return resp.status_code == 200
    except Exception as e:
        if verbose:
            print(f"\n  [debug] erro de rede ao validar a chave: {e}")
        return False


def _validate_username(key: str, username: str, verbose: bool = False) -> str | None:
    try:
        resp = requests.get(
            "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/",
            params={"key": key, "vanityurl": username},
            timeout=5,
        )
        if verbose:
            print(f"\n  [debug] GET ResolveVanityURL ({username}) → HTTP {resp.status_code}")
        data = resp.json().get("response", {})
        if data.get("success") == 1:
            steamid: str = data["steamid"]
            return steamid
        return None
    except Exception as e:
        if verbose:
            print(f"\n  [debug] erro de rede ao validar o username: {e}")
        return None


def _prompt_api_key(verbose: bool = False) -> str:
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
        if _validate_api_key(key, verbose=verbose):
            print("OK")
            return key
        print("inválida ou sem internet.")
        retry = input("  Tentar de novo? [S/n] ").strip().lower()
        if retry in ("n", "não", "nao"):
            print("  Seguindo com a chave informada (não validada).")
            return key


def _prompt_username(api_key: str, verbose: bool = False) -> str:
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
        steamid = _validate_username(api_key, username, verbose=verbose)
        if steamid:
            print(f"OK (SteamID: {steamid})")
            return username
        print("não encontrado.")
        retry = input("  Tentar de novo? [S/n] ").strip().lower()
        if retry in ("n", "não", "nao"):
            print("  Seguindo com o username informado (não validado).")
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
