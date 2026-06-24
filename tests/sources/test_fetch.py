from unittest.mock import MagicMock, patch

import pytest

from steam_hltb.sources.fetch import migrate_igdb_data


def test_load_cache_returns_empty_dict_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import importlib

    from steam_hltb.sources import fetch

    importlib.reload(fetch)
    assert fetch.load_cache() == {}


def test_save_and_load_cache_roundtrip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import importlib

    from steam_hltb.sources import fetch

    importlib.reload(fetch)
    data = {"Half-Life 2": {"hltb": {"main_story": 12}}}
    fetch.save_cache(data)
    assert fetch.load_cache() == data


def test_fetch_hltb_returns_none_when_no_results():
    with patch("steam_hltb.sources.fetch.HowLongToBeat") as MockHLTB:
        MockHLTB.return_value.search.return_value = []
        from steam_hltb.sources import fetch

        assert fetch.fetch_hltb("NonExistentGame99999") is None


def test_fetch_hltb_returns_none_when_low_similarity():
    with patch("steam_hltb.sources.fetch.HowLongToBeat") as MockHLTB:
        r = MagicMock()
        r.similarity = 0.3
        MockHLTB.return_value.search.return_value = [r]
        from steam_hltb.sources import fetch

        assert fetch.fetch_hltb("SomeGame") is None


def test_fetch_hltb_returns_none_at_boundary_similarity():
    """similarity < 0.6 deve rejeitar — garante que FEZTAL (0.55) é rejeitado."""
    with patch("steam_hltb.sources.fetch.HowLongToBeat") as MockHLTB:
        r = MagicMock()
        r.similarity = 0.55
        r.game_name = "FEZTAL"
        MockHLTB.return_value.search.return_value = [r]
        from steam_hltb.sources import fetch

        assert fetch.fetch_hltb("FEZ") is None


def test_fetch_hltb_returns_data_when_good_match():
    with patch("steam_hltb.sources.fetch.HowLongToBeat") as MockHLTB:
        r = MagicMock()
        r.similarity = 0.9
        r.game_name = "Half-Life 2"
        r.main_story = 12.0
        r.main_extra = 15.0
        r.completionist = 19.0
        MockHLTB.return_value.search.return_value = [r]
        from steam_hltb.sources import fetch

        result = fetch.fetch_hltb("Half-Life 2")
        assert result == {
            "game_name": "Half-Life 2",
            "main_story": 12,
            "main_extra": 15,
            "completionist": 19,
        }


def test_fetch_hltb_returns_none_for_missing_or_zero_times():
    """Tempos negativos ou zero = dado ausente → None, não 0."""
    with patch("steam_hltb.sources.fetch.HowLongToBeat") as MockHLTB:
        r = MagicMock()
        r.similarity = 0.9
        r.game_name = "Some Game"
        r.main_story = -1.0
        r.main_extra = 0.0
        r.completionist = 5.0
        MockHLTB.return_value.search.return_value = [r]
        from steam_hltb.sources import fetch

        result = fetch.fetch_hltb("Some Game")
        assert result["main_story"] is None
        assert result["main_extra"] is None
        assert result["completionist"] == 5


def test_fetch_steam_app_details_returns_none_on_non_200():
    with patch("steam_hltb.sources.fetch.requests.get") as mock_get:
        mock_get.return_value.status_code = 500
        from steam_hltb.sources import fetch

        assert fetch.fetch_steam_app_details(220) is None


def test_fetch_steam_app_details_returns_none_when_not_success():
    with patch("steam_hltb.sources.fetch.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"220": {"success": False}}
        from steam_hltb.sources import fetch

        assert fetch.fetch_steam_app_details(220) is None


def test_fetch_steam_app_details_returns_metacritic_genres_categories():
    with patch("steam_hltb.sources.fetch.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "220": {
                "success": True,
                "data": {
                    "metacritic": {"score": 96},
                    "genres": [{"id": "1", "description": "Action"}],
                    "categories": [
                        {"id": 2, "description": "Single-player"},
                        {"id": 22, "description": "Steam Achievements"},
                    ],
                },
            }
        }
        from steam_hltb.sources import fetch

        result = fetch.fetch_steam_app_details(220)
        assert result == {
            "metacritic": 96,
            "genres": ["action"],
            "categories": ["single-player", "steam achievements"],
            "release_year": None,
        }


