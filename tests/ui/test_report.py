def test_print_table_shows_genres_by_default(capsys):
    games = [
        {
            "name": "Hades",
            "metacritic": 93,
            "steam_pct": 97,
            "main_extra": 22,
            "hours_played": 0,
            "_score": 42.1,
            "genres": ["action", "roguelike", "rpg"],
            "tags": ["indie", "great soundtrack"],
        }
    ]
    from steam_hltb.ui.report import print_table

    print_table(games, "shortest", show_tags=False)
    out = capsys.readouterr().out
    assert "action" in out
    assert "roguelike" in out
    assert "indie" not in out


def test_print_table_shows_steam_categories_when_flag(capsys):
    games = [
        {
            "name": "Hades",
            "metacritic": 93,
            "steam_pct": 97,
            "main_extra": 22,
            "hours_played": 0,
            "_score": 42.1,
            "genres": ["action"],
            "tags": ["single-player", "full controller support", "steam achievements"],
        }
    ]
    from steam_hltb.ui.report import print_table

    print_table(games, "shortest", show_tags=True)
    out = capsys.readouterr().out
    assert "single-player" in out
    assert "full controller support" in out
    assert "steam achievements" not in out  # noise filtrado


def test_list_available_genres(capsys):
    cache = {
        "Hades": {"steam": {"genres": ["action", "roguelike"], "categories": []}, "rawg": None},
        "Portal 2": {"steam": {"genres": ["puzzle", "action"], "categories": []}, "rawg": None},
    }
    from steam_hltb.ui.report import list_available

    list_available(cache, "genres")
    out = capsys.readouterr().out
    assert "action" in out
    assert "roguelike" in out
    assert "puzzle" in out
    assert "2x" in out  # action aparece 2x


def test_list_available_categories(capsys):
    cache = {
        "Hades": {
            "steam": {"genres": [], "categories": ["single-player", "steam achievements"]},
            "rawg": None,
        },
    }
    from steam_hltb.ui.report import list_available

    list_available(cache, "categories")
    out = capsys.readouterr().out
    assert "single-player" in out
    assert "steam achievements" not in out  # noise, filtrado


def test_list_available_empty_cache(capsys):
    from steam_hltb.ui.report import list_available

    list_available({}, "genres")
    out = capsys.readouterr().out
    assert "Try --refresh" in out


def test_list_collections_cmd_prints_names(capsys):
    from steam_hltb.ui.report import list_collections_cmd

    collection_map = {
        "220": ["Terminados"],
        "620": ["Jogando", "Terminados"],
        "570": ["Multiplayer"],
    }
    list_collections_cmd(collection_map)
    out = capsys.readouterr().out
    assert "Terminados" in out
    assert "Jogando" in out
    assert "Multiplayer" in out


def test_list_collections_cmd_shows_count(capsys):
    from steam_hltb.ui.report import list_collections_cmd

    collection_map = {"220": ["Terminados"], "620": ["Terminados"], "570": ["Jogando"]}
    list_collections_cmd(collection_map)
    out = capsys.readouterr().out
    assert "2" in out
    assert "1" in out


def test_print_table_shows_year(capsys):
    games = [
        {
            "name": "Half-Life 2",
            "metacritic": 96,
            "steam_pct": 97,
            "main_extra": 15,
            "hours_played": 0,
            "_score": 50.0,
            "genres": ["action"],
            "tags": [],
            "release_year": 2004,
        }
    ]
    from steam_hltb.ui.report import print_table

    print_table(games, "shortest")
    out = capsys.readouterr().out
    assert "2004" in out


def test_print_table_shows_dash_for_missing_year(capsys):
    games = [
        {
            "name": "Unknown Game",
            "metacritic": 80,
            "steam_pct": 90,
            "main_extra": 10,
            "hours_played": 0,
            "_score": 30.0,
            "genres": [],
            "tags": [],
            "release_year": None,
        }
    ]
    from steam_hltb.ui.report import print_table

    print_table(games, "shortest")
    out = capsys.readouterr().out
    # a linha do jogo deve conter "-" no campo de ano
    game_line = next(line for line in out.splitlines() if "Unknown Game" in line)
    assert "-" in game_line


def test_save_results_creates_csv_and_md(tmp_path):
    games = [
        {
            "name": "Hades",
            "category": "singleplayer",
            "metacritic": 93,
            "steam_pct": 97,
            "_score": 42.1,
            "hours_played": 0.0,
            "main_story": 20,
            "main_extra": 22,
            "completionist": 90,
        }
    ]
    from steam_hltb.ui.report import save_results

    output_base = str(tmp_path / "output")
    save_results(games, output_base)
    assert (tmp_path / "output.csv").exists()
    assert (tmp_path / "output.md").exists()
    csv_content = (tmp_path / "output.csv").read_text()
    assert "Hades" in csv_content
    md_content = (tmp_path / "output.md").read_text()
    assert "Hades" in md_content


def test_print_table_caps_genres_at_four(capsys):
    games = [
        {
            "name": "Game",
            "metacritic": 80,
            "steam_pct": 90,
            "main_extra": 10,
            "hours_played": 0,
            "_score": 30.0,
            "genres": ["a", "b", "c", "d", "e", "f"],
            "tags": [],
        }
    ]
    from steam_hltb.ui.report import print_table

    print_table(games, "shortest", show_tags=False)
    out = capsys.readouterr().out
    after_arrow = out.split("↳")[1] if "↳" in out else ""
    assert "e" not in after_arrow
    assert "f" not in after_arrow


def test_print_table_show_tags_with_only_noise_cats(capsys):
    from steam_hltb.ui.report import print_table

    games = [
        {
            "name": "G",
            "metacritic": 80,
            "steam_pct": 90,
            "main_extra": 10,
            "hours_played": 0,
            "_score": 30.0,
            "genres": [],
            "tags": ["steam achievements"],  # só ruído → sem linha de cat
            "release_year": None,
        }
    ]
    print_table(games, "shortest", show_tags=True)
    assert "cat:" not in capsys.readouterr().out


def test_list_collections_cmd_empty(capsys):
    from steam_hltb.ui.report import list_collections_cmd

    list_collections_cmd({})
    assert "No collections" in capsys.readouterr().out
