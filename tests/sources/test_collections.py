import pytest

from steam_hltb.sources.collections import filter_collection, load_collections

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


def test_exclude_finished_removes_the_configured_collection(vdf_file, monkeypatch):
    from steam_hltb.sources.collections import exclude_finished

    monkeypatch.setenv("HOWL_FINISHED_COLLECTION", "Terminados")
    games = [
        {"appid": 220, "name": "Half-Life 2"},  # in the finished collection
        {"appid": 620, "name": "Portal 2"},  # playing + finished
        {"appid": 570, "name": "Dota 2"},  # untagged
    ]
    result = exclude_finished(games, vdf_file)
    names = [g["name"] for g in result]
    assert "Half-Life 2" not in names
    assert "Portal 2" not in names
    assert "Dota 2" in names


def test_exclude_finished_silent_when_vdf_missing(monkeypatch):
    from steam_hltb.sources.collections import exclude_finished

    monkeypatch.setenv("HOWL_FINISHED_COLLECTION", "Terminados")
    games = [{"appid": 220, "name": "Half-Life 2"}]
    result = exclude_finished(games, "/nonexistent/path.vdf")
    assert result == games


def test_exclude_finished_no_op_when_the_game_is_untagged(vdf_file, monkeypatch):
    from steam_hltb.sources.collections import exclude_finished

    monkeypatch.setenv("HOWL_FINISHED_COLLECTION", "Terminados")
    games = [{"appid": 570, "name": "Dota 2"}]  # untagged
    result = exclude_finished(games, vdf_file)
    assert result == games


def test_load_collections_uses_steam_vdf_path_env(monkeypatch, tmp_path):
    vdf = tmp_path / "sharedconfig.vdf"
    vdf.write_text('"UserRoamingConfigStore"\n{\n"Software"\n{\n}\n}\n')
    monkeypatch.setenv("STEAM_VDF_PATH", str(vdf))
    import importlib

    import steam_hltb.sources.collections as sc

    importlib.reload(sc)
    assert str(vdf) == sc.DEFAULT_VDF_PATH
    importlib.reload(sc)  # restaura


def test_load_collections_skips_blocks_without_tags(tmp_path):
    from steam_hltb.sources.collections import load_collections

    vdf = tmp_path / "sc.vdf"
    vdf.write_text('"123"\n{\n"tags"\n{\n}\n}\n')
    # bloco tem seção tags mas vazia → não entra no resultado
    assert load_collections(str(vdf)) == {}


def test_finished_collection_defaults_to_unset(monkeypatch):
    monkeypatch.delenv("HOWL_FINISHED_COLLECTION", raising=False)
    from steam_hltb.sources import collections

    assert collections.finished_collection() is None


def test_finished_collection_reads_the_environment(monkeypatch):
    monkeypatch.setenv("HOWL_FINISHED_COLLECTION", "Zerados")
    from steam_hltb.sources import collections

    assert collections.finished_collection() == "Zerados"


def test_exclude_finished_drops_nothing_when_unconfigured(monkeypatch):
    monkeypatch.delenv("HOWL_FINISHED_COLLECTION", raising=False)
    from steam_hltb.sources.collections import exclude_finished

    games = [{"appid": 1}, {"appid": 2}]
    monkeypatch.setattr(
        "steam_hltb.sources.collections.load_collections", lambda p: {"1": ["Terminados"]}
    )
    assert exclude_finished(games, "x.vdf") == games


def test_exclude_finished_uses_the_configured_name(monkeypatch):
    monkeypatch.setenv("HOWL_FINISHED_COLLECTION", "Finished")
    from steam_hltb.sources.collections import exclude_finished

    monkeypatch.setattr(
        "steam_hltb.sources.collections.load_collections",
        lambda p: {"1": ["Finished"], "2": ["Playing"]},
    )
    result = exclude_finished([{"appid": 1}, {"appid": 2}], "x.vdf")
    assert [g["appid"] for g in result] == [2]


def test_exclude_finished_matches_the_name_case_insensitively(monkeypatch):
    monkeypatch.setenv("HOWL_FINISHED_COLLECTION", "finished")
    from steam_hltb.sources.collections import exclude_finished

    monkeypatch.setattr(
        "steam_hltb.sources.collections.load_collections", lambda p: {"1": ["Finished"]}
    )
    assert exclude_finished([{"appid": 1}], "x.vdf") == []


def test_exclude_finished_accepts_an_explicit_name(monkeypatch):
    monkeypatch.delenv("HOWL_FINISHED_COLLECTION", raising=False)
    from steam_hltb.sources.collections import exclude_finished

    monkeypatch.setattr(
        "steam_hltb.sources.collections.load_collections", lambda p: {"1": ["Done"]}
    )
    assert exclude_finished([{"appid": 1}], "x.vdf", name="Done") == []
