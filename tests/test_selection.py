from steam_hltb.selection import select_games


def _game(name, mc, steam, hours, genres=None, played=0.0, category="singleplayer", appid=0):
    return {
        "name": name,
        "appid": appid,
        "metacritic": mc,
        "steam_pct": steam,
        "main_story": hours,
        "main_extra": hours,
        "completionist": hours,
        "hours_played": played,
        "genres": genres or [],
        "tags": [],
        "category": category,
        "release_year": 2018,
    }


BASE = {"sort": "rated", "weights": {"mc": 0.5, "steam": 0.5}, "show_finished": True}


def test_sorts_by_score_desc():
    games = [_game("Low", 70, 70, 10), _game("High", 95, 95, 10)]
    result = select_games(games, BASE)
    assert [g["name"] for g in result] == ["High", "Low"]
    assert result[0]["_score"] >= result[1]["_score"]


def test_computes_score_rated_is_metacritic():
    result = select_games([_game("G", 80, 90, 10)], BASE)
    assert result[0]["_score"] == 80.0


def test_applies_genre_filter():
    games = [_game("RPG", 90, 90, 10, genres=["rpg"]), _game("Act", 90, 90, 10, genres=["action"])]
    result = select_games(games, {**BASE, "genre": ["rpg"]})
    assert [g["name"] for g in result] == ["RPG"]


def test_applies_name_query():
    games = [_game("Hades", 90, 90, 10), _game("Celeste", 90, 90, 10)]
    result = select_games(games, {**BASE, "name_query": "had"})
    assert [g["name"] for g in result] == ["Hades"]


def test_excludes_multiplayer_by_default():
    games = [_game("Solo", 90, 90, 10), _game("MP", 90, 90, 10, category="multiplayer")]
    result = select_games(games, BASE)
    assert [g["name"] for g in result] == ["Solo"]


def test_does_not_slice_top():
    games = [_game(f"G{i}", 90, 90, 10) for i in range(5)]
    result = select_games(games, {**BASE, "top": 2})
    assert len(result) == 5  # select_games ordena mas não corta no top


def test_applies_collection_filter(monkeypatch):
    from steam_hltb import selection

    monkeypatch.setattr(selection, "load_collections", lambda vdf: {"1": ["Jogando"]})
    games = [_game("A", 90, 90, 10, appid=1), _game("B", 90, 90, 10, appid=2)]
    result = selection.select_games(games, {**BASE, "collection": "Jogando"})
    assert [g["name"] for g in result] == ["A"]


def test_excludes_finished_when_not_show_finished(monkeypatch):
    from steam_hltb import selection

    # show_finished ausente → exclude_finished roda (aqui mockado pra cortar 1)
    monkeypatch.setattr(selection, "exclude_finished", lambda rows, vdf: rows[:1])
    games = [_game("A", 90, 90, 10), _game("B", 90, 90, 10)]
    result = selection.select_games(games, {"sort": "rated", "weights": {"mc": 0.5, "steam": 0.5}})
    assert len(result) == 1
