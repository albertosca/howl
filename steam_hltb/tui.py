from textual.app import App, ComposeResult
from textual.widgets import DataTable, Input, Select, Footer, Header, Label, Static, Checkbox
from textual.containers import Horizontal, Vertical
from textual.binding import Binding
from textual.reactive import reactive

from .classify import apply_filters, filter_name, ERA_LABELS
from .score import compute_score, SORT_OPTIONS


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


class SteamHLTBApp(App):
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

    BINDINGS = [
        Binding("q", "quit", "Sair"),
        Binding("f", "toggle_filters", "Filtros"),
        Binding("g", "toggle_genres", "Gêneros"),
        Binding("t", "toggle_tags", "Tags"),
        Binding("s", "save", "Salvar"),
    ]

    show_genres: reactive[bool] = reactive(True)
    show_tags: reactive[bool] = reactive(False)

    def __init__(self, all_games: list, initial_filters: dict | None = None):
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
        self._games: list = []

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
        rows = apply_filters(
            self.all_games,
            genre=self.filters["genre"],
            genre_any=self.filters["genre_any"],
            exclude_genre=self.filters["exclude_genre"],
            progress=self.filters["progress"],
            category=self.filters["category"],
            min_hours=self.filters["min_hours"],
            max_hours=self.filters["max_hours"],
            eras=self.filters.get("eras"),
        )
        rows = filter_name(rows, query=self.filters.get("name_query"))
        vdf_path = self.filters.get("vdf_path", "sharedconfig.vdf")
        if not self.filters.get("show_finished", False):
            from .steam_collections import exclude_finished
            rows = exclude_finished(rows, vdf_path)
        if self.filters.get("collection"):
            try:
                from .steam_collections import load_collections, filter_collection
                collection_map = load_collections(vdf_path)
                rows = filter_collection(rows, self.filters["collection"], collection_map)
            except Exception:
                pass
        sort_by = self.filters["sort"]
        weights = self.filters["weights"]
        for g in rows:
            g["_score"] = compute_score(g, sort_by, weights)
        rows.sort(key=lambda g: g["_score"], reverse=True)
        top_n = self.filters["top"]
        self._games = rows[:top_n]

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
                f"{g['main_extra']}h",
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
        self.query_one("#top-input", Input).value = str(self.filters["top"])
        sort_val = self.filters["sort"]
        if sort_val in SORT_OPTIONS:
            self.query_one("#sort-select", Select).value = sort_val
        progress = self.filters["progress"]
        if progress in ("default", "not_started", "in_progress", "all"):
            self.query_one("#progress-select", Select).value = progress
        category = self.filters["category"]
        if category in ("all", "singleplayer", "coop"):
            self.query_one("#category-select", Select).value = category
        if self.filters["genre"]:
            self.query_one("#genre-input", Input).value = ", ".join(self.filters["genre"])
        if self.filters["exclude_genre"]:
            self.query_one("#exclude-genre-input", Input).value = ", ".join(self.filters["exclude_genre"])
        if self.filters["min_hours"] is not None:
            self.query_one("#min-hours-input", Input).value = str(self.filters["min_hours"])
        if self.filters["max_hours"] is not None:
            self.query_one("#max-hours-input", Input).value = str(self.filters["max_hours"])
        col = self.filters.get("collection") or "todas"
        if col in ("todas", "Jogando", "Multiplayer"):
            self.query_one("#collection-select", Select).value = col
        # era checkboxes: se eras != None, desmarcar as que não estão na lista
        eras = self.filters.get("eras")
        if eras is not None:
            for era in ERA_LABELS:
                try:
                    cb = self.query_one(f"#{_era_id(era)}", Checkbox)
                    cb.value = era in eras
                except Exception:
                    pass

    def _read_filters_from_panel(self) -> None:
        try:
            raw = self.query_one("#name-input", Input).value.strip()
            self.filters["name_query"] = raw if raw else None
        except Exception:
            pass
        try:
            raw = self.query_one("#top-input", Input).value.strip()
            self.filters["top"] = int(raw) if raw.isdigit() else self.filters["top"]
        except Exception:
            pass
        try:
            val = self.query_one("#sort-select", Select).value
            if val and val in SORT_OPTIONS:
                self.filters["sort"] = val
        except Exception:
            pass
        try:
            raw = self.query_one("#genre-input", Input).value.strip()
            self.filters["genre"] = [v.strip() for v in raw.split(",") if v.strip()] or None
        except Exception:
            pass
        try:
            raw = self.query_one("#exclude-genre-input", Input).value.strip()
            self.filters["exclude_genre"] = [v.strip() for v in raw.split(",") if v.strip()] or None
        except Exception:
            pass
        try:
            val = self.query_one("#progress-select", Select).value
            if val and val in ("default", "not_started", "in_progress", "all"):
                self.filters["progress"] = val
        except Exception:
            pass
        try:
            val = self.query_one("#category-select", Select).value
            if val and val in ("all", "singleplayer", "coop"):
                self.filters["category"] = val
        except Exception:
            pass
        try:
            raw = self.query_one("#min-hours-input", Input).value.strip()
            self.filters["min_hours"] = float(raw) if raw else None
        except Exception:
            pass
        try:
            raw = self.query_one("#max-hours-input", Input).value.strip()
            self.filters["max_hours"] = float(raw) if raw else None
        except Exception:
            pass
        try:
            val = self.query_one("#collection-select", Select).value
            self.filters["collection"] = None if val == "todas" else val
        except Exception:
            pass
        # era checkboxes
        try:
            checked = []
            for era in ERA_LABELS:
                cb = self.query_one(f"#era-{era}", Checkbox)
                if cb.value:
                    checked.append(era)
            # None = todas marcadas (sem filtro); lista = subconjunto
            self.filters["eras"] = None if len(checked) == len(ERA_LABELS) else (checked or None)
        except Exception:
            pass

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
        from .main import save_results
        save_results(self._games, "how_long_to_beat_output")
        self.notify("Salvo em how_long_to_beat_output.csv e .md")


def run_tui(all_games: list, initial_filters: dict | None = None) -> None:
    SteamHLTBApp(all_games, initial_filters).run()
