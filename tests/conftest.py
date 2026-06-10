import pytest

@pytest.fixture
def sample_cache():
    return {
        "Half-Life 2": {
            "hltb": {
                "game_name": "Half-Life 2",
                "main_story": 12,
                "main_extra": 15,
                "completionist": 19,
            },
            "rawg": {
                "metacritic": 96,
                "genres": ["action", "shooter"],
                "tags": ["singleplayer", "fps", "atmospheric"],
            },
            "steam": {
                "appid": 220,
                "positive_pct": 97,
                "total_reviews": 158000,
            },
        },
        "Portal 2": {
            "hltb": {
                "game_name": "Portal 2",
                "main_story": 9,
                "main_extra": 12,
                "completionist": 17,
            },
            "rawg": {
                "metacritic": 95,
                "genres": ["puzzle", "platformer"],
                "tags": ["co-op", "co-op campaign", "singleplayer", "puzzle"],
            },
            "steam": {
                "appid": 620,
                "positive_pct": 98,
                "total_reviews": 120000,
            },
        },
        "Dota 2": {
            "hltb": None,
            "rawg": {
                "metacritic": 90,
                "genres": ["strategy"],
                "tags": ["multiplayer", "online multiplayer", "pvp", "mmo"],
            },
            "steam": {
                "appid": 570,
                "positive_pct": 81,
                "total_reviews": 2000000,
            },
        },
    }

@pytest.fixture
def sample_steam_games():
    return [
        {"name": "Half-Life 2", "appid": 220, "hours_played": 0.0},
        {"name": "Portal 2",    "appid": 620, "hours_played": 3.0},
        {"name": "Dota 2",      "appid": 570, "hours_played": 100.0},
    ]
