from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich import box

from classify import apply_filters
from score import compute_score, SORT_OPTIONS

console = Console()

DEFAULT_FILTERS = {
    "genre": None,
    "genre_any": None,
    "exclude_genre": None,
    "progress": "default",
    "category": "all",
    "min_hours": None,
    "max_hours": None,
    "sort": "hltb_short",
    "top": 10,
    "weights": {"mc": 0.5, "steam": 0.5},
}


def _render(games: list, filters: dict) -> None:
    console.clear()

    active = []
    if filters["genre"]:         active.append(f"gênero={','.join(filters['genre'])}")
    if filters["genre_any"]:     active.append(f"genre-any={','.join(filters['genre_any'])}")
    if filters["exclude_genre"]: active.append(f"excluir={','.join(filters['exclude_genre'])}")
    if filters["progress"] != "default": active.append(f"progresso={filters['progress']}")
    if filters["category"] != "all":     active.append(f"categoria={filters['category']}")
    if filters["min_hours"]:     active.append(f"min={filters['min_hours']}h")
    if filters["max_hours"]:     active.append(f"max={filters['max_hours']}h")
    active.append(f"sort={filters['sort']}")

    console.print(f"[bold cyan]Filtros:[/] {' | '.join(active) if active else 'nenhum'}")
    console.print(f"[bold cyan]Jogos:[/] {len(games)} após filtros\n")

    table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold magenta")
    table.add_column("#",       justify="right", width=4)
    table.add_column("Nome",    width=45)
    table.add_column("MC",      justify="right", width=4)
    table.add_column("Steam",   justify="right", width=7)
    table.add_column("HLTB",    justify="right", width=6)
    table.add_column("Jogadas", justify="right", width=8)
    table.add_column("Score",   justify="right", width=8)

    for i, g in enumerate(games[:filters["top"]], 1):
        mc    = str(g["metacritic"]) if g["metacritic"] else "-"
        steam = f"{g['steam_pct']}%" if g["steam_pct"] else "-"
        table.add_row(
            str(i),
            g["name"],
            mc,
            steam,
            f"{g['main_extra']}h",
            f"{g['hours_played']}h",
            f"{g['_score']:.1f}",
        )

    console.print(table)
    console.print("[bold]\\[f][/] filtros  [bold]\\[s][/] salvar  [bold]\\[q][/] sair")


def _apply_and_score(all_games: list, filters: dict) -> list:
    rows = apply_filters(
        all_games,
        genre=filters["genre"],
        genre_any=filters["genre_any"],
        exclude_genre=filters["exclude_genre"],
        progress=filters["progress"],
        category=filters["category"],
        min_hours=filters["min_hours"],
        max_hours=filters["max_hours"],
    )
    for g in rows:
        g["_score"] = compute_score(g, filters["sort"], filters["weights"])
    rows.sort(key=lambda g: g["_score"], reverse=True)
    return rows


def _csv_or_none(value: str) -> list | None:
    if not value.strip():
        return None
    return [v.strip() for v in value.split(",") if v.strip()]


def _edit_filters(filters: dict) -> dict:
    console.print("\n[bold yellow]Editar filtros[/] (Enter = manter atual)\n")

    def _prompt(label, current):
        return Prompt.ask(f"  {label}", default=str(current) if current else "")

    genre_raw = _prompt("Gêneros obrigatórios (vírgula-sep)", ",".join(filters["genre"]) if filters["genre"] else "")
    any_raw   = _prompt("Qualquer gênero (vírgula-sep)", ",".join(filters["genre_any"]) if filters["genre_any"] else "")
    excl_raw  = _prompt("Excluir gêneros (vírgula-sep)", ",".join(filters["exclude_genre"]) if filters["exclude_genre"] else "")
    progress  = _prompt(f"Progresso {['default','not_started','in_progress','all']}", filters["progress"])
    category  = _prompt("Categoria [all/singleplayer/coop]", filters["category"])
    min_h     = _prompt("Min horas (vazio=sem)", str(filters["min_hours"]) if filters["min_hours"] else "")
    max_h     = _prompt("Max horas (vazio=sem)", str(filters["max_hours"]) if filters["max_hours"] else "")
    sort_by   = _prompt(f"Sort [{'/'.join(SORT_OPTIONS)}]", filters["sort"])
    top_raw   = _prompt("Top N", str(filters["top"]))

    return {
        "genre":         _csv_or_none(genre_raw),
        "genre_any":     _csv_or_none(any_raw),
        "exclude_genre": _csv_or_none(excl_raw),
        "progress":      progress if progress in ("default", "not_started", "in_progress", "all") else "default",
        "category":      category if category in ("all", "singleplayer", "coop") else "all",
        "min_hours":     float(min_h) if min_h else None,
        "max_hours":     float(max_h) if max_h else None,
        "sort":          sort_by if sort_by in SORT_OPTIONS else "hltb_short",
        "top":           int(top_raw) if top_raw.isdigit() else 10,
        "weights":       filters["weights"],
    }


def run_tui(all_games: list) -> None:
    filters = DEFAULT_FILTERS.copy()
    games = _apply_and_score(all_games, filters)
    _render(games, filters)

    while True:
        cmd = Prompt.ask("").strip().lower()

        if cmd == "q":
            console.print("[bold]Saindo.[/]")
            break

        if cmd == "f":
            filters = _edit_filters(filters)
            games = _apply_and_score(all_games, filters)
            _render(games, filters)

        elif cmd == "s":
            from main import save_results
            output = Prompt.ask("Nome base do arquivo", default="how_long_to_beat_output")
            save_results(games, output)
            console.print("[green]Salvo![/]")

        else:
            _render(games, filters)
