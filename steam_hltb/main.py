import argparse

from .classify import build_game_rows
from .cli import _resolve_username, filters_from_args, parse_args
from .fetch import build_library, get_api_key, load_cache
from .report import list_available, list_collections_cmd, print_table, save_results
from .selection import select_games
from .steam_collections import load_collections


def run(args: argparse.Namespace) -> None:
    steam_key = get_api_key("STEAM_API_KEY", "Steam API key")
    username = _resolve_username(args)

    cache = load_cache()
    cache, steam_games = build_library(
        steam_key, username, cache, refresh=args.refresh, verbose=args.verbose
    )

    all_games = build_game_rows(cache, steam_games)
    rows = select_games(all_games, filters_from_args(args))
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
    run_tui(rows, filters_from_args(args))


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
