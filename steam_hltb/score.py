import math

SORT_OPTIONS = [
    "shortest",  # curto, qualidade ajuda: composite / √h
    "longest",  # longo, qualidade ajuda: composite × √h / 10
    "rated",  # Metacritic puro
    "loved",  # Steam % positivo puro
    "quick-wins",  # jogo bom (≥75 composite) e curto: composite / (1 + h/5)
    "hidden-gems",  # muito amado pelos players (≥80% steam), ignorado pela crítica
    "composto",  # média ponderada mc+steam configurável
]


def score_composto(game: dict, weights: dict | None = None) -> float:
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
    return sum(sources[k] * weights.get(k, 0) / total_weight for k in sources)


def score_shortest(game: dict, weights: dict | None = None) -> float:
    """Bons jogos mais curtos: composite / √horas."""
    score = score_composto(game, weights)
    hours = game.get("main_extra") or 0
    if score == 0:
        return 0.0
    if hours > 0:
        return score / math.sqrt(hours)
    return score


def score_longest(game: dict, weights: dict | None = None) -> float:
    """Jogos mais longos: composite × √horas / 10. Sem dado de duração = excluído."""
    score = score_composto(game, weights)
    hours = game.get("main_extra")
    if not score or not hours:
        return 0.0
    return score * math.sqrt(hours) / 10


def score_rated(game: dict) -> float:
    """Mais aclamados pela crítica: Metacritic puro."""
    return float(game.get("metacritic") or 0)


def score_loved(game: dict) -> float:
    """Mais amados pelos jogadores: Steam % positivo."""
    return float(game.get("steam_pct") or 0)


def score_quick_wins(game: dict, weights: dict | None = None) -> float:
    """Jogo bom (composite ≥ 75) e curto: composite / (1 + horas/5). Sem dado = excluído."""
    score = score_composto(game, weights)
    hours = game.get("main_extra")
    if not score or not hours or score < 75:
        return 0.0
    return score / (1 + hours / 5)


def score_hidden_gems(game: dict) -> float:
    """Muito amado pelos players (≥80% steam), ignorado pela crítica: steam × (1 - mc/100).
    Sem MC = dado ausente → excluído. Steam < 80% = não é muito aclamado → excluído."""
    steam = game.get("steam_pct")
    mc = game.get("metacritic")
    if steam is None or mc is None or steam < 80:
        return 0.0
    return float(steam) * (1 - mc / 100)


def compute_score(game: dict, sort_by: str, weights: dict | None = None) -> float:
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
