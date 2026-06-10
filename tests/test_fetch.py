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


def test_fetch_rawg_returns_none_on_non_200():
    with patch("fetch.requests.get") as mock_get:
        mock_get.return_value.status_code = 404
        import fetch
        assert fetch.fetch_rawg("RAWG_KEY", "Half-Life 2") is None


def test_fetch_rawg_returns_none_when_no_results():
    with patch("fetch.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"results": []}
        import fetch
        assert fetch.fetch_rawg("RAWG_KEY", "Half-Life 2") is None


def test_fetch_rawg_returns_metacritic_genres_tags():
    with patch("fetch.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "results": [{
                "metacritic": 96,
                "genres": [{"name": "Action"}, {"name": "Shooter"}],
                "tags": [{"name": "Singleplayer"}, {"name": "FPS"}],
            }]
        }
        import fetch
        result = fetch.fetch_rawg("RAWG_KEY", "Half-Life 2")
        assert result == {
            "metacritic": 96,
            "genres": ["action", "shooter"],
            "tags": ["singleplayer", "fps"],
        }
