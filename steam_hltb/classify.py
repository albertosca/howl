COOP_CATEGORIES = {"co-op", "online co-op", "local co-op", "shared/split screen co-op"}
MULTIPLAYER_ONLY_CATEGORIES = {"multi-player", "multiplayer", "online pvp", "mmo", "massively multiplayer"}


def _category(categories: list, main_story: int) -> str:
    cat_set = {c.lower() for c in categories}
    has_coop = bool(cat_set & COOP_CATEGORIES)
    has_single = "single-player" in cat_set or "singleplayer" in cat_set
    is_mp_only = bool(cat_set & MULTIPLAYER_ONLY_CATEGORIES) and not has_single and not has_coop
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
        steam = entry.get("steam")
        if not hltb:
            continue
        # suporte a cache antigo (rawg) e novo (steam com genres/categories)
        rawg = entry.get("rawg")
        if steam and "genres" in steam:
            genres = steam.get("genres", [])
            categories = steam.get("categories", [])
            metacritic = steam.get("metacritic")
        elif rawg:
            genres = rawg.get("genres", [])
            categories = rawg.get("tags", [])
            metacritic = rawg.get("metacritic")
        else:
            genres, categories, metacritic = [], [], None
        rows.append({
            "name": hltb["game_name"],
            "steam_name": name,
            "appid": steam.get("appid") if steam else game.get("appid"),
            "hours_played": game["hours_played"],
            "category": _category(categories, hltb["main_story"]),
            "genres": genres,
            "tags": categories,
            "metacritic": metacritic,
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


def _fuzzy(query: str, name: str) -> bool:
    """Subsequência fzf-style: cada char do query deve aparecer em ordem em name."""
    q = query.lower()
    n = name.lower()
    qi = 0
    for c in n:
        if c == q[qi]:
            qi += 1
            if qi == len(q):
                return True
    return False


def filter_name(games: list, query: str = None) -> list:
    if not query:
        return games
    return [g for g in games if _fuzzy(query, g["name"])]


def apply_filters(
    games: list,
    genre: list = None,
    genre_any: list = None,
    exclude_genre: list = None,
    progress: str = "default",
    category: str = "all",
    min_hours: float = None,
    max_hours: float = None,
    name_query: str = None,
) -> list:
    games = filter_genre(games, must_have=genre, any_of=genre_any, exclude=exclude_genre)
    games = filter_progress(games, mode=progress)
    games = filter_category(games, category=category)
    games = filter_time(games, min_hours=min_hours, max_hours=max_hours)
    games = filter_name(games, query=name_query)
    return games
