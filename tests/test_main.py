import sys
import pytest


def _parse(argv):
    sys.argv = ["main.py"] + argv
    from steam_hltb.main import parse_args
    return parse_args()


def test_parse_args_defaults():
    args = _parse([])
    assert args.top == 10
    assert args.sort == "shortest"
    assert args.verbose is False
    assert args.show_tags is False


def test_parse_args_verbose_short():
    args = _parse(["-v"])
    assert args.verbose is True


def test_parse_args_show_tags():
    args = _parse(["--show-tags"])
    assert args.show_tags is True


def test_parse_args_top():
    args = _parse(["--top", "25"])
    assert args.top == 25


def test_print_table_shows_genres_by_default(capsys):
    games = [{
        "name": "Hades",
        "metacritic": 93,
        "steam_pct": 97,
        "main_extra": 22,
        "hours_played": 0,
        "_score": 42.1,
        "genres": ["action", "roguelike", "rpg"],
        "tags": ["indie", "great soundtrack"],
    }]
    from steam_hltb.main import print_table
    print_table(games, "shortest", show_tags=False)
    out = capsys.readouterr().out
    assert "action" in out
    assert "roguelike" in out
    assert "indie" not in out


def test_print_table_shows_steam_categories_when_flag(capsys):
    games = [{
        "name": "Hades",
        "metacritic": 93,
        "steam_pct": 97,
        "main_extra": 22,
        "hours_played": 0,
        "_score": 42.1,
        "genres": ["action"],
        "tags": ["single-player", "full controller support", "steam achievements"],
    }]
    from steam_hltb.main import print_table
    print_table(games, "shortest", show_tags=True)
    out = capsys.readouterr().out
    assert "single-player" in out
    assert "full controller support" in out
    assert "steam achievements" not in out  # noise filtrado


def test_parse_args_list_tags():
    args = _parse(["--list-tags"])
    assert args.list_tags is True


def test_parse_args_list_genres():
    args = _parse(["--list-genres"])
    assert args.list_genres is True


def test_list_available_genres(capsys):
    cache = {
        "Hades": {"steam": {"genres": ["action", "roguelike"], "categories": []}, "rawg": None},
        "Portal 2": {"steam": {"genres": ["puzzle", "action"], "categories": []}, "rawg": None},
    }
    from steam_hltb.main import list_available
    list_available(cache, "genres")
    out = capsys.readouterr().out
    assert "action" in out
    assert "roguelike" in out
    assert "puzzle" in out
    assert "2x" in out  # action aparece 2x


def test_list_available_categories(capsys):
    cache = {
        "Hades": {"steam": {"genres": [], "categories": ["single-player", "steam achievements"]}, "rawg": None},
    }
    from steam_hltb.main import list_available
    list_available(cache, "categories")
    out = capsys.readouterr().out
    assert "single-player" in out
    assert "steam achievements" not in out  # noise, filtrado


def test_list_available_empty_cache(capsys):
    from steam_hltb.main import list_available
    list_available({}, "genres")
    out = capsys.readouterr().out
    assert "Tente --refresh" in out


def test_parse_args_list_collections():
    args = _parse(["--list-collections"])
    assert args.list_collections is True


def test_list_collections_cmd_prints_names(capsys):
    from steam_hltb.main import list_collections_cmd
    collection_map = {"220": ["Terminados"], "620": ["Jogando", "Terminados"], "570": ["Multiplayer"]}
    list_collections_cmd(collection_map)
    out = capsys.readouterr().out
    assert "Terminados" in out
    assert "Jogando" in out
    assert "Multiplayer" in out


def test_list_collections_cmd_shows_count(capsys):
    from steam_hltb.main import list_collections_cmd
    collection_map = {"220": ["Terminados"], "620": ["Terminados"], "570": ["Jogando"]}
    list_collections_cmd(collection_map)
    out = capsys.readouterr().out
    assert "2" in out
    assert "1" in out


def test_parse_args_era_flag():
    args = _parse(["--era", "2010-2015,2020+"])
    assert args.era == "2010-2015,2020+"


def test_parse_args_era_not_set_by_default():
    args = _parse([])
    assert getattr(args, "era", None) is None


def test_parse_args_show_finished():
    args = _parse(["--show-finished"])
    assert args.show_finished is True


def test_print_table_shows_year(capsys):
    games = [{
        "name": "Half-Life 2",
        "metacritic": 96,
        "steam_pct": 97,
        "main_extra": 15,
        "hours_played": 0,
        "_score": 50.0,
        "genres": ["action"],
        "tags": [],
        "release_year": 2004,
    }]
    from steam_hltb.main import print_table
    print_table(games, "shortest")
    out = capsys.readouterr().out
    assert "2004" in out


