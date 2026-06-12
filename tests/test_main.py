import sys
import pytest


def _parse(argv):
    sys.argv = ["main.py"] + argv
    from main import parse_args
    return parse_args()


def test_parse_args_defaults():
    args = _parse([])
    assert args.top == 10
    assert args.sort == "hltb_short"
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
    from main import print_table
    print_table(games, "hltb_short", show_tags=False)
    out = capsys.readouterr().out
    assert "action" in out
    assert "roguelike" in out
    assert "indie" not in out


def test_print_table_shows_tags_when_flag(capsys):
    games = [{
        "name": "Hades",
        "metacritic": 93,
        "steam_pct": 97,
        "main_extra": 22,
        "hours_played": 0,
        "_score": 42.1,
        "genres": ["action"],
        "tags": ["indie", "great soundtrack"],
    }]
    from main import print_table
    print_table(games, "hltb_short", show_tags=True)
    out = capsys.readouterr().out
    assert "indie" in out
    assert "great soundtrack" in out


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
    from main import list_available
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
    from main import list_available
    list_available(cache, "categories")
    out = capsys.readouterr().out
    assert "single-player" in out
    assert "steam achievements" in out


def test_list_available_empty_cache(capsys):
    from main import list_available
    list_available({}, "genres")
    out = capsys.readouterr().out
    assert "Tente --refresh" in out


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
    from main import print_table
    print_table(games, "hltb_short", show_tags=False)
    out = capsys.readouterr().out
    after_arrow = out.split("↳")[1] if "↳" in out else ""
    assert "e" not in after_arrow
    assert "f" not in after_arrow
