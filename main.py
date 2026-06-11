import argparse
import csv
import os
import sys

from fetch import get_api_key, load_cache, build_library
from score import compute_score, SORT_OPTIONS
from classify import build_game_rows, apply_filters

STEAM_USERNAME = "gabelogannewell"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Classifica jogos da biblioteca Steam com notas HLTB, Metacritic e Steam.",
        epilog="""
Exemplos:
  python main.py --top 25 --sort metacritic
  python main.py --genre "action,rpg" --not-started --top 10
  python main.py --tui --top 25 --sort hltb_short
  python main.py --min-hours 5 --max-hours 30 --sort composto

Formatos de entrada:
  --genre / --genre-any / --exclude-genre  nomes separados por vírgula (ex: "action,rpg")
  --sort                                   hltb_short | hltb_long | metacritic | steam | composto | custom
  --weight-mc / --weight-steam             pesos de 0.0 a 1.0 que somam 1.0 (ex: 0.6 e 0.4)
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--username", default=STEAM_USERNAME,
                   help="Vanity URL do perfil Steam (padrão: %(default)s)")
    p.add_argument("--sort", default="hltb_short", choices=SORT_OPTIONS,
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
    p.add_argument("--top", type=int, default=10,
                   help="Quantos jogos exibir (padrão: %(default)s)")
    p.add_argument("--output", default="how_long_to_beat_output",
                   help="Nome base dos arquivos de saída .csv e .md")
    p.add_argument("--weight-mc", type=float, default=0.5,
                   help="Peso do Metacritic no score composto (padrão: %(default)s)")
    p.add_argument("--weight-steam", type=float, default=0.5,
                   help="Peso do Steam no score composto (padrão: %(default)s)")
    p.add_argument("--refresh", action="store_true",
                   help="Ignora o cache e rebusca todos os jogos")
    p.add_argument("-v", "--verbose", action="store_true",
                   help="Exibe progresso detalhado de todos os jogos (inclusive cache)")
    p.add_argument("--show-tags", action="store_true",
                   help="Exibe tags dos jogos na tabela (além de gêneros)")
    p.add_argument("--interactive", action="store_true",
                   help="Modo interativo via prompts")
    p.add_argument("--tui", action="store_true",
                   help="Abre interface visual interativa (htop-style)")
    return p.parse_args()


def _progress_mode(args: argparse.Namespace) -> str:
    if args.not_started:
        return "not_started"
    if args.in_progress:
        return "in_progress"
    if args.all_progress:
        return "all"
    return "default"


def _weights(args: argparse.Namespace) -> dict:
    w = {"mc": args.weight_mc, "steam": args.weight_steam}
    total = sum(w.values())
    if abs(total - 1.0) > 0.01:
        print(f"Aviso: pesos somam {total:.2f}, esperado 1.0. Normalizando.", file=sys.stderr)
        w = {k: v / total for k, v in w.items()}
    return w


def _csv_list(value: str | None) -> list | None:
    if not value:
        return None
    return [v.strip() for v in value.split(",") if v.strip()]


def print_table(games: list, sort_by: str, show_tags: bool = False) -> None:
    header = f"{'#':>3}  {'Nome':<45}  {'MC':>4}  {'Steam':>6}  {'HLTB':>5}  {'Jogadas':>8}  {'Score':>8}"
    print(header)
    print("-" * len(header))
    for i, g in enumerate(games, 1):
        mc    = str(g["metacritic"]) if g["metacritic"] else "-"
        steam = f"{g['steam_pct']}%" if g["steam_pct"] else "-"
        hltb  = f"{g['main_extra']}h"
        jogou = f"{g['hours_played']}h"
        score = f"{g['_score']:.1f}"
        print(f"{i:>3}  {g['name']:<45}  {mc:>4}  {steam:>6}  {hltb:>5}  {jogou:>8}  {score:>8}")
        parts = []
        genres = g.get("genres", [])
        if genres:
            parts.append(", ".join(genres[:4]))
        if show_tags:
            tags = g.get("tags", [])
            if tags:
                parts.append("tags: " + ", ".join(tags[:4]))
        if parts:
            print(f"     ↳ {' · '.join(parts)}")


def save_results(games: list, output_base: str) -> None:
    csv_path = output_base + ".csv"
    md_path  = output_base + ".md"

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "name", "category", "metacritic", "steam_pct", "score",
            "hours_played", "main_story", "main_extra", "completionist",
        ])
        writer.writeheader()
        for g in games:
            writer.writerow({k: g.get(k) for k in writer.fieldnames if k != "score"} | {"score": round(g["_score"], 2)})

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("| # | Nome | MC | Steam | HLTB | Jogadas | Score |\n")
        f.write("|---|------|----|-------|------|---------|-------|\n")
        for i, g in enumerate(games, 1):
            mc    = str(g["metacritic"]) if g["metacritic"] else "-"
            steam = f"{g['steam_pct']}%" if g["steam_pct"] else "-"
            f.write(f"| {i} | {g['name']} | {mc} | {steam} | {g['main_extra']}h | {g['hours_played']}h | {g['_score']:.1f} |\n")

    print(f"\nSalvo em '{csv_path}' e '{md_path}'")


def run(args: argparse.Namespace) -> None:
    steam_key = get_api_key("STEAM_API_KEY", "Steam API key")
    rawg_key  = get_api_key("RAWG_API_KEY",  "RAWG API key")

    cache = load_cache()
    cache, steam_games = build_library(steam_key, rawg_key, args.username, cache, refresh=args.refresh, verbose=args.verbose)

    rows = build_game_rows(cache, steam_games)
    rows = apply_filters(
        rows,
        genre=_csv_list(args.genre),
        genre_any=_csv_list(getattr(args, "genre_any", None)),
        exclude_genre=_csv_list(getattr(args, "exclude_genre", None)),
        progress=_progress_mode(args),
        category=args.category,
        min_hours=args.min_hours,
        max_hours=args.max_hours,
    )

    weights = _weights(args)
    for g in rows:
        g["_score"] = compute_score(g, args.sort, weights)

    rows.sort(key=lambda g: g["_score"], reverse=True)
    top = rows[:args.top]

    total_filtered = len(rows)
    print(f"\n{'='*60}")
    print(f" TOP {args.top} — sort: {args.sort}  ({len(top)} de {total_filtered} filtrados)")
    print(f"{'='*60}")
    print_table(top, args.sort, show_tags=args.show_tags)
    save_results(rows, args.output)


def main() -> None:
    args = parse_args()
    if args.tui:
        from tui import run_tui
        steam_key = get_api_key("STEAM_API_KEY", "Steam API key")
        rawg_key  = get_api_key("RAWG_API_KEY",  "RAWG API key")
        cache = load_cache()
        cache, steam_games = build_library(steam_key, rawg_key, args.username, cache, refresh=args.refresh, verbose=args.verbose)
        rows = build_game_rows(cache, steam_games)
        run_tui(rows)
        return
    if args.interactive:
        from interactive import run_interactive
        run_interactive(args)
        return
    run(args)


if __name__ == "__main__":
    main()
