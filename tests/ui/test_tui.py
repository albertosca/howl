SAMPLE_GAMES = [
    {
        "name": "Hades",
        "steam_name": "Hades",
        "appid": 1145360,
        "hours_played": 0.0,
        "category": "singleplayer",
        "genres": ["action", "roguelike"],
        "tags": ["indie", "great soundtrack"],
        "metacritic": 93,
        "steam_pct": 97,
        "steam_total_reviews": 50000,
        "main_story": 20,
        "main_extra": 22,
        "completionist": 90,
        "release_year": 2020,
        "_score": 42.1,
    },
    {
        "name": "Hollow Knight",
        "steam_name": "Hollow Knight",
        "appid": 367520,
        "hours_played": 5.0,
        "category": "singleplayer",
        "genres": ["action", "platformer"],
        "tags": ["indie", "metroidvania"],
        "metacritic": 87,
        "steam_pct": 95,
        "steam_total_reviews": 80000,
        "main_story": 24,
        "main_extra": 40,
        "completionist": 60,
        "release_year": 2017,
        "_score": 38.6,
    },
]

INITIAL_FILTERS = {
    "genre": None,
    "genre_any": None,
    "exclude_genre": None,
    "progress": "all",
    "category": "all",
    "min_hours": None,
    "max_hours": None,
    "sort": "shortest",
    "top": 10,
    "weights": {"mc": 0.5, "steam": 0.5},
    "show_finished": True,  # testes não dependem do VDF local
    "vdf_path": "sharedconfig.vdf",
    "collection": None,
    "eras": None,
}


async def test_tui_app_starts_and_renders_table():
    from textual.widgets import DataTable

    from steam_hltb.ui.tui import SteamHLTBApp

    app = SteamHLTBApp(SAMPLE_GAMES, INITIAL_FILTERS)
    async with app.run_test():
        table = app.query_one(DataTable)
        assert table.row_count == 2


async def test_tui_filter_panel_hidden_by_default():
    from steam_hltb.ui.tui import FilterPanel, SteamHLTBApp

    app = SteamHLTBApp(SAMPLE_GAMES, INITIAL_FILTERS)
    async with app.run_test():
        panel = app.query_one(FilterPanel)
        assert panel.display is False


async def test_tui_filter_panel_toggles_with_f():
    from steam_hltb.ui.tui import FilterPanel, SteamHLTBApp

    app = SteamHLTBApp(SAMPLE_GAMES, INITIAL_FILTERS)
    async with app.run_test() as pilot:
        panel = app.query_one(FilterPanel)
        await pilot.press("f")
        assert panel.display is True
        await pilot.press("f")
        assert panel.display is False


async def test_tui_fuzzy_filter_reduces_rows():
    from textual.widgets import DataTable, Input

    from steam_hltb.ui.tui import SteamHLTBApp

    app = SteamHLTBApp(SAMPLE_GAMES, INITIAL_FILTERS)
    async with app.run_test() as pilot:
        await pilot.press("f")
        await pilot.pause()
        name_input = app.query_one("#name-input", Input)
        name_input.value = "hol"  # subsequência de "Hollow Knight"
        await pilot.pause()
        assert app.query_one(DataTable).row_count == 1
        assert app._games[0]["name"] == "Hollow Knight"


async def test_tui_fuzzy_filter_no_match_shows_zero_rows():
    from textual.widgets import DataTable, Input

    from steam_hltb.ui.tui import SteamHLTBApp

    app = SteamHLTBApp(SAMPLE_GAMES, INITIAL_FILTERS)
    async with app.run_test() as pilot:
        await pilot.press("f")
        await pilot.pause()
        name_input = app.query_one("#name-input", Input)
        name_input.value = "zzzzz"
        await pilot.pause()
        assert app.query_one(DataTable).row_count == 0


async def test_tui_fuzzy_filter_cleared_restores_all_rows():
    from textual.widgets import DataTable, Input

    from steam_hltb.ui.tui import SteamHLTBApp

    app = SteamHLTBApp(SAMPLE_GAMES, INITIAL_FILTERS)
    async with app.run_test() as pilot:
        await pilot.press("f")
        await pilot.pause()
        name_input = app.query_one("#name-input", Input)
        name_input.value = "hol"
        await pilot.pause()
        assert app.query_one(DataTable).row_count == 1
        name_input.value = ""
        await pilot.pause()
        assert app.query_one(DataTable).row_count == 2


