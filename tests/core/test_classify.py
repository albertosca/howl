from steam_hltb.core.classify import (
    ERA_LABELS,
    _era_label,
    _fuzzy,
    apply_filters,
    build_game_rows,
    filter_category,
    filter_era,
    filter_genre,
    filter_name,
    filter_progress,
    filter_time,
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
        {"hours_played": 4.0, "main_extra": 10},  # 40%, kept
        {"hours_played": 6.0, "main_extra": 10},  # 60%, hidden
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


# --- filter_era / _era_label ---


def test_era_label_boundaries():
    assert _era_label(2004) == "pre-2005"
    assert _era_label(2005) == "2005-2010"
    assert _era_label(2009) == "2005-2010"
    assert _era_label(2010) == "2010-2015"
    assert _era_label(2014) == "2010-2015"
    assert _era_label(2015) == "2015-2020"
    assert _era_label(2019) == "2015-2020"
    assert _era_label(2020) == "2020+"
    assert _era_label(2025) == "2020+"
    assert _era_label(None) == "unknown"


def test_era_labels_constant_covers_all():
    # garantia de que ERA_LABELS cobre todos os retornos possíveis de _era_label
    possible = {_era_label(y) for y in [2000, 2005, 2010, 2015, 2020, None]}
    assert possible.issubset(set(ERA_LABELS))


def test_filter_era_none_returns_all():
    games = [{"release_year": 2003}, {"release_year": 2012}, {"release_year": None}]
    assert filter_era(games, eras=None) == games


def test_filter_era_single_era():
    games = [
        {"release_year": 2003},  # pre-2005
        {"release_year": 2012},  # 2010-2015
        {"release_year": 2022},  # 2020+
    ]
    result = filter_era(games, eras=["pre-2005"])
    assert len(result) == 1
    assert result[0]["release_year"] == 2003


def test_filter_era_multiple_eras():
    games = [
        {"release_year": 2003},
        {"release_year": 2012},
        {"release_year": 2022},
        {"release_year": None},
    ]
    result = filter_era(games, eras=["pre-2005", "2020+"])
    assert len(result) == 2
    years = {g["release_year"] for g in result}
    assert years == {2003, 2022}


def test_filter_era_unknown():
    games = [{"release_year": None}, {"release_year": 2015}]
    result = filter_era(games, eras=["unknown"])
    assert len(result) == 1
    assert result[0]["release_year"] is None


def test_filter_era_empty_list_returns_nothing():
    games = [{"release_year": 2010}, {"release_year": 2020}]
    assert filter_era(games, eras=[]) == []


# --- release_year in build_game_rows ---


def test_build_game_rows_has_release_year_field(sample_cache, sample_steam_games):
    rows = build_game_rows(sample_cache, sample_steam_games)
    hl2 = next(r for r in rows if r["name"] == "Half-Life 2")
    assert "release_year" in hl2
    assert hl2["release_year"] is None  # sample_cache não tem release_year em steam


def test_apply_filters_with_eras(sample_cache, sample_steam_games):
    rows = build_game_rows(sample_cache, sample_steam_games)
    # todos têm release_year=None → era 'unknown'
    result = apply_filters(rows, eras=["unknown"])
    assert len(result) == len(rows)  # todos passam (todos são 'unknown')
    result_none = apply_filters(rows, eras=["pre-2005"])
    assert len(result_none) == 0  # nenhum tem ano pré-2005


def test_build_game_rows_picks_up_release_year_from_steam():
    """Quando steam já tem release_year, deve aparecer na row."""
    cache = {
        "Half-Life 2": {
            "hltb": {
                "game_name": "Half-Life 2",
                "main_story": 12,
                "main_extra": 15,
                "completionist": 19,
            },
            "steam": {
                "appid": 220,
                "positive_pct": 97,
                "total_reviews": 158000,
                "genres": ["action", "shooter"],
                "categories": ["single-player"],
                "metacritic": 96,
                "release_year": 2004,
            },
        }
    }
    steam_games = [{"name": "Half-Life 2", "appid": 220, "hours_played": 0.0}]
    rows = build_game_rows(cache, steam_games)
    assert rows[0]["release_year"] == 2004


def test_filter_time_both_bounds():
    games = [{"main_extra": 5}, {"main_extra": 10}, {"main_extra": 20}, {"main_extra": 40}]
    result = filter_time(games, min_hours=8, max_hours=25)
    assert len(result) == 2
    hours = [g["main_extra"] for g in result]
    assert 10 in hours
    assert 20 in hours


def test_apply_filters_era_and_genre_combined():
    """Filtros de era e genre devem ser aplicados juntos (AND)."""
    games = [
        {
            "name": "A",
            "genres": ["action"],
            "tags": [],
            "hours_played": 0,
            "main_extra": 10,
            "category": "singleplayer",
            "release_year": 2012,
        },
        {
            "name": "B",
            "genres": ["rpg"],
            "tags": [],
            "hours_played": 0,
            "main_extra": 10,
            "category": "singleplayer",
            "release_year": 2012,
        },
        {
            "name": "C",
            "genres": ["action"],
            "tags": [],
            "hours_played": 0,
            "main_extra": 10,
            "category": "singleplayer",
            "release_year": 2021,
        },
    ]
    result = apply_filters(games, genre=["action"], eras=["2010-2015"], progress="all")
    assert len(result) == 1
    assert result[0]["name"] == "A"


def test_filter_category_coop_campaign_kept_under_singleplayer():
    """coop_campaign aparece no filtro 'all' mas não no 'singleplayer'."""
    games = [{"category": "singleplayer"}, {"category": "coop_campaign"}]
    # all inclui ambos (exclui só multiplayer)
    assert len(filter_category(games, category="all")) == 2
    # singleplayer exclui coop_campaign
    assert len(filter_category(games, category="singleplayer")) == 1


# --- None em main_extra (HLTB sem dado) ---


def test_filter_time_none_main_extra_treated_as_zero():
    """main_extra=None (sem dado HLTB) é tratado como 0h nos filtros de tempo."""
    games = [{"main_extra": None}, {"main_extra": 10}, {"main_extra": 20}]
    # min_hours=5: None (0) é excluído, 10 e 20 passam
    result = filter_time(games, min_hours=5)
    assert len(result) == 2
    # max_hours=15: None (0) e 10 passam, 20 não
    result = filter_time(games, max_hours=15)
    assert len(result) == 2


def test_filter_progress_none_main_extra_treated_as_zero():
    """main_extra=None não deve causar TypeError no filter_progress."""
    games = [{"hours_played": 0.0, "main_extra": None}, {"hours_played": 0.5, "main_extra": None}]
    # mode in_progress: 0 < hours < 0.5 * max(0, 1) = 0.5 → only 0.5 is ambiguous
    # just verifying no exception
    result = filter_progress(games, mode="in_progress")
    assert isinstance(result, list)
    result = filter_progress(games, mode="default")
    assert isinstance(result, list)


# --- overrides ---


def test_build_game_rows_applies_overrides(tmp_path, monkeypatch):
    """howl_overrides.json deve sobrescrever metacritic/release_year na row."""
    import json as json_mod

    overrides = {"Half-Life 2": {"metacritic": 99, "release_year": 2004, "comment": "test"}}
    (tmp_path / "howl_overrides.json").write_text(json_mod.dumps(overrides))
    monkeypatch.chdir(tmp_path)

    cache = {
        "Half-Life 2": {
            "hltb": {
                "game_name": "Half-Life 2",
                "main_story": 12,
                "main_extra": 15,
                "completionist": 19,
            },
            "steam": {
                "appid": 220,
                "positive_pct": 97,
                "total_reviews": 158000,
                "genres": ["action"],
                "categories": ["single-player"],
                "metacritic": None,
                "release_year": None,
            },
        }
    }
    steam_games = [{"name": "Half-Life 2", "appid": 220, "hours_played": 0.0}]

    import importlib

    import steam_hltb.core.classify as classify_mod

    importlib.reload(classify_mod)

    rows = classify_mod.build_game_rows(cache, steam_games)
    assert rows[0]["metacritic"] == 99
    assert rows[0]["release_year"] == 2004
    assert "comment" not in rows[0]


def test_build_game_rows_no_overrides_file(tmp_path, monkeypatch):
    """Sem howl_overrides.json, build_game_rows funciona normalmente."""
    monkeypatch.chdir(tmp_path)
    cache = {
        "Half-Life 2": {
            "hltb": {
                "game_name": "Half-Life 2",
                "main_story": 12,
                "main_extra": 15,
                "completionist": 19,
            },
            "steam": {
                "appid": 220,
                "positive_pct": 97,
                "total_reviews": 158000,
                "genres": ["action"],
                "categories": ["single-player"],
                "metacritic": 96,
                "release_year": 2004,
            },
        }
    }
    steam_games = [{"name": "Half-Life 2", "appid": 220, "hours_played": 0.0}]

    import importlib

    import steam_hltb.core.classify as classify_mod

    importlib.reload(classify_mod)

    rows = classify_mod.build_game_rows(cache, steam_games)
    assert rows[0]["metacritic"] == 96
    assert rows[0]["release_year"] == 2004


def test_build_game_rows_uses_igdb_metacritic_when_steam_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # isola do howl_overrides.json real
    cache = {
        "Fake IGDB Game": {
            "hltb": {
                "game_name": "Fake IGDB Game",
                "main_story": 50,
                "main_extra": 100,
                "completionist": 200,
            },
            "steam": {
                "appid": 999001,
                "metacritic": None,
                "genres": [],
                "release_year": None,
                "positive_pct": 94,
                "total_reviews": 500000,
                "categories": [],
            },
            "igdb": {
                "aggregated_rating": 90,
                "aggregated_rating_count": 8,
                "genres": ["Role-playing (RPG)"],
                "release_year": 2021,
            },
        }
    }
    steam_games = [{"name": "Fake IGDB Game", "appid": 999001, "hours_played": 10}]
    import importlib

    import steam_hltb.core.classify as classify_mod

    importlib.reload(classify_mod)
    rows = classify_mod.build_game_rows(cache, steam_games)
    assert len(rows) == 1
    assert rows[0]["metacritic"] == 90
    assert rows[0]["release_year"] == 2021


def test_build_game_rows_uses_igdb_genres_when_steam_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # isola do howl_overrides.json real
    cache = {
        "Fake IGDB Game": {
            "hltb": {
                "game_name": "Fake IGDB Game",
                "main_story": 50,
                "main_extra": 100,
                "completionist": 200,
            },
            "steam": {
                "appid": 999001,
                "metacritic": None,
                "genres": [],
                "release_year": None,
                "positive_pct": 94,
                "total_reviews": 500000,
                "categories": [],
            },
            "igdb": {
                "aggregated_rating": 90,
                "aggregated_rating_count": 8,
                "genres": ["Role-playing (RPG)", "Indie"],
                "release_year": 2021,
            },
        }
    }
    steam_games = [{"name": "Fake IGDB Game", "appid": 999001, "hours_played": 10}]
    import importlib

    import steam_hltb.core.classify as classify_mod

    importlib.reload(classify_mod)
    rows = classify_mod.build_game_rows(cache, steam_games)
    assert "role-playing (rpg)" in rows[0]["genres"]


def test_build_game_rows_steam_metacritic_overrides_igdb():
    cache = {
        "Half-Life 2": {
            "hltb": {
                "game_name": "Half-Life 2",
                "main_story": 12,
                "main_extra": 15,
                "completionist": 19,
            },
            "steam": {
                "appid": 220,
                "metacritic": 96,
                "genres": ["action"],
                "release_year": 2004,
                "positive_pct": 98,
                "total_reviews": 100000,
                "categories": ["single-player"],
            },
            "igdb": {
                "aggregated_rating": 80,
                "aggregated_rating_count": 10,
                "genres": ["Shooter"],
                "release_year": 2004,
            },
        }
    }
    steam_games = [{"name": "Half-Life 2", "appid": 220, "hours_played": 15}]
    rows = build_game_rows(cache, steam_games)
    assert rows[0]["metacritic"] == 96  # steam prevalece


def test_build_game_rows_no_igdb_data_unaffected():
    cache = {
        "No IGDB": {
            "hltb": {
                "game_name": "No IGDB",
                "main_story": 10,
                "main_extra": 15,
                "completionist": 20,
            },
            "steam": {
                "appid": 999,
                "metacritic": None,
                "genres": [],
                "release_year": None,
                "positive_pct": 80,
                "total_reviews": 100,
                "categories": [],
            },
        }
    }
    steam_games = [{"name": "No IGDB", "appid": 999, "hours_played": 0}]
    rows = build_game_rows(cache, steam_games)
    assert rows[0]["metacritic"] is None
    assert rows[0]["release_year"] is None


def test_build_game_rows_override_skips_comment_key(tmp_path, monkeypatch):
    from steam_hltb.core import classify

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        classify, "_load_overrides", lambda: {"Hades": {"comment": "nota", "metacritic": 99}}
    )
    cache = {
        "Hades": {
            "hltb": {"game_name": "Hades", "main_story": 20, "main_extra": 25},
            "steam": {"genres": ["action"], "categories": [], "metacritic": 90},
        }
    }
    steam_games = [{"name": "Hades", "appid": 1, "hours_played": 0}]
    rows = classify.build_game_rows(cache, steam_games)
    assert rows[0]["metacritic"] == 99  # override aplicado
    assert "comment" not in rows[0]  # chave 'comment' ignorada


