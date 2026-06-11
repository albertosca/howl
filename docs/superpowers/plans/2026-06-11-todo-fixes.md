# TODO Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Corrigir 5 itens do TODO: verbose scan, --help claro, gêneros/tags na tabela CLI, aviso top N, e TUI htop-like com Textual.

**Architecture:** Mudanças independentes em `fetch.py` e `main.py` para os itens 1–3; reescrita completa de `tui.py` com Textual para o item 5. Cada task produz código testado e commitado.

**Tech Stack:** Python 3.11+, pytest, rich (existente), textual (nova dep)

---

## Mapa de arquivos

| Arquivo | O que muda |
|---------|-----------|
| `fetch.py` | `build_library()` ganha `verbose: bool = False` |
| `main.py` | `--verbose`, `--show-tags`, help melhorado, `print_table()` com gêneros/tags, aviso top N, passa filtros iniciais pro TUI |
| `tui.py` | Reescrita completa com Textual |
| `requirements.txt` | + `textual` |
| `tests/test_fetch.py` | Testes de verbose |
| `tests/test_main.py` | Testes de print_table, top N warning, parse_args |

---

## Task 1: Flag `--verbose` em `build_library()`

**Files:**
- Modify: `fetch.py` — `build_library()` recebe `verbose=False`
- Modify: `main.py` — adiciona `--verbose`/`-v`, passa para `build_library()`
- Test: `tests/test_fetch.py`

- [ ] **Step 1: Escrever os testes que vão falhar**

Adicionar ao final de `tests/test_fetch.py`:

```python
def test_build_library_verbose_false_hides_cache_lines(capsys, monkeypatch):
    monkeypatch.setattr("fetch.resolve_steamid", lambda key, user: "76561198000000")
    monkeypatch.setattr("fetch.get_steam_games", lambda key, sid: [
        {"name": "Half-Life 2", "appid": 220, "hours_played": 1.0}
    ])
    monkeypatch.setattr("fetch.save_cache", lambda c: None)

    cache = {
        "Half-Life 2": {
            "hltb": {"game_name": "Half-Life 2", "main_story": 12, "main_extra": 15, "completionist": 19},
            "rawg": None,
            "steam": {"appid": 220},
        }
    }

    import fetch
    fetch.build_library("key", "rawg", "user", cache, verbose=False)

    out = capsys.readouterr().out
    assert "[1/1] Half-Life 2 (cache)" not in out


def test_build_library_verbose_true_shows_cache_lines(capsys, monkeypatch):
    monkeypatch.setattr("fetch.resolve_steamid", lambda key, user: "76561198000000")
    monkeypatch.setattr("fetch.get_steam_games", lambda key, sid: [
        {"name": "Half-Life 2", "appid": 220, "hours_played": 1.0}
    ])
    monkeypatch.setattr("fetch.save_cache", lambda c: None)

    cache = {
        "Half-Life 2": {
            "hltb": {"game_name": "Half-Life 2", "main_story": 12, "main_extra": 15, "completionist": 19},
            "rawg": None,
            "steam": {"appid": 220},
        }
    }

    import fetch
    fetch.build_library("key", "rawg", "user", cache, verbose=True)

    out = capsys.readouterr().out
    assert "[1/1] Half-Life 2 (cache)" in out
```

- [ ] **Step 2: Rodar e confirmar FAIL**

```bash
cd /Users/albertosca/Programming/steam-howlongtobeat
source venv/bin/activate
pytest tests/test_fetch.py::test_build_library_verbose_false_hides_cache_lines tests/test_fetch.py::test_build_library_verbose_true_shows_cache_lines -v
```

Esperado: `TypeError: build_library() got an unexpected keyword argument 'verbose'`

- [ ] **Step 3: Implementar em `fetch.py`**

Alterar a assinatura e os prints dentro de `build_library()`:

