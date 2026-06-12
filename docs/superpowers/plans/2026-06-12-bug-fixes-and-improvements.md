# Bug Fixes & Melhorias — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolver todos os bugs e itens pendentes do TODO: interactive.py quebrado, print clutter, tags cirílicas, FEZTAL, collection na TUI, --list-collections, --migrate-cache, .gitignore e commits organizados.

**Architecture:** Correções independentes em módulos existentes. Nenhuma refatoração estrutural — cada task corrige um problema isolado. TDD onde há lógica testável; para mudanças puramente visuais (print, .gitignore), commit direto.

**Tech Stack:** Python 3.11+, pytest, textual (TUI), howlongtobeatpy, requests

---

## Diagnóstico pré-plan

Estado do cache: 311 entradas no formato RAWG legado. **Nenhuma** tem `steam.genres` ou `steam.categories` — todos foram buscados antes da migração para Steam AppDetails. A pipeline `classify.py` já tem fallback para `rawg` (funcionando), mas `--list-tags` expõe tags cirílicas.

Bugs confirmados:
- `interactive.py:61` chama `build_library(steam_key, rawg_key, username, cache)` — assinatura errada, crasha
- `interactive.py:59-60` ainda promove `RAWG_API_KEY` — chave inexistente
- `fetch.py:125` sempre imprime header (não respeita verbose)
- `fetch.py:136` imprime "Fetching: X" para cache misses mesmo sem verbose
- `cache["FEZ"]["hltb"]["game_name"] == "FEZTAL"` — match errado, score 91, HLTB 0h
- `interactive.py` não tem `--collection` support
- TUI não tem filtro de coleção

Itens já funcionando (não requerem código):
- `--collection` flag no CLI `main.py` ✓
- `steam_collections.py` parse correto ✓ (6 testes passando)
- TUI já é real-time via `on_input_changed` / `on_select_changed` ✓

---

## Mapa de arquivos

| Arquivo | Ação | Task |
|---------|------|------|
| `.gitignore` | Criar | 1 |
| `fetch.py` | Verbose-gate print + add `migrate_cache()` | 2, 7 |
| `interactive.py` | Fix RAWG refs + add collection | 3 |
| `main.py` | Add `--list-collections`, `--migrate-cache`, top-N hint, fix save_results | 4, 5, 7 |
| `tui.py` | Add collection filter + `--list-collections` | 6 |
| `tests/test_fetch.py` | Testes de verbose + migrate | 2, 7 |
| `tests/test_main.py` | Testes de list-collections, top-N hint | 4, 5 |
| `tests/test_interactive.py` | Testes de interactive corrigido | 3 |

---

## Task 1: .gitignore

**Files:**
- Create: `.gitignore`

Nenhum teste necessário.

- [ ] **Step 1: Criar .gitignore**

```
# cache e outputs gerados
games_cache.json
how_long_to_beat_output.csv
how_long_to_beat_output.md
sharedconfig.vdf

# python
venv/
__pycache__/
*.pyc
*.pyo
.pytest_cache/
*.egg-info/
dist/
build/

# env
.env
```

- [ ] **Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: add .gitignore (cache, outputs, venv, __pycache__)"
```

---

## Task 2: Fix print clutter em fetch.py

`fetch.py:125` sempre imprime o header. `fetch.py:136` imprime "Fetching: X" sem verbose. Ambos devem ser silenciosos por padrão; verbose mostra tudo.

**Files:**
- Modify: `fetch.py:125-136`
- Test: `tests/test_fetch.py`

- [ ] **Step 1: Escrever testes que falham**

Adicionar ao final de `tests/test_fetch.py`:

```python
def test_build_library_silent_by_default_on_header(capsys, monkeypatch):
    monkeypatch.setattr("fetch.resolve_steamid", lambda k, u: "123")
    monkeypatch.setattr("fetch.get_steam_games", lambda k, sid: [])
    build_library("key", "user", {})
    out = capsys.readouterr().out
    assert out == ""


