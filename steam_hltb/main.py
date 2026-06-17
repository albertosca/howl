import argparse

from .classify import apply_filters, build_game_rows
from .cli import _csv_list, _progress_mode, _resolve_username, _weights, parse_args
from .fetch import build_library, get_api_key, load_cache
from .report import list_available, list_collections_cmd, print_table, save_results
from .score import compute_score
from .steam_collections import filter_collection, load_collections


def run(args: argparse.Namespace) -> None:
    steam_key = get_api_key("STEAM_API_KEY", "Steam API key")
    username = _resolve_username(args)

    cache = load_cache()
    cache, steam_games = build_library(
        steam_key, username, cache, refresh=args.refresh, verbose=args.verbose
    )

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
    top = rows[: args.top]

    total_filtered = len(rows)
    print(f"\n{'=' * 60}")
    print(f" TOP {args.top} — sort: {args.sort}  ({len(top)} de {total_filtered} filtrados)")
    if len(top) < args.top and total_filtered < args.top:
        print(f" ⚠  Apenas {total_filtered} jogos passaram nos filtros (pedido: {args.top})")
    print(f"{'=' * 60}")
    print_table(top, args.sort, show_tags=args.show_tags)
    save_results(rows, args.output)


def _run_tui(args: argparse.Namespace) -> None:
    from .tui import run_tui

    steam_key = get_api_key("STEAM_API_KEY", "Steam API key")
    username = _resolve_username(args)
    cache = load_cache()
    cache, steam_games = build_library(
        steam_key, username, cache, refresh=args.refresh, verbose=args.verbose
    )
    rows = build_game_rows(cache, steam_games)
    initial_filters = {
        "genre": _csv_list(args.genre),
        "genre_any": _csv_list(args.genre_any),
        "exclude_genre": _csv_list(args.exclude_genre),
        "progress": _progress_mode(args),
        "category": args.category,
        "min_hours": args.min_hours,
        "max_hours": args.max_hours,
        "sort": args.sort,
        "top": args.top,
        "weights": _weights(args),
        "vdf_path": args.vdf_path,
        "show_finished": args.show_finished,
        "eras": _csv_list(args.era),
    }
    run_tui(rows, initial_filters)


def main() -> None:
    from dotenv import load_dotenv

    from .paths import config_path

    load_dotenv(config_path())
    args = parse_args()

    if args.setup:
        from .setup import run_setup

        run_setup(verbose=args.verbose)
        return

    if args.migrate_cache:
        from .fetch import migrate_steam_details

        print("⚠  Isso pode demorar 15-30 min. Ctrl+C para interromper (progresso salvo).")
        migrate_steam_details(load_cache(), verbose=True)
        print("Migração concluída.")
        return

    if args.migrate_igdb:
        from .fetch import migrate_igdb_data

        cache = load_cache()
        migrate_igdb_data(cache, verbose=True)
        print("Migração IGDB concluída.")
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
        _run_tui(args)
        return

    if args.interactive:
        from .interactive import run_interactive

        run_interactive(args)
        return

    run(args)


if __name__ == "__main__":
    main()
