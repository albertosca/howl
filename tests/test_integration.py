import json
import os

import pytest

from steam_hltb.core.classify import apply_filters, build_game_rows
from steam_hltb.core.score import compute_score

CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "games_cache.json")


@pytest.fixture
def real_cache():
    if not os.path.exists(CACHE_FILE):
        pytest.skip("games_cache.json não encontrado — rode o script de fetch primeiro")
    with open(CACHE_FILE, encoding="utf-8") as f:
        return json.load(f)


def test_build_game_rows_produces_valid_rows(real_cache):
    steam_games = [
        {
            "name": name,
            "appid": entry.get("steam", {}).get("appid", 0) if entry.get("steam") else 0,
            "hours_played": 0.0,
        }
        for name, entry in real_cache.items()
    ]
    rows = build_game_rows(real_cache, steam_games)
    assert len(rows) > 0
    for r in rows:
        assert "name" in r
        assert "category" in r
        assert r["category"] in ("singleplayer", "coop_campaign", "multiplayer")


def test_filter_and_score_pipeline(real_cache):
    steam_games = [{"name": name, "appid": 0, "hours_played": 0.0} for name in real_cache]
    rows = build_game_rows(real_cache, steam_games)
    filtered = apply_filters(rows, progress="all", category="all")
    for g in filtered:
        g["_score"] = compute_score(g, "shortest")
    filtered.sort(key=lambda g: g["_score"], reverse=True)
    assert len(filtered) > 0
    scores = [g["_score"] for g in filtered]
    assert scores == sorted(scores, reverse=True)
