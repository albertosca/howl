"""Interactive wizard layer: VDF detection, Steam API validation and prompts."""

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
            print(f"\n  [debug] network error validating key: {e}")
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
            print(f"\n  [debug] network error validating username: {e}")
        return None


def _prompt_api_key(verbose: bool = False) -> str:
    existing = os.environ.get("STEAM_API_KEY", "")
    if existing:
        print(f"  STEAM_API_KEY already set (***{existing[-4:]})")
        choice = input("  Use existing? [Y/n] ").strip().lower()
        if choice not in ("n", "não", "nao", "no"):
            return existing

    print("\n  STEAM_API_KEY:")
    print("  1. Go to https://steamcommunity.com/dev/apikey")
    print("  2. Log in with your Steam account")
    print("  3. Fill 'Domain Name' with any value (e.g. localhost)")
    print("  4. Copy the generated key")
    while True:
        key = input("\n  Paste your key: ").strip()
        if not key:
            print("  Key is required.")
            continue
        print("  Validating...", end=" ", flush=True)
        if _validate_api_key(key, verbose=verbose):
            print("OK")
            return key
        print("invalid or no internet.")
        retry = input("  Try again? [Y/n] ").strip().lower()
        if retry in ("n", "não", "nao", "no"):
            print("  Proceeding with the provided key (not validated).")
            return key


def _prompt_username(api_key: str, verbose: bool = False) -> str:
    existing = os.environ.get("STEAM_USERNAME", "")
    if existing:
        print(f"\n  STEAM_USERNAME already set: {existing}")
        choice = input("  Use existing? [Y/n] ").strip().lower()
        if choice not in ("n", "não", "nao", "no"):
            return existing

    print("\n  STEAM_USERNAME:")
    print("  This is the vanity URL of your Steam profile.")
    print("  e.g. steamcommunity.com/id/gabelogannewell → username is gabelogannewell")
    while True:
        username = input("\n  Your username: ").strip()
        if not username:
            print("  Username is required.")
            continue
        print("  Validating...", end=" ", flush=True)
        steamid = _validate_username(api_key, username, verbose=verbose)
        if steamid:
            print(f"OK (SteamID: {steamid})")
            return username
        print("not found.")
        retry = input("  Try again? [Y/n] ").strip().lower()
        if retry in ("n", "não", "nao", "no"):
            print("  Proceeding with the provided username (not validated).")
            return username


def _prompt_vdf_path() -> str | None:
    existing = os.environ.get("STEAM_VDF_PATH", "")
    if existing:
        print(f"\n  STEAM_VDF_PATH already set: {existing}")
        choice = input("  Use existing? [Y/n] ").strip().lower()
        if choice not in ("n", "não", "nao", "no"):
            return existing

    print("\n  STEAM_VDF_PATH (optional — required for collection filters):")
    detected = _detect_vdf_paths()
    if detected:
        print(f"  Found {len(detected)} VDF file(s):")
        for i, path in enumerate(detected, 1):
            print(f"  {i}. {path}")
        choice = input(f"  Choose [1-{len(detected)}] or Enter to skip: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(detected):
            return detected[int(choice) - 1]
        return None

    print("  No VDF detected automatically.")
    manual = input("  Paste the path manually (or Enter to skip): ").strip()
    return manual if manual else None