```python
def build_library(
    steam_key: str, rawg_key: str, username: str, cache: dict,
    refresh: bool = False, verbose: bool = False
) -> tuple:
    steamid = resolve_steamid(steam_key, username)
    steam_games = get_steam_games(steam_key, steamid)
    total = len(steam_games)
    print(f"{total} games in library. {len(cache)} already cached.\n")
    for idx, game in enumerate(steam_games, 1):
        name = game["name"]
        appid = game["appid"]
        if name in cache and not refresh:
            if verbose:
                print(f"[{idx}/{total}] {name} (cache)")
            continue
        if verbose:
            print(f"[{idx}/{total}] {name}")
        else:
            print(f"Fetching: {name}")
        hltb = fetch_hltb(name)
        if not hltb:
            cache[name] = {"hltb": None, "rawg": None, "steam": None}
            save_cache(cache)
            continue
        rawg = fetch_rawg(rawg_key, name)
        steam_reviews = fetch_steam_reviews(appid)
        time.sleep(0.25)
        cache[name] = {
            "hltb": hltb,
            "rawg": rawg,
            "steam": {"appid": appid, **(steam_reviews or {})},
        }
        save_cache(cache)
    return cache, steam_games
```

- [ ] **Step 4: Adicionar `--verbose` em `main.py`**

Em `parse_args()`, após `p.add_argument("--refresh", ...)`:

```python
p.add_argument("--verbose", "-v", action="store_true",
               help="Exibe progresso de cada jogo durante o scan (padrão: silencioso)")
```

Em `run()`, alterar a chamada de `build_library`:

```python
cache, steam_games = build_library(
    steam_key, rawg_key, args.username, cache,
    refresh=args.refresh, verbose=args.verbose
)
```

Fazer o mesmo no bloco `if args.tui:` dentro de `main()`:

```python
cache, steam_games = build_library(
    steam_key, rawg_key, args.username, cache,
    refresh=args.refresh, verbose=args.verbose
)
```

- [ ] **Step 5: Rodar e confirmar PASS**

```bash
pytest tests/test_fetch.py::test_build_library_verbose_false_hides_cache_lines tests/test_fetch.py::test_build_library_verbose_true_shows_cache_lines -v
```

Esperado: `2 passed`

- [ ] **Step 6: Suite completa verde**

```bash
pytest --tb=short -q
```

Esperado: todos passando (mesmo número de antes + 2 novos).

- [ ] **Step 7: Commit**

```bash
git add fetch.py main.py tests/test_fetch.py
git commit -m "feat: add --verbose flag to build_library() scan output"
```

---

## Task 2: Melhorar `--help`

**Files:**
- Modify: `main.py` — `parse_args()` com description, epilog e help= melhorados
- Test: `tests/test_main.py` — verificar que novos args existem

- [ ] **Step 1: Criar `tests/test_main.py` com testes de parse_args**

```python
import sys
import pytest


def _parse(argv):
    sys.argv = ["main.py"] + argv
    from main import parse_args
    return parse_args()


def test_parse_args_defaults():
    args = _parse([])
    assert args.top == 10
    assert args.sort == "hltb_short"
    assert args.verbose is False
    assert args.show_tags is False


def test_parse_args_verbose_short():
    args = _parse(["-v"])
    assert args.verbose is True


def test_parse_args_show_tags():
    args = _parse(["--show-tags"])
    assert args.show_tags is True


def test_parse_args_top():
    args = _parse(["--top", "25"])
    assert args.top == 25
```

- [ ] **Step 2: Rodar — deve PASSAR (verbose já existe após Task 1, show-tags ainda não)**

```bash
pytest tests/test_main.py::test_parse_args_defaults tests/test_main.py::test_parse_args_verbose_short tests/test_main.py::test_parse_args_top -v
```

Esperado: `3 passed`

```bash
pytest tests/test_main.py::test_parse_args_show_tags -v
```

Esperado: `FAIL` — `AttributeError: Namespace object has no attribute 'show_tags'`

- [ ] **Step 3: Reescrever `parse_args()` em `main.py`**