def test_fetch_steam_app_details_extracts_release_year():
    with patch("steam_hltb.sources.fetch.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "220": {
                "success": True,
                "data": {
                    "release_date": {"date": "16 Nov, 2004"},
                    "genres": [],
                    "categories": [],
                },
            }
        }
        from steam_hltb.sources import fetch

        result = fetch.fetch_steam_app_details(220)
        assert result["release_year"] == 2004


def test_fetch_steam_app_details_release_year_none_when_missing():
    with patch("steam_hltb.sources.fetch.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "220": {
                "success": True,
                "data": {
                    "genres": [],
                    "categories": [],
                },
            }
        }
        from steam_hltb.sources import fetch

        result = fetch.fetch_steam_app_details(220)
        assert result["release_year"] is None


def test_fetch_steam_reviews_returns_none_on_non_200():
    with patch("steam_hltb.sources.fetch.requests.get") as mock_get:
        mock_get.return_value.status_code = 500
        from steam_hltb.sources import fetch

        assert fetch.fetch_steam_reviews(220) is None


def test_fetch_steam_reviews_returns_none_when_zero_reviews():
    with patch("steam_hltb.sources.fetch.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "query_summary": {"total_reviews": 0, "total_positive": 0}
        }
        from steam_hltb.sources import fetch

        assert fetch.fetch_steam_reviews(220) is None


def test_fetch_steam_reviews_returns_positive_pct():
    with patch("steam_hltb.sources.fetch.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "query_summary": {
                "total_reviews": 1000,
                "total_positive": 970,
            }
        }
        from steam_hltb.sources import fetch

        result = fetch.fetch_steam_reviews(220)
        assert result == {"positive_pct": 97, "total_reviews": 1000}


def test_get_steam_games_parses_response():
    with patch("steam_hltb.sources.fetch.requests.get") as mock_get:
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "response": {
                "games": [
                    {"name": "Half-Life 2", "appid": 220, "playtime_forever": 120},
                    {"name": "Portal 2", "appid": 620, "playtime_forever": 0},
                ]
            }
        }
        from steam_hltb.sources import fetch

        games = fetch.get_steam_games("KEY", "STEAMID")
        assert len(games) == 2
        assert games[0] == {"name": "Half-Life 2", "appid": 220, "hours_played": 2.0}
        assert games[1] == {"name": "Portal 2", "appid": 620, "hours_played": 0.0}


def test_resolve_steamid_raises_on_failure():
    with patch("steam_hltb.sources.fetch.requests.get") as mock_get:
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "response": {"success": 42, "message": "No match"}
        }
        from steam_hltb.sources import fetch

        with pytest.raises(ValueError, match="not found"):
            fetch.resolve_steamid("KEY", "unknownuser")


def test_build_library_verbose_false_hides_cache_lines(capsys, monkeypatch):
    monkeypatch.setattr(
        "steam_hltb.sources.fetch.resolve_steamid", lambda key, user: "76561198000000"
    )
    monkeypatch.setattr(
        "steam_hltb.sources.fetch.get_steam_games",
        lambda key, sid: [{"name": "Half-Life 2", "appid": 220, "hours_played": 1.0}],
    )
    monkeypatch.setattr("steam_hltb.sources.fetch.save_cache", lambda c: None)

    cache = {
        "Half-Life 2": {
            "hltb": {
                "game_name": "Half-Life 2",
                "main_story": 12,
                "main_extra": 15,
                "completionist": 19,
            },
            "rawg": None,
            "steam": {"appid": 220},
        }
    }

    from steam_hltb.sources import fetch

    fetch.build_library("key", "user", cache, verbose=False)

    out = capsys.readouterr().out
    assert "[1/1] Half-Life 2 (cache)" not in out


