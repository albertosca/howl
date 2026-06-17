"""Client IGDB com OAuth automático via Twitch client_credentials."""

import json
import os
import time
from datetime import datetime, timezone

import requests

from steam_hltb import paths

IGDB_API = "https://api.igdb.com/v4"
TWITCH_URL = "https://id.twitch.tv/oauth2/token"
MIN_RATING_COUNT = 3


# ---------------------------------------------------------------------------
# Token management
# ---------------------------------------------------------------------------

def _load_token() -> dict | None:
    """Lê ~/.config/howl/.igdb_token.json se existir."""
    token_file = paths.token_path()
    if not os.path.exists(token_file):
        return None
    with open(token_file, "r") as f:
        return json.load(f)


def _save_token(access_token: str, expires_at: float) -> None:
    """Salva token em ~/.config/howl/.igdb_token.json."""
    paths.ensure_config_dir()
    with open(paths.token_path(), "w") as f:
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
    )
    resp.raise_for_status()
    data = resp.json()
    expires_at = time.time() + data["expires_in"] - 60
    access_token = data["access_token"]
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
        return cached["access_token"]

    access_token, _ = _refresh_token(client_id, client_secret)
    return access_token


# ---------------------------------------------------------------------------
# API calls
# ---------------------------------------------------------------------------

def _post(client_id: str, token: str, endpoint: str, body: str) -> list:
    """Faz POST na API IGDB e retorna lista de resultados."""
    resp = requests.post(
        f"{IGDB_API}/{endpoint}",
        headers={
            "Client-ID": client_id,
            "Authorization": f"Bearer {token}",
        },
        data=body,
    )
    if not resp.ok:
        print(f"IGDB API error {resp.status_code}: {resp.text[:200]}", file=__import__('sys').stderr)
        return []
    return resp.json()


def _parse_result(data: dict) -> dict | None:
    """
    Extrai rating/genres/release_year do resultado IGDB.
    Retorna None se aggregated_rating_count < MIN_RATING_COUNT.
    """
    count = data.get("aggregated_rating_count", 0) or 0
    if count < MIN_RATING_COUNT:
        return None

    rating = data.get("aggregated_rating")
    genres = [g["name"] for g in data.get("genres") or []]

    ts = data.get("first_release_date")
    release_year = None
    if ts:
        release_year = datetime.fromtimestamp(ts, tz=timezone.utc).year

    return {
        "aggregated_rating": round(rating) if rating is not None else None,
        "aggregated_rating_count": count,
        "genres": genres,
        "release_year": release_year,
    }


def fetch_by_appid(client_id: str | None, token: str | None, appid: int) -> dict | None:
    """Busca jogo no IGDB pelo Steam appid (external_games.category = 1)."""
    if not client_id or not token:
        return None

    body = (
        f'fields name,aggregated_rating,aggregated_rating_count,genres.name,first_release_date; '
        f'where external_games.category = 1 & external_games.uid = "{appid}"; limit 1;'
    )
    results = _post(client_id, token, "games", body)
    if not results:
        return None
    return _parse_result(results[0])


def fetch_by_name(client_id: str | None, token: str | None, name: str) -> dict | None:
    """Busca jogo por nome. Retorna o primeiro resultado IGDB — sem validação de similaridade."""
    if not client_id or not token:
        return None

    safe_name = name.replace('"', '\\"')
    body = (
        f'fields name,aggregated_rating,aggregated_rating_count,genres.name,first_release_date; '
        f'search "{safe_name}"; limit 1;'
    )
    results = _post(client_id, token, "games", body)
    if not results:
        return None
    return _parse_result(results[0])
