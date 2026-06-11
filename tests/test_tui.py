import pytest

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
        "_score": 38.6,
    },
]

INITIAL_FILTERS = {
    "genre": None, "genre_any": None, "exclude_genre": None,
    "progress": "all", "category": "all",
    "min_hours": None, "max_hours": None,
    "sort": "hltb_short", "top": 10,
    "weights": {"mc": 0.5, "steam": 0.5},
}


async def test_tui_app_starts_and_renders_table():
    from tui import SteamHLTBApp
    from textual.widgets import DataTable
    app = SteamHLTBApp(SAMPLE_GAMES, INITIAL_FILTERS)
    async with app.run_test() as pilot:
        table = app.query_one(DataTable)
        assert table.row_count == 2


async def test_tui_filter_panel_hidden_by_default():
    from tui import SteamHLTBApp, FilterPanel
    app = SteamHLTBApp(SAMPLE_GAMES, INITIAL_FILTERS)
    async with app.run_test() as pilot:
        panel = app.query_one(FilterPanel)
        assert panel.display is False


async def test_tui_filter_panel_toggles_with_f():
    from tui import SteamHLTBApp, FilterPanel
    app = SteamHLTBApp(SAMPLE_GAMES, INITIAL_FILTERS)
    async with app.run_test() as pilot:
        panel = app.query_one(FilterPanel)
        await pilot.press("f")
        assert panel.display is True
        await pilot.press("f")
        assert panel.display is False