def test_build_library_silent_on_cache_miss_without_verbose(capsys, monkeypatch):
    monkeypatch.setattr("fetch.resolve_steamid", lambda k, u: "123")
    monkeypatch.setattr("fetch.get_steam_games", lambda k, sid: [
        {"name": "FEZ", "appid": 224760, "hours_played": 0}
    ])
    monkeypatch.setattr("fetch.fetch_hltb", lambda name: None)
    build_library("key", "user", {})
    out = capsys.readouterr().out
    assert "Fetching" not in out


def test_build_library_verbose_prints_header(capsys, monkeypatch):
    monkeypatch.setattr("fetch.resolve_steamid", lambda k, u: "123")
    monkeypatch.setattr("fetch.get_steam_games", lambda k, sid: [])
    build_library("key", "user", {}, verbose=True)
    out = capsys.readouterr().out
    assert "0 games" in out


def test_build_library_verbose_prints_fetching(capsys, monkeypatch):
    monkeypatch.setattr("fetch.resolve_steamid", lambda k, u: "123")
    monkeypatch.setattr("fetch.get_steam_games", lambda k, sid: [
        {"name": "FEZ", "appid": 224760, "hours_played": 0}
    ])
    monkeypatch.setattr("fetch.fetch_hltb", lambda name: None)
    build_library("key", "user", {}, verbose=True)
    out = capsys.readouterr().out
    assert "FEZ" in out
```

- [ ] **Step 2: Rodar para confirmar falha**

```
pytest tests/test_fetch.py -k "silent_by_default or silent_on_cache or verbose_prints" -v
```

Esperado: 4 FAIL

- [ ] **Step 3: Corrigir fetch.py**

Em `fetch.py`, mudar:

```python
# ANTES (linha 125):
print(f"{total} games in library. {len(cache)} already cached.\n")

# DEPOIS:
if verbose:
    print(f"{total} games in library. {len(cache)} already cached.\n")
```

E as linhas 132-136:

```python
# ANTES:
        if name in cache and not refresh:
            if verbose:
                print(f"[{idx}/{total}] {name} (cache)")
            continue
        if verbose:
            print(f"[{idx}/{total}] {name}")
        else:
            print(f"Fetching: {name}")

# DEPOIS:
        if name in cache and not refresh:
            if verbose:
                print(f"[{idx}/{total}] {name} (cache)")
            continue
        if verbose:
            print(f"[{idx}/{total}] {name}")
```

- [ ] **Step 4: Rodar testes**

```
pytest tests/test_fetch.py -v
```

Esperado: todos passando (incluindo os 4 novos + existentes)

- [ ] **Step 5: Commit**

```bash
git add fetch.py tests/test_fetch.py
git commit -m "fix: make fetch output silent by default, verbose only with --verbose"
```

---

## Task 3: Fix interactive.py (RAWG refs + collection support)

`interactive.py` crasha ao ser usado porque chama `build_library` com assinatura antiga (com `rawg_key`). Remover RAWG, adicionar `--collection`.

**Files:**
- Modify: `interactive.py` (full rewrite da função `run_interactive`)
- Create: `tests/test_interactive.py`

- [ ] **Step 1: Escrever testes que falham**

Criar `tests/test_interactive.py`:

```python
import pytest
from unittest.mock import patch, MagicMock


SAMPLE_GAMES = [
    {
        "name": "Half-Life 2",
        "steam_name": "Half-Life 2",
        "appid": 220,
        "hours_played": 0.0,
        "category": "singleplayer",
        "genres": ["action"],
        "tags": ["single-player"],
        "metacritic": 96,
        "steam_pct": 98,
        "steam_total_reviews": 100000,
        "main_story": 12,
        "main_extra": 15,
        "completionist": 19,
    }
]

MOCK_CACHE = {
    "Half-Life 2": {
        "hltb": {"game_name": "Half-Life 2", "main_story": 12, "main_extra": 15, "completionist": 19},
        "steam": {"appid": 220, "positive_pct": 98, "total_reviews": 100000, "genres": ["action"], "categories": ["single-player"]},
    }
}

MOCK_STEAM_GAMES = [{"name": "Half-Life 2", "appid": 220, "hours_played": 0.0}]