def test_build_library_verbose_true_shows_cache_lines(capsys, monkeypatch):
    monkeypatch.setattr(
        "steam_hltb.sources.fetch.resolve_steamid", lambda key, user: "76561198000000"
    )
    monkeypatch.setattr(
        "steam_hltb.sources.fetch.get_steam_games",
        lambda key, sid: [{"name": "Half-Life 2", "appid": 220, "hours_played": 1.0}],
    )
    monkeypatch.setattr("steam_hltb.sources.fetch.save_cache", lambda c: None)

    cache = {
        "Half-Life 2": {
            "hltb": {
                "game_name": "Half-Life 2",
                "main_story": 12,
                "main_extra": 15,
                "completionist": 19,
            },
            "rawg": None,
            "steam": {"appid": 220},
        }
    }

    from steam_hltb.sources import fetch

    fetch.build_library("key", "user", cache, verbose=True)

    out = capsys.readouterr().out
    assert "[1/1] Half-Life 2 (cache)" in out


def test_migrate_steam_details_fills_missing_genres(monkeypatch):
    cache = {
        "Half-Life 2": {
            "hltb": {
                "game_name": "Half-Life 2",
                "main_story": 12,
                "main_extra": 15,
                "completionist": 19,
            },
            "steam": {"appid": 220, "positive_pct": 98, "total_reviews": 100000},
            "rawg": {"metacritic": 96, "genres": ["action"], "tags": []},
        }
    }
    monkeypatch.setattr(
        "steam_hltb.sources.fetch.fetch_steam_app_details",
        lambda appid: {
            "metacritic": 96,
            "genres": ["action"],
            "categories": ["single-player"],
        },
    )
    monkeypatch.setattr("steam_hltb.sources.fetch.save_cache", lambda c: None)
    monkeypatch.setattr("steam_hltb.sources.fetch.time.sleep", lambda s: None)
    from steam_hltb.sources.fetch import migrate_steam_details

    updated = migrate_steam_details(cache, verbose=False)
    steam = updated["Half-Life 2"]["steam"]
    assert steam["genres"] == ["action"]
    assert steam["categories"] == ["single-player"]
    assert steam["metacritic"] == 96


def test_migrate_steam_details_skips_already_migrated(monkeypatch):
    cache = {
        "Hades": {
            "hltb": {"game_name": "Hades", "main_story": 20, "main_extra": 22, "completionist": 90},
            "steam": {
                "appid": 1145360,
                "positive_pct": 97,
                "total_reviews": 50000,
                "genres": ["action"],
                "categories": ["single-player"],
                "release_year": 2020,
            },
        }
    }
    called = []
    monkeypatch.setattr(
        "steam_hltb.sources.fetch.fetch_steam_app_details", lambda appid: called.append(appid) or {}
    )
    monkeypatch.setattr("steam_hltb.sources.fetch.save_cache", lambda c: None)
    monkeypatch.setattr("steam_hltb.sources.fetch.time.sleep", lambda s: None)
    from steam_hltb.sources.fetch import migrate_steam_details

    migrate_steam_details(cache, verbose=False)
    assert called == []


def test_migrate_steam_details_skips_no_appid(monkeypatch):
    cache = {
        "GameNoAppid": {
            "hltb": {"game_name": "X", "main_story": 5, "main_extra": 8, "completionist": 10},
            "steam": {"positive_pct": 90, "total_reviews": 1000},
        }
    }
    called = []
    monkeypatch.setattr(
        "steam_hltb.sources.fetch.fetch_steam_app_details", lambda appid: called.append(appid) or {}
    )
    monkeypatch.setattr("steam_hltb.sources.fetch.save_cache", lambda c: None)
    monkeypatch.setattr("steam_hltb.sources.fetch.time.sleep", lambda s: None)
    from steam_hltb.sources.fetch import migrate_steam_details

    migrate_steam_details(cache, verbose=False)
    assert called == []
    assert "genres" not in cache["GameNoAppid"]["steam"]


