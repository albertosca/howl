import json
import os

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
    if best.similarity < 0.5:
        return None
    return {
        "game_name": best.game_name,
        "main_story": int(best.main_story) if best.main_story and best.main_story > 0 else 0,
        "main_extra": int(best.main_extra) if best.main_extra and best.main_extra > 0 else 0,
        "completionist": int(best.completionist) if best.completionist and best.completionist > 0 else 0,
    }


def fetch_rawg(rawg_key: str, name: str) -> dict | None:
    resp = requests.get(
        "https://api.rawg.io/api/games",
        params={"key": rawg_key, "search": name, "search_precise": True, "page_size": 5},
    )
    if resp.status_code != 200:
        return None
    results = resp.json().get("results", [])
    if not results:
        return None
    game = results[0]
    return {
        "metacritic": game.get("metacritic"),
        "genres": [g["name"].lower() for g in game.get("genres", [])],
        "tags": [t["name"].lower() for t in game.get("tags", [])],
    }
