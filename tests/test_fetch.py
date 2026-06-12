import json
import pytest
from unittest.mock import patch, MagicMock


def test_load_cache_returns_empty_dict_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import importlib, fetch
    importlib.reload(fetch)
    assert fetch.load_cache() == {}


def test_save_and_load_cache_roundtrip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import importlib, fetch
    importlib.reload(fetch)
    data = {"Half-Life 2": {"hltb": {"main_story": 12}}}
    fetch.save_cache(data)
    assert fetch.load_cache() == data


def test_fetch_hltb_returns_none_when_no_results():
    with patch("fetch.HowLongToBeat") as MockHLTB:
        MockHLTB.return_value.search.return_value = []
        import fetch
        assert fetch.fetch_hltb("NonExistentGame99999") is None


def test_fetch_hltb_returns_none_when_low_similarity():
    with patch("fetch.HowLongToBeat") as MockHLTB:
        r = MagicMock()
        r.similarity = 0.3
        MockHLTB.return_value.search.return_value = [r]
        import fetch
        assert fetch.fetch_hltb("SomeGame") is None


def test_fetch_hltb_returns_data_when_good_match():
    with patch("fetch.HowLongToBeat") as MockHLTB:
        r = MagicMock()
        r.similarity = 0.9
        r.game_name = "Half-Life 2"
        r.main_story = 12.0
        r.main_extra = 15.0
        r.completionist = 19.0
        MockHLTB.return_value.search.return_value = [r]
        import fetch
        result = fetch.fetch_hltb("Half-Life 2")
        assert result == {
            "game_name": "Half-Life 2",
            "main_story": 12,
            "main_extra": 15,
            "completionist": 19,
        }


def test_fetch_hltb_returns_zero_for_negative_times():
    with patch("fetch.HowLongToBeat") as MockHLTB:
        r = MagicMock()
        r.similarity = 0.9
        r.game_name = "Some Game"
        r.main_story = -1.0
        r.main_extra = 0.0
        r.completionist = 5.0
        MockHLTB.return_value.search.return_value = [r]
        import fetch
        result = fetch.fetch_hltb("Some Game")
        assert result["main_story"] == 0
        assert result["main_extra"] == 0
        assert result["completionist"] == 5


def test_fetch_steam_app_details_returns_none_on_non_200():
    with patch("fetch.requests.get") as mock_get:
        mock_get.return_value.status_code = 500
        import fetch
        assert fetch.fetch_steam_app_details(220) is None


def test_fetch_steam_app_details_returns_none_when_not_success():
    with patch("fetch.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"220": {"success": False}}
        import fetch
        assert fetch.fetch_steam_app_details(220) is None


def test_fetch_steam_app_details_returns_metacritic_genres_categories():
    with patch("fetch.requests.get") as mock_get:
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
        import fetch
        result = fetch.fetch_steam_app_details(220)
        assert result == {
            "metacritic": 96,
            "genres": ["action"],
            "categories": ["single-player", "steam achievements"],
        }


def test_fetch_steam_reviews_returns_none_on_non_200():
    with patch("fetch.requests.get") as mock_get:
        mock_get.return_value.status_code = 500
        import fetch
        assert fetch.fetch_steam_reviews(220) is None


def test_fetch_steam_reviews_returns_none_when_zero_reviews():
    with patch("fetch.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "query_summary": {"total_reviews": 0, "total_positive": 0}
        }
        import fetch
        assert fetch.fetch_steam_reviews(220) is None


def test_fetch_steam_reviews_returns_positive_pct():
    with patch("fetch.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "query_summary": {
                "total_reviews": 1000,
                "total_positive": 970,
            }
        }
        import fetch
        result = fetch.fetch_steam_reviews(220)
        assert result == {"positive_pct": 97, "total_reviews": 1000}


