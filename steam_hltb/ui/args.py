import argparse
import os
import sys

from ..core.score import SORT_OPTIONS
from ..core.types import Filters


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="howl",
        description=(
            "HOWL — Hoard Optimizer, What to Launch. "
            "Ranks your Steam library by quality × time invested."
        ),
        epilog="""
Examples:
  howl --username mysteamid --top 25 --sort rated
  howl --username mysteamid --genre "action,rpg" --not-started --top 10
  howl --username mysteamid --tui --sort shortest
  howl --username mysteamid --era "2010-2015,2015-2020" --sort quick-wins

  Tip: set STEAM_USERNAME in your environment to avoid passing --username every time.

Input formats:
  --genre / --genre-any / --exclude-genre  comma-separated names (e.g. "action,rpg")
  --sort      shortest | longest | rated | loved | quick-wins | hidden-gems | composto
  --era       comma-separated: pre-2005, 2005-2010, 2010-2015, 2015-2020, 2020+, unknown
  --weight-mc / --weight-steam             weights 0.0-1.0 that sum to 1.0 (e.g. 0.6 and 0.4)
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--username",
        default=os.environ.get("STEAM_USERNAME"),
        help="Steam profile vanity URL (or STEAM_USERNAME env var)",
    )
    p.add_argument(
        "--sort",
        default="shortest",
        choices=SORT_OPTIONS,
        help="Ranking criterion (default: %(default)s)",
    )
    p.add_argument("--genre", help="Required genres, comma-separated (e.g. 'action,rpg')")
    p.add_argument("--genre-any", help="At least one of these genres (comma-separated)")
    p.add_argument("--exclude-genre", help="Genres to exclude (comma-separated)")

    prog = p.add_mutually_exclusive_group()
    prog.add_argument("--not-started", action="store_true", help="Only games never played (0h)")
    prog.add_argument(
        "--in-progress", action="store_true", help="Only games started but not completed"
    )
    prog.add_argument(
        "--all-progress",
        action="store_true",
        help="No progress filter (includes completed games)",
    )

    p.add_argument(
        "--category",
        default="all",
        choices=["all", "singleplayer", "coop"],
        help="Filter by game type (default: %(default)s)",
    )
    p.add_argument("--min-hours", type=float, help="Minimum HLTB duration in hours")
    p.add_argument("--max-hours", type=float, help="Maximum HLTB duration in hours")
    p.add_argument(
        "--era",
        help=(
            "Release eras (comma-separated): "
            "pre-2005, 2005-2010, 2010-2015, 2015-2020, 2020+, unknown"
        ),
    )
    p.add_argument(
        "--top", type=int, default=10, help="Number of games to show (default: %(default)s)"
    )
    p.add_argument(
        "--output",
        default="output/howl",
        help="Base name for .csv and .md output files (default: %(default)s)",
    )
    p.add_argument(
        "--weight-mc",
        type=float,
        default=0.5,
        help="Metacritic weight in composite score (default: %(default)s)",
    )
    p.add_argument(
        "--weight-steam",
        type=float,
        default=0.5,
        help="Steam review weight in composite score (default: %(default)s)",
    )
    p.add_argument(
        "--collection", help="Filter by Steam collection name (e.g. 'Playing', 'Multiplayer')"
    )
    p.add_argument(
        "--vdf-path",
        default=os.environ.get("STEAM_VDF_PATH", "sharedconfig.vdf"),
        help=("Path to Steam's sharedconfig.vdf (default: STEAM_VDF_PATH env or sharedconfig.vdf)"),
    )
    p.add_argument(
        "--show-finished",
        action="store_true",
        help="Include games from the 'Finished' collection (excluded by default)",
    )
    p.add_argument(
        "--list-tags",
        action="store_true",
        help="List all Steam categories available in cache and exit",
    )
    p.add_argument(
        "--list-genres",
        action="store_true",
        help="List all genres available in cache and exit",
    )
    p.add_argument(
        "--list-collections",
        action="store_true",
        help="List Steam collections available in the VDF and exit",
    )
    p.add_argument(
        "--refresh",
        action="store_true",
        help="Fetch new games from Steam library (same as default behaviour)",
    )
    p.add_argument(
        "--refresh-all",
        action="store_true",
        help="Re-fetch data for all games, including cached ones (slow)",
    )
    p.add_argument(
        "--migrate-cache",
        action="store_true",
        help="Fill steam.genres/categories/release_year for incomplete cache entries (~15-30 min)",
    )
    p.add_argument(
        "--migrate-igdb",
        action="store_true",
        help=(
            "Fetch IGDB data for games without Metacritic in cache "
            "(requires IGDB_CLIENT_ID and IGDB_CLIENT_SECRET)"
        ),
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed progress for all games (including cached)",
    )
    p.add_argument(
        "--show-tags",
        action="store_true",
        help="Show Steam categories in the table (in addition to genres)",
    )
    p.add_argument("--interactive", action="store_true", help="Interactive mode via prompts")
    p.add_argument(
        "--tui", action="store_true", help="Open interactive visual interface (htop-style)"
    )
    p.add_argument(
        "--setup", action="store_true", help="Configure environment variables interactively"
    )
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
