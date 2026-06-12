import pytest
import math
from steam_hltb.score import (
    score_hltb_short, score_hltb_long, score_metacritic,
    score_steam, score_composto, compute_score, SORT_OPTIONS,
)


def test_sort_options_contains_all_expected():
    assert set(SORT_OPTIONS) == {"hltb_short", "hltb_long", "metacritic", "steam", "composto", "custom"}


def test_hltb_short_formula():
    game = {"metacritic": 90, "main_extra": 9}
    assert score_hltb_short(game) == pytest.approx(30.0)  # 90 / sqrt(9)


def test_hltb_short_no_extra_hours_returns_metacritic():
    game = {"metacritic": 90, "main_extra": 0}
    assert score_hltb_short(game) == 90.0


def test_hltb_short_missing_metacritic_returns_zero():
    game = {"metacritic": None, "main_extra": 10}
    assert score_hltb_short(game) == 0.0


def test_hltb_long_formula():
    game = {"metacritic": 90, "main_extra": 9}
    assert score_hltb_long(game) == pytest.approx(270.0)  # 90 * sqrt(9)


def test_score_metacritic_direct():
    assert score_metacritic({"metacritic": 85}) == 85.0
    assert score_metacritic({"metacritic": None}) == 0.0


def test_score_steam_direct():
    assert score_steam({"steam_pct": 92}) == 92.0
    assert score_steam({"steam_pct": None}) == 0.0


def test_score_composto_default_weights():
    game = {"metacritic": 80, "steam_pct": 60}
    result = score_composto(game)
    assert result == pytest.approx(70.0)  # 0.5*80 + 0.5*60


def test_score_composto_custom_weights():
    game = {"metacritic": 80, "steam_pct": 60}
    result = score_composto(game, weights={"mc": 0.7, "steam": 0.3})
    assert result == pytest.approx(74.0)  # 0.7*80 + 0.3*60


def test_score_composto_redistributes_missing_source():
    game = {"metacritic": 80, "steam_pct": None}
    result = score_composto(game, weights={"mc": 0.5, "steam": 0.5})
    assert result == pytest.approx(80.0)  # só mc disponível, peso total vira 1.0


def test_score_composto_no_sources_returns_zero():
    game = {"metacritic": None, "steam_pct": None}
    assert score_composto(game) == 0.0


def test_compute_score_dispatches_correctly():
    game = {"metacritic": 90, "main_extra": 9, "steam_pct": 80}
    assert compute_score(game, "hltb_short") == pytest.approx(30.0)
    assert compute_score(game, "metacritic") == 90.0
    assert compute_score(game, "steam") == 80.0
    assert compute_score(game, "composto") == pytest.approx(85.0)


def test_compute_score_custom_uses_weights():
    game = {"metacritic": 100, "steam_pct": 0}
    result = compute_score(game, "custom", weights={"mc": 1.0, "steam": 0.0})
    assert result == pytest.approx(100.0)


def test_compute_score_raises_on_unknown_sort():
    with pytest.raises(ValueError, match="Unknown sort"):
        compute_score({}, "invalid_sort")
