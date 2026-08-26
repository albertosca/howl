"""Interactive wizard layer: VDF detection, Steam API validation and prompts."""

import os
import platform
from pathlib import Path

import requests

from ..i18n import t

_YES = ("y", "yes", "s", "sim")
_NO = ("n", "no", "nao")


def _is_yes(answer: str) -> bool:
    return answer.strip().lower() in (*_YES, t("setup.answer_yes"))


def _is_no(answer: str) -> bool:
    return answer.strip().lower() in (*_NO, t("setup.answer_no"))


_LANGUAGE_CHOICES: dict[str, str] = {"1": "en", "2": "pt-BR"}


def _prompt_language() -> str:
    """The one prompt that cannot use the catalog: it runs before a language exists."""
    print("\n  Language / Idioma:")
    print("    [1] English")
    print("    [2] Português")
    return _LANGUAGE_CHOICES.get(input("  Choose / Escolha [1]: ").strip(), "en")


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
            print(t("setup.debug_valve", status=resp.status_code))
        return resp.status_code == 200
    except Exception as e:
        if verbose:
            print(t("setup.debug_key_neterr", error=e))
        return False


def _validate_username(key: str, username: str, verbose: bool = False) -> str | None:
    try:
        resp = requests.get(
            "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/",
            params={"key": key, "vanityurl": username},
            timeout=5,
        )
        if verbose:
            print(t("setup.debug_resolve", host=username, status=resp.status_code))
        data = resp.json().get("response", {})
        if data.get("success") == 1:
            steamid: str = data["steamid"]
            return steamid
        return None
    except Exception as e:
        if verbose:
            print(t("setup.debug_user_neterr", error=e))
        return None


def _prompt_api_key(verbose: bool = False) -> str:
    existing = os.environ.get("STEAM_API_KEY", "")
    if existing:
        print(t("setup.api_key_present", suffix=existing[-4:]))
        choice = input(t("setup.prompt_use_existing")).strip().lower()
        if not _is_no(choice):
            return existing

    print(t("setup.api_key_title"))
    print(t("setup.api_key_step1"))
    print(t("setup.api_key_step2"))
    print(t("setup.api_key_step3"))
    print(t("setup.api_key_step4"))
    while True:
        key = input(t("setup.prompt_key")).strip()
        if not key:
            print(t("setup.key_required"))
            continue
        print(t("setup.validating"), end=" ", flush=True)
        if _validate_api_key(key, verbose=verbose):
            print("OK")
            return key
        print(t("setup.key_invalid"))
        retry = input(t("setup.prompt_retry")).strip().lower()
        if _is_no(retry):
            print(t("setup.key_unvalidated"))
            return key


def _prompt_username(api_key: str, verbose: bool = False) -> str:
    existing = os.environ.get("STEAM_USERNAME", "")
    if existing:
        print(t("setup.username_present", username=existing))
        choice = input(t("setup.prompt_use_existing")).strip().lower()
        if not _is_no(choice):
            return existing

    print(t("setup.username_title"))
    print(t("setup.username_explain"))
    print(t("setup.username_example"))
    while True:
        username = input(t("setup.prompt_username")).strip()
        if not username:
            print(t("setup.username_required"))
            continue
        print(t("setup.validating"), end=" ", flush=True)
        steamid = _validate_username(api_key, username, verbose=verbose)
        if steamid:
            print(t("setup.username_ok", steamid=steamid))
            return username
        print(t("setup.username_not_found"))
        retry = input(t("setup.prompt_retry")).strip().lower()
        if _is_no(retry):
            print(t("setup.username_unvalidated"))
            return username


def _prompt_vdf_path() -> str | None:
    existing = os.environ.get("STEAM_VDF_PATH", "")
    if existing:
        print(t("setup.vdf_present", path=existing))
        choice = input(t("setup.prompt_use_existing")).strip().lower()
        if not _is_no(choice):
            return existing

    print(t("setup.vdf_title"))
    detected = _detect_vdf_paths()
    if detected:
        print(t("setup.vdf_found", count=len(detected)))
        for i, path in enumerate(detected, 1):
            print(f"  {i}. {path}")
        choice = input(t("setup.prompt_vdf_choice", max=len(detected))).strip()
        if choice.isdigit() and 1 <= int(choice) <= len(detected):
            return detected[int(choice) - 1]
        return None

    print(t("setup.vdf_none_found"))
    manual = input(t("setup.prompt_vdf_manual")).strip()
    return manual if manual else None
