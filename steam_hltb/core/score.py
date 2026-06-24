import math
from typing import Any

SORT_OPTIONS = [
    "shortest",  # curto, qualidade ajuda: composite / √h
    "longest",  # longo, qualidade ajuda: composite × √h / 10
    "rated",  # Metacritic puro
    "loved",  # Steam % positivo puro
    "quick-wins",  # jogo bom (≥75 composite) e curto: composite / (1 + h/5)
    "hidden-gems",  # muito amado pelos players (≥80% steam), ignorado pela crítica
    "composto",  # média ponderada mc+steam configurável
]


def score_composto(game: dict[str, Any], weights: dict[str, float] | None = None) -> float:
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
        return 0.0
    total_weight = sum(weights.get(k, 0) for k in sources)
    if total_weight == 0:
        return 0.0
    return float(sum(sources[k] * weights.get(k, 0) / total_weight for k in sources))


SHORTEST_HOURS_FLOOR = 1.0  # abaixo disso é "muito curto"; não infla além do composite


def score_shortest(game: dict[str, Any], weights: dict[str, float] | None = None) -> float:
    """Bons jogos mais curtos: composite / √max(horas, 1).

    O piso de 1h evita que jogos curtíssimos (ex: 0.25h) estourem o composite
    (sem ele, 90/√0.25 = 180). Score ≤ composite. Sem duração também rende
    o composite cheio (sem penalidade de tempo)."""
    score = score_composto(game, weights)
    if score == 0:
        return 0.0
    hours = game.get("main_extra") or 0
    return score / math.sqrt(max(float(hours), SHORTEST_HOURS_FLOOR))


LONGEST_HOURS_CAP = 100.0  # acima disso é "muito longo"; horas extras não inflam o score


def score_longest(game: dict[str, Any], weights: dict[str, float] | None = None) -> float:
    """Jogos mais longos, curva log com teto: composite × ln(1+min(h,cap)) / ln(1+cap).

    Cresce suave com a duração até `cap` (100h) e satura depois — então jogos
    endless/grind com horas absurdas do HLTB (ex: MOBAs com 1000h+) não dominam,
    e entre os longos a qualidade desempata. Score ≤ composite. Sem duração = 0.
    """
    score = score_composto(game, weights)
    hours = game.get("main_extra")
    if not score or not hours:
        return 0.0
    capped = min(float(hours), LONGEST_HOURS_CAP)
    return score * math.log1p(capped) / math.log1p(LONGEST_HOURS_CAP)


def score_rated(game: dict[str, Any]) -> float:
    """Mais aclamados pela crítica: Metacritic puro."""
    return float(game.get("metacritic") or 0)


def score_loved(game: dict[str, Any]) -> float:
    """Mais amados pelos jogadores: Steam % positivo."""
    return float(game.get("steam_pct") or 0)


def score_quick_wins(game: dict[str, Any], weights: dict[str, float] | None = None) -> float:
    """Jogo bom (composite ≥ 75) e curto: composite / (1 + horas/5). Sem dado = excluído."""
    score = score_composto(game, weights)
    hours = game.get("main_extra")
    if not score or not hours or score < 75:
        return 0.0
    return score / (1 + float(hours) / 5)


def score_hidden_gems(game: dict[str, Any]) -> float:
    """Muito amado pelos players (≥80% steam), ignorado pela crítica: steam × (1 - mc/100).
    Sem MC = dado ausente → excluído. Steam < 80% = não é muito aclamado → excluído."""
    steam = game.get("steam_pct")
    mc = game.get("metacritic")
    if steam is None or mc is None or steam < 80:
        return 0.0
    return float(steam) * (1 - float(mc) / 100)


def compute_score(
    game: dict[str, Any], sort_by: str, weights: dict[str, float] | None = None
) -> float:
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
