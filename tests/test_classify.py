import pytest
from steam_hltb.classify import (
    build_game_rows, filter_genre, filter_progress,
    filter_category, filter_time, apply_filters,
    filter_name, _fuzzy,
)


# --- build_game_rows ---

def test_build_game_rows_skips_entries_without_hltb(sample_cache, sample_steam_games):
    rows = build_game_rows(sample_cache, sample_steam_games)
    names = [r["name"] for r in rows]
    assert "Dota 2" not in names  # hltb is None


def test_build_game_rows_includes_all_fields(sample_cache, sample_steam_games):
    rows = build_game_rows(sample_cache, sample_steam_games)
    hl2 = next(r for r in rows if r["name"] == "Half-Life 2")
    assert hl2["metacritic"] == 96
    assert hl2["steam_pct"] == 97
    assert hl2["genres"] == ["action", "shooter"]
    assert hl2["hours_played"] == 0.0
    assert hl2["category"] == "singleplayer"


def test_build_game_rows_classifies_coop(sample_cache, sample_steam_games):
    rows = build_game_rows(sample_cache, sample_steam_games)
    p2 = next(r for r in rows if r["name"] == "Portal 2")
    assert p2["category"] == "coop_campaign"


# --- filter_genre ---

def test_filter_genre_must_have_all():
    games = [
        {"genres": ["action", "shooter"]},
        {"genres": ["action", "rpg"]},
        {"genres": ["rpg"]},
    ]
    result = filter_genre(games, must_have=["action", "shooter"])
    assert len(result) == 1


def test_filter_genre_any_of():
    games = [
        {"genres": ["action"]},
        {"genres": ["rpg"]},
        {"genres": ["puzzle"]},
    ]
    result = filter_genre(games, any_of=["action", "rpg"])
    assert len(result) == 2


def test_filter_genre_exclude():
    games = [{"genres": ["action"]}, {"genres": ["rpg"]}, {"genres": ["puzzle"]}]
    result = filter_genre(games, exclude=["rpg", "puzzle"])
    assert len(result) == 1
    assert result[0]["genres"] == ["action"]


def test_filter_genre_case_insensitive():
    games = [{"genres": ["Action", "Shooter"]}]
    result = filter_genre(games, must_have=["action"])
    assert len(result) == 1


def test_filter_genre_no_filters_returns_all():
    games = [{"genres": ["action"]}, {"genres": ["rpg"]}]
    assert filter_genre(games) == games


# --- filter_progress ---

def test_filter_progress_not_started():
    games = [
        {"hours_played": 0.0, "main_extra": 10},
        {"hours_played": 2.0, "main_extra": 10},
    ]
    result = filter_progress(games, mode="not_started")
    assert len(result) == 1
    assert result[0]["hours_played"] == 0.0


def test_filter_progress_in_progress():
    games = [
        {"hours_played": 0.0, "main_extra": 10},
        {"hours_played": 3.0, "main_extra": 10},
        {"hours_played": 8.0, "main_extra": 10},  # >50%, excluded
    ]
    result = filter_progress(games, mode="in_progress")
    assert len(result) == 1
    assert result[0]["hours_played"] == 3.0


def test_filter_progress_all_returns_everything():
    games = [
        {"hours_played": 0.0, "main_extra": 10},
        {"hours_played": 100.0, "main_extra": 10},
    ]
    assert len(filter_progress(games, mode="all")) == 2


def test_filter_progress_default_hides_over_50_pct():
    games = [
        {"hours_played": 4.0, "main_extra": 10},   # 40%, kept
        {"hours_played": 6.0, "main_extra": 10},   # 60%, hidden
    ]
    result = filter_progress(games, mode="default")
    assert len(result) == 1
    assert result[0]["hours_played"] == 4.0


# --- filter_category ---

def test_filter_category_all_excludes_multiplayer():
    games = [
        {"category": "singleplayer"},
        {"category": "coop_campaign"},
        {"category": "multiplayer"},
    ]
    result = filter_category(games, category="all")
    assert len(result) == 2


def test_filter_category_singleplayer_only():
    games = [{"category": "singleplayer"}, {"category": "coop_campaign"}]
    result = filter_category(games, category="singleplayer")
    assert len(result) == 1


# --- filter_time ---

def test_filter_time_max_hours():
    games = [{"main_extra": 5}, {"main_extra": 20}, {"main_extra": 40}]
    result = filter_time(games, max_hours=20)
    assert len(result) == 2


def test_filter_time_min_hours():
    games = [{"main_extra": 5}, {"main_extra": 20}]
    result = filter_time(games, min_hours=10)
    assert len(result) == 1


# --- fuzzy name filter ---

def test_fuzzy_subsequence_match():
    assert _fuzzy("hl2", "Half-Life 2")
    assert _fuzzy("por", "Portal")
    assert _fuzzy("dota", "Dota 2")
    assert _fuzzy("halflife", "Half-Life 2")


def test_fuzzy_case_insensitive():
    assert _fuzzy("PORTAL", "Portal")
    assert _fuzzy("portal", "Portal")


def test_fuzzy_no_match():
    assert not _fuzzy("xyz", "Portal")
    assert not _fuzzy("halflife3", "Half-Life 2")


def test_filter_name_empty_query_returns_all():
    games = [{"name": "Portal"}, {"name": "Half-Life 2"}]
    assert filter_name(games) == games
    assert filter_name(games, query="") == games


def test_filter_name_fuzzy():
    games = [{"name": "Portal"}, {"name": "Half-Life 2"}, {"name": "Dota 2"}]
    result = filter_name(games, query="hl2")
    assert len(result) == 1
    assert result[0]["name"] == "Half-Life 2"


def test_filter_name_multiple_matches():
    games = [{"name": "Portal"}, {"name": "Portal 2"}, {"name": "Half-Life"}]
    result = filter_name(games, query="por")
    names = [g["name"] for g in result]
    assert "Portal" in names
    assert "Portal 2" in names
    assert "Half-Life" not in names


# --- apply_filters combines all ---

def test_apply_filters_combines(sample_cache, sample_steam_games):
    rows = build_game_rows(sample_cache, sample_steam_games)
    result = apply_filters(rows, genre=["action"], progress="not_started")
    assert all(r["hours_played"] == 0.0 for r in result)
    assert all("action" in r["genres"] for r in result)
