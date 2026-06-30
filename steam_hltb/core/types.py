"""Domain aliases for howl."""

from typing import Any

# A "game row": produced by classify.build_game_rows and consumed by filters,
# scoring, selection and presentation. dict[str, Any] rather than TypedDict
# because fields are dynamic — arbitrary overrides and `_score` added after build.
Game = dict[str, Any]

# Filter configuration derived from CLI args (cli.filters_from_args),
# consumed by selection.select_games and the TUI.
Filters = dict[str, Any]