Substituir a função inteira por:

```python
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Classifica jogos da biblioteca Steam com notas HLTB, Metacritic e Steam.",
        epilog="""
Exemplos:
  python main.py --top 25 --sort metacritic
  python main.py --genre "action,rpg" --not-started --top 10
  python main.py --tui --top 25 --sort hltb_short
  python main.py --min-hours 5 --max-hours 30 --sort composto

Formatos de entrada:
  --genre / --genre-any / --exclude-genre  nomes separados por vírgula (ex: "action,rpg")
  --sort                                   hltb_short | hltb_long | metacritic | steam | composto | custom
  --weight-mc / --weight-steam             pesos de 0.0 a 1.0 que somam 1.0 (ex: 0.6 e 0.4)
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--username", default=STEAM_USERNAME,
                   help="Vanity URL do perfil Steam (padrão: %(default)s)")
    p.add_argument("--sort", default="hltb_short", choices=SORT_OPTIONS,
                   help="Critério de ordenação (padrão: %(default)s)")
    p.add_argument("--genre",
                   help="Gêneros obrigatórios, separados por vírgula (ex: 'action,rpg')")
    p.add_argument("--genre-any",
                   help="Pelo menos um desses gêneros (separados por vírgula)")
    p.add_argument("--exclude-genre",
                   help="Gêneros a excluir (separados por vírgula)")

    prog = p.add_mutually_exclusive_group()
    prog.add_argument("--not-started", action="store_true",
                      help="Somente jogos nunca jogados (0h)")
    prog.add_argument("--in-progress", action="store_true",
                      help="Somente jogos iniciados e não zerados")
    prog.add_argument("--all-progress", action="store_true",
                      help="Sem filtro de progresso (inclui jogos já zerados)")

    p.add_argument("--category", default="all", choices=["all", "singleplayer", "coop"],
                   help="Filtrar por tipo de jogo (padrão: %(default)s)")
    p.add_argument("--min-hours", type=float,
                   help="Duração mínima HLTB em horas")
    p.add_argument("--max-hours", type=float,
                   help="Duração máxima HLTB em horas")
    p.add_argument("--top", type=int, default=10,
                   help="Quantos jogos exibir (padrão: %(default)s)")
    p.add_argument("--output", default="how_long_to_beat_output",
                   help="Nome base dos arquivos de saída .csv e .md")
    p.add_argument("--weight-mc", type=float, default=0.5,
                   help="Peso do Metacritic no score composto (padrão: %(default)s)")
    p.add_argument("--weight-steam", type=float, default=0.5,
                   help="Peso do Steam no score composto (padrão: %(default)s)")
    p.add_argument("--refresh", action="store_true",
                   help="Ignora o cache e rebusca todos os jogos")
    p.add_argument("--verbose", "-v", action="store_true",
                   help="Exibe progresso de cada jogo durante o scan")
    p.add_argument("--show-tags", action="store_true",
                   help="Exibe tags dos jogos na tabela (além de gêneros)")
    p.add_argument("--interactive", action="store_true",
                   help="Modo interativo via prompts")
    p.add_argument("--tui", action="store_true",
                   help="Abre interface visual interativa (htop-style)")
    return p.parse_args()
```

- [ ] **Step 4: Rodar todos os testes de parse_args**

```bash
pytest tests/test_main.py -v
```

Esperado: `4 passed`

- [ ] **Step 5: Suite completa**

```bash
pytest --tb=short -q
```

- [ ] **Step 6: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: improve --help with examples and add --show-tags flag"
```

---

## Task 3: Gêneros/tags na tabela CLI + aviso top N

**Files:**
- Modify: `main.py` — `print_table()` e `run()`
- Test: `tests/test_main.py`

- [ ] **Step 1: Escrever testes que vão falhar**

Adicionar ao `tests/test_main.py`:

```python
def test_print_table_shows_genres_by_default(capsys):
    games = [{
        "name": "Hades",
        "metacritic": 93,
        "steam_pct": 97,
        "main_extra": 22,
        "hours_played": 0,
        "_score": 42.1,
        "genres": ["action", "roguelike", "rpg"],
        "tags": ["indie", "great soundtrack"],
    }]
    from main import print_table
    print_table(games, "hltb_short", show_tags=False)
    out = capsys.readouterr().out
    assert "action" in out
    assert "roguelike" in out
    assert "indie" not in out


