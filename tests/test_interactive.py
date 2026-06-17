import argparse
from unittest.mock import patch

MOCK_CACHE = {
    "Half-Life 2": {
        "hltb": {
            "game_name": "Half-Life 2",
            "main_story": 12,
            "main_extra": 15,
            "completionist": 19,
        },
        "steam": {
            "appid": 220,
            "positive_pct": 98,
            "total_reviews": 100000,
            "genres": ["action"],
            "categories": ["single-player"],
        },
    }
}
MOCK_STEAM_GAMES = [{"name": "Half-Life 2", "appid": 220, "hours_played": 0.0}]


def _make_args(**kwargs):
    defaults = dict(username="testuser", weight_mc=0.5, weight_steam=0.5, vdf_path="no.vdf")
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _run(inputs, **args_kwargs):
    args = _make_args(**args_kwargs)
    with (
        patch("builtins.input", side_effect=inputs + [""] * 20),
        patch("steam_hltb.fetch.get_api_key", return_value="fake_key"),
        patch("steam_hltb.fetch.load_cache", return_value=MOCK_CACHE),
        patch("steam_hltb.fetch.build_library", return_value=(MOCK_CACHE, MOCK_STEAM_GAMES)),
        patch("steam_hltb.main.save_results"),
        patch("steam_hltb.steam_collections.load_collections", return_value={}),
    ):
        from steam_hltb.interactive import run_interactive

        run_interactive(args)


def test_interactive_runs_without_error():
    _run([""] * 10)


def test_interactive_does_not_ask_rawg_key():
    asked = []

    def mock_input(prompt):
        asked.append(prompt)
        return ""

    args = _make_args()
    with (
        patch("builtins.input", side_effect=mock_input),
        patch("steam_hltb.fetch.get_api_key", return_value="fake"),
        patch("steam_hltb.fetch.load_cache", return_value=MOCK_CACHE),
        patch("steam_hltb.fetch.build_library", return_value=(MOCK_CACHE, MOCK_STEAM_GAMES)),
        patch("steam_hltb.main.save_results"),
        patch("steam_hltb.steam_collections.load_collections", return_value={}),
    ):
        from steam_hltb.interactive import run_interactive

        run_interactive(args)

    assert not any("rawg" in a.lower() for a in asked)


def test_interactive_accepts_collection_input(capsys):
    inputs = ["", "", "", "", "", "", "", "", "", "Jogando", ""]
    _run(inputs)
    # não deve crashar


def test_interactive_default_sort_is_shortest():
    """O prompt de sort deve sugerir 'shortest' como default."""
    prompts_seen = []

    def mock_input(prompt):
        prompts_seen.append(prompt)
        return ""

    args = _make_args()
    with (
        patch("builtins.input", side_effect=mock_input),
        patch("steam_hltb.fetch.get_api_key", return_value="fake"),
        patch("steam_hltb.fetch.load_cache", return_value=MOCK_CACHE),
        patch("steam_hltb.fetch.build_library", return_value=(MOCK_CACHE, MOCK_STEAM_GAMES)),
        patch("steam_hltb.main.save_results"),
        patch("steam_hltb.steam_collections.load_collections", return_value={}),
    ):
        from steam_hltb.interactive import run_interactive

        run_interactive(args)

    sort_prompts = [p for p in prompts_seen if "Ordenar" in p or "sort" in p.lower()]
    assert any("shortest" in p for p in sort_prompts)


def test_interactive_output_shows_results(capsys):
    """run_interactive deve imprimir a tabela de resultados."""
    _run([""] * 15)
    out = capsys.readouterr().out
    assert "Half-Life 2" in out or "TOP" in out