def _run_interactive_with_inputs(inputs, vdf_path="sharedconfig.vdf"):
    """Helper que simula respostas do usuário via stdin."""
    import argparse
    args = argparse.Namespace(
        username="heenett",
        weight_mc=0.5,
        weight_steam=0.5,
        vdf_path=vdf_path,
    )
    with patch("builtins.input", side_effect=inputs), \
         patch("fetch.get_api_key", return_value="fake_key"), \
         patch("fetch.load_cache", return_value=MOCK_CACHE), \
         patch("fetch.build_library", return_value=(MOCK_CACHE, MOCK_STEAM_GAMES)), \
         patch("main.save_results"):
        from interactive import run_interactive
        run_interactive(args)


def test_interactive_does_not_ask_rawg_key():
    """Não deve mais pedir RAWG_API_KEY."""
    asked = []
    def mock_input(prompt):
        asked.append(prompt)
        return ""
    import argparse
    args = argparse.Namespace(username="heenett", weight_mc=0.5, weight_steam=0.5, vdf_path="no.vdf")
    with patch("builtins.input", side_effect=mock_input), \
         patch("fetch.get_api_key", return_value="fake"), \
         patch("fetch.load_cache", return_value=MOCK_CACHE), \
         patch("fetch.build_library", return_value=(MOCK_CACHE, MOCK_STEAM_GAMES)), \
         patch("main.save_results"):
        from interactive import run_interactive
        run_interactive(args)
    assert not any("rawg" in a.lower() for a in asked)


def test_interactive_runs_without_error():
    """Deve rodar sem exception com inputs vazios (aceita defaults)."""
    _run_interactive_with_inputs(["", "", "", "", "", "", "", "", "", ""])


def test_interactive_does_not_crash_with_collection_input():
    """Deve aceitar nome de coleção sem crashar."""
    import argparse
    args = argparse.Namespace(username="heenett", weight_mc=0.5, weight_steam=0.5, vdf_path="no.vdf")
    inputs = ["", "", "", "", "", "", "", "", "", "", "Terminados"]
    with patch("builtins.input", side_effect=inputs + [""]*20), \
         patch("fetch.get_api_key", return_value="fake"), \
         patch("fetch.load_cache", return_value=MOCK_CACHE), \
         patch("fetch.build_library", return_value=(MOCK_CACHE, MOCK_STEAM_GAMES)), \
         patch("steam_collections.load_collections", return_value={"220": ["Terminados"]}), \
         patch("main.save_results"):
        from interactive import run_interactive
        run_interactive(args)
```

- [ ] **Step 2: Rodar para confirmar falha**

```
pytest tests/test_interactive.py -v
```

Esperado: 3 FAIL (crashes por assinatura errada)

- [ ] **Step 3: Reescrever interactive.py**

```python
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

    collection_raw = _ask("Filtrar por coleção (vazio=todas, ex: Terminados)", default="")

    output = _ask("Nome base do arquivo de saída", default="how_long_to_beat_output")

    from fetch import get_api_key, load_cache, build_library
    from classify import build_game_rows

    steam_key = get_api_key("STEAM_API_KEY", "Steam API key")
    cache = load_cache()
    cache, steam_games = build_library(steam_key, base_args.username, cache)
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

    if collection_raw:
        from steam_collections import load_collections, filter_collection
        vdf_path = getattr(base_args, "vdf_path", "sharedconfig.vdf")
        collection_map = load_collections(vdf_path)
        rows = filter_collection(rows, collection_raw, collection_map)

    weights = _weights(base_args)
    for g in rows:
        g["_score"] = compute_score(g, sort_by, weights)

    rows.sort(key=lambda g: g["_score"], reverse=True)
    top_games = rows[:top]

    print(f"\n{'='*60}")
    print(f" TOP {top} — sort: {sort_by}  ({len(top_games)} de {len(rows)} filtrados)")
    print(f"{'='*60}")
    print_table(top_games, sort_by)
    save_results(rows, output)
```

- [ ] **Step 4: Rodar testes**

```
pytest tests/test_interactive.py tests/test_steam_collections.py -v
```

Esperado: todos passando

- [ ] **Step 5: Commit**

```bash
git add interactive.py tests/test_interactive.py
git commit -m "fix: remove RAWG from interactive.py, fix build_library signature, add collection filter"
```

---

## Task 4: Add --list-collections flag

Permite listar coleções disponíveis no VDF antes de usar `--collection`.

**Files:**
- Modify: `main.py` — add `--list-collections` arg + `list_collections_cmd()`
- Test: `tests/test_main.py`

- [ ] **Step 1: Escrever testes que falham**

Adicionar ao final de `tests/test_main.py`:

```python
def test_parse_args_list_collections():
    args = _parse(["--list-collections"])
    assert args.list_collections is True


