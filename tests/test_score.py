import pytest
import math
from steam_hltb.score import (
    score_shortest, score_longest, score_rated, score_loved,
    score_quick_wins, score_hidden_gems, score_composto,
    compute_score, SORT_OPTIONS,
)


def test_sort_options_contains_all_expected():
    assert set(SORT_OPTIONS) == {"shortest", "longest", "rated", "loved", "quick-wins", "hidden-gems", "composto"}


def test_score_composto_default_weights():
    game = {"metacritic": 80, "steam_pct": 60}
    assert score_composto(game) == pytest.approx(70.0)  # 0.5*80 + 0.5*60


def test_score_composto_custom_weights():
    game = {"metacritic": 80, "steam_pct": 60}
    assert score_composto(game, weights={"mc": 0.7, "steam": 0.3}) == pytest.approx(74.0)


def test_score_composto_redistributes_missing_source():
    game = {"metacritic": 80, "steam_pct": None}
    assert score_composto(game, weights={"mc": 0.5, "steam": 0.5}) == pytest.approx(80.0)


def test_score_composto_no_sources_returns_zero():
    assert score_composto({"metacritic": None, "steam_pct": None}) == 0.0


def test_shortest_formula():
    game = {"metacritic": 80, "steam_pct": 80, "main_extra": 4}
    # composite = 80, sqrt(4) = 2 → 40
    assert score_shortest(game) == pytest.approx(40.0)


def test_shortest_no_hours_returns_composite():
    game = {"metacritic": 80, "steam_pct": 80, "main_extra": 0}
    assert score_shortest(game) == pytest.approx(80.0)


def test_shortest_missing_both_returns_zero():
    assert score_shortest({"metacritic": None, "steam_pct": None, "main_extra": 10}) == 0.0


def test_longest_formula():
    game = {"metacritic": 80, "steam_pct": 80, "main_extra": 4}
    # composite = 80, sqrt(4) = 2 → 160
    assert score_longest(game) == pytest.approx(160.0)


def test_longest_no_hours_uses_sqrt_1():
    game = {"metacritic": 80, "steam_pct": 80, "main_extra": 0}
    assert score_longest(game) == pytest.approx(80.0)  # composite * sqrt(1)


def test_rated_direct():
    assert score_rated({"metacritic": 85}) == 85.0
    assert score_rated({"metacritic": None}) == 0.0


def test_loved_direct():
    assert score_loved({"steam_pct": 92}) == 92.0
    assert score_loved({"steam_pct": None}) == 0.0


def test_quick_wins_formula():
    game = {"metacritic": 80, "steam_pct": 80, "main_extra": 8}
    # composite = 80, 80² / 8 = 800
    assert score_quick_wins(game) == pytest.approx(800.0)


def test_quick_wins_no_hours_returns_composite_squared():
    game = {"metacritic": 80, "steam_pct": 80, "main_extra": 0}
    assert score_quick_wins(game) == pytest.approx(6400.0)


def test_hidden_gems_formula():
    game = {"steam_pct": 90, "metacritic": 50}
    # 90 * (1 - 50/100) = 90 * 0.5 = 45
    assert score_hidden_gems(game) == pytest.approx(45.0)


def test_hidden_gems_no_metacritic_returns_steam():
    game = {"steam_pct": 90, "metacritic": None}
    assert score_hidden_gems(game) == pytest.approx(90.0)


def test_hidden_gems_no_steam_returns_zero():
    game = {"steam_pct": None, "metacritic": 80}
    assert score_hidden_gems(game) == 0.0


def test_compute_score_dispatches_correctly():
    game = {"metacritic": 90, "steam_pct": 90, "main_extra": 9}
    # composite = 90
    assert compute_score(game, "shortest") == pytest.approx(90 / math.sqrt(9))  # 30
    assert compute_score(game, "longest") == pytest.approx(90 * math.sqrt(9))   # 270
    assert compute_score(game, "rated") == 90.0
    assert compute_score(game, "loved") == 90.0
    assert compute_score(game, "composto") == pytest.approx(90.0)


def test_compute_score_quick_wins():
    game = {"metacritic": 90, "steam_pct": 90, "main_extra": 9}
    # 90² / 9 = 900
    assert compute_score(game, "quick-wins") == pytest.approx(900.0)


def test_compute_score_hidden_gems():
    game = {"steam_pct": 90, "metacritic": 50}
    assert compute_score(game, "hidden-gems") == pytest.approx(45.0)


def test_compute_score_custom_uses_composto():
    game = {"metacritic": 100, "steam_pct": 0}
    result = compute_score(game, "custom", weights={"mc": 1.0, "steam": 0.0})
    assert result == pytest.approx(100.0)


def test_compute_score_raises_on_unknown_sort():
    with pytest.raises(ValueError, match="Unknown sort"):
        compute_score({}, "invalid_sort")
