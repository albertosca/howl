import json
import os
import re
import time
from pathlib import Path
from typing import Any

import requests
from howlongtobeatpy import HowLongToBeat

from . import igdb

CACHE_FILE = ".cache/games_cache.json"
HTTP_TIMEOUT = 15  # seconds — prevents hanging indefinitely if the API stalls
HLTB_MIN_SIMILARITY = 0.6  # below this the HowLongToBeat match is too weak
_STEAM_RATE_LIMIT_S = 1.0  # pause between new games in build_library
_IGDB_RATE_LIMIT_S = 0.25  # pause between IGDB lookups
_DETAILS_RATE_LIMIT_S = 0.5  # pause between detail lookups in migration


def load_cache() -> dict[str, Any]:
    path = Path(CACHE_FILE)
    if path.exists():
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        return data
    return {}


def save_cache(cache: dict[str, Any]) -> None:
    path = Path(CACHE_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def _hltb_hours(val: float | None) -> int | None:
    """Returns hours as int, or None if HLTB has no data for this field."""
    return int(val) if val and val > 0 else None


def fetch_hltb(name: str) -> dict[str, Any] | None:
    results = HowLongToBeat().search(name)
    if not results:
        return None
    best = max(results, key=lambda e: e.similarity)
    if best.similarity < HLTB_MIN_SIMILARITY:
        return None
    return {
        "game_name": best.game_name,
        "main_story": _hltb_hours(best.main_story),
        "main_extra": _hltb_hours(best.main_extra),
        "completionist": _hltb_hours(best.completionist),
    }


def fetch_steam_app_details(appid: int) -> dict[str, Any] | None:
    params: dict[str, str | int] = {"appids": appid, "cc": "US", "l": "english"}
    resp = requests.get(
        "https://store.steampowered.com/api/appdetails", params=params, timeout=HTTP_TIMEOUT
    )
    if resp.status_code != 200:
        return None
    result = resp.json().get(str(appid), {})
    if not result.get("success"):
        return None
    data = result.get("data", {})
    mc_data = data.get("metacritic")
    genres = [g["description"].lower() for g in data.get("genres", [])]
    categories = [c["description"].lower() for c in data.get("categories", [])]
    date_str = data.get("release_date", {}).get("date", "")
    year_match = re.search(r"\b(19|20)\d{2}\b", date_str)
    return {
        "metacritic": mc_data["score"] if mc_data else None,
        "genres": genres,
        "categories": categories,
        "release_year": int(year_match.group()) if year_match else None,
    }


def fetch_steam_reviews(appid: int) -> dict[str, Any] | None:
    params: dict[str, str | int] = {"json": 1, "language": "all", "purchase_type": "all"}
    resp = requests.get(
        f"https://store.steampowered.com/appreviews/{appid}", params=params, timeout=HTTP_TIMEOUT
    )
    if resp.status_code != 200:
        return None
    summary = resp.json().get("query_summary", {})
    total = summary.get("total_reviews", 0)
    if total == 0:
        return None
    positive = summary.get("total_positive", 0)
    return {
        "positive_pct": round(positive / total * 100),
        "total_reviews": total,
    }


def get_api_key(env_var: str, prompt: str) -> str:
    key = os.environ.get(env_var)
    if not key:
        key = input(f"{prompt}: ").strip()
    return key


def resolve_steamid(api_key: str, username: str) -> str:
    resp = requests.get(
        "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/",
        params={"key": api_key, "vanityurl": username},
        timeout=HTTP_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()["response"]
    if data["success"] != 1:
        raise ValueError(f"Username '{username}' not found on Steam.")
    steamid_resolved: str = data["steamid"]
    return steamid_resolved


def get_steam_games(api_key: str, steamid: str) -> list[dict[str, Any]]:
    params: dict[str, str | int] = {
        "key": api_key,
        "steamid": steamid,
        "include_appinfo": True,
        "include_played_free_games": True,
    }
    resp = requests.get(
        "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/",
        params=params,
        timeout=HTTP_TIMEOUT,
    )
    resp.raise_for_status()
    games = resp.json()["response"].get("games", [])
    return [
        {
            "name": g["name"],
            "appid": g["appid"],
            "hours_played": round(g.get("playtime_forever", 0) / 60, 1),
        }
        for g in games
    ]


def build_library(
    steam_key: str,
    username: str,
    cache: dict[str, Any],
    refresh: bool = False,
    verbose: bool = False,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    steamid = resolve_steamid(steam_key, username)
    steam_games = get_steam_games(steam_key, steamid)
    total = len(steam_games)
    if verbose:
        print(f"{total} games in library. {len(cache)} already cached.\n")
    for idx, game in enumerate(steam_games, 1):
        name = game["name"]
        appid = game["appid"]
        if name in cache and not refresh:
            if verbose:
                print(f"[{idx}/{total}] {name} (cache)")
            continue
        if verbose:
            print(f"[{idx}/{total}] {name}")
        hltb = fetch_hltb(name)
        if not hltb:
            cache[name] = {"hltb": None, "steam": None}
            save_cache(cache)
            continue
        steam_reviews = fetch_steam_reviews(appid)
        steam_details = fetch_steam_app_details(appid)
        time.sleep(_STEAM_RATE_LIMIT_S)
        cache[name] = {
            "hltb": hltb,
            "steam": {
                "appid": appid,
                **(steam_reviews or {}),
                **(steam_details or {}),
            },
        }
        save_cache(cache)
    return cache, steam_games


def migrate_igdb_data(
    cache: dict[str, Any],
    client_id: str | None = None,
    client_secret: str | None = None,
    verbose: bool = False,
) -> dict[str, Any]:
    """Fills the 'igdb' field for games without Metacritic on Steam."""
    client_id = client_id or os.environ.get("IGDB_CLIENT_ID")
    client_secret = client_secret or os.environ.get("IGDB_CLIENT_SECRET")
    if not client_id or not client_secret:
        if verbose:
            print("IGDB_CLIENT_ID / IGDB_CLIENT_SECRET not configured — skipping.")
        return cache

    token = igdb.get_token(client_id, client_secret)
    if not token:
        if verbose:
            print("Failed to get IGDB token.")
        return cache

    pending = [
        (name, entry)
        for name, entry in cache.items()
        if entry.get("steam") and entry["steam"].get("metacritic") is None and "igdb" not in entry
    ]
    if verbose:
        print(f"Fetching IGDB data for {len(pending)} games without Metacritic...")

    for idx, (name, entry) in enumerate(pending, 1):
        if verbose:
            print(f"  [{idx}/{len(pending)}] {name}")
        appid = entry["steam"].get("appid")
        result = igdb.fetch_by_appid(client_id, token, appid, verbose=verbose) if appid else None
        if result is None:
            result = igdb.fetch_by_name(client_id, token, name, verbose=verbose)
        if result:
            cache[name]["igdb"] = result
            if verbose:
                rating = result.get("aggregated_rating")
                if rating is not None:
                    print(
                        f"    → ✓ rating={rating}"
                        f" (count={result.get('aggregated_rating_count')},"
                        f" genres={result.get('genres')})"
                    )
                else:
                    print(
                        f"    → ~ partial: genres={result.get('genres')},"
                        f" year={result.get('release_year')}"
                        f" (no rating: count={result.get('aggregated_rating_count')})"
                    )
        else:
            if verbose:
                print("    → ✗ not found")
        save_cache(cache)
        time.sleep(_IGDB_RATE_LIMIT_S)

    return cache


def migrate_steam_details(cache: dict[str, Any], verbose: bool = False) -> dict[str, Any]:
    """Fills missing fields (genres, categories, release_year) in incomplete entries."""

    def _needs_migration(steam: dict[str, Any]) -> bool:
        return "genres" not in steam or "release_year" not in steam

    pending = [
        (name, entry["steam"]["appid"])
        for name, entry in cache.items()
        if entry.get("steam") and entry["steam"].get("appid") and _needs_migration(entry["steam"])
    ]
    if verbose:
        n = len(pending)
        print(f"Migrating {n} incomplete entries (missing genres and/or release_year)...")
    for idx, (name, appid) in enumerate(pending, 1):
        details = fetch_steam_app_details(appid)
        if details:
            cache[name]["steam"].update(details)
        if verbose:
            print(f"[{idx}/{len(pending)}] {name}")
        save_cache(cache)
        time.sleep(_DETAILS_RATE_LIMIT_S)
    return cache