def test_fetch_steam_app_details_us_date_format():
    """Formato "Nov 16, 2004" também deve extrair o ano."""
    with patch("steam_hltb.sources.fetch.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "220": {
                "success": True,
                "data": {
                    "release_date": {"date": "Nov 16, 2004"},
                    "genres": [],
                    "categories": [],
                },
            }
        }
        from steam_hltb.sources import fetch

        result = fetch.fetch_steam_app_details(220)
        assert result["release_year"] == 2004


def test_fetch_steam_app_details_invalid_date_returns_none():
    with patch("steam_hltb.sources.fetch.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "220": {
                "success": True,
                "data": {
                    "release_date": {"date": "Coming Soon"},
                    "genres": [],
                    "categories": [],
                },
            }
        }
        from steam_hltb.sources import fetch

        result = fetch.fetch_steam_app_details(220)
        assert result["release_year"] is None


def test_resolve_steamid_returns_steamid_on_success():
    with patch("steam_hltb.sources.fetch.requests.get") as mock_get:
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "response": {"success": 1, "steamid": "76561198012345678"}
        }
        from steam_hltb.sources import fetch

        result = fetch.resolve_steamid("KEY", "testuser")
        assert result == "76561198012345678"


def test_build_library_refresh_re_fetches_cached_games(capsys, monkeypatch):
    """Com refresh=True, games já no cache devem ser rebuscados."""
    monkeypatch.setattr(
        "steam_hltb.sources.fetch.resolve_steamid", lambda key, user: "76561198000000"
    )
    monkeypatch.setattr(
        "steam_hltb.sources.fetch.get_steam_games",
        lambda key, sid: [{"name": "Half-Life 2", "appid": 220, "hours_played": 1.0}],
    )
    monkeypatch.setattr("steam_hltb.sources.fetch.save_cache", lambda c: None)
    fetch_calls = []
    monkeypatch.setattr(
        "steam_hltb.sources.fetch.fetch_hltb", lambda name: fetch_calls.append(name) or None
    )

    cache = {
        "Half-Life 2": {
            "hltb": {
                "game_name": "Half-Life 2",
                "main_story": 12,
                "main_extra": 15,
                "completionist": 19,
            },
            "steam": {"appid": 220},
        }
    }

    from steam_hltb.sources import fetch

    fetch.build_library("key", "user", cache, refresh=True, verbose=False)
    assert "Half-Life 2" in fetch_calls  # foi rebuscado apesar de estar no cache


def test_migrate_steam_details_verbose_prints_progress(capsys, monkeypatch):
    cache = {
        "Half-Life 2": {
            "hltb": {
                "game_name": "Half-Life 2",
                "main_story": 12,
                "main_extra": 15,
                "completionist": 19,
            },
            "steam": {"appid": 220, "positive_pct": 98, "total_reviews": 100000},
        }
    }
    monkeypatch.setattr(
        "steam_hltb.sources.fetch.fetch_steam_app_details",
        lambda appid: {
            "metacritic": 96,
            "genres": ["action"],
            "categories": ["single-player"],
            "release_year": 2004,
        },
    )
    monkeypatch.setattr("steam_hltb.sources.fetch.save_cache", lambda c: None)
    monkeypatch.setattr("steam_hltb.sources.fetch.time.sleep", lambda s: None)
    from steam_hltb.sources.fetch import migrate_steam_details

    migrate_steam_details(cache, verbose=True)
    out = capsys.readouterr().out
    assert "Half-Life 2" in out
    assert "Migrando" in out or "incompletas" in out


def test_build_library_verbose_false_silent_for_new_games(capsys, monkeypatch):
    monkeypatch.setattr(
        "steam_hltb.sources.fetch.resolve_steamid", lambda key, user: "76561198000000"
    )
    monkeypatch.setattr(
        "steam_hltb.sources.fetch.get_steam_games",
        lambda key, sid: [{"name": "Half-Life 2", "appid": 220, "hours_played": 1.0}],
    )
    monkeypatch.setattr("steam_hltb.sources.fetch.save_cache", lambda c: None)
    monkeypatch.setattr("steam_hltb.sources.fetch.fetch_hltb", lambda name: None)

    cache = {}

    from steam_hltb.sources import fetch

    fetch.build_library("key", "user", cache, verbose=False)

    out = capsys.readouterr().out
    assert out == ""


