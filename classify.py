COOP_TAGS = {"co-op", "online co-op", "local co-op", "co-operative", "co-op campaign"}
MULTIPLAYER_ONLY_TAGS = {"multiplayer", "online multiplayer", "pvp", "mmo"}


def _category(tags: list, main_story: int) -> str:
    tag_set = {t.lower() for t in tags}
    has_coop = bool(tag_set & COOP_TAGS)
    has_single = "singleplayer" in tag_set or "single-player" in tag_set
    is_mp_only = bool(tag_set & MULTIPLAYER_ONLY_TAGS) and not has_single and not has_coop
    if is_mp_only:
        return "multiplayer"
    if has_coop and main_story > 0:
        return "coop_campaign"
    return "singleplayer"


def build_game_rows(cache: dict, steam_games: list) -> list:
    rows = []
    for game in steam_games:
        name = game["name"]
        entry = cache.get(name, {})
        hltb = entry.get("hltb")
        rawg = entry.get("rawg")
        steam = entry.get("steam")
        if not hltb:
            continue
        tags = rawg.get("tags", []) if rawg else []
        rows.append({
            "name": hltb["game_name"],
            "steam_name": name,
            "appid": steam.get("appid") if steam else game.get("appid"),
            "hours_played": game["hours_played"],
            "category": _category(tags, hltb["main_story"]),
            "genres": [g.lower() for g in (rawg.get("genres", []) if rawg else [])],
            "tags": tags,
            "metacritic": rawg.get("metacritic") if rawg else None,
            "steam_pct": steam.get("positive_pct") if steam else None,
            "steam_total_reviews": steam.get("total_reviews") if steam else None,
            "main_story": hltb["main_story"],
            "main_extra": hltb["main_extra"],
            "completionist": hltb["completionist"],
        })
    return rows


def filter_genre(
    games: list,
    must_have: list = None,
    any_of: list = None,
    exclude: list = None,
) -> list:
    result = games
    if must_have:
        lower = [g.lower() for g in must_have]
        result = [g for g in result if all(m in [x.lower() for x in g["genres"]] for m in lower)]
    if any_of:
        lower = [g.lower() for g in any_of]
        result = [g for g in result if any(m in [x.lower() for x in g["genres"]] for m in lower)]
    if exclude:
        lower = [g.lower() for g in exclude]
        result = [g for g in result if not any(e in [x.lower() for x in g["genres"]] for e in lower)]
    return result


def filter_progress(games: list, mode: str = "default") -> list:
    if mode == "all":
        return games
    if mode == "not_started":
        return [g for g in games if g["hours_played"] == 0]
    if mode == "in_progress":
        return [g for g in games if 0 < g["hours_played"] < 0.5 * max(g["main_extra"], 1)]
    return [g for g in games if g["hours_played"] <= 0.5 * max(g["main_extra"], 1)]


def filter_category(games: list, category: str = "all") -> list:
    if category == "all":
        return [g for g in games if g["category"] != "multiplayer"]
    return [g for g in games if g["category"] == category]


def filter_time(games: list, min_hours: float = None, max_hours: float = None) -> list:
    result = games
    if min_hours is not None:
        result = [g for g in result if g["main_extra"] >= min_hours]
    if max_hours is not None:
        result = [g for g in result if g["main_extra"] <= max_hours]
    return result


def apply_filters(
    games: list,
    genre: list = None,
    genre_any: list = None,
    exclude_genre: list = None,
    progress: str = "default",
    category: str = "all",
    min_hours: float = None,
    max_hours: float = None,
) -> list:
    games = filter_genre(games, must_have=genre, any_of=genre_any, exclude=exclude_genre)
    games = filter_progress(games, mode=progress)
    games = filter_category(games, category=category)
    games = filter_time(games, min_hours=min_hours, max_hours=max_hours)
    return games
