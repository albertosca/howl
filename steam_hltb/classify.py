import json
from pathlib import Path
from typing import Any

OVERRIDES_FILE = "howl_overrides.json"

COOP_CATEGORIES: frozenset[str] = frozenset(
    {
        "co-op",
        "online co-op",
        "local co-op",
        "shared/split screen co-op",
    }
)
MULTIPLAYER_ONLY_CATEGORIES: frozenset[str] = frozenset(
    {
        "multi-player",
        "multiplayer",
        "online pvp",
        "mmo",
        "massively multiplayer",
    }
)

ERA_LABELS: list[str] = ["pre-2005", "2005-2010", "2010-2015", "2015-2020", "2020+", "unknown"]


def _category(categories: list[str], main_story: int) -> str:
    cat_set = {c.lower() for c in categories}
    has_coop = bool(cat_set & COOP_CATEGORIES)
    has_single = "single-player" in cat_set or "singleplayer" in cat_set
    is_mp_only = bool(cat_set & MULTIPLAYER_ONLY_CATEGORIES) and not has_single and not has_coop
    if is_mp_only:
        return "multiplayer"
    if has_coop and main_story > 0:
        return "coop_campaign"
    return "singleplayer"


def _normalize_name(name: str) -> str:
    """Remove ™ e ® do nome do jogo para matching tolerante com Steam."""
    return name.replace("™", "").replace("®", "").strip()


def _load_overrides() -> dict[str, Any]:
    """Carrega howl_overrides.json com chaves normalizadas (sem ™/®)."""
    path = Path(OVERRIDES_FILE)
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {_normalize_name(k): v for k, v in raw.items()}


def build_game_rows(
    cache: dict[str, Any], steam_games: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    overrides = _load_overrides()
    rows: list[dict[str, Any]] = []
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
        # fallback IGDB para campos ausentes do Steam
        igdb_data = entry.get("igdb") or {}
        if igdb_data:
            if metacritic is None:
                metacritic = igdb_data.get("aggregated_rating")
            if not genres:
                genres = [g.lower() for g in igdb_data.get("genres", [])]
        row: dict[str, Any] = {
            "name": hltb["game_name"],
            "steam_name": name,
            "appid": steam.get("appid") if steam else game.get("appid"),
            "hours_played": game["hours_played"],
            "category": _category(categories, hltb.get("main_story") or 0),
            "genres": genres,
            "tags": categories,
            "metacritic": metacritic,
            "steam_pct": steam.get("positive_pct") if steam else None,
            "steam_total_reviews": steam.get("total_reviews") if steam else None,
            "main_story": hltb.get("main_story"),
            "main_extra": hltb.get("main_extra"),
            "completionist": hltb.get("completionist"),
            "release_year": (steam.get("release_year") if steam else None)
            or igdb_data.get("release_year"),
        }
        # aplica overrides (ex: howl_overrides.json com metacritic/release_year hardcoded)
        ov = overrides.get(_normalize_name(name), {})
        if isinstance(ov, dict):
            for key, val in ov.items():
                if key != "comment":
                    row[key] = val
        rows.append(row)
    return rows


def filter_genre(
    games: list[dict[str, Any]],
    must_have: list[str] | None = None,
    any_of: list[str] | None = None,
    exclude: list[str] | None = None,
) -> list[dict[str, Any]]:
    result = games
    if must_have:
        lower = [g.lower() for g in must_have]
        result = [g for g in result if all(m in [x.lower() for x in g["genres"]] for m in lower)]
    if any_of:
        lower = [g.lower() for g in any_of]
        result = [g for g in result if any(m in [x.lower() for x in g["genres"]] for m in lower)]
    if exclude:
        lower = [g.lower() for g in exclude]
        result = [
            g for g in result if not any(e in [x.lower() for x in g["genres"]] for e in lower)
        ]
    return result


def filter_progress(games: list[dict[str, Any]], mode: str = "default") -> list[dict[str, Any]]:
    if mode == "all":
        return games
    if mode == "not_started":
        return [g for g in games if g["hours_played"] == 0]
    if mode == "in_progress":
        return [g for g in games if 0 < g["hours_played"] < 0.5 * max(g["main_extra"] or 0, 1)]
    return [g for g in games if g["hours_played"] <= 0.5 * max(g["main_extra"] or 0, 1)]


def filter_category(games: list[dict[str, Any]], category: str = "all") -> list[dict[str, Any]]:
    if category == "all":
        return [g for g in games if g["category"] != "multiplayer"]
    return [g for g in games if g["category"] == category]


def filter_time(
    games: list[dict[str, Any]],
    min_hours: float | None = None,
    max_hours: float | None = None,
) -> list[dict[str, Any]]:
    result = games
    if min_hours is not None:
        result = [g for g in result if (g["main_extra"] or 0) >= min_hours]
    if max_hours is not None:
        result = [g for g in result if (g["main_extra"] or 0) <= max_hours]
    return result


def _era_label(year: int | None) -> str:
    if year is None:
        return "unknown"
    if year < 2005:
        return "pre-2005"
    if year < 2010:
        return "2005-2010"
    if year < 2015:
        return "2010-2015"
    if year < 2020:
        return "2015-2020"
    return "2020+"


def filter_era(games: list[dict[str, Any]], eras: list[str] | None = None) -> list[dict[str, Any]]:
    """Mantém apenas jogos cuja era de lançamento está em `eras`. None = sem filtro."""
    if eras is None:
        return games
    era_set = set(eras)
    return [g for g in games if _era_label(g.get("release_year")) in era_set]


def _fuzzy(query: str, name: str) -> bool:
    """Subsequência fzf-style: cada char do query deve aparecer em ordem em name."""
    q = query.lower()
    qi = 0
    for c in name.lower():
        if c == q[qi]:
            qi += 1
            if qi == len(q):
                return True
    return False


def filter_name(games: list[dict[str, Any]], query: str | None = None) -> list[dict[str, Any]]:
    if not query:
        return games
    return [g for g in games if _fuzzy(query, g["name"])]


def apply_filters(
    games: list[dict[str, Any]],
    genre: list[str] | None = None,
    genre_any: list[str] | None = None,
    exclude_genre: list[str] | None = None,
    progress: str = "default",
    category: str = "all",
    min_hours: float | None = None,
    max_hours: float | None = None,
    name_query: str | None = None,
    eras: list[str] | None = None,
) -> list[dict[str, Any]]:
    games = filter_genre(games, must_have=genre, any_of=genre_any, exclude=exclude_genre)
    games = filter_progress(games, mode=progress)
    games = filter_category(games, category=category)
    games = filter_time(games, min_hours=min_hours, max_hours=max_hours)
    games = filter_name(games, query=name_query)
    return filter_era(games, eras=eras)
