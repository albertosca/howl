import json
import os
import time
from unittest.mock import MagicMock, patch

import pytest

from steam_hltb.sources import igdb
from steam_hltb.sources.igdb import (
    _name_similarity,
    _normalize_for_igdb,
    fetch_by_appid,
    fetch_by_name,
    get_token,
)


def test_save_token_writes_to_config_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    igdb._save_token("tok123", time.time() + 9999)
    token_file = tmp_path / "howl" / ".igdb_token.json"
    assert token_file.exists()
    assert json.loads(token_file.read_text())["access_token"] == "tok123"
    assert (os.stat(tmp_path / "howl").st_mode & 0o777) == 0o700


def test_load_token_reads_from_config_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    cfg = tmp_path / "howl"
    cfg.mkdir()
    (cfg / ".igdb_token.json").write_text(
        json.dumps({"access_token": "fromcfg", "expires_at": time.time() + 9999})
    )
    assert igdb._load_token()["access_token"] == "fromcfg"


def test_get_token_fetches_when_no_file():
    with (
        patch("steam_hltb.sources.igdb._load_token", return_value=None),
        patch(
            "steam_hltb.sources.igdb._refresh_token", return_value=("tok123", time.time() + 9999)
        ) as mock_refresh,
    ):
        token = get_token("cid", "csecret")
    assert token == "tok123"
    mock_refresh.assert_called_once_with("cid", "csecret")


def test_get_token_uses_cached_when_valid():
    valid = {"access_token": "cached", "expires_at": time.time() + 9999}
    with patch("steam_hltb.sources.igdb._load_token", return_value=valid):
        token = get_token("cid", "csecret")
    assert token == "cached"


def test_get_token_refreshes_when_expired():
    expired = {"access_token": "old", "expires_at": time.time() - 1}
    with (
        patch("steam_hltb.sources.igdb._load_token", return_value=expired),
        patch(
            "steam_hltb.sources.igdb._refresh_token", return_value=("new", time.time() + 9999)
        ) as mock_r,
    ):
        token = get_token("cid", "csecret")
    assert token == "new"
    mock_r.assert_called_once()


def test_get_token_returns_none_when_no_credentials():
    assert get_token(None, None) is None
    assert get_token("", "") is None


def test_fetch_by_appid_returns_data():
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = [
        {
            "name": "Valheim",
            "aggregated_rating": 90.0,
            "aggregated_rating_count": 8,
            "genres": [{"name": "Role-playing (RPG)"}, {"name": "Indie"}],
            "first_release_date": 1613000000,
        }
    ]
    with patch("requests.post", return_value=mock_resp):
        result = fetch_by_appid("cid", "tok", 892970)
    assert result["aggregated_rating"] == 90
    assert result["release_year"] == 2021
    assert "Role-playing (RPG)" in result["genres"]


def test_fetch_by_appid_returns_none_when_empty():
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = []
    with patch("requests.post", return_value=mock_resp):
        result = fetch_by_appid("cid", "tok", 99999)
    assert result is None


def test_fetch_by_name_returns_data():
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = [
        {
            "name": "Deus Ex: Human Revolution",
            "aggregated_rating": 89.0,
            "aggregated_rating_count": 25,
            "genres": [{"name": "Shooter"}, {"name": "Role-playing (RPG)"}],
            "first_release_date": 1313000000,
        }
    ]
    with patch("requests.post", return_value=mock_resp):
        result = fetch_by_name("cid", "tok", "Deus Ex: Human Revolution")
    assert result["aggregated_rating"] == 89
    assert result["release_year"] == 2011


def test_fetch_by_name_ignores_low_rating_count_no_genres():
    """Rating count < 3 e sem gêneros/ano → None."""
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = [
        {
            "name": "Some Obscure Game",
            "aggregated_rating": 95.0,
            "aggregated_rating_count": 1,
            "genres": [],
            "first_release_date": None,
        }
    ]
    with patch("requests.post", return_value=mock_resp):
        result = fetch_by_name("cid", "tok", "Some Obscure Game")
    assert result is None


