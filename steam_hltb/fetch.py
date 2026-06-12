import json
import os
import re
import time

import requests
from howlongtobeatpy import HowLongToBeat

CACHE_FILE = "games_cache.json"


def load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache: dict) -> None:
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def fetch_hltb(name: str) -> dict | None:
    results = HowLongToBeat().search(name)
    if not results:
        return None
    best = max(results, key=lambda e: e.similarity)
    if best.similarity < 0.6:
        return None
    return {
        "game_name": best.game_name,
        "main_story": int(best.main_story) if best.main_story and best.main_story > 0 else 0,
        "main_extra": int(best.main_extra) if best.main_extra and best.main_extra > 0 else 0,
        "completionist": int(best.completionist) if best.completionist and best.completionist > 0 else 0,
    }


def fetch_steam_app_details(appid: int) -> dict | None:
    resp = requests.get(
        "https://store.steampowered.com/api/appdetails",
        params={"appids": appid, "cc": "US", "l": "english"},
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
    release_date_str = data.get("release_date", {}).get("date", "")
    year_match = re.search(r'\b(19|20)\d{2}\b', release_date_str)
    release_year = int(year_match.group()) if year_match else None
    return {
        "metacritic": mc_data["score"] if mc_data else None,
        "genres": genres,
        "categories": categories,
        "release_year": release_year,
    }


def fetch_steam_reviews(appid: int) -> dict | None:
    resp = requests.get(
        f"https://store.steampowered.com/appreviews/{appid}",
        params={"json": 1, "language": "all", "purchase_type": "all"},
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
    )
    resp.raise_for_status()
    data = resp.json()["response"]
    if data["success"] != 1:
        raise ValueError(f"Username '{username}' not found on Steam.")
    return data["steamid"]


def get_steam_games(api_key: str, steamid: str) -> list:
    resp = requests.get(
        "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/",
        params={
            "key": api_key,
            "steamid": steamid,
            "include_appinfo": True,
            "include_played_free_games": True,
        },
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
    steam_key: str, username: str, cache: dict,
    refresh: bool = False, verbose: bool = False
) -> tuple:
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
        time.sleep(1.0)
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


def migrate_steam_details(cache: dict, verbose: bool = False) -> dict:
    """Preenche steam.genres/categories/metacritic para entradas sem esses campos."""
    import time
    pending = [
        (name, entry["steam"]["appid"])
        for name, entry in cache.items()
        if entry.get("steam") and entry["steam"].get("appid") and "genres" not in entry.get("steam", {})
    ]
    if verbose:
        print(f"Migrando {len(pending)} entradas sem steam.genres...")
    for idx, (name, appid) in enumerate(pending, 1):
        details = fetch_steam_app_details(appid)
        if details:
            cache[name]["steam"].update(details)
        if verbose:
            print(f"[{idx}/{len(pending)}] {name}")
        save_cache(cache)
        time.sleep(0.5)
    return cache