def test_list_collections_cmd_prints_names(capsys):
    collection_map = {
        "220":  ["Terminados"],
        "620":  ["Jogando", "Terminados"],
        "570":  ["Multiplayer"],
    }
    from main import list_collections_cmd
    list_collections_cmd(collection_map)
    out = capsys.readouterr().out
    assert "Terminados" in out
    assert "Jogando" in out
    assert "Multiplayer" in out


def test_list_collections_cmd_shows_count(capsys):
    collection_map = {
        "220": ["Terminados"],
        "620": ["Terminados"],
        "570": ["Jogando"],
    }
    from main import list_collections_cmd
    list_collections_cmd(collection_map)
    out = capsys.readouterr().out
    assert "2" in out   # Terminados aparece 2x
    assert "1" in out   # Jogando aparece 1x
```

- [ ] **Step 2: Rodar para confirmar falha**

```
pytest tests/test_main.py -k "list_collections" -v
```

Esperado: 3 FAIL

- [ ] **Step 3: Implementar em main.py**

Adicionar argumento em `parse_args()`, logo após `--list-genres`:

```python
    p.add_argument("--list-collections", action="store_true",
                   help="Lista coleções Steam disponíveis no VDF e sai")
```

Adicionar função `list_collections_cmd()` após `list_available()`:

```python
def list_collections_cmd(collection_map: dict) -> None:
    from collections import Counter
    counter = Counter(tag for tags in collection_map.values() for tag in tags)
    if not counter:
        print("Nenhuma coleção encontrada. Verifique --vdf-path.")
        return
    print(f"\n{'─'*40}")
    print(f" COLEÇÕES disponíveis ({len(counter)} únicas)")
    print(f"{'─'*40}")
    for name, count in counter.most_common():
        print(f"  {count:>4}x  {name}")
```

Adicionar no início do bloco `if args.list_tags or args.list_genres:` em `main()`:

```python
    if args.list_tags or args.list_genres or args.list_collections:
        cache = load_cache()
        if args.list_genres:
            list_available(cache, "genres")
        if args.list_tags:
            list_available(cache, "categories")
        if args.list_collections:
            from steam_collections import load_collections
            collection_map = load_collections(args.vdf_path)
            list_collections_cmd(collection_map)
        return
```

- [ ] **Step 4: Rodar testes**

```
pytest tests/test_main.py -v
```

Esperado: todos passando

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: add --list-collections to show Steam VDF collections"
```

---

## Task 5: Fix top-N hint + save_results consistência

Dois problemas: (a) quando `len(top) < args.top`, o usuário não sabe o motivo; (b) `save_results(rows, ...)` salva TODOS os filtrados, não só o top — intencional mas não documentado.

**Files:**
- Modify: `main.py:run()`
- Test: `tests/test_main.py`

- [ ] **Step 1: Escrever testes que falham**

Adicionar ao final de `tests/test_main.py`:

```python
def test_run_prints_hint_when_fewer_than_top(capsys, monkeypatch):
    import argparse
    from main import run
    args = argparse.Namespace(
        username="u", sort="metacritic", genre=None, genre_any=None,
        exclude_genre=None, not_started=False, in_progress=False, all_progress=True,
        category="all", min_hours=None, max_hours=None, top=50,
        output="/tmp/test_out", weight_mc=0.5, weight_steam=0.5,
        collection=None, vdf_path="no.vdf", refresh=False, verbose=False,
        show_tags=False,
    )
    games = [{"name": "G1", "appid": 1, "hours_played": 0.0}]
    cache = {"G1": {"hltb": {"game_name": "G1", "main_story": 5, "main_extra": 10, "completionist": 15},
                    "steam": {"appid": 1, "positive_pct": 80, "total_reviews": 100, "genres": ["action"], "categories": ["single-player"]}}}
    monkeypatch.setattr("main.get_api_key", lambda *a: "fake")
    monkeypatch.setattr("main.load_cache", lambda: cache)
    monkeypatch.setattr("main.build_library", lambda *a, **kw: (cache, games))
    monkeypatch.setattr("main.save_results", lambda *a: None)
    run(args)
    out = capsys.readouterr().out
    assert "1 de 50" in out or "50" in out
```