def test_print_table_shows_tags_when_flag(capsys):
    games = [{
        "name": "Hades",
        "metacritic": 93,
        "steam_pct": 97,
        "main_extra": 22,
        "hours_played": 0,
        "_score": 42.1,
        "genres": ["action"],
        "tags": ["indie", "great soundtrack"],
    }]
    from main import print_table
    print_table(games, "hltb_short", show_tags=True)
    out = capsys.readouterr().out
    assert "indie" in out
    assert "great soundtrack" in out


def test_print_table_caps_genres_at_four(capsys):
    games = [{
        "name": "Game",
        "metacritic": 80,
        "steam_pct": 90,
        "main_extra": 10,
        "hours_played": 0,
        "_score": 30.0,
        "genres": ["a", "b", "c", "d", "e", "f"],
        "tags": [],
    }]
    from main import print_table
    print_table(games, "hltb_short", show_tags=False)
    out = capsys.readouterr().out
    assert "e" not in out.split("↳")[1] if "↳" in out else True
```

- [ ] **Step 2: Rodar e confirmar FAIL**

```bash
pytest tests/test_main.py::test_print_table_shows_genres_by_default tests/test_main.py::test_print_table_shows_tags_when_flag -v
```

Esperado: `TypeError: print_table() got an unexpected keyword argument 'show_tags'`

- [ ] **Step 3: Reescrever `print_table()` em `main.py`**

```python
def print_table(games: list, sort_by: str, show_tags: bool = False) -> None:
    header = f"{'#':>3}  {'Nome':<45}  {'MC':>4}  {'Steam':>6}  {'HLTB':>5}  {'Jogadas':>8}  {'Score':>8}"
    print(header)
    print("-" * len(header))
    for i, g in enumerate(games, 1):
        mc    = str(g["metacritic"]) if g["metacritic"] else "-"
        steam = f"{g['steam_pct']}%" if g["steam_pct"] else "-"
        hltb  = f"{g['main_extra']}h"
        jogou = f"{g['hours_played']}h"
        score = f"{g['_score']:.1f}"
        print(f"{i:>3}  {g['name']:<45}  {mc:>4}  {steam:>6}  {hltb:>5}  {jogou:>8}  {score:>8}")
        parts = []
        genres = g.get("genres", [])
        if genres:
            parts.append(", ".join(genres[:4]))
        if show_tags:
            tags = g.get("tags", [])
            if tags:
                parts.append("tags: " + ", ".join(tags[:4]))
        if parts:
            print(f"     ↳ {' · '.join(parts)}")
```

- [ ] **Step 4: Atualizar a chamada de `print_table` em `run()`**

Localizar em `run()`:

```python
print_table(top, args.sort)
```

Substituir por:

```python
total_filtered = len(rows)
print(f"\n{'='*60}")
print(f" TOP {args.top} — sort: {args.sort}  ({len(top)} de {total_filtered} filtrados)")
print(f"{'='*60}")
print_table(top, args.sort, show_tags=args.show_tags)
```

- [ ] **Step 5: Rodar e confirmar PASS**

```bash
pytest tests/test_main.py -v
```

Esperado: todos passando.

- [ ] **Step 6: Suite completa**

```bash
pytest --tb=short -q
```

- [ ] **Step 7: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: show genres in CLI table and add --show-tags flag, fix top N warning"
```

---

## Task 4: Adicionar `textual` ao `requirements.txt`

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Adicionar textual**

Editar `requirements.txt` e adicionar a linha:

```
textual>=0.47.0
```

