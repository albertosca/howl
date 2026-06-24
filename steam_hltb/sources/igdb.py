"""Client IGDB com OAuth automático via Twitch client_credentials."""

import json
import re
import sys
import time
from datetime import UTC, datetime
from difflib import SequenceMatcher
from typing import Any

import requests

from ..config import paths

IGDB_API = "https://api.igdb.com/v4"
TWITCH_URL = "https://id.twitch.tv/oauth2/token"
MIN_RATING_COUNT = 3
HTTP_TIMEOUT = 15  # segundos — evita travar indefinidamente se a API pendurar
_TOKEN_EXPIRY_MARGIN_S = 60  # renova o token 60s antes de expirar (folga de relógio)

# Sufixos após separador (-–:) que indicam edição especial/DLC.
# (?:the\s+)? cobre "The Definitive Edition", "The Complete Edition", etc.
_EDITION_RE = re.compile(
    r"\s*[-–:]\s*(?:the\s+)?(?:gold|deluxe|complete|goty|game of the year|enhanced|"
    r"definitive|ultimate|special|premium|season pass|anniversary|director'?s cut|"
    r"legendary|commander|titans?|remaster(?:ed)?|censored)(?:\s+(?:edition|version))?\s*$",
    re.IGNORECASE,
)
# Palavras-chave de edição coladas ao nome sem separador: "Borderlands GOTY Enhanced".
# Aplicado após _EDITION_RE; aceita múltiplas keywords em sequência.
_STANDALONE_EDITION_RE = re.compile(
    r"(?:\s+(?:goty|enhanced|remastered?|deluxe|ultimate|gold|complete|"
    r"definitive|special|anniversary|legendary))+\s*$",
    re.IGNORECASE,
)
_TRADEMARK_RE = re.compile(r"[™®©]")
_IGDB_MIN_SIMILARITY = 0.6  # abaixo disso o resultado é um jogo diferente


# ---------------------------------------------------------------------------
# Token management
# ---------------------------------------------------------------------------


def _load_token() -> dict[str, Any] | None:
    token_file = paths.token_path()
    if not token_file.exists():
        return None
    with token_file.open() as f:
        data: dict[str, Any] = json.load(f)
    return data


def _save_token(access_token: str, expires_at: float) -> None:
    paths.ensure_config_dir()
    with paths.token_path().open("w") as f:
        json.dump({"access_token": access_token, "expires_at": expires_at}, f)