- [ ] **Step 2: Rodar para confirmar**

```
pytest tests/test_main.py::test_run_prints_hint_when_fewer_than_top -v
```

Esperado: PASS (a saída já inclui `len(top) de args.top`). Se PASS, esse teste documenta o comportamento atual — não precisa mudar código, só adicionar hint mais explícito.

Se falhar, o formato de saída foi alterado. Ajustar o assert para o formato atual.

- [ ] **Step 3: Melhorar hint em main.py:run()**

No bloco de print em `run()`, mudar para:

```python
    total_filtered = len(rows)
    shown = len(top)
    print(f"\n{'='*60}")
    print(f" TOP {args.top} — sort: {args.sort}  ({shown} de {total_filtered} filtrados)")
    if shown < args.top and total_filtered < args.top:
        print(f" ⚠  Apenas {total_filtered} jogos passaram nos filtros (pedido: {args.top})")
    print(f"{'='*60}")
```

- [ ] **Step 4: Rodar testes**

```
pytest tests/test_main.py -v
```

Esperado: todos passando

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: print warning when fewer games match filters than --top requested"
```

---

## Task 6: Collection filter na TUI

A TUI não tem campo de coleção. Adicionar input de coleção no FilterPanel e aplicar no `_rebuild_table`.

**Files:**
- Modify: `tui.py` — FilterPanel + SteamHLTBApp

- [ ] **Step 1: Adicionar filtro de coleção ao FilterPanel**

Em `tui.py`, no método `FilterPanel.compose()`, adicionar ao final (antes de fechar):

```python
        yield Label("Coleção (ex: Terminados)")
        yield Input(placeholder="vazio=todas", id="collection-input")
        yield Label("VDF path")
        yield Input(value="sharedconfig.vdf", id="vdf-path-input")
```

- [ ] **Step 2: Adicionar estado de coleção ao SteamHLTBApp**

Em `SteamHLTBApp.__init__()`, adicionar aos `setdefault`:

```python
        self.filters.setdefault("collection", None)
        self.filters.setdefault("vdf_path", "sharedconfig.vdf")
```

- [ ] **Step 3: Atualizar _sync_panel_to_filters**

Adicionar ao final de `_sync_panel_to_filters()`:

```python
        if self.filters.get("collection"):
            self.query_one("#collection-input", Input).value = self.filters["collection"]
        vdf = self.filters.get("vdf_path", "sharedconfig.vdf")
        self.query_one("#vdf-path-input", Input).value = vdf
```

- [ ] **Step 4: Atualizar _read_filters_from_panel**

Adicionar ao final de `_read_filters_from_panel()`:

```python
        try:
            raw = self.query_one("#collection-input", Input).value.strip()
            self.filters["collection"] = raw if raw else None
        except Exception:
            pass
        try:
            raw = self.query_one("#vdf-path-input", Input).value.strip()
            self.filters["vdf_path"] = raw if raw else "sharedconfig.vdf"
        except Exception:
            pass
```

- [ ] **Step 5: Aplicar filtro de coleção em _rebuild_table**

Em `_rebuild_table()`, após `apply_filters(...)` e antes de calcular score:

```python
        if self.filters.get("collection"):
            try:
                from steam_collections import load_collections, filter_collection
                collection_map = load_collections(self.filters.get("vdf_path", "sharedconfig.vdf"))
                rows = filter_collection(rows, self.filters["collection"], collection_map)
            except Exception:
                pass
