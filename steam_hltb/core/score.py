import math

from .types import Game

SORT_OPTIONS = [
    "shortest",  # short, quality helps: composite / √h
    "longest",  # long, quality helps: composite × √h / 10
    "rated",  # pure Metacritic
    "loved",  # pure Steam % positive
    "quick-wins",  # good game (≥75 composite) and short: composite / (1 + h/5)
    "hidden-gems",  # loved by players (≥80% steam), ignored by critics
    "composto",  # configurable weighted average mc+steam
]

# Fallback for games with no quality data (no MC and no Steam%).
# Uses hours as proxy: HLTB (positive signal) + personal (weight 2×).
# Range [50, 60] — never competes with well-rated games (which reach 100).
_FALLBACK_NEUTRAL = 50.0
_FALLBACK_MAX = 60.0
_FALLBACK_HLTB_CAP_H = 40.0  # saturation: 40h HLTB = max HLTB signal
_FALLBACK_PERSONAL_CAP_H = 20.0  # saturation: 20h personal = max personal signal
_FALLBACK_PERSONAL_WEIGHT = 2.0  # personal hours count double vs HLTB hours


def _fallback_score(game: Game) -> float:
    """Proxy score when no quality data (no MC or Steam%).

    No hours at all → neutral (50, unknown).
    With HLTB or personal hours → above 50 (positive signal).
    Personal hours have 2× weight relative to HLTB hours.
    Ceiling 60 — a well-rated game always wins.
    """
    hltb_h = float(game.get("main_extra") or 0)
    personal_h = float(game.get("hours_played") or 0)
    if hltb_h == 0 and personal_h == 0:
        return _FALLBACK_NEUTRAL
    hltb_sig = min(hltb_h / _FALLBACK_HLTB_CAP_H, 1.0)
    personal_sig = min(personal_h / _FALLBACK_PERSONAL_CAP_H, 1.0)
    w_total = 1.0 + _FALLBACK_PERSONAL_WEIGHT
    weighted = (hltb_sig + _FALLBACK_PERSONAL_WEIGHT * personal_sig) / w_total
    return _FALLBACK_NEUTRAL + weighted * (_FALLBACK_MAX - _FALLBACK_NEUTRAL)


def score_composto(game: Game, weights: dict[str, float] | None = None) -> float:
    if weights is None:
        weights = {"mc": 0.5, "steam": 0.5}
    sources = {}
    mc = game.get("metacritic")
    steam = game.get("steam_pct")
    if mc is not None:
        sources["mc"] = mc
    if steam is not None:
        sources["steam"] = steam
    if not sources:
        return _fallback_score(game)
    total_weight = sum(weights.get(k, 0) for k in sources)
    if total_weight == 0:
        return 0.0
    return float(sum(sources[k] * weights.get(k, 0) / total_weight for k in sources))


SHORTEST_HOURS_FLOOR = 1.0  # below this is "very short"; doesn't inflate beyond composite


def score_shortest(game: Game, weights: dict[str, float] | None = None) -> float:
    """Good and short games: composite / √max(hours, 1).

    The 1h floor prevents ultra-short games (e.g. 0.25h) from blowing up composite
    (without it, 90/√0.25 = 180). Score ≤ composite. No duration also yields
    the full composite (no time penalty)."""
    score = score_composto(game, weights)
    if score == 0:
        return 0.0
    hours = game.get("main_extra") or 0
    return score / math.sqrt(max(float(hours), SHORTEST_HOURS_FLOOR))


LONGEST_HOURS_CAP = 100.0  # above this is "very long"; extra hours don't inflate the score


def score_longest(game: Game, weights: dict[str, float] | None = None) -> float:
    """Longer games, log curve with cap: composite × ln(1+min(h,cap)) / ln(1+cap).

    Grows smoothly with duration up to `cap` (100h) then saturates — so
    endless/grind games with absurd HLTB hours (e.g. MOBAs at 1000h+) don't
    dominate, and quality breaks ties among long games. Score ≤ composite. No duration = 0.
    """
    score = score_composto(game, weights)
    hours = game.get("main_extra")
    if not score or not hours:
        return 0.0
    capped = min(float(hours), LONGEST_HOURS_CAP)
    return score * math.log1p(capped) / math.log1p(LONGEST_HOURS_CAP)


def score_rated(game: Game) -> float:
    """Most critically acclaimed: pure Metacritic."""
    return float(game.get("metacritic") or 0)


def score_loved(game: Game) -> float:
    """Most loved by players: pure Steam % positive."""
    return float(game.get("steam_pct") or 0)


def score_quick_wins(game: Game, weights: dict[str, float] | None = None) -> float:
    """Good game (composite ≥ 75) and short: composite / (1 + hours/5). No data = excluded."""
    score = score_composto(game, weights)
    hours = game.get("main_extra")
    if not score or not hours or score < 75:
        return 0.0
    return score / (1 + float(hours) / 5)


def score_hidden_gems(game: Game) -> float:
    """Loved by players (≥80% steam), ignored by critics: steam × (1 - mc/100).
    No MC = missing data → excluded. Steam < 80% = not widely loved → excluded."""
    steam = game.get("steam_pct")
    mc = game.get("metacritic")
    if steam is None or mc is None or steam < 80:
        return 0.0
    return float(steam) * (1 - float(mc) / 100)


def compute_score(game: Game, sort_by: str, weights: dict[str, float] | None = None) -> float:
    if sort_by == "shortest":
        return score_shortest(game, weights)
    if sort_by == "longest":
        return score_longest(game, weights)
    if sort_by == "rated":
        return score_rated(game)
    if sort_by == "loved":
        return score_loved(game)
    if sort_by == "quick-wins":
        return score_quick_wins(game, weights)
    if sort_by == "hidden-gems":
        return score_hidden_gems(game)
    if sort_by in ("composto", "custom"):
        return score_composto(game, weights)
    raise ValueError(f"Unknown sort: {sort_by}")
