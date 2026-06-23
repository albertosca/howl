"""Pipeline de seleção: filtra, pontua e ordena jogos. Sem dependência de UI."""

from typing import Any

from ..sources.collections import exclude_finished, filter_collection, load_collections
from .classify import apply_filters, filter_name
from .score import compute_score


def select_games(all_games: list[dict[str, Any]], filters: dict[str, Any]) -> list[dict[str, Any]]:
    """Aplica filtros, calcula `_score` e ordena (desc). Não corta no top — o
    chamador fatia `[: filters['top']]` conforme precisa (CLI salva tudo, TUI
    mostra o top)."""
    rows = apply_filters(
        all_games,
        genre=filters.get("genre"),
        genre_any=filters.get("genre_any"),
        exclude_genre=filters.get("exclude_genre"),
        progress=filters.get("progress", "default"),
        category=filters.get("category", "all"),
        min_hours=filters.get("min_hours"),
        max_hours=filters.get("max_hours"),
        eras=filters.get("eras"),
    )
    rows = filter_name(rows, query=filters.get("name_query"))

    vdf_path = filters.get("vdf_path", "sharedconfig.vdf")
    if not filters.get("show_finished", False):
        rows = exclude_finished(rows, vdf_path)
    if filters.get("collection"):
        collection_map = load_collections(vdf_path)
        rows = filter_collection(rows, filters["collection"], collection_map)

    weights = filters["weights"]
    sort_by = filters["sort"]
    for g in rows:
        g["_score"] = compute_score(g, sort_by, weights)
    rows.sort(key=lambda g: g["_score"], reverse=True)
    return rows