def test_print_table_shows_dash_for_missing_year(capsys):
    games = [{
        "name": "Unknown Game",
        "metacritic": 80,
        "steam_pct": 90,
        "main_extra": 10,
        "hours_played": 0,
        "_score": 30.0,
        "genres": [],
        "tags": [],
        "release_year": None,
    }]
    from steam_hltb.main import print_table
    print_table(games, "shortest")
    out = capsys.readouterr().out
    # a linha do jogo deve conter "-" no campo de ano
    game_line = [l for l in out.splitlines() if "Unknown Game" in l][0]
    assert "-" in game_line


def test_progress_mode_all():
    import argparse
    args = argparse.Namespace(not_started=False, in_progress=False, all_progress=True)
    from steam_hltb.main import _progress_mode
    assert _progress_mode(args) == "all"


def test_progress_mode_not_started():
    import argparse
    args = argparse.Namespace(not_started=True, in_progress=False, all_progress=False)
    from steam_hltb.main import _progress_mode
    assert _progress_mode(args) == "not_started"


def test_progress_mode_default_when_nothing_set():
    import argparse
    args = argparse.Namespace(not_started=False, in_progress=False, all_progress=False)
    from steam_hltb.main import _progress_mode
    assert _progress_mode(args) == "default"


def test_weights_normalization_warns_and_normalizes(capsys):
    import argparse
    args = argparse.Namespace(weight_mc=0.6, weight_steam=0.6)
    from steam_hltb.main import _weights
    w = _weights(args)
    err = capsys.readouterr().err
    assert "Aviso" in err
    assert abs(sum(w.values()) - 1.0) < 0.01


def test_csv_list_parses_comma_separated():
    from steam_hltb.main import _csv_list
    assert _csv_list("action,rpg") == ["action", "rpg"]
    assert _csv_list("action, rpg , puzzle") == ["action", "rpg", "puzzle"]


def test_csv_list_returns_none_for_empty():
    from steam_hltb.main import _csv_list
    assert _csv_list(None) is None
    assert _csv_list("") is None
    assert _csv_list("  ") is None


def test_save_results_creates_csv_and_md(tmp_path):
    games = [{
        "name": "Hades",
        "category": "singleplayer",
        "metacritic": 93,
        "steam_pct": 97,
        "_score": 42.1,
        "hours_played": 0.0,
        "main_story": 20,
        "main_extra": 22,
        "completionist": 90,
    }]
    from steam_hltb.main import save_results
    output_base = str(tmp_path / "output")
    save_results(games, output_base)
    assert (tmp_path / "output.csv").exists()
    assert (tmp_path / "output.md").exists()
    csv_content = (tmp_path / "output.csv").read_text()
    assert "Hades" in csv_content
    md_content = (tmp_path / "output.md").read_text()
    assert "Hades" in md_content


def test_run_e2e_smoke(tmp_path, monkeypatch):
    """run() completo com tudo mockado — verifica que não crasha."""
    import argparse
    from unittest.mock import patch
    args = argparse.Namespace(
        username="testuser",
        sort="shortest",
        genre=None, genre_any=None, exclude_genre=None,
        not_started=False, in_progress=False, all_progress=False,
        category="all",
        min_hours=None, max_hours=None,
        top=5,
        output=str(tmp_path / "out"),
        weight_mc=0.5, weight_steam=0.5,
        collection=None,
        vdf_path=str(tmp_path / "no.vdf"),
        show_finished=True,
        refresh=False, verbose=False,
        era=None,
        show_tags=False,
    )
    sample_game = {
        "name": "Hades", "steam_name": "Hades", "appid": 1145360,
        "hours_played": 0.0, "category": "singleplayer",
        "genres": ["action"], "tags": ["single-player"],
        "metacritic": 93, "steam_pct": 97,
        "steam_total_reviews": 50000,
        "main_story": 20, "main_extra": 22, "completionist": 90,
        "release_year": 2020,
    }
    with patch("steam_hltb.main.get_api_key", return_value="fake"), \
         patch("steam_hltb.main.load_cache", return_value={}), \
         patch("steam_hltb.main.build_library", return_value=({}, [])), \
         patch("steam_hltb.main.build_game_rows", return_value=[sample_game]):
        from steam_hltb.main import run
        run(args)  # não deve lançar exceção


def test_print_table_caps_genres_at_four(capsys):
    games = [{
        "name": "Game",
        "metacritic": 80,
        "steam_pct": 90,
        "main_extra": 10,
        "hours_played": 0,
        "_score": 30.0,
        "genres": ["a", "b", "c", "d", "e", "f"],
        "tags": [],
    }]
    from steam_hltb.main import print_table
    print_table(games, "shortest", show_tags=False)
    out = capsys.readouterr().out
    after_arrow = out.split("↳")[1] if "↳" in out else ""
    assert "e" not in after_arrow
    assert "f" not in after_arrow


def test_setup_flag_invokes_run_setup(monkeypatch):
    called = []
    monkeypatch.setattr("steam_hltb.setup.run_setup", lambda *a, **k: called.append(True))
    monkeypatch.setattr("sys.argv", ["howl", "--setup"])
    from steam_hltb import main as m
    import importlib; importlib.reload(m)
    m.main()
    assert called == [True]