- [ ] **Step 2: Instalar**

```bash
source venv/bin/activate
pip install "textual>=0.47.0"
```

Esperado: instalação sem erros.

- [ ] **Step 3: Verificar import**

```bash
python -c "import textual; print(textual.__version__)"
```

Esperado: versão >= 0.47.0 impressa.

- [ ] **Step 4: Commit**

```bash
git add requirements.txt
git commit -m "feat: add textual dependency for new TUI"
```

---

## Task 5: Reescrever TUI com Textual

**Files:**
- Modify: `tui.py` — reescrita completa
- Modify: `main.py` — passa `initial_filters` para `run_tui()`

- [ ] **Step 1: Escrever smoke test**

Criar `tests/test_tui.py`:

```python
import pytest
from unittest.mock import patch


SAMPLE_GAMES = [
    {
        "name": "Hades",
        "steam_name": "Hades",
        "appid": 1145360,
        "hours_played": 0.0,
        "category": "singleplayer",
        "genres": ["action", "roguelike"],
        "tags": ["indie", "great soundtrack"],
        "metacritic": 93,
        "steam_pct": 97,
        "steam_total_reviews": 50000,
        "main_story": 20,
        "main_extra": 22,
        "completionist": 90,
        "_score": 42.1,
    },
    {
        "name": "Hollow Knight",
        "steam_name": "Hollow Knight",
        "appid": 367520,
        "hours_played": 5.0,
        "category": "singleplayer",
        "genres": ["action", "platformer"],
        "tags": ["indie", "metroidvania"],
        "metacritic": 87,
        "steam_pct": 95,
        "steam_total_reviews": 80000,
        "main_story": 24,
        "main_extra": 40,
        "completionist": 60,
        "_score": 38.6,
    },
]


@pytest.mark.asyncio
async def test_tui_app_starts_and_renders_table():
    from tui import SteamHLTBApp
    initial_filters = {
        "genre": None, "genre_any": None, "exclude_genre": None,
        "progress": "all", "category": "all",
        "min_hours": None, "max_hours": None,
        "sort": "hltb_short", "top": 10,
        "weights": {"mc": 0.5, "steam": 0.5},
    }
    app = SteamHLTBApp(SAMPLE_GAMES, initial_filters)
    async with app.run_test() as pilot:
        # Table deve estar visível e ter linhas
        from textual.widgets import DataTable
        table = app.query_one(DataTable)
        assert table.row_count == 2


@pytest.mark.asyncio
async def test_tui_filter_panel_toggles_with_f():
    from tui import SteamHLTBApp, FilterPanel
    initial_filters = {
        "genre": None, "genre_any": None, "exclude_genre": None,
        "progress": "all", "category": "all",
        "min_hours": None, "max_hours": None,
        "sort": "hltb_short", "top": 10,
        "weights": {"mc": 0.5, "steam": 0.5},
    }
    app = SteamHLTBApp(SAMPLE_GAMES, initial_filters)
    async with app.run_test() as pilot:
        panel = app.query_one(FilterPanel)
        assert panel.display is False  # começa escondido
        await pilot.press("f")
        assert panel.display is True
        await pilot.press("f")
        assert panel.display is False
```

- [ ] **Step 2: Instalar pytest-asyncio**

```bash
pip install pytest-asyncio
```

Adicionar ao `requirements.txt`:

```
pytest-asyncio
```

- [ ] **Step 3: Adicionar config ao `pytest.ini` ou `pyproject.toml`**

Se não existir `pytest.ini`, criar na raiz do projeto:

```ini
[pytest]
asyncio_mode = auto
```

- [ ] **Step 4: Rodar smoke test — deve FAIL**

```bash
pytest tests/test_tui.py -v
```

Esperado: `ImportError: cannot import name 'SteamHLTBApp' from 'tui'`

- [ ] **Step 5: Reescrever `tui.py` completo**

