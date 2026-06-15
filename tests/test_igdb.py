import json, time, pytest
from unittest.mock import patch, mock_open, MagicMock
from steam_hltb.igdb import get_token, fetch_by_appid, fetch_by_name


def test_get_token_fetches_when_no_file():
    with patch("os.path.exists", return_value=False), \
         patch("steam_hltb.igdb._refresh_token", return_value=("tok123", time.time() + 9999)) as mock_refresh:
        token = get_token("cid", "csecret")
    assert token == "tok123"
    mock_refresh.assert_called_once_with("cid", "csecret")


def test_get_token_uses_cached_when_valid():
    valid = {"access_token": "cached", "expires_at": time.time() + 9999}
    m = mock_open(read_data=json.dumps(valid))
    with patch("os.path.exists", return_value=True), patch("builtins.open", m):
        token = get_token("cid", "csecret")
    assert token == "cached"


def test_get_token_refreshes_when_expired():
    expired = {"access_token": "old", "expires_at": time.time() - 1}
    m = mock_open(read_data=json.dumps(expired))
    with patch("os.path.exists", return_value=True), patch("builtins.open", m), \
         patch("steam_hltb.igdb._refresh_token", return_value=("new", time.time() + 9999)) as mock_r:
        token = get_token("cid", "csecret")
    assert token == "new"
    mock_r.assert_called_once()


def test_get_token_returns_none_when_no_credentials():
    assert get_token(None, None) is None
    assert get_token("", "") is None


def test_fetch_by_appid_returns_data():
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = [{
        "name": "Valheim",
        "aggregated_rating": 90.0,
        "aggregated_rating_count": 8,
        "genres": [{"name": "Role-playing (RPG)"}, {"name": "Indie"}],
        "first_release_date": 1613000000,
    }]
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
    mock_resp.json.return_value = [{
        "name": "Deus Ex: Human Revolution",
        "aggregated_rating": 89.0,
        "aggregated_rating_count": 25,
        "genres": [{"name": "Shooter"}, {"name": "Role-playing (RPG)"}],
        "first_release_date": 1313000000,
    }]
    with patch("requests.post", return_value=mock_resp):
        result = fetch_by_name("cid", "tok", "Deus Ex: Human Revolution")
    assert result["aggregated_rating"] == 89
    assert result["release_year"] == 2011


def test_fetch_by_name_ignores_low_rating_count():
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = [{
        "name": "Some Obscure Game",
        "aggregated_rating": 95.0,
        "aggregated_rating_count": 1,
        "genres": [],
        "first_release_date": None,
    }]
    with patch("requests.post", return_value=mock_resp):
        result = fetch_by_name("cid", "tok", "Some Obscure Game")
    assert result is None


def test_missing_credentials_returns_none():
    assert fetch_by_appid(None, None, 892970) is None
    assert fetch_by_name(None, None, "game") is None
