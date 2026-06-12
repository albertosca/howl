import math

SORT_OPTIONS = ["hltb_short", "hltb_long", "metacritic", "steam", "composto", "custom"]


def score_hltb_short(game: dict) -> float:
    mc = game.get("metacritic")
    hours = game.get("main_extra", 0)
    if mc is None:
        return 0.0
    if hours and hours > 0:
        return mc / math.sqrt(hours)
    return float(mc)


def score_hltb_long(game: dict) -> float:
    mc = game.get("metacritic")
    hours = game.get("main_extra", 0)
    if mc is None:
        return 0.0
    if hours and hours > 0:
        return mc * math.sqrt(hours)
    return float(mc)


def score_metacritic(game: dict) -> float:
    return float(game.get("metacritic") or 0)


def score_steam(game: dict) -> float:
    return float(game.get("steam_pct") or 0)


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


def compute_score(game: dict, sort_by: str, weights: dict | None = None) -> float:
    if sort_by == "hltb_short":
        return score_hltb_short(game)
    if sort_by == "hltb_long":
        return score_hltb_long(game)
    if sort_by == "metacritic":
        return score_metacritic(game)
    if sort_by == "steam":
        return score_steam(game)
    if sort_by in ("composto", "custom"):
        return score_composto(game, weights)
    raise ValueError(f"Unknown sort: {sort_by}")
