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

    from steam_hltb.tui import SteamHLTBApp

    app = SteamHLTBApp(SAMPLE_GAMES, INITIAL_FILTERS)
    async with app.run_test() as pilot:
        table = app.query_one(DataTable)
        assert table.row_count == 2


async def test_tui_filter_panel_hidden_by_default():
    from steam_hltb.tui import FilterPanel, SteamHLTBApp

    app = SteamHLTBApp(SAMPLE_GAMES, INITIAL_FILTERS)
    async with app.run_test() as pilot:
        panel = app.query_one(FilterPanel)
        assert panel.display is False


async def test_tui_filter_panel_toggles_with_f():
    from steam_hltb.tui import FilterPanel, SteamHLTBApp

    app = SteamHLTBApp(SAMPLE_GAMES, INITIAL_FILTERS)
    async with app.run_test() as pilot:
        panel = app.query_one(FilterPanel)
        await pilot.press("f")
        assert panel.display is True
        await pilot.press("f")
        assert panel.display is False


async def test_tui_fuzzy_filter_reduces_rows():
    from textual.widgets import DataTable, Input

    from steam_hltb.tui import SteamHLTBApp

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

    from steam_hltb.tui import SteamHLTBApp

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

    from steam_hltb.tui import SteamHLTBApp

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

    from steam_hltb.tui import SteamHLTBApp

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

    from steam_hltb.tui import SteamHLTBApp

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

    from steam_hltb.tui import SteamHLTBApp

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
    from steam_hltb.tui import SteamHLTBApp

    app = SteamHLTBApp(SAMPLE_GAMES, INITIAL_FILTERS)
    async with app.run_test() as pilot:
        # Hades: 2020 → era "2020+"; Hollow Knight: 2017 → era "2015-2020"
        app.filters["eras"] = ["2015-2020"]
        app._rebuild_table()
        await pilot.pause()
        assert len(app._games) == 1
        assert app._games[0]["name"] == "Hollow Knight"


async def test_tui_era_filter_all_excluded():
    """Era vazia → nenhum jogo aparece."""
    from steam_hltb.tui import SteamHLTBApp

    app = SteamHLTBApp(SAMPLE_GAMES, INITIAL_FILTERS)
    async with app.run_test() as pilot:
        app.filters["eras"] = []  # lista vazia = filtrar tudo
        app._rebuild_table()
        await pilot.pause()
        assert len(app._games) == 0


async def test_tui_era_filter_none_shows_all():
    """Era=None (padrão) → sem filtro, todos os jogos aparecem."""
    from steam_hltb.tui import SteamHLTBApp

    app = SteamHLTBApp(SAMPLE_GAMES, INITIAL_FILTERS)
    async with app.run_test() as pilot:
        app.filters["eras"] = None
        app._rebuild_table()
        await pilot.pause()
        assert len(app._games) == 2


async def test_tui_read_filters_era_all_checked_returns_none():
    """Quando todos os checkboxes de era estão marcados, eras deve ser None (sem filtro)."""
    from steam_hltb.tui import SteamHLTBApp

    app = SteamHLTBApp(SAMPLE_GAMES, INITIAL_FILTERS)
    async with app.run_test() as pilot:
        await pilot.press("f")
        await pilot.pause()
        # estado inicial: todos marcados
        app._read_filters_from_panel()
        assert app.filters.get("eras") is None


async def test_tui_show_genres_toggle_adds_column():
    from textual.widgets import DataTable

    from steam_hltb.tui import SteamHLTBApp

    app = SteamHLTBApp(SAMPLE_GAMES, INITIAL_FILTERS)
    async with app.run_test() as pilot:
        # show_genres começa True → coluna Gêneros existe
        table = app.query_one(DataTable)
        col_keys = [c.label.plain for c in table.columns.values()]
        assert "Gêneros" in col_keys
        # toggle off
        await pilot.press("g")
        await pilot.pause()
        col_keys_after = [c.label.plain for c in table.columns.values()]
        assert "Gêneros" not in col_keys_after


async def test_tui_status_bar_shows_count():

    from steam_hltb.tui import SteamHLTBApp

    app = SteamHLTBApp(SAMPLE_GAMES, INITIAL_FILTERS)
    async with app.run_test() as pilot:
        # verifica indiretamente via _games (a status bar reflete _games)
        assert len(app._games) == 2