def test_build_game_rows_ignores_non_dict_override(tmp_path, monkeypatch):
    from steam_hltb.core import classify

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(classify, "_load_overrides", lambda: {"Hades": "malformed"})
    cache = {
        "Hades": {
            "hltb": {"game_name": "Hades", "main_story": 20, "main_extra": 25},
            "steam": {"genres": ["action"], "categories": [], "metacritic": 90},
        }
    }
    steam_games = [{"name": "Hades", "appid": 1, "hours_played": 0}]
    rows = classify.build_game_rows(cache, steam_games)
    assert rows[0]["metacritic"] == 90  # override não-dict é ignorado


def test_category_multiplayer_only():
    from steam_hltb.core.classify import _category

    # só categoria multiplayer, sem single/coop → "multiplayer"
    assert _category(["multiplayer"], 0) == "multiplayer"


def test_build_game_rows_no_genres_no_rawg(tmp_path, monkeypatch):
    from steam_hltb.core import classify

    monkeypatch.chdir(tmp_path)  # isola do howl_overrides.json real
    cache = {
        "G": {
            "hltb": {"game_name": "G", "main_story": 10, "main_extra": 12},
            "steam": {"appid": 1},  # sem 'genres' e sem rawg → ramo else
        }
    }
    steam_games = [{"name": "G", "appid": 1, "hours_played": 0}]
    rows = classify.build_game_rows(cache, steam_games)
    assert rows[0]["genres"] == []
    assert rows[0]["metacritic"] is None
