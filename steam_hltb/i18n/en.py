_EPILOG = """
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
"""

MESSAGES: dict[str, str] = {
    "test.plain": "plain english",
    "test.interpolated": "{count} items",
    "report.header": " TOP {top} — sort: {sort}  ({shown} of {total} filtered)",
    "report.too_few": " ⚠  Only {total} games passed the filters (requested: {top})",
    "report.col_name": "Name",
    "report.col_year": "Year",
    "report.col_played": "Played",
    "report.col_score": "Score",
    "report.no_collections": "No collections found. Check --vdf-path.",
    "report.available_collections": " Available collections ({count} unique)",
    "report.no_items": "No {field} found in cache. Try --refresh or --migrate-cache.",
    "report.available_items": " Available {field} ({count} unique)",
    "report.saved": "\nSaved to '{csv}' and '{md}'",
    "report.interactive_header": "\n=== Interactive Mode ===\n",
    "migrate.slow_warning": "⚠  This can take 15-30 min. Ctrl+C to interrupt (progress is saved).",
    "migrate.done": "Migration complete.",
    "migrate.igdb_done": "IGDB migration complete.",
    "args.description": (
        "HOWL — Hoard Optimizer, What to Launch. Ranks your Steam library by quality "
        "× time invested."
    ),
    "args.lang": "Interface language (default: from setup, environment or system locale)",
    "args.epilog": _EPILOG,
    "args.username": "Steam profile vanity URL (or STEAM_USERNAME env var)",
    "args.sort": "Ranking criterion (default: %(default)s)",
    "args.genre": "Required genres, comma-separated (e.g. 'action,rpg')",
    "args.genre_any": "At least one of these genres (comma-separated)",
    "args.exclude_genre": "Genres to exclude (comma-separated)",
    "args.not_started": "Only games never played (0h)",
    "args.in_progress": "Only games started but not completed",
    "args.all_progress": "No progress filter (includes completed games)",
    "args.category": "Filter by game type (default: %(default)s)",
    "args.min_hours": "Minimum HLTB duration in hours",
    "args.max_hours": "Maximum HLTB duration in hours",
    "args.era": (
        "Release eras (comma-separated): pre-2005, 2005-2010, 2010-2015, 2015-2020, 2020+, unknown"
    ),
    "args.top": "Number of games to show (default: %(default)s)",
    "args.output": "Base name for .csv and .md output files (default: %(default)s)",
    "args.weight_mc": "Metacritic weight in composite score (default: %(default)s)",
    "args.weight_steam": "Steam review weight in composite score (default: %(default)s)",
    "args.collection": "Filter by Steam collection name (e.g. 'Playing', 'Multiplayer')",
    "args.vdf_path": (
        "Path to Steam's sharedconfig.vdf (default: STEAM_VDF_PATH env or sharedconfig.vdf)"
    ),
    "args.show_finished": "Include games from the 'Finished' collection (excluded by default)",
    "args.list_tags": "List all Steam categories available in cache and exit",
    "args.list_genres": "List all genres available in cache and exit",
    "args.list_collections": "List Steam collections available in the VDF and exit",
    "args.refresh": "Fetch new games from Steam library (same as default behaviour)",
    "args.refresh_all": "Re-fetch data for all games, including cached ones (slow)",
    "args.migrate_cache": (
        "Fill steam.genres/categories/release_year for incomplete cache entries (~15-30 min)"
    ),
    "args.migrate_igdb": (
        "Fetch IGDB data for games without Metacritic in cache (requires "
        "IGDB_CLIENT_ID and IGDB_CLIENT_SECRET)"
    ),
    "args.verbose": "Show detailed progress for all games (including cached)",
    "args.show_tags": "Show Steam categories in the table (in addition to genres)",
    "args.interactive": "Interactive mode via prompts",
    "args.tui": "Open interactive visual interface (htop-style)",
    "args.setup": "Configure environment variables interactively",
    "setup.legacy_found": "\n  Found a legacy .env at {path}",
    "setup.legacy_now_reads": "  From now on howl reads from {path}.",
    "setup.legacy_migrated": "  Migrated to {path}",
    "setup.legacy_remove_hint": "  You can remove the old one whenever: rm {path}",
    "setup.header": "\n=== howl setup ===\n",
    "setup.igdb_intro": "\n  IGDB (optional — scores for delisted/Metacritic-less games):",
    "setup.igdb_step1": "  1. Go to https://dev.twitch.tv/console and create an app",
    "setup.igdb_step2": "  2. Category: Website Integration, OAuth Redirect URL: http://localhost",
    "setup.igdb_step3": "  3. Copy the Client ID and generate a Client Secret",
    "setup.summary": "\n--- Summary ---",
    "setup.saved": "\n  Saved to {path}",
    "setup.complete": "\nSetup complete! Run 'howl' to get started.\n",
    "setup.already_has": "\n  {path} already has values for: {keys}",
    "setup.cancelled": "\n\n  Setup cancelled.",
    "setup.unexpected_error": "\n  Unexpected error during setup: {error}",
    "setup.error_logged": "  Details logged to {path}",
    "setup.keeping_existing": "  Keeping existing values.",
    "setup.prompt_igdb_id": "  IGDB Client ID: ",
    "setup.prompt_igdb_secret": "  IGDB Client Secret: ",
    "setup.prompt_migrate": "  Migrate there now? [Y/n] ",
    "setup.prompt_igdb_now": "  Configure IGDB now? [y/N] ",
    "setup.prompt_overwrite": "  Overwrite these values? [y/N] ",
    "setup.api_key_title": "\n  STEAM_API_KEY:",
    "setup.api_key_step1": "  1. Go to https://steamcommunity.com/dev/apikey",
    "setup.api_key_step2": "  2. Log in with your Steam account",
    "setup.api_key_step3": "  3. Fill 'Domain Name' with any value (e.g. localhost)",
    "setup.api_key_step4": "  4. Copy the generated key",
    "setup.username_title": "\n  STEAM_USERNAME:",
    "setup.username_explain": "  This is the vanity URL of your Steam profile.",
    "setup.username_example": (
        "  e.g. steamcommunity.com/id/gabelogannewell → username is gabelogannewell"
    ),
    "setup.vdf_title": "\n  STEAM_VDF_PATH (optional — required for collection filters):",
    "setup.vdf_none_found": "  No VDF detected automatically.",
    "setup.api_key_present": "  STEAM_API_KEY already set (***{suffix})",
    "setup.validating": "  Validating...",
    "setup.key_invalid": "invalid or no internet.",
    "setup.username_present": "\n  STEAM_USERNAME already set: {username}",
    "setup.username_not_found": "not found.",
    "setup.vdf_present": "\n  STEAM_VDF_PATH already set: {path}",
    "setup.vdf_found": "  Found {count} VDF file(s):",
    "setup.debug_valve": "\n  [debug] GET ResolveVanityURL (valve) → HTTP {status}",
    "setup.debug_resolve": "\n  [debug] GET ResolveVanityURL ({host}) → HTTP {status}",
    "setup.key_required": "  Key is required.",
    "setup.key_unvalidated": "  Proceeding with the provided key (not validated).",
    "setup.username_required": "  Username is required.",
    "setup.username_ok": "OK (SteamID: {steamid})",
    "setup.username_unvalidated": "  Proceeding with the provided username (not validated).",
    "setup.prompt_vdf_manual": "  Paste the path manually (or Enter to skip): ",
    "setup.debug_key_neterr": "\n  [debug] network error validating key: {error}",
    "setup.debug_user_neterr": "\n  [debug] network error validating username: {error}",
    "setup.prompt_key": "\n  Paste your key: ",
    "setup.prompt_username": "\n  Your username: ",
    "setup.prompt_vdf_choice": "  Choose [1-{max}] or Enter to skip: ",
    "setup.prompt_use_existing": "  Use existing? [Y/n] ",
    "setup.prompt_retry": "  Try again? [Y/n] ",
    "setup.answer_no": "  answer_no",
    "setup.answer_yes": "  answer_yes",
}
