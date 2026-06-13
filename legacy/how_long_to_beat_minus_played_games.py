import json
import math
import os
import time
import requests
from howlongtobeatpy import HowLongToBeat

STEAM_USERNAME = os.environ.get("STEAM_USERNAME", "")
CACHE_FILE = "games_cache.json"

COOP_TAGS = {"co-op", "online co-op", "local co-op", "co-operative", "co-op campaign"}
MULTIPLAYER_ONLY_TAGS = {"multiplayer", "online multiplayer", "pvp", "mmo"}

def get_api_key(env_var, prompt):
    key = os.environ.get(env_var)
    if not key:
        key = input(f"{prompt}: ").strip()
    return key

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def resolve_steamid(api_key, username):
    resp = requests.get(
        "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/",
        params={"key": api_key, "vanityurl": username},
    )
    resp.raise_for_status()
    data = resp.json()["response"]
    if data["success"] != 1:
        raise ValueError(f"Username '{username}' não encontrado na Steam.")
    return data["steamid"]

def get_steam_games(api_key, steamid):
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
            "hours_played": round(g.get("playtime_forever", 0) / 60, 1),
        }
        for g in games
    ]

def fetch_hltb(name):
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

def fetch_rawg(rawg_key, game_name):
    resp = requests.get(
        "https://api.rawg.io/api/games",
        params={"key": rawg_key, "search": game_name, "search_precise": True, "page_size": 5},
    )
    if resp.status_code != 200:
        return None
    results = resp.json().get("results", [])
    if not results:
        return None
    game = results[0]
    return {
        "metacritic": game.get("metacritic"),
        "tags": [t["name"].lower() for t in game.get("tags", [])],
    }

def classify(tags_list, main_story):
    tags = set(tags_list)
    has_coop = bool(tags & COOP_TAGS)
    has_singleplayer = "singleplayer" in tags or "single-player" in tags
    is_multiplayer_only = bool(tags & MULTIPLAYER_ONLY_TAGS) and not has_singleplayer and not has_coop
    if is_multiplayer_only:
        return "multiplayer"
    if has_coop and main_story > 0:
        return "coop_campaign"
    return "singleplayer"

# --- main ---

steam_key = get_api_key("STEAM_API_KEY", "Steam API key")
rawg_key  = get_api_key("RAWG_API_KEY",  "RAWG API key")

cache = load_cache()
cached_count = len(cache)

steamid = resolve_steamid(steam_key, STEAM_USERNAME)
print(f"SteamID: {steamid}")

steam_games = get_steam_games(steam_key, steamid)
print(f"{len(steam_games)} jogos na biblioteca. {cached_count} já no cache.\n")

total = len(steam_games)
for idx, game in enumerate(steam_games, 1):
    name = game["name"]

    if name in cache:
        print(f"[{idx}/{total}] {name} (cache)")
        continue

    print(f"[{idx}/{total}] {name}")

    hltb = fetch_hltb(name)
    if not hltb:
        cache[name] = {"hltb": None, "rawg": None}
        save_cache(cache)
        continue

    rawg = fetch_rawg(rawg_key, name)
    time.sleep(0.25)

    cache[name] = {"hltb": hltb, "rawg": rawg}
    save_cache(cache)

print(f"\nCache completo. Calculando resultados...\n")

results = []
for game in steam_games:
    name = game["name"]
    hours_played = game["hours_played"]
    entry = cache.get(name, {})

    hltb = entry.get("hltb")
    rawg = entry.get("rawg")

    if not hltb:
        continue

    main_story = hltb["main_story"]
    main_extra = hltb["main_extra"]

    if main_extra > 0 and hours_played > 0.5 * main_extra:
        continue

    if not rawg or not rawg.get("metacritic"):
        continue

    metacritic = rawg["metacritic"]
    tags = rawg.get("tags", [])
    category = classify(tags, main_story)

    if category == "multiplayer":
        continue

    score = metacritic / math.sqrt(main_extra) if main_extra > 0 else float(metacritic)

    results.append({
        "name": hltb["game_name"],
        "category": category,
        "metacritic": metacritic,
        "hours_played": hours_played,
        "main_story": main_story,
        "main_extra": main_extra,
        "completionist": hltb["completionist"],
        "score": round(score, 2),
    })

singleplayer  = sorted([g for g in results if g["category"] == "singleplayer"],  key=lambda x: x["score"], reverse=True)
coop_campaign = sorted([g for g in results if g["category"] == "coop_campaign"], key=lambda x: x["score"], reverse=True)

def print_top10(title, games):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")
    for i, g in enumerate(games[:10], 1):
        print(f"{i:2}. {g['name']:<45} score {g['score']:5.1f} | {g['metacritic']} MC | {g['main_extra']}h | {g['hours_played']}h jogadas")

print_top10("TOP 10 — SINGLE-PLAYER", singleplayer)
print_top10("TOP 10 — CO-OP COM CAMPANHA", coop_campaign)

output_file = "how_long_to_beat_output.csv"
with open(output_file, "w", encoding="utf-8") as f:
    f.write("Name,Category,Metacritic,Score,Hours Played,Main Story,Main + Extra,Completionist\n")
    for g in sorted(results, key=lambda x: x["score"], reverse=True):
        f.write(f"{g['name']},{g['category']},{g['metacritic']},{g['score']},{g['hours_played']},{g['main_story']},{g['main_extra']},{g['completionist']}\n")

print(f"\nLista completa ({len(results)} jogos) salva em '{output_file}'")