```python
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Input, Select, Footer, Header, Label, Static
from textual.containers import Horizontal, Vertical
from textual.binding import Binding
from textual.reactive import reactive

from classify import apply_filters
from score import compute_score, SORT_OPTIONS


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
    """

    def compose(self) -> ComposeResult:
        yield Label("── Filtros ──────────────")
        yield Label("Sort")
        yield Select(
            [(opt, opt) for opt in SORT_OPTIONS],
            id="sort-select",
            value="hltb_short",
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

    show_genres: reactive[bool] = reactive(False)
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
        self.filters.setdefault("sort", "hltb_short")
        self.filters.setdefault("top", 10)
        self.filters.setdefault("weights", {"mc": 0.5, "steam": 0.5})
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
        )
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
            mc = str(g["metacritic"]) if g["metacritic"] else "-"
            steam = f"{g['steam_pct']}%" if g["steam_pct"] else "-"
            row_data = [
                str(i),
                g["name"],
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

        status = self.query_one("#status-bar", Static)
        status.update(
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

    def _read_filters_from_panel(self) -> None:
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

    def on_input_changed(self, _: Input.Changed) -> None:
        self._read_filters_from_panel()
        self._rebuild_table()

    def on_select_changed(self, _: Select.Changed) -> None:
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
        from main import save_results
        save_results(self._games, "how_long_to_beat_output")
        self.notify("Salvo em how_long_to_beat_output.csv e .md")


def run_tui(all_games: list, initial_filters: dict | None = None) -> None:
    app = SteamHLTBApp(all_games, initial_filters)
    app.run()
```

- [ ] **Step 6: Atualizar `main()` em `main.py` para passar `initial_filters`**

Substituir o bloco `if args.tui:` em `main()`:

```python
    if args.tui:
        from tui import run_tui
        steam_key = get_api_key("STEAM_API_KEY", "Steam API key")
        rawg_key  = get_api_key("RAWG_API_KEY",  "RAWG API key")
        cache = load_cache()
        cache, steam_games = build_library(
            steam_key, rawg_key, args.username, cache,
            refresh=args.refresh, verbose=args.verbose
        )
        rows = build_game_rows(cache, steam_games)
        initial_filters = {
            "genre":         _csv_list(args.genre),
            "genre_any":     _csv_list(getattr(args, "genre_any", None)),
            "exclude_genre": _csv_list(getattr(args, "exclude_genre", None)),
            "progress":      _progress_mode(args),
            "category":      args.category,
            "min_hours":     args.min_hours,
            "max_hours":     args.max_hours,
            "sort":          args.sort,
            "top":           args.top,
            "weights":       _weights(args),
        }
        run_tui(rows, initial_filters)
        return
```

- [ ] **Step 7: Rodar smoke tests**

```bash
pytest tests/test_tui.py -v
```

Esperado: `2 passed`

- [ ] **Step 8: Suite completa**

```bash
pytest --tb=short -q
```

Esperado: todos passando.

- [ ] **Step 9: Commit**

```bash
git add tui.py main.py tests/test_tui.py requirements.txt pytest.ini
git commit -m "feat: rewrite TUI with Textual (htop-style, real-time filters)"
```

---

## Self-review

**Cobertura do spec:**
- ✓ Item 1 (top N bugado) — Task 5 (TUI recebe `initial_filters` com `top` do CLI) + Task 3 (aviso no modo flags)
- ✓ Item 2 (--help) — Task 2
- ✓ Item 4 (gêneros/tags) — Task 3 + Task 5 (`g`/`t` no TUI)
- ✓ Item 5 (TUI htop-like) — Task 5
- ✓ Item 6 (verbose) — Task 1
- Item 3 (coleções) — fora de escopo, aguardando VDF

**Tipos consistentes:** `run_tui(all_games, initial_filters)` definida em Task 5 Step 5, chamada em Step 6. `print_table(games, sort_by, show_tags)` definida em Task 3 Step 3, chamada em Step 4.

**Sem placeholders:** ✓