def _refresh_token(client_id: str, client_secret: str) -> tuple[str, float]:
    resp = requests.post(
        TWITCH_URL,
        params={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        },
        timeout=HTTP_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    expires_at: float = time.time() + data["expires_in"] - _TOKEN_EXPIRY_MARGIN_S
    access_token: str = data["access_token"]
    _save_token(access_token, expires_at)
    return access_token, expires_at


def get_token(client_id: str | None, client_secret: str | None) -> str | None:
    if not client_id or not client_secret:
        return None

    cached = _load_token()
    if cached and cached.get("expires_at", 0) > time.time():
        token: str = cached["access_token"]
        return token

    access_token, _ = _refresh_token(client_id, client_secret)
    return access_token


# ---------------------------------------------------------------------------
# Name normalization
# ---------------------------------------------------------------------------


def _normalize_for_igdb(name: str) -> str:
    # "Assassin's Creed® IV - Gold Edition" → "Assassin's Creed IV"
    # "Borderlands GOTY Enhanced" → "Borderlands"
    name = _TRADEMARK_RE.sub("", name)
    name = _EDITION_RE.sub("", name)
    name = _STANDALONE_EDITION_RE.sub("", name)
    return name.strip()


def _name_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


# ---------------------------------------------------------------------------
# API calls
# ---------------------------------------------------------------------------


def _post(client_id: str, token: str, endpoint: str, body: str) -> list[dict[str, Any]]:
    resp = requests.post(
        f"{IGDB_API}/{endpoint}",
        headers={
            "Client-ID": client_id,
            "Authorization": f"Bearer {token}",
        },
        data=body,
        timeout=HTTP_TIMEOUT,
    )
    if not resp.ok:
        print(f"IGDB API error {resp.status_code}: {resp.text[:200]}", file=sys.stderr)
        return []
    results: list[dict[str, Any]] = resp.json()
    return results


def _parse_result(data: dict[str, Any]) -> dict[str, Any] | None:
    # Com count < MIN_RATING_COUNT, ainda salva gêneros/ano — rating seria pouco confiável.
    genres = [g["name"] for g in data.get("genres") or []]
    ts = data.get("first_release_date")
    release_year: int | None = datetime.fromtimestamp(ts, tz=UTC).year if ts else None
    count = data.get("aggregated_rating_count", 0) or 0

    if count < MIN_RATING_COUNT:
        if not genres and release_year is None:
            return None
        # Rating insuficiente mas tem gêneros/ano — retorna resultado parcial
        return {
            "aggregated_rating": None,
            "aggregated_rating_count": count,
            "genres": genres,
            "release_year": release_year,
        }

    rating = data.get("aggregated_rating")
    return {
        "aggregated_rating": round(rating) if rating is not None else None,
        "aggregated_rating_count": count,
        "genres": genres,
        "release_year": release_year,
    }


def fetch_by_appid(
    client_id: str | None, token: str | None, appid: int, *, verbose: bool = False
) -> dict[str, Any] | None:
    # external_games.category = 1 é o código Steam na API do IGDB.
    if not client_id or not token:
        return None

    body = (
        f"fields name,aggregated_rating,aggregated_rating_count,genres.name,first_release_date; "
        f'where external_games.category = 1 & external_games.uid = "{appid}"; limit 1;'
    )
    results = _post(client_id, token, "games", body)
    if not results:
        if verbose:
            print(f"    appid {appid}: não encontrado no IGDB", file=sys.stderr)
        return None
    igdb_name = results[0].get("name", "")
    result = _parse_result(results[0])
    if verbose:
        count = results[0].get("aggregated_rating_count", 0) or 0
        if result is None:
            print(
                f"    appid {appid}: '{igdb_name}' encontrado mas descartado"
                f" (count={count} < {MIN_RATING_COUNT}, sem gêneros/ano)",
                file=sys.stderr,
            )
        else:
            print(f"    appid {appid}: '{igdb_name}' ✓", file=sys.stderr)
    return result


def fetch_by_name(
    client_id: str | None, token: str | None, name: str, *, verbose: bool = False
) -> dict[str, Any] | None:
    if not client_id or not token:
        return None

    normalized = _normalize_for_igdb(name)
    safe = normalized.replace('"', '\\"')
    body = (
        "fields name,aggregated_rating,aggregated_rating_count,genres.name,first_release_date; "
        f'search "{safe}"; limit 1;'
    )
    results = _post(client_id, token, "games", body)
    if not results:
        if verbose:
            print(f"    nome '{normalized}': sem resultados na API", file=sys.stderr)
        return None

    igdb_name = results[0].get("name", "")
    sim = _name_similarity(normalized, igdb_name)
    if sim < _IGDB_MIN_SIMILARITY:
        if verbose:
            print(
                f"    nome '{normalized}': API retornou '{igdb_name}'"
                f" (sim={sim:.2f} < {_IGDB_MIN_SIMILARITY}, descartado)",
                file=sys.stderr,
            )
        return None

    result = _parse_result(results[0])
    if verbose:
        count = results[0].get("aggregated_rating_count", 0) or 0
        if result is None:
            print(
                f"    nome '{normalized}' → '{igdb_name}' (sim={sim:.2f})"
                f" mas descartado (count={count} < {MIN_RATING_COUNT}, sem gêneros/ano)",
                file=sys.stderr,
            )
        else:
            print(
                f"    nome '{normalized}' → '{igdb_name}' (sim={sim:.2f}) ✓",
                file=sys.stderr,
            )
    return result
