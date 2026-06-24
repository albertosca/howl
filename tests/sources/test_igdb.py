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
    assert (
        _normalize_for_igdb("BioShock Infinite: Burial at Sea")
        == "BioShock Infinite: Burial at Sea"
    )
    assert _normalize_for_igdb("Mass Effect: Andromeda") == "Mass Effect: Andromeda"
    assert _normalize_for_igdb("The Witcher 3: Wild Hunt") == "The Witcher 3: Wild Hunt"


def test_normalize_no_change_for_clean_name():
    assert _normalize_for_igdb("Ticket to Ride") == "Ticket to Ride"
    assert _normalize_for_igdb("Portal 2") == "Portal 2"
    assert _normalize_for_igdb("Stardew Valley") == "Stardew Valley"


def test_normalize_strips_special_edition():
    assert (
        _normalize_for_igdb("The Elder Scrolls V: Skyrim - Special Edition")
        == "The Elder Scrolls V: Skyrim"
    )


def test_normalize_strips_goty():
    assert _normalize_for_igdb("Fallout 4 - Game of the Year Edition") == "Fallout 4"


def test_normalize_strips_definitive_edition():
    assert _normalize_for_igdb("Mafia II: Definitive Edition") == "Mafia II"


def test_normalize_strips_the_definitive_edition():
    """'The X Edition' com artigo — variante muito comum no Steam (ex: GTA Trilogy)."""
    assert _normalize_for_igdb("Grand Theft Auto V: The Definitive Edition") == "Grand Theft Auto V"
    assert _normalize_for_igdb("Mafia: The Definitive Edition") == "Mafia"


def test_normalize_strips_the_complete_edition():
    assert _normalize_for_igdb("L.A. Noire: The Complete Edition") == "L.A. Noire"


def test_normalize_strips_enhanced_edition():
    assert (
        _normalize_for_igdb("The Witcher 2: Assassins of Kings - Enhanced Edition")
        == "The Witcher 2: Assassins of Kings"
    )


def test_normalize_strips_trademark_only():
    """Apenas trademark, sem sufixo de edição — só remove símbolo."""
    assert _normalize_for_igdb("XCOM® 2") == "XCOM 2"
    assert _normalize_for_igdb("Deus Ex: Mankind Divided™") == "Deus Ex: Mankind Divided"
    assert _normalize_for_igdb("DARK SOULS™ III") == "DARK SOULS III"


def test_normalize_combined_trademark_and_the_edition():
    assert (
        _normalize_for_igdb("Batman™: The Complete Series")
        == "Batman: The Complete Series"  # "Series" não é "edition/version" → preservado
    )


# ---------------------------------------------------------------------------
# _name_similarity — grafias similares mas não idênticas
# ---------------------------------------------------------------------------


def test_name_similarity_exact():
    assert _name_similarity("Batman", "Batman") == pytest.approx(1.0)


def test_name_similarity_case_insensitive():
    assert _name_similarity("batman", "BATMAN") == pytest.approx(1.0)
    assert _name_similarity("DARK SOULS III", "Dark Souls III") == pytest.approx(1.0)


def test_name_similarity_missing_colon():
    """Dois-pontos ausentes: grafia comum em bases de dados alternativas."""
    assert _name_similarity("Batman Arkham Knight", "Batman: Arkham Knight") >= 0.6


def test_name_similarity_missing_apostrophe():
    """Apóstrofo ausente — frequente em tags e scrapers."""
    assert (
        _name_similarity("Assassins Creed IV Black Flag", "Assassin's Creed IV Black Flag") >= 0.6
    )


def test_name_similarity_missing_article():
    """Artigo 'The' ausente — comum em buscas informais."""
    assert _name_similarity("Witcher 3 Wild Hunt", "The Witcher 3: Wild Hunt") >= 0.6
    assert _name_similarity("Elder Scrolls V Skyrim", "The Elder Scrolls V: Skyrim") >= 0.6


def test_name_similarity_roman_vs_arabic():
    """Número romano vs arábico — Steam e IGDB às vezes divergem."""
    assert _name_similarity("Civilization V", "Civilization 5") >= 0.6
    assert _name_similarity("Battlefield 1942", "Battlefield 1942") >= 0.6


def test_name_similarity_missing_hyphen():
    """Hífen ausente: 'Half Life 2' vs 'Half-Life 2'."""
    assert _name_similarity("Half Life 2", "Half-Life 2") >= 0.6


def test_name_similarity_extra_subtitle_proportional():
    """Subtítulo curto relativo ao nome base → passa. Extensão desproporcional → rejeita.

    SequenceMatcher: ratio = 2*matches / (len(a)+len(b)).
    'Ticket to Ride' (14) vs '...Europe' (22) → ~0.78 ✓
    'Portal 2' (8) vs '...Still Alive' (21) → ~0.55 ✗ (corretamente descartado;
    busca por appid teria encontrado antes do fallback por nome).
    """
    assert _name_similarity("Ticket to Ride", "Ticket to Ride: Europe") >= 0.6
    assert _name_similarity("Portal 2", "Portal 2: Still Alive") < 0.6  # extensão desproporcional


def test_name_similarity_different_sequel_acknowledged_limitation():
    """Sequências da mesma série têm similaridade alta — limitação do SequenceMatcher.
    A API de busca do IGDB é responsável por retornar o jogo correto para a query;
    a similaridade só filtra resultados completamente errados."""
    assert _name_similarity("Civilization V", "Civilization VI") >= 0.6  # limitação documentada


def test_name_similarity_completely_different_games():
    """Jogos sem relação: similaridade < 0.6 → descartado."""
    assert _name_similarity("Portal 2", "The Elder Scrolls V: Skyrim") < 0.6
    assert _name_similarity("Dota 2", "Stardew Valley") < 0.6
    assert _name_similarity("Batman", "Superman Returns") < 0.6
    assert _name_similarity("Ticket to Ride", "Rayman Legends") < 0.6


def test_name_similarity_short_vs_very_long():
    """Nome muito curto vs versão muito expandida: similaridade cai abaixo de 0.6."""
    assert _name_similarity("Batman", "Batman: Arkham Origins - Cold Cold Heart DLC") < 0.6


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
