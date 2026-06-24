import argparse


def _ns(**over):
    base = {
        "username": "u",
        "refresh": False,
        "verbose": False,
        "sort": "rated",
        "top": 10,
        "genre": None,
        "genre_any": None,
        "exclude_genre": None,
        "not_started": False,
        "in_progress": False,
        "all_progress": False,
        "category": "all",
        "min_hours": None,
        "max_hours": None,
        "era": None,
        "weight_mc": 0.5,
        "weight_steam": 0.5,
        "vdf_path": "no.vdf",
        "show_finished": True,
        "collection": None,
        "output": "out",
        "show_tags": False,
    }
    base.update(over)
    return argparse.Namespace(**base)


def test_run_e2e_smoke(tmp_path, monkeypatch):
    """run() completo com tudo mockado — verifica que não crasha."""
    from unittest.mock import patch

    args = _ns(
        sort="shortest",
        top=5,
        output=str(tmp_path / "out"),
        vdf_path=str(tmp_path / "no.vdf"),
    )
    sample_game = {
        "name": "Hades",
        "steam_name": "Hades",
        "appid": 1145360,
        "hours_played": 0.0,
        "category": "singleplayer",
        "genres": ["action"],
        "tags": ["single-player"],
        "metacritic": 93,
        "steam_pct": 97,
        "steam_total_reviews": 50000,
        "main_story": 20,
        "main_extra": 22,
        "completionist": 90,
        "release_year": 2020,
    }
    with (
        patch("steam_hltb.main.get_api_key", return_value="fake"),
        patch("steam_hltb.main.load_cache", return_value={}),
        patch("steam_hltb.main.build_library", return_value=({}, [])),
        patch("steam_hltb.main.build_game_rows", return_value=[sample_game]),
    ):
        from steam_hltb.main import run

        run(args)  # não deve lançar exceção


def test_run_no_warning_when_enough_games(tmp_path, monkeypatch, capsys):
    from steam_hltb import main as m

    game = {
        "name": "G",
        "metacritic": 90,
        "steam_pct": 90,
        "main_extra": 10,
        "main_story": 10,
        "completionist": 10,
        "hours_played": 0,
        "genres": [],
        "tags": [],
        "category": "singleplayer",
        "release_year": 2018,
        "appid": 1,
    }
    monkeypatch.setattr(m, "get_api_key", lambda *a: "k")
    monkeypatch.setattr(m, "load_cache", lambda: {})
    monkeypatch.setattr(m, "build_library", lambda *a, **k: ({}, []))
    monkeypatch.setattr(m, "build_game_rows", lambda *a: [game])
    m.run(_ns(top=1, output=str(tmp_path / "out")))
    assert "Apenas" not in capsys.readouterr().out


def test_run_tui_invokes_run_tui(monkeypatch):
    from steam_hltb import main as m

    captured = {}
    monkeypatch.setattr(
        "steam_hltb.ui.tui.run_tui",
        lambda rows, filters: captured.update(rows=rows, filters=filters),
    )
    monkeypatch.setattr(m, "get_api_key", lambda *a: "k")
    monkeypatch.setattr(m, "_resolve_username", lambda args: "u")
    monkeypatch.setattr(m, "load_cache", lambda: {})
    monkeypatch.setattr(m, "build_library", lambda *a, **k: ({}, []))
    monkeypatch.setattr(m, "build_game_rows", lambda *a: [{"name": "G"}])
    m._run_tui(_ns())
    assert captured["rows"] == [{"name": "G"}]


def _call_main(monkeypatch, argv):
    monkeypatch.setattr("sys.argv", ["howl", *argv])
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: None)
    from steam_hltb import main as m

    m.main()


def test_main_dispatch_migrate_cache(monkeypatch):
    called = []
    monkeypatch.setattr("steam_hltb.main.load_cache", lambda: {})
    monkeypatch.setattr(
        "steam_hltb.sources.fetch.migrate_steam_details",
        lambda c, verbose=False: called.append("mc"),
    )
    _call_main(monkeypatch, ["--migrate-cache"])
    assert called == ["mc"]


def test_main_dispatch_migrate_igdb(monkeypatch):
    called = []
    monkeypatch.setattr("steam_hltb.main.load_cache", lambda: {})
    monkeypatch.setattr(
        "steam_hltb.sources.fetch.migrate_igdb_data", lambda c, verbose=False: called.append("ig")
    )
    _call_main(monkeypatch, ["--migrate-igdb"])
    assert called == ["ig"]


def test_main_dispatch_list_genres(monkeypatch):
    called = []
    monkeypatch.setattr("steam_hltb.main.load_cache", lambda: {})
    monkeypatch.setattr("steam_hltb.main.list_available", lambda cache, field: called.append(field))
    _call_main(monkeypatch, ["--list-genres"])
    assert called == ["genres"]


def test_main_dispatch_list_tags(monkeypatch):
    called = []
    monkeypatch.setattr("steam_hltb.main.load_cache", lambda: {})
    monkeypatch.setattr("steam_hltb.main.list_available", lambda cache, field: called.append(field))
    _call_main(monkeypatch, ["--list-tags"])
    assert called == ["categories"]


def test_main_dispatch_list_collections(monkeypatch):
    called = []
    monkeypatch.setattr("steam_hltb.main.load_cache", lambda: {})
    monkeypatch.setattr("steam_hltb.main.load_collections", lambda v: {})
    monkeypatch.setattr("steam_hltb.main.list_collections_cmd", lambda mp: called.append("col"))
    _call_main(monkeypatch, ["--list-collections"])
    assert called == ["col"]


def test_main_dispatch_tui(monkeypatch):
    called = []
    monkeypatch.setattr("steam_hltb.main._run_tui", lambda args: called.append("tui"))
    _call_main(monkeypatch, ["--tui"])
    assert called == ["tui"]


def test_main_dispatch_interactive(monkeypatch):
    called = []
    monkeypatch.setattr(
        "steam_hltb.ui.interactive.run_interactive", lambda args: called.append("int")
    )
    _call_main(monkeypatch, ["--interactive"])
    assert called == ["int"]


def test_main_dispatch_default_run(monkeypatch):
    called = []
    monkeypatch.setattr("steam_hltb.main.run", lambda args: called.append("run"))
    _call_main(monkeypatch, [])
    assert called == ["run"]


def test_setup_flag_invokes_run_setup(monkeypatch):
    called = []
    monkeypatch.setattr("steam_hltb.config.setup.run_setup", lambda *a, **k: called.append(True))
    monkeypatch.setattr("sys.argv", ["howl", "--setup"])
    import importlib

    from steam_hltb import main as m

    importlib.reload(m)
    m.main()
    assert called == [True]
