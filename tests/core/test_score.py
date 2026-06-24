import math

import pytest

from steam_hltb.core.score import (
    SORT_OPTIONS,
    _fallback_score,
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


# --- fallback (sem dados de qualidade) ---


def test_score_composto_no_scores_no_hours_returns_neutral():
    """Sem MC, sem Steam%, sem horas → neutro (50) — desconhecido ≠ ruim."""
    assert score_composto({"metacritic": None, "steam_pct": None}) == pytest.approx(50.0)
    assert score_composto({}) == pytest.approx(50.0)
    assert score_composto(
        {"metacritic": None, "steam_pct": None, "main_extra": 0, "hours_played": 0}
    ) == pytest.approx(50.0)


def test_score_composto_no_scores_hltb_hours_above_neutral():
    """Sem MC/Steam% mas com horas HLTB → acima de 50."""
    assert score_composto({"main_extra": 20}) > 50.0


def test_score_composto_no_scores_personal_hours_above_neutral():
    """Sem MC/Steam% mas com horas pessoais → acima de 50."""
    assert score_composto({"hours_played": 10}) > 50.0


def test_score_composto_personal_outweighs_hltb():
    """Horas pessoais têm peso 2× — mesmo volume em horas rende mais que HLTB."""
    hltb_only = score_composto({"main_extra": 20, "hours_played": 0})
    personal_only = score_composto({"main_extra": 0, "hours_played": 20})
    assert personal_only > hltb_only


# --- _fallback_score ---


def test_fallback_neutral_when_no_hours():
    assert _fallback_score({}) == pytest.approx(50.0)
    assert _fallback_score({"main_extra": 0, "hours_played": 0}) == pytest.approx(50.0)


def test_fallback_positive_from_hltb():
    assert _fallback_score({"main_extra": 20}) > 50.0


def test_fallback_positive_from_personal():
    assert _fallback_score({"hours_played": 5}) > 50.0


def test_fallback_personal_outweighs_hltb():
    hltb_max = _fallback_score({"main_extra": 40, "hours_played": 0})
    personal_max = _fallback_score({"main_extra": 0, "hours_played": 20})
    assert personal_max > hltb_max


def test_fallback_capped_at_60():
    assert _fallback_score({"main_extra": 9999, "hours_played": 9999}) == pytest.approx(60.0)


def test_fallback_always_in_range():
    cases = [
        {},
        {"main_extra": 10},
        {"hours_played": 5},
        {"main_extra": 40, "hours_played": 20},
        {"main_extra": 9999, "hours_played": 9999},
    ]
    for g in cases:
        s = _fallback_score(g)
        assert 50.0 <= s <= 60.0 + 1e-9, f"fora de [50,60]: {s} para {g}"


# --- shortest ---


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


def test_shortest_no_quality_uses_fallback():
    """Sem MC/Steam%, score_shortest usa fallback dividido pela raiz das horas."""
    g = {"metacritic": None, "steam_pct": None, "main_extra": 10, "hours_played": 0}
    s = score_shortest(g)
    assert s > 0.0  # não é mais zero — fallback entra
    assert s < 50.0  # penalizado pela duração (sqrt(10) > 1)


def test_shortest_ultra_short_does_not_inflate():
    """Piso de 1h: jogo de 0.25h não estoura o composite (bug: 90/√0.25 = 180)."""
    g = {"metacritic": 90, "steam_pct": 90, "main_extra": 0.25}
    assert score_shortest(g) <= 90.0


def test_shortest_floored_below_one_hour():
    """Abaixo de 1h tudo conta como 1h → score == composite (não cresce)."""
    half = {"metacritic": 80, "steam_pct": 80, "main_extra": 0.5}
    one = {"metacritic": 80, "steam_pct": 80, "main_extra": 1}
    assert score_shortest(half) == pytest.approx(80.0)
    assert score_shortest(half) == pytest.approx(score_shortest(one))


# --- longest ---


def test_longest_log_cap_formula():
    game = {"metacritic": 80, "steam_pct": 80, "main_extra": 4}
    # composite=80, curva log+cap: 80 * ln(1+4) / ln(1+100)
    assert score_longest(game) == pytest.approx(80 * math.log1p(4) / math.log1p(100))


def test_longest_no_hours_returns_zero():
    """Sem dado de duração: não dá pra ranquear como 'longo' → 0.0."""
    assert score_longest({"metacritic": 80, "steam_pct": 80, "main_extra": 0}) == 0.0
    assert score_longest({"metacritic": 80, "steam_pct": 80, "main_extra": None}) == 0.0


def test_longest_caps_hours_at_100():
    """Acima de 100h satura: score == composite, e horas absurdas não inflam."""
    g100 = {"metacritic": 90, "steam_pct": 90, "main_extra": 100}
    g_endless = {"metacritic": 90, "steam_pct": 90, "main_extra": 1140}
    assert score_longest(g100) == pytest.approx(90.0)  # ln(101)/ln(101) = 1 → composite
    assert score_longest(g_endless) == pytest.approx(score_longest(g100))


def test_longest_never_exceeds_composite():
    """Teto: score <= composite (escala alinhada com os outros sorts, ≤100)."""
    g = {"metacritic": 95, "steam_pct": 95, "main_extra": 5000}
    assert score_longest(g) <= 95.0 + 1e-9


def test_longest_quality_decides_among_long_games():
    """Campanha longa de qualidade vence grind infinito de qualidade menor (bug do Dota)."""
    witcher = {"metacritic": 95, "steam_pct": 95, "main_extra": 103}
    dota = {"metacritic": 85, "steam_pct": 86, "main_extra": 1140}
    assert score_longest(witcher) > score_longest(dota)


def test_longest_smooth_below_cap():
    """Abaixo do teto, mais longo pontua mais (mesma qualidade)."""
    g25 = {"metacritic": 90, "steam_pct": 90, "main_extra": 25}
    g100 = {"metacritic": 90, "steam_pct": 90, "main_extra": 100}
    assert score_longest(g100) > score_longest(g25)


def test_longest_no_quality_with_hltb_hours_uses_fallback():
    """Sem MC/Steam% mas com HLTB: longest usa fallback × fator de duração."""
    g = {"metacritic": None, "steam_pct": None, "main_extra": 20, "hours_played": 0}
    assert score_longest(g) > 0.0  # fallback ativa, horas presentes


# --- rated / loved ---


def test_rated_direct():
    assert score_rated({"metacritic": 85}) == 85.0
    assert score_rated({"metacritic": None}) == 0.0


def test_loved_direct():
    assert score_loved({"steam_pct": 92}) == 92.0
    assert score_loved({"steam_pct": None}) == 0.0


# --- quick-wins ---


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


def test_quick_wins_unscored_excluded():
    """Sem MC/Steam%: fallback é max 60 < 75 → nunca entra em quick-wins."""
    assert score_quick_wins({"main_extra": 5, "hours_played": 20}) == 0.0


# --- hidden-gems ---


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


# --- compute_score dispatch ---


def test_compute_score_dispatches_correctly():
    game = {"metacritic": 90, "steam_pct": 90, "main_extra": 9}
    # composite = 90
    assert compute_score(game, "shortest") == pytest.approx(90 / math.sqrt(9))  # 30
    assert compute_score(game, "longest") == pytest.approx(90 * math.log1p(9) / math.log1p(100))
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
    from steam_hltb.core.score import score_composto

    # mc presente mas peso zero → total_weight == 0 → 0.0
    assert score_composto({"metacritic": 80}, {"mc": 0.0, "steam": 0.0}) == 0.0


# --- propriedades transversais ---

# Scorers que devolvem 0.0 para jogo completamente vazio (sem horas, sem qualidade)
_ZERO_FOR_EMPTY_SORTS = ["longest", "rated", "loved", "quick-wins", "hidden-gems"]


@pytest.mark.parametrize("sort", _ZERO_FOR_EMPTY_SORTS)
def test_scorers_return_zero_for_empty_game(sort):
    """Sem qualquer dado, estes scorers devolvem 0.0."""
    assert compute_score({}, sort) == 0.0


def test_composto_returns_neutral_for_empty_game():
    """Sem qualquer dado, composto retorna neutro (50) — desconhecido ≠ ruim."""
    assert compute_score({}, "composto") == pytest.approx(50.0)


def test_shortest_returns_neutral_for_empty_game():
    """Sem qualquer dado, shortest retorna neutro (50/√1 = 50)."""
    assert compute_score({}, "shortest") == pytest.approx(50.0)


@pytest.mark.parametrize("sort", [*_ZERO_FOR_EMPTY_SORTS, "composto", "shortest"])
def test_all_scorers_never_negative(sort):
    g = {"metacritic": 70, "steam_pct": 60, "main_extra": 30}
    assert compute_score(g, sort) >= 0.0


def test_rated_none_returns_zero():
    assert score_rated({"metacritic": None}) == 0.0
    assert score_rated({}) == 0.0


def test_loved_none_returns_zero():
    assert score_loved({"steam_pct": None}) == 0.0
    assert score_loved({}) == 0.0


def test_quick_wins_at_quality_floor_included():
    # composite exatamente 75 não é < 75 → entra no quick-wins
    assert score_quick_wins({"metacritic": 75, "steam_pct": 75, "main_extra": 10}) > 0


def test_hidden_gems_at_steam_floor_included():
    # steam exatamente 80 não é < 80 → entra em hidden-gems
    assert score_hidden_gems({"steam_pct": 80, "metacritic": 50}) > 0


def test_bounded_scorers_stay_within_0_100():
    """rated/loved/composto/longest ficam em [0, 100] mesmo com horas absurdas."""
    g = {"metacritic": 100, "steam_pct": 100, "main_extra": 100000}
    for sort in ("rated", "loved", "composto", "longest", "shortest"):
        assert 0.0 <= compute_score(g, sort) <= 100.0


def test_shortest_zero_total_weight_returns_zero():
    """score_composto retorna 0 quando total_weight=0 → score_shortest também retorna 0."""
    assert score_shortest({"metacritic": 80}, {"mc": 0.0, "steam": 0.0}) == 0.0


def test_fallback_never_beats_rated_game():
    """Jogo com qualquer score real sempre supera um jogo sem score com max fallback."""
    rated = {"metacritic": 61, "steam_pct": 61}
    fallback = {"main_extra": 9999, "hours_played": 9999}
    assert score_composto(rated) > score_composto(fallback)