def test_missing_credentials_returns_none():
    assert fetch_by_appid(None, None, 892970) is None
    assert fetch_by_name(None, None, "game") is None


def test_load_token_returns_none_when_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))  # sem arquivo de token
    assert igdb._load_token() is None


def test_refresh_token_posts_and_saves(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    resp = MagicMock()
    resp.json.return_value = {"access_token": "newtok", "expires_in": 5000}
    with patch("requests.post", return_value=resp):
        token, expires = igdb._refresh_token("cid", "csec")
    assert token == "newtok"
    assert expires > time.time()
    assert (tmp_path / "howl" / ".igdb_token.json").exists()


def test_post_returns_empty_on_error():
    resp = MagicMock()
    resp.ok = False
    resp.status_code = 500
    resp.text = "boom"
    with patch("requests.post", return_value=resp):
        assert igdb._post("cid", "tok", "games", "body") == []


def test_fetch_by_appid_release_year_none_without_date():
    resp = MagicMock()
    resp.ok = True
    resp.json.return_value = [
        {"aggregated_rating": 85, "aggregated_rating_count": 10, "genres": [{"name": "RPG"}]}
    ]
    with patch("requests.post", return_value=resp):
        result = igdb.fetch_by_appid("cid", "tok", 5)
    assert result is not None
    assert result["release_year"] is None


def test_fetch_by_name_returns_none_when_empty():
    resp = MagicMock()
    resp.ok = True
    resp.json.return_value = []
    with patch("requests.post", return_value=resp):
        assert igdb.fetch_by_name("cid", "tok", "x") is None


def test_igdb_post_uses_timeout():
    """Robustez: o POST na API IGDB não pode ficar sem timeout."""
    resp = MagicMock()
    resp.ok = True
    resp.json.return_value = []
    with patch("requests.post", return_value=resp) as mock_post:
        igdb._post("cid", "tok", "games", "body")
    assert mock_post.call_args.kwargs.get("timeout") == igdb.HTTP_TIMEOUT


# ---------------------------------------------------------------------------
# _normalize_for_igdb
# ---------------------------------------------------------------------------


def test_normalize_strips_trademarks():
    assert _normalize_for_igdb("Assassin's Creed® IV") == "Assassin's Creed IV"
    assert _normalize_for_igdb("Batman™: Arkham Knight") == "Batman: Arkham Knight"
    assert _normalize_for_igdb("Game©") == "Game"


def test_normalize_strips_gold_edition():
    assert (
        _normalize_for_igdb("Assassin's Creed IV Black Flag - Gold Edition")
        == "Assassin's Creed IV Black Flag"
    )


def test_normalize_strips_season_pass():
    assert (
        _normalize_for_igdb("Batman: The Telltale Series - Season Pass")
        == "Batman: The Telltale Series"
    )


def test_normalize_strips_titans_subtitle():
    assert _normalize_for_igdb("Planetary Annihilation: TITANS") == "Planetary Annihilation"


def test_normalize_strips_combined_trademark_and_edition():
    assert (
        _normalize_for_igdb("Assassin's Creed® IV Black Flag - Gold Edition")
        == "Assassin's Creed IV Black Flag"
    )


def test_normalize_preserves_regular_subtitles():
    """Subtítulos legítimos (não edição) devem ser preservados."""
    assert _normalize_for_igdb("Batman: Arkham Knight") == "Batman: Arkham Knight"
    assert _normalize_for_igdb("Deus Ex: Human Revolution") == "Deus Ex: Human Revolution"


def test_normalize_no_change_for_clean_name():
    assert _normalize_for_igdb("Ticket to Ride") == "Ticket to Ride"
    assert _normalize_for_igdb("Portal 2") == "Portal 2"


# ---------------------------------------------------------------------------
# _name_similarity
# ---------------------------------------------------------------------------


def test_name_similarity_exact():
    assert _name_similarity("Batman", "Batman") == pytest.approx(1.0)


def test_name_similarity_case_insensitive():
    assert _name_similarity("batman", "BATMAN") == pytest.approx(1.0)


def test_name_similarity_very_different():
    assert _name_similarity("Batman", "Completely Different Game") < 0.6


def test_name_similarity_partial_match():
    sim = _name_similarity("Assassin's Creed IV Black Flag", "Assassin's Creed IV Black Flag")
    assert sim == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# fetch_by_name — normalização e validação de similaridade
# ---------------------------------------------------------------------------


def test_fetch_by_name_normalizes_before_search():
    """A busca usa nome normalizado — sem ® e sem 'Gold Edition' no body da request."""
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = [
        {
            "name": "Assassin's Creed IV Black Flag",
            "aggregated_rating": 85.0,
            "aggregated_rating_count": 30,
            "genres": [{"name": "Action-adventure"}],
            "first_release_date": 1383177600,
        }
    ]
    with patch("requests.post", return_value=mock_resp) as mock_post:
        result = fetch_by_name("cid", "tok", "Assassin's Creed® IV Black Flag - Gold Edition")
    assert result is not None
    assert result["aggregated_rating"] == 85
    body = mock_post.call_args.kwargs.get("data", "")
    assert "Gold Edition" not in body
    assert "®" not in body


def test_fetch_by_name_rejects_wrong_game():
    """Resultado IGDB com nome muito diferente do query é descartado."""
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = [
        {
            "name": "Completely Different Game",
            "aggregated_rating": 90.0,
            "aggregated_rating_count": 15,
            "genres": [{"name": "Action"}],
            "first_release_date": 1000000000,
        }
    ]
    with patch("requests.post", return_value=mock_resp):
        result = fetch_by_name("cid", "tok", "Ticket to Ride")
    assert result is None


def test_fetch_by_name_accepts_similar_game():
    """Resultado IGDB com nome próximo do query (≥0.6) é aceito."""
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = [
        {
            "name": "Batman: The Telltale Series",
            "aggregated_rating": 75.0,
            "aggregated_rating_count": 10,
            "genres": [{"name": "Adventure"}],
            "first_release_date": 1470009600,
        }
    ]
    with patch("requests.post", return_value=mock_resp):
        result = fetch_by_name("cid", "tok", "Batman: The Telltale Series - Season Pass")
    assert result is not None
    assert result["aggregated_rating"] == 75


# ---------------------------------------------------------------------------
# _parse_result — resultado parcial quando rating insuficiente mas tem gêneros
# ---------------------------------------------------------------------------


def test_parse_result_partial_when_genres_present_low_rating():
    """Rating count < 3 mas com gêneros → resultado parcial sem rating."""
    data = {
        "name": "Indie Game",
        "aggregated_rating": 80.0,
        "aggregated_rating_count": 2,
        "genres": [{"name": "Indie"}, {"name": "Adventure"}],
        "first_release_date": 1500000000,
    }
    result = igdb._parse_result(data)
    assert result is not None
    assert result["aggregated_rating"] is None  # rating descartado (count insuficiente)
    assert "Indie" in result["genres"]
    assert result["release_year"] == 2017


def test_parse_result_none_when_low_rating_and_no_genres():
    """Rating count < 3 e sem gêneros/ano → None (nada útil)."""
    data = {
        "name": "Mystery",
        "aggregated_rating": 90.0,
        "aggregated_rating_count": 1,
        "genres": [],
        "first_release_date": None,
    }
    assert igdb._parse_result(data) is None


def test_parse_result_full_when_sufficient_rating():
    """Rating count >= 3 → resultado completo com rating."""
    data = {
        "name": "Great Game",
        "aggregated_rating": 88.5,
        "aggregated_rating_count": 10,
        "genres": [{"name": "RPG"}],
        "first_release_date": 1400000000,
    }
    result = igdb._parse_result(data)
    assert result is not None
    assert result["aggregated_rating"] == round(88.5)  # banker's rounding Python 3 → 88
    assert result["genres"] == ["RPG"]
