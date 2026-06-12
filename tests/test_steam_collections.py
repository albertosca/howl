import pytest
import tempfile
import os
from steam_collections import load_collections, filter_collection


SAMPLE_VDF = """
"UserLocalConfigStore"
{
    "Software"
    {
        "valve"
        {
            "steam"
            {
                "apps"
                {
                    "220"
                    {
                        "tags"
                        {
                            "0"    "Terminados"
                        }
                    }
                    "620"
                    {
                        "tags"
                        {
                            "0"    "Jogando"
                            "1"    "Terminados"
                        }
                    }
                    "570"
                    {
                        "LastPlayed"    "1234567890"
                    }
                }
            }
        }
    }
}
"""


@pytest.fixture
def vdf_file(tmp_path):
    p = tmp_path / "sharedconfig.vdf"
    p.write_text(SAMPLE_VDF, encoding="utf-8")
    return str(p)


def test_load_collections_returns_empty_when_file_missing():
    assert load_collections("/nonexistent/path.vdf") == {}


def test_load_collections_parses_single_tag(vdf_file):
    result = load_collections(vdf_file)
    assert result["220"] == ["Terminados"]


def test_load_collections_parses_multiple_tags(vdf_file):
    result = load_collections(vdf_file)
    assert set(result["620"]) == {"Jogando", "Terminados"}


def test_load_collections_skips_app_without_tags(vdf_file):
    result = load_collections(vdf_file)
    assert "570" not in result


def test_filter_collection_keeps_matching_games(vdf_file):
    collection_map = load_collections(vdf_file)
    games = [
        {"appid": 220, "name": "Half-Life 2"},
        {"appid": 620, "name": "Portal 2"},
        {"appid": 570, "name": "Dota 2"},
    ]
    result = filter_collection(games, "Terminados", collection_map)
    names = [g["name"] for g in result]
    assert "Half-Life 2" in names
    assert "Portal 2" in names
    assert "Dota 2" not in names


def test_filter_collection_is_case_insensitive(vdf_file):
    collection_map = load_collections(vdf_file)
    games = [{"appid": 220, "name": "Half-Life 2"}]
    assert filter_collection(games, "terminados", collection_map) == games
    assert filter_collection(games, "TERMINADOS", collection_map) == games


def test_filter_collection_returns_empty_when_no_match(vdf_file):
    collection_map = load_collections(vdf_file)
    games = [{"appid": 220, "name": "Half-Life 2"}]
    assert filter_collection(games, "NaoExiste", collection_map) == []