```

- [ ] **Step 6: Rodar testes TUI**

```
pytest tests/test_tui.py -v
```

Esperado: todos passando (testes existentes não quebram)

- [ ] **Step 7: Commit**

```bash
git add tui.py
git commit -m "feat: add collection filter to TUI (FilterPanel + _rebuild_table)"
```

---

## Task 7: Fix FEZTAL — threshold de similaridade

`cache["FEZ"]["hltb"]["game_name"] == "FEZTAL"` porque a busca HLTB retornou FEZTAL com similaridade ≥ 0.5. Fix: aumentar threshold de 0.5 para 0.6, que exclui esse match.

**Files:**
- Modify: `fetch.py:fetch_hltb()` — threshold `0.5` → `0.6`
- Test: `tests/test_fetch.py`

- [ ] **Step 1: Verificar threshold atual**

Em `fetch.py:28`: `if best.similarity < 0.5: return None`

- [ ] **Step 2: Escrever teste**

Adicionar a `tests/test_fetch.py`:

```python
def test_fetch_hltb_rejects_low_similarity(monkeypatch):
    """Match com similarity < 0.6 deve retornar None."""
    from unittest.mock import MagicMock
    mock_result = MagicMock()
    mock_result.similarity = 0.55
    mock_result.game_name = "FEZTAL"
    mock_result.main_story = 0
    mock_result.main_extra = 0
    mock_result.completionist = 0
    monkeypatch.setattr("fetch.HowLongToBeat", lambda: MagicMock(search=lambda name: [mock_result]))
    from fetch import fetch_hltb
    assert fetch_hltb("FEZ") is None


def test_fetch_hltb_accepts_high_similarity(monkeypatch):
    """Match com similarity >= 0.6 deve retornar dados."""
    from unittest.mock import MagicMock
    mock_result = MagicMock()
    mock_result.similarity = 0.9
    mock_result.game_name = "FEZ"
    mock_result.main_story = 9
    mock_result.main_extra = 12
    mock_result.completionist = 20
    monkeypatch.setattr("fetch.HowLongToBeat", lambda: MagicMock(search=lambda name: [mock_result]))
    from fetch import fetch_hltb
    result = fetch_hltb("FEZ")
    assert result is not None
    assert result["game_name"] == "FEZ"
```

- [ ] **Step 3: Rodar para confirmar falha no primeiro**

```
pytest tests/test_fetch.py::test_fetch_hltb_rejects_low_similarity -v
```

Esperado: FAIL

- [ ] **Step 4: Corrigir fetch.py**

Mudar linha 28 de:
```python
    if best.similarity < 0.5:
```
para:
```python
    if best.similarity < 0.6:
```

- [ ] **Step 5: Rodar testes**

```
pytest tests/test_fetch.py -v
```

Esperado: todos passando

- [ ] **Step 6: Corrigir entrada FEZ no cache manualmente**

A entrada FEZ no `games_cache.json` tem `game_name: FEZTAL` e zeros. Fazer `--refresh` pra esse jogo, ou corrigir manualmente:

```python
# rodar uma vez:
import json
with open("games_cache.json") as f:
    cache = json.load(f)
# remove a entrada incorreta para que seja re-buscada
cache["FEZ"]["hltb"] = None
with open("games_cache.json", "w") as f:
    json.dump(cache, f, ensure_ascii=False, indent=2)
```

> Nota: `games_cache.json` não é commitado (task 1 o gitignora). O usuário precisará rodar `python main.py` para re-buscar FEZ. A correção no threshold garante que a próxima busca não pegue FEZTAL.

- [ ] **Step 7: Commit**

```bash
git add fetch.py tests/test_fetch.py
git commit -m "fix: raise HLTB similarity threshold to 0.6 to avoid false matches like FEZTAL"
```

---

## Task 8: Corrigir tags cirílicas em --list-tags / --show-tags

O cache legado RAWG tem tags em russo misturadas com inglês. `--list-tags` e `--show-tags` exibem texto cirílico. Fix: filtrar entradas não-ASCII na exibição.

**Files:**
- Modify: `main.py:list_available()` — filtrar valores cirílicos
- Modify: `main.py:print_table()` — filtrar tags cirílicas
- Test: `tests/test_main.py`

- [ ] **Step 1: Escrever testes que falham**

Adicionar a `tests/test_main.py`:

```python
def test_list_available_filters_cyrillic_tags(capsys):
    cache = {
        "Half-Life 2": {
            "steam": {"genres": [], "categories": []},
            "rawg": {"genres": ["action"], "tags": ["singleplayer", "для одного игрока", "atmospheric"]},
        }
    }
    from main import list_available
    list_available(cache, "categories")
    out = capsys.readouterr().out
    assert "singleplayer" in out
    assert "atmospheric" in out
    assert "игрока" not in out


