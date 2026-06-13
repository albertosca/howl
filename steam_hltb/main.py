import argparse
import csv
import os
import sys

from .fetch import get_api_key, load_cache, build_library
from .score import compute_score, SORT_OPTIONS
from .classify import build_game_rows, apply_filters, ERA_LABELS
from .steam_collections import load_collections, filter_collection

# Categorias Steam de infraestrutura — não relevantes para gameplay
STEAM_NOISE_CATEGORIES: frozenset[str] = frozenset({
    "steam achievements", "steam cloud", "steam leaderboards",
    "steam trading cards", "steam workshop", "valve anti-cheat enabled",
    "stats", "steam turn notifications", "remote play on phone",
    "remote play on tablet", "remote play on tv", "remote play together",
    "in-app purchases", "partial controller support",
})


def _gameplay_categories(game: dict) -> list[str]:
    """Retorna steam.categories filtradas de ruído de infraestrutura."""
    return [c for c in game.get("tags", []) if c.lower() not in STEAM_NOISE_CATEGORIES]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="howl",
        description="HOWL — Hoard Optimizer, What to Launch. Ranqueia sua biblioteca Steam por qualidade × tempo.",
        epilog="""
Exemplos:
  howl --username mysteamid --top 25 --sort rated
  howl --username mysteamid --genre "action,rpg" --not-started --top 10
  howl --username mysteamid --tui --sort shortest
  howl --username mysteamid --era "2010-2015,2015-2020" --sort quick-wins

  Dica: defina STEAM_USERNAME no ambiente para não precisar de --username.

Formatos de entrada:
  --genre / --genre-any / --exclude-genre  nomes separados por vírgula (ex: "action,rpg")
  --sort                                   shortest | longest | rated | loved | quick-wins | hidden-gems | composto
  --era                                    épocas separadas por vírgula: pre-2005, 2005-2010, 2010-2015, 2015-2020, 2020+, unknown
  --weight-mc / --weight-steam             pesos de 0.0 a 1.0 que somam 1.0 (ex: 0.6 e 0.4)
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--username", default=os.environ.get("STEAM_USERNAME"),
                   help="Vanity URL do perfil Steam (ou env STEAM_USERNAME)")
    p.add_argument("--sort", default="shortest", choices=SORT_OPTIONS,
                   help="Critério de ordenação (padrão: %(default)s)")
    p.add_argument("--genre",
                   help="Gêneros obrigatórios, separados por vírgula (ex: 'action,rpg')")
    p.add_argument("--genre-any",
                   help="Pelo menos um desses gêneros (separados por vírgula)")
    p.add_argument("--exclude-genre",
                   help="Gêneros a excluir (separados por vírgula)")

    prog = p.add_mutually_exclusive_group()
    prog.add_argument("--not-started", action="store_true",
                      help="Somente jogos nunca jogados (0h)")
    prog.add_argument("--in-progress", action="store_true",
                      help="Somente jogos iniciados e não zerados")
    prog.add_argument("--all-progress", action="store_true",
                      help="Sem filtro de progresso (inclui jogos já zerados)")

    p.add_argument("--category", default="all", choices=["all", "singleplayer", "coop"],
                   help="Filtrar por tipo de jogo (padrão: %(default)s)")
    p.add_argument("--min-hours", type=float, help="Duração mínima HLTB em horas")
    p.add_argument("--max-hours", type=float, help="Duração máxima HLTB em horas")
    p.add_argument("--era",
                   help="Épocas de lançamento (vírgula-sep): pre-2005, 2005-2010, 2010-2015, 2015-2020, 2020+, unknown")
    p.add_argument("--top", type=int, default=10,
                   help="Quantos jogos exibir (padrão: %(default)s)")
    p.add_argument("--output", default="howl_output",
                   help="Nome base dos arquivos de saída .csv e .md (padrão: %(default)s)")
    p.add_argument("--weight-mc", type=float, default=0.5,
                   help="Peso do Metacritic no score composto (padrão: %(default)s)")
    p.add_argument("--weight-steam", type=float, default=0.5,
                   help="Peso do Steam no score composto (padrão: %(default)s)")
    p.add_argument("--collection",
                   help="Filtrar por coleção Steam (ex: 'Jogando', 'Multiplayer')")
    p.add_argument("--vdf-path", default=os.environ.get("STEAM_VDF_PATH", "sharedconfig.vdf"),
                   help="Caminho para o sharedconfig.vdf do Steam (padrão: STEAM_VDF_PATH env ou sharedconfig.vdf)")
    p.add_argument("--show-finished", action="store_true",
                   help="Incluir jogos da coleção 'Terminados' (excluídos por padrão)")
    p.add_argument("--list-tags", action="store_true",
                   help="Lista todas as categorias disponíveis no cache e sai")
    p.add_argument("--list-genres", action="store_true",
                   help="Lista todos os gêneros disponíveis no cache e sai")
    p.add_argument("--list-collections", action="store_true",
                   help="Lista coleções Steam disponíveis no VDF e sai")
    p.add_argument("--refresh", action="store_true",
                   help="Ignora o cache e rebusca todos os jogos")
    p.add_argument("--migrate-cache", action="store_true",
                   help="Preenche steam.genres/categories/release_year para entradas incompletas (~15-30 min)")
    p.add_argument("-v", "--verbose", action="store_true",
                   help="Exibe progresso detalhado de todos os jogos (inclusive cache)")
    p.add_argument("--show-tags", action="store_true",
                   help="Exibe categorias Steam dos jogos na tabela (além de gêneros)")
    p.add_argument("--interactive", action="store_true",
                   help="Modo interativo via prompts")
    p.add_argument("--tui", action="store_true",
                   help="Abre interface visual interativa (htop-style)")
    return p.parse_args()


def _resolve_username(args: argparse.Namespace) -> str:
    """Retorna username do argparse, env var, ou prompt interativo."""
    if args.username:
        return args.username
    username = input("Steam username (vanity URL do perfil): ").strip()
    if not username:
        print("Erro: username obrigatório.", file=sys.stderr)
        sys.exit(1)
    return username


def _progress_mode(args: argparse.Namespace) -> str:
    if args.not_started:
        return "not_started"
    if args.in_progress:
        return "in_progress"
    if args.all_progress:
        return "all"
    return "default"


def _weights(args: argparse.Namespace) -> dict[str, float]:
    w: dict[str, float] = {"mc": args.weight_mc, "steam": args.weight_steam}
    total = sum(w.values())
    if abs(total - 1.0) > 0.01:
        print(f"Aviso: pesos somam {total:.2f}, esperado 1.0. Normalizando.", file=sys.stderr)
        w = {k: v / total for k, v in w.items()}
    return w


def _csv_list(value: str | None) -> list[str] | None:
    if not value:
        return None
    result = [v.strip() for v in value.split(",") if v.strip()]
    return result or None


def print_table(games: list[dict], sort_by: str, show_tags: bool = False) -> None:
    header = f"{'#':>3}  {'Nome':<45}  {'Ano':>4}  {'MC':>4}  {'Steam':>6}  {'HLTB':>5}  {'Jogadas':>8}  {'Score':>8}"
    print(header)
    print("-" * len(header))
    for i, g in enumerate(games, 1):
        ano   = str(g["release_year"]) if g.get("release_year") else "-"
        mc    = str(g["metacritic"]) if g["metacritic"] else "-"
        steam = f"{g['steam_pct']}%" if g["steam_pct"] else "-"
        hltb  = f"{g['main_extra']}h" if g.get("main_extra") else "-"
        jogou = f"{g['hours_played']}h"
        score = f"{g['_score']:.1f}"
        print(f"{i:>3}  {g['name']:<45}  {ano:>4}  {mc:>4}  {steam:>6}  {hltb:>5}  {jogou:>8}  {score:>8}")
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
    counter: Counter[str] = Counter(
        tag for tags in collection_map.values() for tag in tags
    )
    if not counter:
        print("Nenhuma coleção encontrada. Verifique --vdf-path.")
        return
    print(f"\n{'─'*40}")
    print(f" COLEÇÕES disponíveis ({len(counter)} únicas)")
    print(f"{'─'*40}")
    for name, count in counter.most_common():
        print(f"  {count:>4}x  {name}")


def list_available(cache: dict, field: str) -> None:
    from collections import Counter
    counter: Counter[str] = Counter()
    for entry in cache.values():
        steam = entry.get("steam") or {}
        rawg  = entry.get("rawg") or {}
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
    print(f"\n{'─'*40}")
    print(f" {field.upper()} disponíveis ({len(counter)} únicos)")
    print(f"{'─'*40}")
    for value, count in counter.most_common():
        print(f"  {count:>4}x  {value}")


def save_results(games: list[dict], output_base: str) -> None:
    csv_path = output_base + ".csv"
    md_path  = output_base + ".md"

    fields = ["name", "category", "metacritic", "steam_pct", "score",
              "hours_played", "main_story", "main_extra", "completionist"]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for g in games:
            writer.writerow(
                {k: g.get(k) for k in fields if k != "score"} | {"score": round(g["_score"], 2)}
            )

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("| # | Nome | MC | Steam | HLTB | Jogadas | Score |\n")
        f.write("|---|------|----|-------|------|---------|-------|\n")
        for i, g in enumerate(games, 1):
            mc    = str(g["metacritic"]) if g["metacritic"] else "-"
            steam = f"{g['steam_pct']}%" if g["steam_pct"] else "-"
            hltb_str = f"{g['main_extra']}h" if g.get("main_extra") else "-"
            f.write(f"| {i} | {g['name']} | {mc} | {steam} | {hltb_str} | {g['hours_played']}h | {g['_score']:.1f} |\n")

    print(f"\nSalvo em '{csv_path}' e '{md_path}'")


def run(args: argparse.Namespace) -> None:
    steam_key = get_api_key("STEAM_API_KEY", "Steam API key")
    username  = _resolve_username(args)

    cache = load_cache()
    cache, steam_games = build_library(steam_key, username, cache,
                                       refresh=args.refresh, verbose=args.verbose)

    rows = build_game_rows(cache, steam_games)
    rows = apply_filters(
        rows,
        genre=_csv_list(args.genre),
        genre_any=_csv_list(args.genre_any),
        exclude_genre=_csv_list(args.exclude_genre),
        progress=_progress_mode(args),
        category=args.category,
        min_hours=args.min_hours,
        max_hours=args.max_hours,
        eras=_csv_list(args.era),
    )
    if not args.show_finished:
        from .steam_collections import exclude_finished
        rows = exclude_finished(rows, args.vdf_path)
    if args.collection:
        collection_map = load_collections(args.vdf_path)
        rows = filter_collection(rows, args.collection, collection_map)

    weights = _weights(args)
    for g in rows:
        g["_score"] = compute_score(g, args.sort, weights)

    rows.sort(key=lambda g: g["_score"], reverse=True)
    top = rows[:args.top]

    total_filtered = len(rows)
    print(f"\n{'='*60}")
    print(f" TOP {args.top} — sort: {args.sort}  ({len(top)} de {total_filtered} filtrados)")
    if len(top) < args.top and total_filtered < args.top:
        print(f" ⚠  Apenas {total_filtered} jogos passaram nos filtros (pedido: {args.top})")
    print(f"{'='*60}")
    print_table(top, args.sort, show_tags=args.show_tags)
    save_results(rows, args.output)


def main() -> None:
    args = parse_args()

    if args.migrate_cache:
        from .fetch import migrate_steam_details
        print("⚠  Isso pode demorar 15-30 min. Ctrl+C para interromper (progresso salvo).")
        migrate_steam_details(load_cache(), verbose=True)
        print("Migração concluída.")
        return

    if args.list_tags or args.list_genres or args.list_collections:
        cache = load_cache()
        if args.list_genres:
            list_available(cache, "genres")
        if args.list_tags:
            list_available(cache, "categories")
        if args.list_collections:
            list_collections_cmd(load_collections(args.vdf_path))
        return

    if args.tui:
        from .tui import run_tui
        steam_key = get_api_key("STEAM_API_KEY", "Steam API key")
        username  = _resolve_username(args)
        cache = load_cache()
        cache, steam_games = build_library(steam_key, username, cache,
                                           refresh=args.refresh, verbose=args.verbose)
        rows = build_game_rows(cache, steam_games)
        initial_filters = {
            "genre":         _csv_list(args.genre),
            "genre_any":     _csv_list(args.genre_any),
            "exclude_genre": _csv_list(args.exclude_genre),
            "progress":      _progress_mode(args),
            "category":      args.category,
            "min_hours":     args.min_hours,
            "max_hours":     args.max_hours,
            "sort":          args.sort,
            "top":           args.top,
            "weights":       _weights(args),
            "vdf_path":      args.vdf_path,
            "show_finished": args.show_finished,
            "eras":          _csv_list(args.era),
        }
        run_tui(rows, initial_filters)
        return

    if args.interactive:
        from .interactive import run_interactive
        run_interactive(args)
        return

    run(args)


if __name__ == "__main__":
    main()
