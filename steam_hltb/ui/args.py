import argparse
import os
import sys

from ..core.score import SORT_OPTIONS
from ..core.types import Filters
from ..i18n import LANGUAGES, set_language, t
from ..i18n.resolve import resolve_language


def parse_args() -> argparse.Namespace:
    from ..config.paths import config_path
    from ..config.setup import _read_env_file
    from ..i18n.argparse_hook import install

    # --lang is read straight from sys.argv: argparse needs the language
    # resolved before it can render a translated --help.
    set_language(resolve_language(sys.argv, os.environ, _read_env_file(config_path())))
    install()

    p = argparse.ArgumentParser(
        prog="howl",
        description=(t("args.description")),
        epilog=t("args.epilog"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--lang", choices=LANGUAGES, help=t("args.lang"))
    p.add_argument(
        "--username",
        default=os.environ.get("STEAM_USERNAME"),
        help=t("args.username"),
    )
    p.add_argument(
        "--sort",
        default="shortest",
        choices=SORT_OPTIONS,
        help=t("args.sort"),
    )
    p.add_argument("--genre", help=t("args.genre"))
    p.add_argument("--genre-any", help=t("args.genre_any"))
    p.add_argument("--exclude-genre", help=t("args.exclude_genre"))

    prog = p.add_mutually_exclusive_group()
    prog.add_argument("--not-started", action="store_true", help=t("args.not_started"))
    prog.add_argument("--in-progress", action="store_true", help=t("args.in_progress"))
    prog.add_argument(
        "--all-progress",
        action="store_true",
        help=t("args.all_progress"),
    )

    p.add_argument(
        "--category",
        default="all",
        choices=["all", "singleplayer", "coop"],
        help=t("args.category"),
    )
    p.add_argument("--min-hours", type=float, help=t("args.min_hours"))
    p.add_argument("--max-hours", type=float, help=t("args.max_hours"))
    p.add_argument(
        "--era",
        help=(t("args.era")),
    )
    p.add_argument("--top", type=int, default=10, help=t("args.top"))
    p.add_argument(
        "--output",
        default="output/howl",
        help=t("args.output"),
    )
    p.add_argument(
        "--weight-mc",
        type=float,
        default=0.5,
        help=t("args.weight_mc"),
    )
    p.add_argument(
        "--weight-steam",
        type=float,
        default=0.5,
        help=t("args.weight_steam"),
    )
    p.add_argument("--collection", help=t("args.collection"))
    p.add_argument(
        "--vdf-path",
        default=os.environ.get("STEAM_VDF_PATH", "sharedconfig.vdf"),
        help=(t("args.vdf_path")),
    )
    p.add_argument(
        "--show-finished",
        action="store_true",
        help=t("args.show_finished"),
    )
    p.add_argument(
        "--list-tags",
        action="store_true",
        help=t("args.list_tags"),
    )
    p.add_argument(
        "--list-genres",
        action="store_true",
        help=t("args.list_genres"),
    )
    p.add_argument(
        "--list-collections",
        action="store_true",
        help=t("args.list_collections"),
    )
    p.add_argument(
        "--refresh",
        action="store_true",
        help=t("args.refresh"),
    )
    p.add_argument(
        "--refresh-all",
        action="store_true",
        help=t("args.refresh_all"),
    )
    p.add_argument(
        "--migrate-cache",
        action="store_true",
        help=t("args.migrate_cache"),
    )
    p.add_argument(
        "--migrate-igdb",
        action="store_true",
        help=(t("args.migrate_igdb")),
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help=t("args.verbose"),
    )
    p.add_argument(
        "--show-tags",
        action="store_true",
        help=t("args.show_tags"),
    )
    p.add_argument("--interactive", action="store_true", help=t("args.interactive"))
    p.add_argument("--tui", action="store_true", help=t("args.tui"))
    p.add_argument("--setup", action="store_true", help=t("args.setup"))
    return p.parse_args()


def _resolve_username(args: argparse.Namespace) -> str:
    if args.username:
        username: str = args.username
        return username
    username = input("Steam username (profile vanity URL): ").strip()
    if not username:
        print("Error: username is required.", file=sys.stderr)
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
        print(f"Warning: weights sum to {total:.2f}, expected 1.0. Normalising.", file=sys.stderr)
        w = {k: v / total for k, v in w.items()}
    return w


def _csv_list(value: str | None) -> list[str] | None:
    if not value:
        return None
    result = [v.strip() for v in value.split(",") if v.strip()]
    return result or None


def filters_from_args(args: argparse.Namespace) -> Filters:
    return {
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
        "collection": args.collection,
        "eras": _csv_list(args.era),
    }