def test_build_library_verbose_true_prints_indexed_for_new_games(capsys, monkeypatch):
    monkeypatch.setattr(
        "steam_hltb.sources.fetch.resolve_steamid", lambda key, user: "76561198000000"
    )
    monkeypatch.setattr(
        "steam_hltb.sources.fetch.get_steam_games",
        lambda key, sid: [{"name": "Half-Life 2", "appid": 220, "hours_played": 1.0}],
    )
    monkeypatch.setattr("steam_hltb.sources.fetch.save_cache", lambda c: None)
    monkeypatch.setattr("steam_hltb.sources.fetch.fetch_hltb", lambda name: None)

    cache = {}

    from steam_hltb.sources import fetch

    fetch.build_library("key", "user", cache, verbose=True)

    out = capsys.readouterr().out
    assert "[1/1] Half-Life 2" in out
    assert "Fetching:" not in out


def test_migrate_igdb_fills_missing_metacritic():
    cache = {
        "Valheim": {
            "hltb": {
                "game_name": "Valheim",
                "main_story": 50,
                "main_extra": 100,
                "completionist": 200,
            },
            "steam": {"appid": 892970, "metacritic": None, "genres": [], "release_year": None},
        }
    }
    igdb_data = {
        "aggregated_rating": 90,
        "aggregated_rating_count": 8,
        "genres": ["RPG"],
        "release_year": 2021,
    }
    with (
        patch("steam_hltb.sources.fetch.igdb.fetch_by_appid", return_value=igdb_data),
        patch("steam_hltb.sources.fetch.igdb.get_token", return_value="tok"),
        patch("steam_hltb.sources.fetch.save_cache"),
        patch("time.sleep"),
    ):
        result = migrate_igdb_data(cache, client_id="cid", client_secret="csec")
    assert result["Valheim"]["igdb"]["aggregated_rating"] == 90
    assert result["Valheim"]["igdb"]["release_year"] == 2021


def test_migrate_igdb_skips_games_with_metacritic():
    cache = {
        "Half-Life 2": {
            "hltb": {
                "game_name": "Half-Life 2",
                "main_story": 12,
                "main_extra": 15,
                "completionist": 19,
            },
            "steam": {"appid": 220, "metacritic": 96, "genres": ["action"], "release_year": 2004},
        }
    }
    with (
        patch("steam_hltb.sources.fetch.igdb.fetch_by_appid") as mock_fetch,
        patch("steam_hltb.sources.fetch.igdb.get_token", return_value="tok"),
        patch("steam_hltb.sources.fetch.save_cache"),
        patch("time.sleep"),
    ):
        migrate_igdb_data(cache, client_id="cid", client_secret="csec")
    mock_fetch.assert_not_called()


def test_migrate_igdb_skips_games_already_with_igdb_entry():
    cache = {
        "Already Cached": {
            "hltb": {"game_name": "Already Cached", "main_story": 10},
            "steam": {"appid": 123, "metacritic": None},
            "igdb": {"aggregated_rating": 80, "genres": ["Action"]},
        }
    }
    with (
        patch("steam_hltb.sources.fetch.igdb.fetch_by_appid") as mock_fetch,
        patch("steam_hltb.sources.fetch.igdb.get_token", return_value="tok"),
        patch("steam_hltb.sources.fetch.save_cache"),
        patch("time.sleep"),
    ):
        migrate_igdb_data(cache, client_id="cid", client_secret="csec")
    mock_fetch.assert_not_called()


def test_migrate_igdb_falls_back_to_name_when_appid_returns_none():
    cache = {
        "Deus Ex: Human Revolution": {
            "hltb": {"game_name": "Deus Ex: Human Revolution", "main_story": 15},
            "steam": {"appid": 28050, "metacritic": None},
        }
    }
    igdb_data = {
        "aggregated_rating": 89,
        "aggregated_rating_count": 25,
        "genres": ["RPG"],
        "release_year": 2011,
    }
    with (
        patch("steam_hltb.sources.fetch.igdb.fetch_by_appid", return_value=None),
        patch("steam_hltb.sources.fetch.igdb.fetch_by_name", return_value=igdb_data),
        patch("steam_hltb.sources.fetch.igdb.get_token", return_value="tok"),
        patch("steam_hltb.sources.fetch.save_cache"),
        patch("time.sleep"),
    ):
        result = migrate_igdb_data(cache, client_id="cid", client_secret="csec")
    assert result["Deus Ex: Human Revolution"]["igdb"]["aggregated_rating"] == 89