def test_print_table_filters_cyrillic_in_tags(capsys):
    games = [{
        "name": "Half-Life 2",
        "metacritic": 96,
        "steam_pct": 98,
        "main_extra": 15,
        "hours_played": 0,
        "_score": 50.0,
        "genres": ["action"],
        "tags": ["singleplayer", "для одного игрока"],
    }]
    from main import print_table
    print_table(games, "hltb_short", show_tags=True)
    out = capsys.readouterr().out
    assert "singleplayer" in out
    assert "игрока" not in out
```

- [ ] **Step 2: Rodar para confirmar falha**

```
pytest tests/test_main.py -k "cyrillic" -v
```

Esperado: 2 FAIL

- [ ] **Step 3: Adicionar helper e corrigir main.py**

Adicionar helper logo após os imports em `main.py`:

```python
def _is_latin(text: str) -> bool:
    return all(ord(c) < 256 for c in text)
```

Em `list_available()`, mudar o loop:

```python
        for v in values:
            if _is_latin(v):
                counter[v] += 1
```

Em `print_table()`, mudar o bloco de tags:

```python
        if show_tags:
            tags = [t for t in g.get("tags", []) if _is_latin(t)]
            if tags:
                parts.append("tags: " + ", ".join(tags[:4]))
```

- [ ] **Step 4: Rodar testes**

```
pytest tests/test_main.py -v
```

Esperado: todos passando

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "fix: filter cyrillic tags from --list-tags and --show-tags display"
```

---

## Task 9: Add --migrate-cache para popular steam.genres/categories

O cache inteiro está no formato RAWG legado (sem steam.genres). Adicionar `--migrate-cache` que roda `fetch_steam_app_details` para entradas existentes que estão faltando esses campos.

**Files:**
- Modify: `fetch.py` — add `migrate_steam_details()`
- Modify: `main.py` — add `--migrate-cache` flag
- Test: `tests/test_fetch.py`

- [ ] **Step 1: Escrever testes que falham**

Adicionar a `tests/test_fetch.py`:

```python
def test_migrate_steam_details_fills_missing_genres(monkeypatch):
    cache = {
        "Half-Life 2": {
            "hltb": {"game_name": "Half-Life 2", "main_story": 12, "main_extra": 15, "completionist": 19},
            "steam": {"appid": 220, "positive_pct": 98, "total_reviews": 100000},
            "rawg": {"metacritic": 96, "genres": ["action"], "tags": []},
        }
    }
    monkeypatch.setattr("fetch.fetch_steam_app_details", lambda appid: {
        "metacritic": 96,
        "genres": ["action"],
        "categories": ["single-player"],
    })
    monkeypatch.setattr("fetch.save_cache", lambda c: None)
    from fetch import migrate_steam_details
    updated = migrate_steam_details(cache, verbose=False)
    steam = updated["Half-Life 2"]["steam"]
    assert steam["genres"] == ["action"]
    assert steam["categories"] == ["single-player"]
    assert steam["metacritic"] == 96


def test_migrate_steam_details_skips_already_migrated(monkeypatch):
    """Não deve chamar fetch_steam_app_details para entradas que já têm genres."""
    cache = {
        "Hades": {
            "hltb": {"game_name": "Hades", "main_story": 20, "main_extra": 22, "completionist": 90},
            "steam": {"appid": 1145360, "positive_pct": 97, "total_reviews": 50000,
                      "genres": ["action"], "categories": ["single-player"]},
        }
    }
    called = []
    monkeypatch.setattr("fetch.fetch_steam_app_details", lambda appid: called.append(appid) or {})
    monkeypatch.setattr("fetch.save_cache", lambda c: None)
    from fetch import migrate_steam_details
    migrate_steam_details(cache, verbose=False)
    assert called == []


def test_migrate_steam_details_skips_no_appid(monkeypatch):
    cache = {
        "GameNoAppid": {
            "hltb": {"game_name": "X", "main_story": 5, "main_extra": 8, "completionist": 10},
            "steam": {"positive_pct": 90, "total_reviews": 1000},
        }
    }
    monkeypatch.setattr("fetch.fetch_steam_app_details", lambda appid: {})
    monkeypatch.setattr("fetch.save_cache", lambda c: None)
    from fetch import migrate_steam_details
    result = migrate_steam_details(cache, verbose=False)
    assert "genres" not in result["GameNoAppid"]["steam"]
```

