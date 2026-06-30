import json
from pathlib import Path
from typing import Any

from .types import Game

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

# "in progress" = played up to half of main+extra (floor of 1h)
_IN_PROGRESS_FRACTION = 0.5


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
    """Strips ™ and ® for tolerant Steam name matching."""
    return name.replace("™", "").replace("®", "").strip()


def _load_overrides() -> dict[str, Any]:
    """Loads howl_overrides.json with normalized keys (no ™/®)."""
    path = Path(OVERRIDES_FILE)
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {_normalize_name(k): v for k, v in raw.items()}


def _resolve_source_fields(entry: dict[str, Any]) -> dict[str, Any]:
    """Resolves genres/categories/metacritic/release_year from a cache entry.

    Prefers Steam (new format), falls back to RAWG (legacy cache) or empty,
    then uses IGDB as fallback for missing metacritic/genres.
    """
    steam = entry.get("steam") or {}
    rawg = entry.get("rawg") or {}
    igdb_data = entry.get("igdb") or {}

    if steam.get("genres") is not None:
        genres, categories, metacritic = (
            steam.get("genres", []),
            steam.get("categories", []),
            steam.get("metacritic"),
        )
    elif rawg:
        genres, categories, metacritic = (
            rawg.get("genres", []),
            rawg.get("tags", []),
            rawg.get("metacritic"),
        )
    else:
        genres, categories, metacritic = [], [], None

    if metacritic is None:
        metacritic = igdb_data.get("aggregated_rating")
    if not genres:
        genres = [g.lower() for g in igdb_data.get("genres", [])]

    return {
        "genres": genres,
        "categories": categories,
        "metacritic": metacritic,
        "release_year": steam.get("release_year") or igdb_data.get("release_year"),
    }


def _apply_overrides(row: Game, overrides: dict[str, Any], name: str) -> None:
    """Merges howl_overrides.json fields into the row (ignores the 'comment' key)."""
    ov = overrides.get(_normalize_name(name), {})
    if isinstance(ov, dict):
        for key, val in ov.items():
            if key != "comment":
                row[key] = val


def build_game_rows(cache: dict[str, Any], steam_games: list[dict[str, Any]]) -> list[Game]:
    overrides = _load_overrides()
    rows: list[dict[str, Any]] = []
    for game in steam_games:
        name = game["name"]
        entry = cache.get(name, {})
        hltb = entry.get("hltb")
        if not hltb:
            continue
        steam = entry.get("steam")
        fields = _resolve_source_fields(entry)
        row: Game = {
            "name": hltb["game_name"],
            "steam_name": name,
            "appid": steam.get("appid") if steam else game.get("appid"),
            "hours_played": game["hours_played"],
            "category": _category(fields["categories"], hltb.get("main_story") or 0),
            "genres": fields["genres"],
            "tags": fields["categories"],
            "metacritic": fields["metacritic"],
            "steam_pct": steam.get("positive_pct") if steam else None,
            "steam_total_reviews": steam.get("total_reviews") if steam else None,
            "main_story": hltb.get("main_story"),
            "main_extra": hltb.get("main_extra"),
            "completionist": hltb.get("completionist"),
            "release_year": fields["release_year"],
        }
        _apply_overrides(row, overrides, name)
        rows.append(row)
    return rows


def _genres_of(game: Game) -> set[str]:
    return {g.lower() for g in game["genres"]}


def filter_genre(
    games: list[Game],
    must_have: list[str] | None = None,
    any_of: list[str] | None = None,
    exclude: list[str] | None = None,
) -> list[Game]:
    result = games
    if must_have:
        wanted = {g.lower() for g in must_have}
        result = [g for g in result if wanted <= _genres_of(g)]  # all must be present
    if any_of:
        wanted = {g.lower() for g in any_of}
        result = [g for g in result if wanted & _genres_of(g)]  # at least one
    if exclude:
        unwanted = {g.lower() for g in exclude}
        result = [g for g in result if not (unwanted & _genres_of(g))]  # none allowed
    return result


def _halfway_hours(game: Game) -> float:
    """Half of main+extra (floor 1h) — threshold for 'not yet finished'."""
    return _IN_PROGRESS_FRACTION * max(game["main_extra"] or 0, 1)


def filter_progress(games: list[Game], mode: str = "default") -> list[Game]:
    if mode == "all":
        return games
    if mode == "not_started":
        return [g for g in games if g["hours_played"] == 0]
    if mode == "in_progress":
        return [g for g in games if 0 < g["hours_played"] < _halfway_hours(g)]
    return [g for g in games if g["hours_played"] <= _halfway_hours(g)]


def filter_category(games: list[Game], category: str = "all") -> list[Game]:
    if category == "all":
        return [g for g in games if g["category"] != "multiplayer"]
    return [g for g in games if g["category"] == category]


def filter_time(
    games: list[Game],
    min_hours: float | None = None,
    max_hours: float | None = None,
) -> list[Game]:
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


def filter_era(games: list[Game], eras: list[str] | None = None) -> list[Game]:
    """Keeps only games whose release era is in `eras`. None = no filter."""
    if eras is None:
        return games
    era_set = set(eras)
    return [g for g in games if _era_label(g.get("release_year")) in era_set]


def _fuzzy(query: str, name: str) -> bool:
    """fzf-style subsequence: every char in query must appear in order in name."""
    q = query.lower()
    qi = 0
    for c in name.lower():
        if c == q[qi]:
            qi += 1
            if qi == len(q):
                return True
    return False


def filter_name(games: list[Game], query: str | None = None) -> list[Game]:
    if not query:
        return games
    return [g for g in games if _fuzzy(query, g["name"])]


def apply_filters(
    games: list[Game],
    genre: list[str] | None = None,
    genre_any: list[str] | None = None,
    exclude_genre: list[str] | None = None,
    progress: str = "default",
    category: str = "all",
    min_hours: float | None = None,
    max_hours: float | None = None,
    name_query: str | None = None,
    eras: list[str] | None = None,
) -> list[Game]:
    games = filter_genre(games, must_have=genre, any_of=genre_any, exclude=exclude_genre)
    games = filter_progress(games, mode=progress)
    games = filter_category(games, category=category)
    games = filter_time(games, min_hours=min_hours, max_hours=max_hours)
    games = filter_name(games, query=name_query)
    return filter_era(games, eras=eras)
