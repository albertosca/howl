"""Aliases de domínio do howl."""

from typing import Any

# Uma "linha de jogo": produzida por classify.build_game_rows e consumida pelos
# filtros, scoring, seleção e apresentação. É dict[str, Any] (e não um TypedDict)
# porque os campos são dinâmicos — overrides arbitrários e `_score` adicionado
# depois da construção.
Game = dict[str, Any]

# Configuração de filtros derivada dos args da CLI (cli.filters_from_args),
# consumida por selection.select_games e pela TUI.
Filters = dict[str, Any]