async def test_tui_genre_filter_reduces_rows():
    from textual.widgets import DataTable, Input

    from steam_hltb.ui.tui import SteamHLTBApp

    app = SteamHLTBApp(SAMPLE_GAMES, INITIAL_FILTERS)
    async with app.run_test() as pilot:
        await pilot.press("f")
        await pilot.pause()
        # "platformer" só existe em Hollow Knight
        genre_input = app.query_one("#genre-input", Input)
        genre_input.value = "platformer"
        await pilot.pause()
        assert app.query_one(DataTable).row_count == 1
        assert app._games[0]["name"] == "Hollow Knight"


async def test_tui_top_n_limits_output():
    from textual.widgets import DataTable, Input

    from steam_hltb.ui.tui import SteamHLTBApp

    app = SteamHLTBApp(SAMPLE_GAMES, INITIAL_FILTERS)
    async with app.run_test() as pilot:
        await pilot.press("f")
        await pilot.pause()
        top_input = app.query_one("#top-input", Input)
        top_input.value = "1"
        await pilot.pause()
        assert app.query_one(DataTable).row_count == 1


async def test_tui_sort_loved_orders_by_steam_pct():
    """sort=loved → Hades (97%) antes de Hollow Knight (95%)."""
    from textual.widgets import Select

    from steam_hltb.ui.tui import SteamHLTBApp

    app = SteamHLTBApp(SAMPLE_GAMES, INITIAL_FILTERS)
    async with app.run_test() as pilot:
        await pilot.press("f")
        await pilot.pause()
        sort_select = app.query_one("#sort-select", Select)
        sort_select.value = "loved"
        await pilot.pause()
        assert app._games[0]["name"] == "Hades"
        assert app._games[1]["name"] == "Hollow Knight"


async def test_tui_era_filter_logic_via_filters():
    """Filtro por era: manipular filters diretamente e rebuildar tabela."""
    from steam_hltb.ui.tui import SteamHLTBApp

    app = SteamHLTBApp(SAMPLE_GAMES, INITIAL_FILTERS)
    async with app.run_test():
        # Hades: 2020 → era "2020+"; Hollow Knight: 2017 → era "2015-2020"
        app.filters["eras"] = ["2015-2020"]
        app._rebuild_table()
        assert len(app._games) == 1
        assert app._games[0]["name"] == "Hollow Knight"


async def test_tui_era_filter_all_excluded():
    """Era vazia → nenhum jogo aparece."""
    from steam_hltb.ui.tui import SteamHLTBApp

    app = SteamHLTBApp(SAMPLE_GAMES, INITIAL_FILTERS)
    async with app.run_test():
        app.filters["eras"] = []  # lista vazia = filtrar tudo
        app._rebuild_table()
        assert len(app._games) == 0


async def test_tui_era_filter_none_shows_all():
    """Era=None (padrão) → sem filtro, todos os jogos aparecem."""
    from steam_hltb.ui.tui import SteamHLTBApp

    app = SteamHLTBApp(SAMPLE_GAMES, INITIAL_FILTERS)
    async with app.run_test():
        app.filters["eras"] = None
        app._rebuild_table()
        assert len(app._games) == 2


async def test_tui_read_filters_era_all_checked_returns_none():
    """Quando todos os checkboxes de era estão marcados, eras deve ser None (sem filtro)."""
    from steam_hltb.ui.tui import SteamHLTBApp

    app = SteamHLTBApp(SAMPLE_GAMES, INITIAL_FILTERS)
    async with app.run_test() as pilot:
        await pilot.press("f")
        await pilot.pause()
        # estado inicial: todos marcados
        app._read_filters_from_panel()
        assert app.filters.get("eras") is None


async def test_tui_show_genres_toggle_adds_column():
    from textual.widgets import DataTable

    from steam_hltb.ui.tui import SteamHLTBApp

    app = SteamHLTBApp(SAMPLE_GAMES, INITIAL_FILTERS)
    async with app.run_test() as pilot:
        # show_genres starts True → Genres column exists
        table = app.query_one(DataTable)
        col_keys = [c.label.plain for c in table.columns.values()]
        assert "Genres" in col_keys
        # toggle off
        await pilot.press("g")
        await pilot.pause()
        col_keys_after = [c.label.plain for c in table.columns.values()]
        assert "Genres" not in col_keys_after