def test_get_steam_games_parses_response():
    with patch("fetch.requests.get") as mock_get:
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "response": {
                "games": [
                    {"name": "Half-Life 2", "appid": 220, "playtime_forever": 120},
                    {"name": "Portal 2",    "appid": 620, "playtime_forever": 0},
                ]
            }
        }
        import fetch
        games = fetch.get_steam_games("KEY", "STEAMID")
        assert len(games) == 2
        assert games[0] == {"name": "Half-Life 2", "appid": 220, "hours_played": 2.0}
        assert games[1] == {"name": "Portal 2",    "appid": 620, "hours_played": 0.0}


def test_resolve_steamid_raises_on_failure():
    with patch("fetch.requests.get") as mock_get:
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "response": {"success": 42, "message": "No match"}
        }
        import fetch
        with pytest.raises(ValueError, match="not found"):
            fetch.resolve_steamid("KEY", "unknownuser")


def test_build_library_verbose_false_hides_cache_lines(capsys, monkeypatch):
    monkeypatch.setattr("fetch.resolve_steamid", lambda key, user: "76561198000000")
    monkeypatch.setattr("fetch.get_steam_games", lambda key, sid: [
        {"name": "Half-Life 2", "appid": 220, "hours_played": 1.0}
    ])
    monkeypatch.setattr("fetch.save_cache", lambda c: None)

    cache = {
        "Half-Life 2": {
            "hltb": {"game_name": "Half-Life 2", "main_story": 12, "main_extra": 15, "completionist": 19},
            "rawg": None,
            "steam": {"appid": 220},
        }
    }

    import fetch
    fetch.build_library("key", "user", cache, verbose=False)

    out = capsys.readouterr().out
    assert "[1/1] Half-Life 2 (cache)" not in out


def test_build_library_verbose_true_shows_cache_lines(capsys, monkeypatch):
    monkeypatch.setattr("fetch.resolve_steamid", lambda key, user: "76561198000000")
    monkeypatch.setattr("fetch.get_steam_games", lambda key, sid: [
        {"name": "Half-Life 2", "appid": 220, "hours_played": 1.0}
    ])
    monkeypatch.setattr("fetch.save_cache", lambda c: None)

    cache = {
        "Half-Life 2": {
            "hltb": {"game_name": "Half-Life 2", "main_story": 12, "main_extra": 15, "completionist": 19},
            "rawg": None,
            "steam": {"appid": 220},
        }
    }

    import fetch
    fetch.build_library("key", "user", cache, verbose=True)

    out = capsys.readouterr().out
    assert "[1/1] Half-Life 2 (cache)" in out


def test_build_library_verbose_false_prints_fetching_for_new_games(capsys, monkeypatch):
    monkeypatch.setattr("fetch.resolve_steamid", lambda key, user: "76561198000000")
    monkeypatch.setattr("fetch.get_steam_games", lambda key, sid: [
        {"name": "Half-Life 2", "appid": 220, "hours_played": 1.0}
    ])
    monkeypatch.setattr("fetch.save_cache", lambda c: None)
    monkeypatch.setattr("fetch.fetch_hltb", lambda name: None)  # jogo sem HLTB = skip

    cache = {}  # vazio: Half-Life 2 NÃO está no cache

    import fetch
    fetch.build_library("key", "user", cache, verbose=False)

    out = capsys.readouterr().out
    assert "Fetching: Half-Life 2" in out
    assert "[1/1] Half-Life 2" not in out


def test_build_library_verbose_true_prints_indexed_for_new_games(capsys, monkeypatch):
    monkeypatch.setattr("fetch.resolve_steamid", lambda key, user: "76561198000000")
    monkeypatch.setattr("fetch.get_steam_games", lambda key, sid: [
        {"name": "Half-Life 2", "appid": 220, "hours_played": 1.0}
    ])
    monkeypatch.setattr("fetch.save_cache", lambda c: None)
    monkeypatch.setattr("fetch.fetch_hltb", lambda name: None)

    cache = {}

    import fetch
    fetch.build_library("key", "user", cache, verbose=True)

    out = capsys.readouterr().out
    assert "[1/1] Half-Life 2" in out
    assert "Fetching:" not in out.split("\n", 1)[1]  # "Fetching:" não aparece após a 1ª linha