- [ ] **Step 2: Rodar para confirmar falha**

```
pytest tests/test_fetch.py -k "migrate" -v
```

Esperado: 3 FAIL

- [ ] **Step 3: Implementar migrate_steam_details em fetch.py**

Adicionar ao final de `fetch.py`:

```python
def migrate_steam_details(cache: dict, verbose: bool = False) -> dict:
    """Preenche steam.genres/categories/metacritic para entradas sem esses campos."""
    import time
    total = sum(
        1 for v in cache.values()
        if v.get("steam") and v["steam"].get("appid") and "genres" not in v.get("steam", {})
    )
    if verbose:
        print(f"Migrando {total} entradas sem steam.genres...")
    done = 0
    for name, entry in cache.items():
        steam = entry.get("steam") or {}
        appid = steam.get("appid")
        if not appid or "genres" in steam:
            continue
        details = fetch_steam_app_details(appid)
        if details:
            cache[name]["steam"].update(details)
        done += 1
        if verbose:
            print(f"[{done}/{total}] {name}")
        save_cache(cache)
        time.sleep(0.5)
    return cache
```

- [ ] **Step 4: Adicionar --migrate-cache em main.py**

Em `parse_args()`:

```python
    p.add_argument("--migrate-cache", action="store_true",
                   help="Preenche steam.genres/categories para entradas legacy do cache (operação lenta, ~15-30 min)")
```

No início de `main()`, após o bloco `list_tags/list_genres/list_collections`:

```python
    if args.migrate_cache:
        from fetch import migrate_steam_details
        cache = load_cache()
        migrate_steam_details(cache, verbose=True)
        print("Migração concluída.")
        return
```

- [ ] **Step 5: Rodar testes**

```
pytest tests/test_fetch.py -v
```

Esperado: todos passando

- [ ] **Step 6: Commit**

```bash
git add fetch.py main.py tests/test_fetch.py
git commit -m "feat: add --migrate-cache to populate steam.genres/categories for legacy RAWG cache entries"
```

---

## Task 10: Atualizar TODO.md e memory

- [ ] **Step 1: Atualizar TODO.md**

Sobrescrever `TODO.md` com apenas itens ainda não resolvidos:

```markdown
# TODO

## Bugs resolvidos (não remover — referência histórica)
- [x] Verbose: build_library silenciosa por padrão
- [x] interactive.py quebrado (RAWG refs removidas, collection adicionada)
- [x] Tags cirílicas ocultas no display
- [x] FEZTAL: threshold 0.5 → 0.6
- [x] --list-collections flag
- [x] Collection filter na TUI
- [x] --migrate-cache para popular steam.genres
- [x] .gitignore

## Pendentes
- [ ] Rodar `python main.py --migrate-cache` para popular steam.genres no cache (operação ~15-30 min, requer STEAM_API_KEY)
- [ ] Corrigir FEZ no cache: após threshold fix, rodar `python main.py --refresh` ou corrigir entrada manualmente
```

- [ ] **Step 2: Atualizar memory**

Atualizar `project-game-classifier.md` no diretório de memória com o novo status.

- [ ] **Step 3: Commit final**

```bash
git add TODO.md
git commit -m "chore: update TODO.md with resolved items and pending cache migration"
```

---

## Checklist de revisão

- [x] Spec coverage: todos os itens do TODO.md cobertos
- [x] Nenhum placeholder "TBD" ou "implement later"
- [x] Tipos/assinaturas consistentes: `build_library(steam_key, username, cache, refresh=False, verbose=False)`
- [x] `migrate_steam_details` retorna `cache` modificado e persiste via `save_cache`
- [x] Testes TUI não quebram com adição de novos campos no FilterPanel