async def test_tui_status_bar_shows_count():
    from steam_hltb.ui.tui import SteamHLTBApp

    app = SteamHLTBApp(SAMPLE_GAMES, INITIAL_FILTERS)
    async with app.run_test():
        # verifica indiretamente via _games (a status bar reflete _games)
        assert len(app._games) == 2


GAME_MISSING = {
    "name": "Bare",
    "steam_name": "Bare",
    "appid": 9,
    "hours_played": 0.0,
    "category": "singleplayer",
    "genres": [],
    "tags": [],
    "metacritic": None,
    "steam_pct": None,
    "steam_total_reviews": 0,
    "main_story": None,
    "main_extra": None,
    "completionist": None,
    "release_year": None,
    "_score": 0.0,
}

FULL_FILTERS = {
    **INITIAL_FILTERS,
    "genre": ["action"],
    "exclude_genre": ["sports"],
    "min_hours": 5.0,
    "max_hours": 50.0,
    "collection": "Jogando",
    "eras": ["2020+"],
    "sort": "rated",
    "progress": "not_started",
    "category": "singleplayer",
}


async def test_tui_renders_missing_fields_as_dash():
    from textual.widgets import DataTable

    from steam_hltb.ui.tui import SteamHLTBApp

    app = SteamHLTBApp([GAME_MISSING], INITIAL_FILTERS)
    async with app.run_test():
        assert app.query_one(DataTable).row_count == 1


async def test_tui_show_tags_toggle():
    from steam_hltb.ui.tui import SteamHLTBApp

    app = SteamHLTBApp(SAMPLE_GAMES, INITIAL_FILTERS)
    async with app.run_test() as pilot:
        await pilot.press("t")
        await pilot.pause()
        assert app.show_tags is True


async def test_tui_syncs_populated_filters_to_panel():
    from textual.widgets import Input, Select

    from steam_hltb.ui.tui import SteamHLTBApp

    app = SteamHLTBApp(SAMPLE_GAMES, FULL_FILTERS)
    async with app.run_test():
        assert app.query_one("#genre-input", Input).value == "action"
        assert app.query_one("#exclude-genre-input", Input).value == "sports"
        assert app.query_one("#min-hours-input", Input).value == "5.0"
        assert app.query_one("#max-hours-input", Input).value == "50.0"
        assert app.query_one("#collection-select", Select).value == "Jogando"


async def test_tui_reads_populated_filters_from_panel():
    from steam_hltb.ui.tui import SteamHLTBApp

    app = SteamHLTBApp(SAMPLE_GAMES, FULL_FILTERS)
    async with app.run_test() as pilot:
        await pilot.press("f")
        await pilot.pause()
        app._read_filters_from_panel()
        assert app.filters["genre"] == ["action"]
        assert app.filters["exclude_genre"] == ["sports"]
        assert app.filters["min_hours"] == 5.0
        assert app.filters["max_hours"] == 50.0
        assert app.filters["collection"] == "Jogando"
        assert app.filters["eras"] == ["2020+"]


async def test_tui_save_action_calls_save_results(monkeypatch):
    from steam_hltb.ui.tui import SteamHLTBApp

    saved = {}
    monkeypatch.setattr(
        "steam_hltb.ui.report.save_results", lambda games, base: saved.update(n=len(games))
    )
    app = SteamHLTBApp(SAMPLE_GAMES, INITIAL_FILTERS)
    async with app.run_test() as pilot:
        await pilot.press("s")
        await pilot.pause()
    assert saved.get("n") == 2


async def test_tui_sync_skips_unknown_collection():
    from textual.widgets import Select

    from steam_hltb.ui.tui import SteamHLTBApp

    filters = {**FULL_FILTERS, "collection": "CustomCol", "vdf_path": "nonexistent.vdf"}
    app = SteamHLTBApp(SAMPLE_GAMES, filters)
    async with app.run_test():
        # coleção fora das opções do Select → fica no default "todas"
        assert app.query_one("#collection-select", Select).value == "todas"


def test_run_tui_constructs_and_runs(monkeypatch):
    from steam_hltb.ui.tui import SteamHLTBApp, run_tui

    ran = []
    monkeypatch.setattr(SteamHLTBApp, "run", lambda self: ran.append(True))
    run_tui(SAMPLE_GAMES, INITIAL_FILTERS)
    assert ran == [True]