def test_migrate_igdb_returns_early_without_credentials():
    cache = {"Game": {"steam": {"metacritic": None}, "hltb": {}}}
    with patch("steam_hltb.sources.fetch.igdb.get_token") as mock_token:
        result = migrate_igdb_data(cache, client_id=None, client_secret=None)
    mock_token.assert_not_called()
    assert "igdb" not in result["Game"]


def test_get_api_key_from_env(monkeypatch):
    from steam_hltb.sources.fetch import get_api_key

    monkeypatch.setenv("MY_KEY", "secret")
    assert get_api_key("MY_KEY", "prompt") == "secret"


def test_get_api_key_prompts_when_absent(monkeypatch):
    from steam_hltb.sources.fetch import get_api_key

    monkeypatch.delenv("MY_KEY", raising=False)
    monkeypatch.setattr("builtins.input", lambda _: "  typed  ")
    assert get_api_key("MY_KEY", "prompt") == "typed"


def test_build_library_fetches_new_game_with_hltb(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from steam_hltb.sources import fetch

    monkeypatch.setattr(fetch, "resolve_steamid", lambda k, u: "1")
    monkeypatch.setattr(
        fetch, "get_steam_games", lambda k, sid: [{"name": "G", "appid": 7, "hours_played": 0}]
    )
    monkeypatch.setattr(
        fetch,
        "fetch_hltb",
        lambda name: {"game_name": name, "main_story": 10, "main_extra": 12, "completionist": 20},
    )
    monkeypatch.setattr(
        fetch, "fetch_steam_reviews", lambda appid: {"positive_pct": 95, "total_reviews": 100}
    )
    monkeypatch.setattr(
        fetch,
        "fetch_steam_app_details",
        lambda appid: {
            "metacritic": 90,
            "genres": ["action"],
            "categories": [],
            "release_year": 2020,
        },
    )
    monkeypatch.setattr(fetch.time, "sleep", lambda s: None)
    cache, _ = fetch.build_library("k", "u", {})
    assert cache["G"]["hltb"]["game_name"] == "G"
    assert cache["G"]["steam"]["appid"] == 7
    assert cache["G"]["steam"]["metacritic"] == 90


def test_migrate_igdb_verbose_no_credentials(capsys, monkeypatch):
    from steam_hltb.sources.fetch import migrate_igdb_data

    monkeypatch.delenv("IGDB_CLIENT_ID", raising=False)
    monkeypatch.delenv("IGDB_CLIENT_SECRET", raising=False)
    migrate_igdb_data({}, verbose=True)
    assert "pulando" in capsys.readouterr().out


def test_migrate_igdb_verbose_token_failure(capsys, monkeypatch):
    from steam_hltb.sources import fetch

    monkeypatch.setattr(fetch.igdb, "get_token", lambda cid, cs: None)
    fetch.migrate_igdb_data({}, client_id="x", client_secret="y", verbose=True)
    assert "Falha ao obter token" in capsys.readouterr().out


def test_migrate_igdb_verbose_found(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from steam_hltb.sources import fetch

    monkeypatch.setattr(fetch.igdb, "get_token", lambda cid, cs: "tok")
    monkeypatch.setattr(
        fetch.igdb, "fetch_by_appid", lambda cid, tok, appid, **kw: {"aggregated_rating": 88}
    )
    monkeypatch.setattr(fetch.time, "sleep", lambda s: None)
    cache = {"G": {"steam": {"appid": 5, "metacritic": None}}}
    fetch.migrate_igdb_data(cache, client_id="x", client_secret="y", verbose=True)
    out = capsys.readouterr().out
    assert "Buscando dados IGDB" in out
    assert "88" in out
    assert cache["G"]["igdb"]["aggregated_rating"] == 88


def test_migrate_igdb_verbose_not_found(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from steam_hltb.sources import fetch

    monkeypatch.setattr(fetch.igdb, "get_token", lambda cid, cs: "tok")
    monkeypatch.setattr(fetch.igdb, "fetch_by_appid", lambda cid, tok, appid, **kw: None)
    monkeypatch.setattr(fetch.igdb, "fetch_by_name", lambda cid, tok, name, **kw: None)
    monkeypatch.setattr(fetch.time, "sleep", lambda s: None)
    cache = {"G": {"steam": {"appid": 5, "metacritic": None}}}
    fetch.migrate_igdb_data(cache, client_id="x", client_secret="y", verbose=True)
    assert "não encontrado" in capsys.readouterr().out


def test_migrate_igdb_verbose_partial(capsys, tmp_path, monkeypatch):
    """Resultado parcial (genres/ano mas sem rating) aparece como '~ parcial' no log."""
    monkeypatch.chdir(tmp_path)
    from steam_hltb.sources import fetch

    partial = {
        "aggregated_rating": None,
        "aggregated_rating_count": 0,
        "genres": ["Adventure"],
        "release_year": 2011,
    }
    monkeypatch.setattr(fetch.igdb, "get_token", lambda cid, cs: "tok")
    monkeypatch.setattr(fetch.igdb, "fetch_by_appid", lambda cid, tok, appid, **kw: partial)
    monkeypatch.setattr(fetch.time, "sleep", lambda s: None)
    cache = {"G": {"steam": {"appid": 5, "metacritic": None}}}
    fetch.migrate_igdb_data(cache, client_id="x", client_secret="y", verbose=True)
    out = capsys.readouterr().out
    assert "parcial" in out
    assert "Adventure" in out
    assert cache["G"]["igdb"]["aggregated_rating"] is None


def test_migrate_steam_details_skips_when_details_none(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from steam_hltb.sources import fetch

    monkeypatch.setattr(fetch, "fetch_steam_app_details", lambda appid: None)
    monkeypatch.setattr(fetch.time, "sleep", lambda s: None)
    cache = {"G": {"steam": {"appid": 5}}}  # falta genres/release_year → pendente
    fetch.migrate_steam_details(cache)
    assert "genres" not in cache["G"]["steam"]  # details None → nada atualizado


def test_migrate_igdb_token_failure_quiet(monkeypatch):
    from steam_hltb.sources import fetch

    monkeypatch.setattr(fetch.igdb, "get_token", lambda cid, cs: None)
    assert fetch.migrate_igdb_data({}, client_id="x", client_secret="y") == {}  # verbose False


def test_migrate_igdb_not_found_quiet(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from steam_hltb.sources import fetch

    monkeypatch.setattr(fetch.igdb, "get_token", lambda cid, cs: "tok")
    monkeypatch.setattr(fetch.igdb, "fetch_by_appid", lambda c, t, a, **kw: None)
    monkeypatch.setattr(fetch.igdb, "fetch_by_name", lambda c, t, n, **kw: None)
    monkeypatch.setattr(fetch.time, "sleep", lambda s: None)
    cache = {"G": {"steam": {"appid": 5, "metacritic": None}}}
    fetch.migrate_igdb_data(cache, client_id="x", client_secret="y")  # verbose False
    assert "igdb" not in cache["G"]


def test_steam_http_calls_use_timeout(monkeypatch):
    """Robustez: chamadas HTTP da Steam não podem ficar sem timeout (trava infinita)."""
    from steam_hltb.sources import fetch

    seen = []

    def fake_get(*args, **kwargs):
        seen.append(kwargs.get("timeout"))
        resp = MagicMock()
        resp.status_code = 500
        return resp

    monkeypatch.setattr("steam_hltb.sources.fetch.requests.get", fake_get)
    fetch.fetch_steam_app_details(1)
    fetch.fetch_steam_reviews(1)
    assert seen and all(t == fetch.HTTP_TIMEOUT for t in seen)
