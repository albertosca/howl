import math

import pytest

from steam_hltb.score import (
    SORT_OPTIONS,
    compute_score,
    score_composto,
    score_hidden_gems,
    score_longest,
    score_loved,
    score_quick_wins,
    score_rated,
    score_shortest,
)


def test_sort_options_contains_all_expected():
    assert set(SORT_OPTIONS) == {
        "shortest",
        "longest",
        "rated",
        "loved",
        "quick-wins",
        "hidden-gems",
        "composto",
    }


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
    """Sem dados de duração (0 ou None) → sem penalidade de tempo, retorna composite."""
    assert score_shortest({"metacritic": 80, "steam_pct": 80, "main_extra": 0}) == pytest.approx(
        80.0
    )
    assert score_shortest({"metacritic": 80, "steam_pct": 80, "main_extra": None}) == pytest.approx(
        80.0
    )


def test_shortest_missing_both_returns_zero():
    assert score_shortest({"metacritic": None, "steam_pct": None, "main_extra": 10}) == 0.0


def test_longest_formula():
    game = {"metacritic": 80, "steam_pct": 80, "main_extra": 4}
    # composite = 80, 80 * sqrt(4) / 10 = 80 * 2 / 10 = 16
    assert score_longest(game) == pytest.approx(16.0)


def test_longest_no_hours_returns_zero():
    """Sem dado de duração: não dá pra ranquear como 'longo' → 0.0."""
    assert score_longest({"metacritic": 80, "steam_pct": 80, "main_extra": 0}) == 0.0
    assert score_longest({"metacritic": 80, "steam_pct": 80, "main_extra": None}) == 0.0


def test_rated_direct():
    assert score_rated({"metacritic": 85}) == 85.0
    assert score_rated({"metacritic": None}) == 0.0


def test_loved_direct():
    assert score_loved({"steam_pct": 92}) == 92.0
    assert score_loved({"steam_pct": None}) == 0.0


def test_quick_wins_formula():
    game = {"metacritic": 80, "steam_pct": 80, "main_extra": 8}
    # composite = 80, 80 / (1 + 8/5) = 80 / 2.6 ≈ 30.77
    assert score_quick_wins(game) == pytest.approx(80 / (1 + 8 / 5))


def test_quick_wins_no_hours_returns_zero():
    """Sem dado de duração: não dá pra avaliar eficiência → 0.0 (não flutua pro topo)."""
    assert score_quick_wins({"metacritic": 80, "steam_pct": 80, "main_extra": 0}) == 0.0
    assert score_quick_wins({"metacritic": 80, "steam_pct": 80, "main_extra": None}) == 0.0


def test_quick_wins_below_quality_floor_returns_zero():
    """Composite < 75 = não é 'bom como um todo' → excluído do quick-wins."""
    assert score_quick_wins({"metacritic": 70, "steam_pct": 70, "main_extra": 1}) == 0.0
    assert score_quick_wins({"metacritic": 74, "steam_pct": 74, "main_extra": 1}) == 0.0


def test_hidden_gems_formula():
    game = {"steam_pct": 90, "metacritic": 50}
    # 90 * (1 - 50/100) = 90 * 0.5 = 45
    assert score_hidden_gems(game) == pytest.approx(45.0)


def test_hidden_gems_no_metacritic_returns_zero():
    """Sem MC = dado ausente, não ausência de hype. Excluído do ranking de hidden gems."""
    assert score_hidden_gems({"steam_pct": 90, "metacritic": None}) == 0.0


def test_hidden_gems_no_steam_returns_zero():
    game = {"steam_pct": None, "metacritic": 80}
    assert score_hidden_gems(game) == 0.0


def test_hidden_gems_low_steam_returns_zero():
    """Steam < 80% = não é muito aclamado pelos jogadores → excluído."""
    assert score_hidden_gems({"steam_pct": 79, "metacritic": 30}) == 0.0
    assert score_hidden_gems({"steam_pct": 70, "metacritic": 40}) == 0.0


def test_compute_score_dispatches_correctly():
    game = {"metacritic": 90, "steam_pct": 90, "main_extra": 9}
    # composite = 90
    assert compute_score(game, "shortest") == pytest.approx(90 / math.sqrt(9))  # 30
    assert compute_score(game, "longest") == pytest.approx(90 * math.sqrt(9) / 10)  # 27
    assert compute_score(game, "rated") == 90.0
    assert compute_score(game, "loved") == 90.0
    assert compute_score(game, "composto") == pytest.approx(90.0)


def test_compute_score_quick_wins():
    game = {"metacritic": 90, "steam_pct": 90, "main_extra": 9}
    # composite = 90, 90 / (1 + 9/5) = 90 / 2.8 ≈ 32.14
    assert compute_score(game, "quick-wins") == pytest.approx(90 / (1 + 9 / 5))


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


def test_score_composto_zero_total_weight():
    from steam_hltb.score import score_composto

    # mc presente mas peso zero → total_weight == 0 → 0.0
    assert score_composto({"metacritic": 80}, {"mc": 0.0, "steam": 0.0}) == 0.0
