import sys
from score import SORT_OPTIONS
from classify import apply_filters
from score import compute_score


def _ask(prompt: str, options: list = None, default: str = None) -> str:
    if options:
        opts_str = "/".join(options)
        full_prompt = f"{prompt} [{opts_str}]"
        if default:
            full_prompt += f" (default: {default})"
    else:
        full_prompt = prompt
        if default:
            full_prompt += f" (default: {default})"
    full_prompt += ": "
    value = input(full_prompt).strip()
    return value if value else (default or "")


def _csv_or_none(value: str) -> list | None:
    if not value:
        return None
    return [v.strip() for v in value.split(",") if v.strip()]


def run_interactive(base_args) -> None:
    from main import _weights, save_results, print_table

    print("\n=== Modo Interativo ===\n")

    genre_raw     = _ask("Gêneros obrigatórios (vírgula-sep, vazio=todos)", default="")
    genre_any_raw = _ask("Qualquer um desses gêneros (vírgula-sep, vazio=ignorar)", default="")
    excl_raw      = _ask("Excluir gêneros (vírgula-sep, vazio=nenhum)", default="")

    progress = _ask(
        "Filtro de progresso",
        options=["default", "not_started", "in_progress", "all"],
        default="default",
    )

    category = _ask("Categoria", options=["all", "singleplayer", "coop"], default="all")

    min_hours_raw = _ask("Mínimo de horas (vazio=sem limite)", default="")
    max_hours_raw = _ask("Máximo de horas (vazio=sem limite)", default="")

    sort_by = _ask("Ordenar por", options=SORT_OPTIONS, default="hltb_short")

    top_raw = _ask("Quantos jogos mostrar", default="10")
    top = int(top_raw) if top_raw.isdigit() else 10

    output = _ask("Nome base do arquivo de saída", default="how_long_to_beat_output")

    from fetch import get_api_key, load_cache, build_library
    from classify import build_game_rows

    steam_key = get_api_key("STEAM_API_KEY", "Steam API key")
    rawg_key  = get_api_key("RAWG_API_KEY",  "RAWG API key")
    cache = load_cache()
    cache, steam_games = build_library(steam_key, rawg_key, base_args.username, cache)
    rows = build_game_rows(cache, steam_games)

    rows = apply_filters(
        rows,
        genre=_csv_or_none(genre_raw),
        genre_any=_csv_or_none(genre_any_raw),
        exclude_genre=_csv_or_none(excl_raw),
        progress=progress,
        category=category,
        min_hours=float(min_hours_raw) if min_hours_raw else None,
        max_hours=float(max_hours_raw) if max_hours_raw else None,
    )

    weights = _weights(base_args)
    for g in rows:
        g["_score"] = compute_score(g, sort_by, weights)

    rows.sort(key=lambda g: g["_score"], reverse=True)
    top_games = rows[:top]

    print(f"\n{'='*60}")
    print(f" TOP {top} — sort: {sort_by}")
    print(f"{'='*60}")
    print_table(top_games, sort_by)
    save_results(rows, output)
