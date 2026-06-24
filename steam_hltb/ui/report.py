import csv
from pathlib import Path
from typing import Any

from ..core.types import Game

# Categorias Steam de infraestrutura — não relevantes para gameplay
STEAM_NOISE_CATEGORIES: frozenset[str] = frozenset(
    {
        "steam achievements",
        "steam cloud",
        "steam leaderboards",
        "steam trading cards",
        "steam workshop",
        "valve anti-cheat enabled",
        "stats",
        "steam turn notifications",
        "remote play on phone",
        "remote play on tablet",
        "remote play on tv",
        "remote play together",
        "in-app purchases",
        "partial controller support",
    }
)


def _gameplay_categories(game: Game) -> list[str]:
    """Retorna steam.categories filtradas de ruído de infraestrutura."""
    return [c for c in game.get("tags", []) if c.lower() not in STEAM_NOISE_CATEGORIES]


def print_table(games: list[Game], sort_by: str, show_tags: bool = False) -> None:
    header = (
        f"{'#':>3}  {'Nome':<45}  {'Ano':>4}  {'MC':>4}  "
        f"{'Steam':>6}  {'HLTB':>5}  {'Jogadas':>8}  {'Score':>8}"
    )
    print(header)
    print("-" * len(header))
    for i, g in enumerate(games, 1):
        ano = str(g["release_year"]) if g.get("release_year") else "-"
        mc = str(g["metacritic"]) if g["metacritic"] else "-"
        steam = f"{g['steam_pct']}%" if g["steam_pct"] else "-"
        hltb = f"{g['main_extra']}h" if g.get("main_extra") else "-"
        jogou = f"{g['hours_played']}h"
        score = f"{g['_score']:.1f}"
        print(
            f"{i:>3}  {g['name']:<45}  {ano:>4}  {mc:>4}  "
            f"{steam:>6}  {hltb:>5}  {jogou:>8}  {score:>8}"
        )
        parts = []
        genres = g.get("genres", [])
        if genres:
            parts.append(", ".join(genres[:4]))
        if show_tags:
            cats = _gameplay_categories(g)
            if cats:
                parts.append("cat: " + ", ".join(cats[:4]))
        if parts:
            print(f"     ↳ {' · '.join(parts)}")


def list_collections_cmd(collection_map: dict[str, list[str]]) -> None:
    from collections import Counter

    counter: Counter[str] = Counter(tag for tags in collection_map.values() for tag in tags)
    if not counter:
        print("Nenhuma coleção encontrada. Verifique --vdf-path.")
        return
    print(f"\n{'─' * 40}")
    print(f" COLEÇÕES disponíveis ({len(counter)} únicas)")
    print(f"{'─' * 40}")
    for name, count in counter.most_common():
        print(f"  {count:>4}x  {name}")


def list_available(cache: dict[str, Any], field: str) -> None:
    from collections import Counter

    counter: Counter[str] = Counter()
    for entry in cache.values():
        steam = entry.get("steam") or {}
        rawg = entry.get("rawg") or {}
        if field == "categories":
            values = steam.get("categories") or []
        else:
            values = steam.get(field) or rawg.get(field, [])
        for v in values:
            if v.lower() not in STEAM_NOISE_CATEGORIES:
                counter[v] += 1
    if not counter:
        print(f"Nenhum(a) {field} encontrado(a) no cache. Tente --refresh ou --migrate-cache.")
        return
    print(f"\n{'─' * 40}")
    print(f" {field.upper()} disponíveis ({len(counter)} únicos)")
    print(f"{'─' * 40}")
    for value, count in counter.most_common():
        print(f"  {count:>4}x  {value}")


def save_results(games: list[Game], output_base: str) -> None:
    csv_path = Path(output_base + ".csv")
    md_path = Path(output_base + ".md")
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "name",
        "category",
        "metacritic",
        "steam_pct",
        "score",
        "hours_played",
        "main_story",
        "main_extra",
        "completionist",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for g in games:
            writer.writerow(
                {k: g.get(k) for k in fields if k != "score"} | {"score": round(g["_score"], 2)}
            )

    with md_path.open("w", encoding="utf-8") as f:
        f.write("| # | Nome | MC | Steam | HLTB | Jogadas | Score |\n")
        f.write("|---|------|----|-------|------|---------|-------|\n")
        for i, g in enumerate(games, 1):
            mc = str(g["metacritic"]) if g["metacritic"] else "-"
            steam = f"{g['steam_pct']}%" if g["steam_pct"] else "-"
            hltb_str = f"{g['main_extra']}h" if g.get("main_extra") else "-"
            f.write(
                f"| {i} | {g['name']} | {mc} | {steam} | "
                f"{hltb_str} | {g['hours_played']}h | {g['_score']:.1f} |\n"
            )

    print(f"\nSalvo em '{csv_path}' e '{md_path}'")
