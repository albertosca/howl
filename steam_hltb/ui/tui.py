from typing import Any, ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Checkbox, DataTable, Footer, Header, Input, Label, Select, Static

from ..core.classify import ERA_LABELS
from ..core.score import SORT_OPTIONS
from ..core.selection import select_games


def _era_id(era: str) -> str:
    """Sanitiza era label para uso como ID Textual (sem +, sem espaços)."""
    return "era-" + era.replace("+", "plus").replace(" ", "_")


class FilterPanel(Vertical):
    DEFAULT_CSS = """
    FilterPanel {
        width: 34;
        background: $panel;
        border-left: solid $accent;
        padding: 1 2;
        display: none;
        overflow-y: auto;
    }
    FilterPanel Label {
        margin-top: 1;
        color: $text-muted;
    }
    FilterPanel Input {
        margin-bottom: 0;
    }
    FilterPanel Checkbox {
        margin: 0;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("── Filtros ──────────────")
        yield Label("Nome (fuzzy)")
        yield Input(placeholder="ex: hl2, por", id="name-input")
        yield Label("Sort")
        yield Select(
            [(opt, opt) for opt in SORT_OPTIONS],
            id="sort-select",
            value="shortest",
        )
        yield Label("Top N")
        yield Input(value="10", id="top-input")
        yield Label("Gêneros (vírgula-sep)")
        yield Input(placeholder="action, rpg", id="genre-input")
        yield Label("Excluir gêneros")
        yield Input(placeholder="sports", id="exclude-genre-input")
        yield Label("Progress")
        yield Select(
            [
                ("default", "default"),
                ("not_started", "not_started"),
                ("in_progress", "in_progress"),
                ("all", "all"),
            ],
            id="progress-select",
            value="default",
        )
        yield Label("Categoria")
        yield Select(
            [("all", "all"), ("singleplayer", "singleplayer"), ("coop", "coop")],
            id="category-select",
            value="all",
        )
        yield Label("Min horas")
        yield Input(placeholder="0", id="min-hours-input")
        yield Label("Max horas")
        yield Input(placeholder="100", id="max-hours-input")
        yield Label("Coleção")
        yield Select(
            [
                ("todas", "todas"),
                ("Jogando", "Jogando"),
                ("Multiplayer", "Multiplayer"),
            ],
            id="collection-select",
            value="todas",
        )
        yield Label("Era de lançamento")
        for era in ERA_LABELS:
            yield Checkbox(era, value=True, id=_era_id(era))


class SteamHLTBApp(App[None]):
    CSS = """
    Screen {
        layout: vertical;
    }
    #main-container {
        layout: horizontal;
        height: 1fr;
    }
    #game-table {
        width: 1fr;
    }
    #status-bar {
        height: 1;
        background: $panel;
        color: $text-muted;
        padding: 0 1;
    }
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("q", "quit", "Sair"),
        Binding("f", "toggle_filters", "Filtros"),
        Binding("g", "toggle_genres", "Gêneros"),
        Binding("t", "toggle_tags", "Tags"),
        Binding("s", "save", "Salvar"),
    ]

    show_genres: reactive[bool] = reactive(True)
    show_tags: reactive[bool] = reactive(False)

    def __init__(
        self, all_games: list[dict[str, Any]], initial_filters: dict[str, Any] | None = None
    ):
        super().__init__()
        self.all_games = all_games
        self.filters = (initial_filters or {}).copy()
        self.filters.setdefault("genre", None)
        self.filters.setdefault("genre_any", None)
        self.filters.setdefault("exclude_genre", None)
        self.filters.setdefault("progress", "default")
        self.filters.setdefault("category", "all")
        self.filters.setdefault("min_hours", None)
        self.filters.setdefault("max_hours", None)
        self.filters.setdefault("sort", "shortest")
        self.filters.setdefault("top", 10)
        self.filters.setdefault("weights", {"mc": 0.5, "steam": 0.5})
        self.filters.setdefault("vdf_path", "sharedconfig.vdf")
        self.filters.setdefault("show_finished", False)
        self.filters.setdefault("collection", None)
        self.filters.setdefault("name_query", None)
        self.filters.setdefault("eras", None)  # None = todas as eras
        self._games: list[dict[str, Any]] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Horizontal(id="main-container"):
            yield DataTable(id="game-table", cursor_type="row")
            yield FilterPanel(id="filter-panel")
        yield Static("", id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        self._setup_columns()
        self._sync_panel_to_filters()
        self._rebuild_table()

    def _setup_columns(self) -> None:
        table = self.query_one(DataTable)
        table.clear(columns=True)
        table.add_column("#", width=4)
        table.add_column("Nome", width=38)
        table.add_column("Ano", width=5)
        table.add_column("MC", width=5)
        table.add_column("Steam", width=7)
        table.add_column("HLTB", width=6)
        table.add_column("Jog", width=6)
        table.add_column("Score", width=7)
        if self.show_genres:
            table.add_column("Gêneros", width=22)
        if self.show_tags:
            table.add_column("Tags", width=22)

    def _rebuild_table(self) -> None:
        rows = select_games(self.all_games, self.filters)
        self._games = rows[: self.filters["top"]]
        sort_by = self.filters["sort"]

        table = self.query_one(DataTable)
        table.clear()
        for i, g in enumerate(self._games, 1):
            ano = str(g.get("release_year")) if g.get("release_year") else "-"
            mc = str(g["metacritic"]) if g["metacritic"] else "-"
            steam = f"{g['steam_pct']}%" if g["steam_pct"] else "-"
            row_data = [
                str(i),
                g["name"],
                ano,
                mc,
                steam,
                f"{g['main_extra']}h" if g.get("main_extra") else "-",
                f"{g['hours_played']}h",
                f"{g['_score']:.1f}",
            ]
            if self.show_genres:
                genres = g.get("genres", [])
                row_data.append(", ".join(genres[:4]) if genres else "-")
            if self.show_tags:
                tags = g.get("tags", [])
                row_data.append(", ".join(tags[:4]) if tags else "-")
            table.add_row(*row_data)

        self.query_one("#status-bar", Static).update(
            f" Mostrando {len(self._games)} de {len(rows)} filtrados · sort: {sort_by}"
        )

    def _sync_panel_to_filters(self) -> None:
        f = self.filters
        self.query_one("#top-input", Input).value = str(f["top"])
        self.query_one("#sort-select", Select).value = f["sort"]
        self.query_one("#progress-select", Select).value = f["progress"]
        self.query_one("#category-select", Select).value = f["category"]
        if f["genre"]:
            self.query_one("#genre-input", Input).value = ", ".join(f["genre"])
        if f["exclude_genre"]:
            self.query_one("#exclude-genre-input", Input).value = ", ".join(f["exclude_genre"])
        if f["min_hours"] is not None:
            self.query_one("#min-hours-input", Input).value = str(f["min_hours"])
        if f["max_hours"] is not None:
            self.query_one("#max-hours-input", Input).value = str(f["max_hours"])
        # --collection é livre; só pré-seleciona se for uma opção do Select
        collection = f.get("collection") or "todas"
        if collection in ("todas", "Jogando", "Multiplayer"):
            self.query_one("#collection-select", Select).value = collection
        # eras != None → desmarca as épocas fora da lista
        eras = f.get("eras")
        if eras is not None:
            for era in ERA_LABELS:
                self.query_one(f"#{_era_id(era)}", Checkbox).value = era in eras

    def _read_filters_from_panel(self) -> None:
        f = self.filters
        f["name_query"] = self.query_one("#name-input", Input).value.strip() or None
        top_raw = self.query_one("#top-input", Input).value.strip()
        f["top"] = int(top_raw) if top_raw.isdigit() else f["top"]
        f["sort"] = self.query_one("#sort-select", Select).value
        genre_raw = self.query_one("#genre-input", Input).value.strip()
        f["genre"] = [v.strip() for v in genre_raw.split(",") if v.strip()] or None
        excl_raw = self.query_one("#exclude-genre-input", Input).value.strip()
        f["exclude_genre"] = [v.strip() for v in excl_raw.split(",") if v.strip()] or None
        f["progress"] = self.query_one("#progress-select", Select).value
        f["category"] = self.query_one("#category-select", Select).value
        min_raw = self.query_one("#min-hours-input", Input).value.strip()
        f["min_hours"] = float(min_raw) if min_raw else None
        max_raw = self.query_one("#max-hours-input", Input).value.strip()
        f["max_hours"] = float(max_raw) if max_raw else None
        collection = self.query_one("#collection-select", Select).value
        f["collection"] = None if collection == "todas" else collection
        checked = [e for e in ERA_LABELS if self.query_one(f"#{_era_id(e)}", Checkbox).value]
        # None = todas marcadas (sem filtro); lista = subconjunto
        f["eras"] = None if len(checked) == len(ERA_LABELS) else (checked or None)

    def on_input_changed(self, _: Input.Changed) -> None:
        self._read_filters_from_panel()
        self._rebuild_table()

    def on_select_changed(self, _: Select.Changed) -> None:
        self._read_filters_from_panel()
        self._rebuild_table()

    def on_checkbox_changed(self, _: Checkbox.Changed) -> None:
        self._read_filters_from_panel()
        self._rebuild_table()

    def watch_show_genres(self, _: bool) -> None:
        self._setup_columns()
        self._rebuild_table()

    def watch_show_tags(self, _: bool) -> None:
        self._setup_columns()
        self._rebuild_table()

    def action_toggle_filters(self) -> None:
        panel = self.query_one(FilterPanel)
        panel.display = not panel.display

    def action_toggle_genres(self) -> None:
        self.show_genres = not self.show_genres

    def action_toggle_tags(self) -> None:
        self.show_tags = not self.show_tags

    def action_save(self) -> None:
        from .report import save_results

        save_results(self._games, "output/howl")
        self.notify("Salvo em output/howl.csv e .md")


def run_tui(all_games: list[dict[str, Any]], initial_filters: dict[str, Any] | None = None) -> None:
    SteamHLTBApp(all_games, initial_filters).run()
