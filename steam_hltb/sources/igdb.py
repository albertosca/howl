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

# Sufixos que indicam edição especial / DLC — não fazem parte do nome canônico.
# (?:the\s+)? cobre variantes como "The Definitive Edition", "The Complete Edition".
_EDITION_RE = re.compile(
    r"\s*[-–:]\s*(?:the\s+)?(?:gold|deluxe|complete|goty|game of the year|enhanced|"
    r"definitive|ultimate|special|premium|season pass|anniversary|director'?s cut|"
    r"legendary|commander|titans?|remaster(?:ed)?|censored)(?:\s+(?:edition|version))?\s*$",
    re.IGNORECASE,
)
_TRADEMARK_RE = re.compile(r"[™®©]")
_IGDB_MIN_SIMILARITY = 0.6  # abaixo disso o resultado é um jogo diferente


# ---------------------------------------------------------------------------
# Token management
# ---------------------------------------------------------------------------


def _load_token() -> dict[str, Any] | None:
    """Lê ~/.config/howl/.igdb_token.json se existir."""
    token_file = paths.token_path()
    if not token_file.exists():
        return None
    with token_file.open() as f:
        data: dict[str, Any] = json.load(f)
    return data


def _save_token(access_token: str, expires_at: float) -> None:
    """Salva token em ~/.config/howl/.igdb_token.json."""
    paths.ensure_config_dir()
    with paths.token_path().open("w") as f:
        json.dump({"access_token": access_token, "expires_at": expires_at}, f)


def _refresh_token(client_id: str, client_secret: str) -> tuple[str, float]:
    """Obtém novo token via Twitch client_credentials, salva e retorna (token, expires_at)."""
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
    """
    Retorna token válido para a API IGDB.
    - Se client_id/secret ausentes: retorna None
    - Se token em cache e não expirado: usa cache
    - Caso contrário: chama _refresh_token
    """
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
    """Remove ™/® e sufixos de edição/DLC para busca mais precisa no IGDB.

    Ex: "Assassin's Creed® IV Black Flag - Gold Edition" →
        "Assassin's Creed IV Black Flag"
    """
    name = _TRADEMARK_RE.sub("", name)
    name = _EDITION_RE.sub("", name)
    return name.strip()


def _name_similarity(a: str, b: str) -> float:
    """Similaridade de sequência entre dois nomes (case-insensitive), em [0, 1]."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


# ---------------------------------------------------------------------------
# API calls
# ---------------------------------------------------------------------------


def _post(client_id: str, token: str, endpoint: str, body: str) -> list[dict[str, Any]]:
    """Faz POST na API IGDB e retorna lista de resultados."""
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
    """Extrai rating/genres/release_year do resultado IGDB.

    Se aggregated_rating_count < MIN_RATING_COUNT, ainda salva gêneros e ano
    (quando disponíveis) — só omite o rating, que seria pouco confiável.
    Retorna None apenas quando não há absolutamente nada útil.
    """
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


def fetch_by_appid(client_id: str | None, token: str | None, appid: int) -> dict[str, Any] | None:
    """Busca jogo no IGDB pelo Steam appid (external_games.category = 1)."""
    if not client_id or not token:
        return None

    body = (
        f"fields name,aggregated_rating,aggregated_rating_count,genres.name,first_release_date; "
        f'where external_games.category = 1 & external_games.uid = "{appid}"; limit 1;'
    )
    results = _post(client_id, token, "games", body)
    if not results:
        return None
    return _parse_result(results[0])


def fetch_by_name(client_id: str | None, token: str | None, name: str) -> dict[str, Any] | None:
    """Busca jogo por nome normalizado, validando similaridade com o resultado.

    Normaliza o nome antes de buscar (remove ™/® e sufixos de edição) para
    evitar mismatches com jogos como "Assassin's Creed® IV - Gold Edition".
    Descarta resultados com similaridade < _IGDB_MIN_SIMILARITY (jogo errado).
    """
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
        return None

    igdb_name = results[0].get("name", "")
    if _name_similarity(normalized, igdb_name) < _IGDB_MIN_SIMILARITY:
        return None

    return _parse_result(results[0])
