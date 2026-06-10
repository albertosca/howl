# Game Classifier Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refatorar o script monolítico em módulos separados e adicionar gêneros, Steam reviews, múltiplos critérios de ordenação, filtros ricos e interface TUI.

**Architecture:** Cinco módulos com responsabilidade única: `fetch.py` (coleta e cache), `score.py` (fórmulas), `classify.py` (filtros e normalização), `tui.py` (interface TUI rich), `main.py` (entrypoint CLI). Scripts antigos permanecem intactos.

**Tech Stack:** Python 3.8+, `requests`, `howlongtobeatpy`, `beautifulsoup4`, `rich`

---

## File Map

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `fetch.py` | Criar | Coleta Steam/HLTB/RAWG, cache load/save |
| `score.py` | Criar | Fórmulas de score e ordenação |
| `classify.py` | Criar | Flatten do cache em rows + todos os filtros |
| `tui.py` | Criar | Modo TUI com rich |
| `main.py` | Criar | Entrypoint: flags, --interactive, --tui |
| `requirements.txt` | Criar | Dependências pinadas |
| `tests/test_fetch.py` | Criar | Testes unitários de fetch |
| `tests/test_score.py` | Criar | Testes unitários de score |
| `tests/test_classify.py` | Criar | Testes unitários de classify |
| `tests/conftest.py` | Criar | Fixtures compartilhadas |

Scripts existentes (`how_long_to_beat.py`, `how_long_to_beat_minus_played_games.py`) **não são modificados**.

---

## Estrutura de dados interna (game row)

Todos os módulos operam sobre dicts com esta shape (produzida por `classify.build_game_rows`):

```python
{
    "name": "Half-Life 2",          # nome do HLTB
    "steam_name": "Half-Life 2",    # nome original da Steam (chave do cache)
    "appid": 220,
    "hours_played": 0.0,
    "category": "singleplayer",     # singleplayer | coop_campaign | multiplayer
    "genres": ["action", "shooter"],
    "tags": ["fps", "atmospheric"],
    "metacritic": 96,               # None se ausente
    "steam_pct": 97,                # None se ausente
    "steam_total_reviews": 158000,  # None se ausente
    "main_story": 12,
    "main_extra": 15,
    "completionist": 19,
}
```

---

## Task 1: Setup do projeto

**Files:**
- Criar: `requirements.txt`
- Criar: `tests/__init__.py`
- Criar: `tests/conftest.py`

- [ ] **Step 1: Criar `requirements.txt`**

```
requests
howlongtobeatpy
beautifulsoup4
rich
pytest
```

- [ ] **Step 2: Instalar dependências**

```bash
pip install -r requirements.txt
```

Esperado: instalação sem erros.

- [ ] **Step 3: Criar `tests/__init__.py`**

Arquivo vazio.

- [ ] **Step 4: Criar `tests/conftest.py`**

```python
import pytest

@pytest.fixture
def sample_cache():
    return {
        "Half-Life 2": {
            "hltb": {
                "game_name": "Half-Life 2",
                "main_story": 12,
                "main_extra": 15,
                "completionist": 19,
            },
            "rawg": {
                "metacritic": 96,
                "genres": ["action", "shooter"],
                "tags": ["singleplayer", "fps", "atmospheric"],
            },
            "steam": {
                "appid": 220,
                "positive_pct": 97,
                "total_reviews": 158000,
            },
        },
        "Portal 2": {
            "hltb": {
                "game_name": "Portal 2",
                "main_story": 9,
                "main_extra": 12,
                "completionist": 17,
            },
            "rawg": {
                "metacritic": 95,
                "genres": ["puzzle", "platformer"],
                "tags": ["co-op", "co-op campaign", "singleplayer", "puzzle"],
            },
            "steam": {
                "appid": 620,
                "positive_pct": 98,
                "total_reviews": 120000,
            },
        },
        "Dota 2": {
            "hltb": None,
            "rawg": {
                "metacritic": 90,
                "genres": ["strategy"],
                "tags": ["multiplayer", "online multiplayer", "pvp", "mmo"],
            },
            "steam": {
                "appid": 570,
                "positive_pct": 81,
                "total_reviews": 2000000,
            },
        },
    }

@pytest.fixture
def sample_steam_games():
    return [
        {"name": "Half-Life 2", "appid": 220, "hours_played": 0.0},
        {"name": "Portal 2",    "appid": 620, "hours_played": 3.0},
        {"name": "Dota 2",      "appid": 570, "hours_played": 100.0},
    ]
```

- [ ] **Step 5: Verificar que pytest roda (sem testes ainda)**

```bash
pytest tests/ -v
```

Esperado: `no tests ran` ou `0 passed`.

---

## Task 2: `fetch.py` — cache e HLTB

**Files:**
- Criar: `fetch.py`
- Criar: `tests/test_fetch.py`

- [ ] **Step 1: Escrever testes de cache**

```python
# tests/test_fetch.py
import json
import pytest
from unittest.mock import patch, MagicMock


def test_load_cache_returns_empty_dict_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import importlib, fetch
    importlib.reload(fetch)
    assert fetch.load_cache() == {}


def test_save_and_load_cache_roundtrip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import importlib, fetch
    importlib.reload(fetch)
    data = {"Half-Life 2": {"hltb": {"main_story": 12}}}
    fetch.save_cache(data)
    assert fetch.load_cache() == data


def test_fetch_hltb_returns_none_when_no_results():
    with patch("fetch.HowLongToBeat") as MockHLTB:
        MockHLTB.return_value.search.return_value = []
        import fetch
        assert fetch.fetch_hltb("NonExistentGame99999") is None


def test_fetch_hltb_returns_none_when_low_similarity():
    with patch("fetch.HowLongToBeat") as MockHLTB:
        r = MagicMock()
        r.similarity = 0.3
        MockHLTB.return_value.search.return_value = [r]
        import fetch
        assert fetch.fetch_hltb("SomeGame") is None


def test_fetch_hltb_returns_data_when_good_match():
    with patch("fetch.HowLongToBeat") as MockHLTB:
        r = MagicMock()
        r.similarity = 0.9
        r.game_name = "Half-Life 2"
        r.main_story = 12.0
        r.main_extra = 15.0
        r.completionist = 19.0
        MockHLTB.return_value.search.return_value = [r]
        import fetch
        result = fetch.fetch_hltb("Half-Life 2")
        assert result == {
            "game_name": "Half-Life 2",
            "main_story": 12,
            "main_extra": 15,
            "completionist": 19,
        }


def test_fetch_hltb_returns_zero_for_negative_times():
    with patch("fetch.HowLongToBeat") as MockHLTB:
        r = MagicMock()
        r.similarity = 0.9
        r.game_name = "Some Game"
        r.main_story = -1.0
        r.main_extra = 0.0
        r.completionist = 5.0
        MockHLTB.return_value.search.return_value = [r]
        import fetch
        result = fetch.fetch_hltb("Some Game")
        assert result["main_story"] == 0
        assert result["main_extra"] == 0
        assert result["completionist"] == 5
```

- [ ] **Step 2: Rodar testes pra confirmar que falham**

```bash
pytest tests/test_fetch.py -v
```

Esperado: `ModuleNotFoundError: No module named 'fetch'`

- [ ] **Step 3: Criar `fetch.py` com cache e HLTB**

```python
import json
import math
import os
import time
import requests
from howlongtobeatpy import HowLongToBeat

CACHE_FILE = "games_cache.json"


def load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache: dict) -> None:
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def fetch_hltb(name: str) -> dict | None:
    results = HowLongToBeat().search(name)
    if not results:
        return None
    best = max(results, key=lambda e: e.similarity)
    if best.similarity < 0.5:
        return None
    return {
        "game_name": best.game_name,
        "main_story": int(best.main_story) if best.main_story and best.main_story > 0 else 0,
        "main_extra": int(best.main_extra) if best.main_extra and best.main_extra > 0 else 0,
        "completionist": int(best.completionist) if best.completionist and best.completionist > 0 else 0,
    }
```

- [ ] **Step 4: Rodar testes de cache e HLTB**

```bash
pytest tests/test_fetch.py -v -k "cache or hltb"
```

Esperado: 6 testes passando.

- [ ] **Step 5: Commitar**

```bash
git add fetch.py tests/test_fetch.py tests/__init__.py tests/conftest.py requirements.txt
git commit -m "feat: add fetch.py with cache load/save and HLTB lookup"
```

---

## Task 3: `fetch.py` — RAWG com gêneros

**Files:**
- Modificar: `fetch.py` (adicionar `fetch_rawg`)
- Modificar: `tests/test_fetch.py` (adicionar testes RAWG)

- [ ] **Step 1: Adicionar testes RAWG em `tests/test_fetch.py`**

```python
def test_fetch_rawg_returns_none_on_non_200():
    with patch("fetch.requests.get") as mock_get:
        mock_get.return_value.status_code = 404
        import fetch
        assert fetch.fetch_rawg("RAWG_KEY", "Half-Life 2") is None


def test_fetch_rawg_returns_none_when_no_results():
    with patch("fetch.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"results": []}
        import fetch
        assert fetch.fetch_rawg("RAWG_KEY", "Half-Life 2") is None


def test_fetch_rawg_returns_metacritic_genres_tags():
    with patch("fetch.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "results": [{
                "metacritic": 96,
                "genres": [{"name": "Action"}, {"name": "Shooter"}],
                "tags": [{"name": "Singleplayer"}, {"name": "FPS"}],
            }]
        }
        import fetch
        result = fetch.fetch_rawg("RAWG_KEY", "Half-Life 2")
        assert result == {
            "metacritic": 96,
            "genres": ["action", "shooter"],
            "tags": ["singleplayer", "fps"],
        }
```

- [ ] **Step 2: Rodar testes RAWG pra confirmar que falham**

```bash
pytest tests/test_fetch.py -v -k "rawg"
```

Esperado: 3 falhas com `AttributeError: module 'fetch' has no attribute 'fetch_rawg'`

- [ ] **Step 3: Adicionar `fetch_rawg` em `fetch.py`**

Adicionar após a função `fetch_hltb`:

```python
def fetch_rawg(rawg_key: str, name: str) -> dict | None:
    resp = requests.get(
        "https://api.rawg.io/api/games",
        params={"key": rawg_key, "search": name, "search_precise": True, "page_size": 5},
    )
    if resp.status_code != 200:
        return None
    results = resp.json().get("results", [])
    if not results:
        return None
    game = results[0]
    return {
        "metacritic": game.get("metacritic"),
        "genres": [g["name"].lower() for g in game.get("genres", [])],
        "tags": [t["name"].lower() for t in game.get("tags", [])],
    }
```

- [ ] **Step 4: Rodar todos os testes de fetch**

```bash
pytest tests/test_fetch.py -v
```

Esperado: todos passando.

- [ ] **Step 5: Commitar**

```bash
git add fetch.py tests/test_fetch.py
git commit -m "feat: add fetch_rawg with genres field"
```

---

## Task 4: `fetch.py` — Steam reviews

**Files:**
- Modificar: `fetch.py` (adicionar `fetch_steam_reviews`)
- Modificar: `tests/test_fetch.py`

- [ ] **Step 1: Adicionar testes Steam reviews**

```python
def test_fetch_steam_reviews_returns_none_on_non_200():
    with patch("fetch.requests.get") as mock_get:
        mock_get.return_value.status_code = 500
        import fetch
        assert fetch.fetch_steam_reviews(220) is None


def test_fetch_steam_reviews_returns_none_when_zero_reviews():
    with patch("fetch.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "query_summary": {"total_reviews": 0, "total_positive": 0}
        }
        import fetch
        assert fetch.fetch_steam_reviews(220) is None


def test_fetch_steam_reviews_returns_positive_pct():
    with patch("fetch.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "query_summary": {
                "total_reviews": 1000,
                "total_positive": 970,
            }
        }
        import fetch
        result = fetch.fetch_steam_reviews(220)
        assert result == {"positive_pct": 97, "total_reviews": 1000}
```

- [ ] **Step 2: Rodar pra confirmar falha**

```bash
pytest tests/test_fetch.py -v -k "steam_reviews"
```

Esperado: 3 falhas.

- [ ] **Step 3: Adicionar `fetch_steam_reviews` em `fetch.py`**

Adicionar após `fetch_rawg`:

```python
def fetch_steam_reviews(appid: int) -> dict | None:
    resp = requests.get(
        f"https://store.steampowered.com/appreviews/{appid}",
        params={"json": 1, "language": "all", "purchase_type": "all"},
    )
    if resp.status_code != 200:
        return None
    summary = resp.json().get("query_summary", {})
    total = summary.get("total_reviews", 0)
    if total == 0:
        return None
    positive = summary.get("total_positive", 0)
    return {
        "positive_pct": round(positive / total * 100),
        "total_reviews": total,
    }
```

- [ ] **Step 4: Rodar suite completa**

```bash
pytest tests/test_fetch.py -v
```

Esperado: todos passando.

- [ ] **Step 5: Commitar**

```bash
git add fetch.py tests/test_fetch.py
git commit -m "feat: add fetch_steam_reviews for user score"
```

---

## Task 5: `fetch.py` — Steam game list e `build_library`

**Files:**
- Modificar: `fetch.py` (adicionar `resolve_steamid`, `get_steam_games`, `build_library`, `get_api_key`)
- Modificar: `tests/test_fetch.py`

- [ ] **Step 1: Adicionar testes**

```python
def test_get_steam_games_parses_response():
    with patch("fetch.requests.get") as mock_get:
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "response": {
                "games": [
                    {"name": "Half-Life 2", "appid": 220, "playtime_forever": 120},
                    {"name": "Portal 2",    "appid": 620, "playtime_forever": 0},
                ]
            }
        }
        import fetch
        games = fetch.get_steam_games("KEY", "STEAMID")
        assert len(games) == 2
        assert games[0] == {"name": "Half-Life 2", "appid": 220, "hours_played": 2.0}
        assert games[1] == {"name": "Portal 2",    "appid": 620, "hours_played": 0.0}


def test_resolve_steamid_raises_on_failure():
    with patch("fetch.requests.get") as mock_get:
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "response": {"success": 42, "message": "No match"}
        }
        import fetch
        with pytest.raises(ValueError, match="not found"):
            fetch.resolve_steamid("KEY", "unknownuser")
```

- [ ] **Step 2: Rodar pra confirmar falha**

```bash
pytest tests/test_fetch.py -v -k "steam_games or steamid"
```

Esperado: falhas.

- [ ] **Step 3: Adicionar funções em `fetch.py`**

Adicionar no final do arquivo:

```python
def get_api_key(env_var: str, prompt: str) -> str:
    key = os.environ.get(env_var)
    if not key:
        key = input(f"{prompt}: ").strip()
    return key


def resolve_steamid(api_key: str, username: str) -> str:
    resp = requests.get(
        "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/",
        params={"key": api_key, "vanityurl": username},
    )
    resp.raise_for_status()
    data = resp.json()["response"]
    if data["success"] != 1:
        raise ValueError(f"Username '{username}' not found on Steam.")
    return data["steamid"]


def get_steam_games(api_key: str, steamid: str) -> list:
    resp = requests.get(
        "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/",
        params={
            "key": api_key,
            "steamid": steamid,
            "include_appinfo": True,
            "include_played_free_games": True,
        },
    )
    resp.raise_for_status()
    games = resp.json()["response"].get("games", [])
    return [
        {
            "name": g["name"],
            "appid": g["appid"],
            "hours_played": round(g.get("playtime_forever", 0) / 60, 1),
        }
        for g in games
    ]


def build_library(
    steam_key: str, rawg_key: str, username: str, cache: dict, refresh: bool = False
) -> tuple:
    steamid = resolve_steamid(steam_key, username)
    steam_games = get_steam_games(steam_key, steamid)
    total = len(steam_games)
    print(f"{total} games in library. {len(cache)} already cached.\n")
    for idx, game in enumerate(steam_games, 1):
        name = game["name"]
        appid = game["appid"]
        if name in cache and not refresh:
            print(f"[{idx}/{total}] {name} (cache)")
            continue
        print(f"[{idx}/{total}] {name}")
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

- [ ] **Step 4: Rodar todos os testes**

```bash
pytest tests/test_fetch.py -v
```

Esperado: todos passando.

- [ ] **Step 5: Commitar**

```bash
git add fetch.py tests/test_fetch.py
git commit -m "feat: add Steam game list, resolve_steamid, build_library"
```

---

## Task 6: `score.py` — fórmulas de scoring

**Files:**
- Criar: `score.py`
- Criar: `tests/test_score.py`

- [ ] **Step 1: Criar `tests/test_score.py`**

```python
import pytest
import math
from score import (
    score_hltb_short, score_hltb_long, score_metacritic,
    score_steam, score_composto, compute_score, SORT_OPTIONS,
)


def test_sort_options_contains_all_expected():
    assert set(SORT_OPTIONS) == {"hltb_short", "hltb_long", "metacritic", "steam", "composto", "custom"}


def test_hltb_short_formula():
    game = {"metacritic": 90, "main_extra": 9}
    assert score_hltb_short(game) == pytest.approx(30.0)  # 90 / sqrt(9)


def test_hltb_short_no_extra_hours_returns_metacritic():
    game = {"metacritic": 90, "main_extra": 0}
    assert score_hltb_short(game) == 90.0


def test_hltb_short_missing_metacritic_returns_zero():
    game = {"metacritic": None, "main_extra": 10}
    assert score_hltb_short(game) == 0.0


def test_hltb_long_formula():
    game = {"metacritic": 90, "main_extra": 9}
    assert score_hltb_long(game) == pytest.approx(270.0)  # 90 * sqrt(9)


def test_score_metacritic_direct():
    assert score_metacritic({"metacritic": 85}) == 85.0
    assert score_metacritic({"metacritic": None}) == 0.0


def test_score_steam_direct():
    assert score_steam({"steam_pct": 92}) == 92.0
    assert score_steam({"steam_pct": None}) == 0.0


def test_score_composto_default_weights():
    game = {"metacritic": 80, "steam_pct": 60}
    result = score_composto(game)
    assert result == pytest.approx(70.0)  # 0.5*80 + 0.5*60


def test_score_composto_custom_weights():
    game = {"metacritic": 80, "steam_pct": 60}
    result = score_composto(game, weights={"mc": 0.7, "steam": 0.3})
    assert result == pytest.approx(74.0)  # 0.7*80 + 0.3*60


def test_score_composto_redistributes_missing_source():
    game = {"metacritic": 80, "steam_pct": None}
    result = score_composto(game, weights={"mc": 0.5, "steam": 0.5})
    assert result == pytest.approx(80.0)  # só mc disponível, peso total vira 1.0


def test_score_composto_no_sources_returns_zero():
    game = {"metacritic": None, "steam_pct": None}
    assert score_composto(game) == 0.0


def test_compute_score_dispatches_correctly():
    game = {"metacritic": 90, "main_extra": 9, "steam_pct": 80}
    assert compute_score(game, "hltb_short") == pytest.approx(30.0)
    assert compute_score(game, "metacritic") == 90.0
    assert compute_score(game, "steam") == 80.0
    assert compute_score(game, "composto") == pytest.approx(85.0)


def test_compute_score_custom_uses_weights():
    game = {"metacritic": 100, "steam_pct": 0}
    result = compute_score(game, "custom", weights={"mc": 1.0, "steam": 0.0})
    assert result == pytest.approx(100.0)


def test_compute_score_raises_on_unknown_sort():
    with pytest.raises(ValueError, match="Unknown sort"):
        compute_score({}, "invalid_sort")
```

- [ ] **Step 2: Rodar pra confirmar falha**

```bash
pytest tests/test_score.py -v
```

Esperado: `ModuleNotFoundError: No module named 'score'`

- [ ] **Step 3: Criar `score.py`**

```python
import math

SORT_OPTIONS = ["hltb_short", "hltb_long", "metacritic", "steam", "composto", "custom"]


def score_hltb_short(game: dict) -> float:
    mc = game.get("metacritic")
    hours = game.get("main_extra", 0)
    if mc is None:
        return 0.0
    if hours and hours > 0:
        return mc / math.sqrt(hours)
    return float(mc)


def score_hltb_long(game: dict) -> float:
    mc = game.get("metacritic")
    hours = game.get("main_extra", 0)
    if mc is None:
        return 0.0
    if hours and hours > 0:
        return mc * math.sqrt(hours)
    return float(mc)


def score_metacritic(game: dict) -> float:
    return float(game.get("metacritic") or 0)


def score_steam(game: dict) -> float:
    return float(game.get("steam_pct") or 0)


def score_composto(game: dict, weights: dict | None = None) -> float:
    if weights is None:
        weights = {"mc": 0.5, "steam": 0.5}
    sources = {}
    mc = game.get("metacritic")
    steam = game.get("steam_pct")
    if mc is not None:
        sources["mc"] = mc
    if steam is not None:
        sources["steam"] = steam
    if not sources:
        return 0.0
    total_weight = sum(weights.get(k, 0) for k in sources)
    if total_weight == 0:
        return 0.0
    return sum(sources[k] * weights.get(k, 0) / total_weight for k in sources)


def compute_score(game: dict, sort_by: str, weights: dict | None = None) -> float:
    if sort_by == "hltb_short":
        return score_hltb_short(game)
    if sort_by == "hltb_long":
        return score_hltb_long(game)
    if sort_by == "metacritic":
        return score_metacritic(game)
    if sort_by == "steam":
        return score_steam(game)
    if sort_by in ("composto", "custom"):
        return score_composto(game, weights)
    raise ValueError(f"Unknown sort: {sort_by}")
```

- [ ] **Step 4: Rodar testes**

```bash
pytest tests/test_score.py -v
```

Esperado: 15 testes passando.

- [ ] **Step 5: Commitar**

```bash
git add score.py tests/test_score.py
git commit -m "feat: add score.py with all scoring formulas"
```

---

## Task 7: `classify.py` — game rows e filtros

**Files:**
- Criar: `classify.py`
- Criar: `tests/test_classify.py`

- [ ] **Step 1: Criar `tests/test_classify.py`**

```python
import pytest
from classify import (
    build_game_rows, filter_genre, filter_progress,
    filter_category, filter_time, apply_filters,
)


# --- build_game_rows ---

def test_build_game_rows_skips_entries_without_hltb(sample_cache, sample_steam_games):
    rows = build_game_rows(sample_cache, sample_steam_games)
    names = [r["name"] for r in rows]
    assert "Dota 2" not in names  # hltb is None


def test_build_game_rows_includes_all_fields(sample_cache, sample_steam_games):
    rows = build_game_rows(sample_cache, sample_steam_games)
    hl2 = next(r for r in rows if r["name"] == "Half-Life 2")
    assert hl2["metacritic"] == 96
    assert hl2["steam_pct"] == 97
    assert hl2["genres"] == ["action", "shooter"]
    assert hl2["hours_played"] == 0.0
    assert hl2["category"] == "singleplayer"


def test_build_game_rows_classifies_coop(sample_cache, sample_steam_games):
    rows = build_game_rows(sample_cache, sample_steam_games)
    p2 = next(r for r in rows if r["name"] == "Portal 2")
    assert p2["category"] == "coop_campaign"


# --- filter_genre ---

def test_filter_genre_must_have_all():
    games = [
        {"genres": ["action", "shooter"]},
        {"genres": ["action", "rpg"]},
        {"genres": ["rpg"]},
    ]
    result = filter_genre(games, must_have=["action", "shooter"])
    assert len(result) == 1


def test_filter_genre_any_of():
    games = [
        {"genres": ["action"]},
        {"genres": ["rpg"]},
        {"genres": ["puzzle"]},
    ]
    result = filter_genre(games, any_of=["action", "rpg"])
    assert len(result) == 2


def test_filter_genre_exclude():
    games = [{"genres": ["action"]}, {"genres": ["rpg"]}, {"genres": ["puzzle"]}]
    result = filter_genre(games, exclude=["rpg", "puzzle"])
    assert len(result) == 1
    assert result[0]["genres"] == ["action"]


def test_filter_genre_case_insensitive():
    games = [{"genres": ["Action", "Shooter"]}]
    result = filter_genre(games, must_have=["action"])
    assert len(result) == 1


def test_filter_genre_no_filters_returns_all():
    games = [{"genres": ["action"]}, {"genres": ["rpg"]}]
    assert filter_genre(games) == games


# --- filter_progress ---

def test_filter_progress_not_started():
    games = [
        {"hours_played": 0.0, "main_extra": 10},
        {"hours_played": 2.0, "main_extra": 10},
    ]
    result = filter_progress(games, mode="not_started")
    assert len(result) == 1
    assert result[0]["hours_played"] == 0.0


def test_filter_progress_in_progress():
    games = [
        {"hours_played": 0.0, "main_extra": 10},
        {"hours_played": 3.0, "main_extra": 10},
        {"hours_played": 8.0, "main_extra": 10},  # >50%, excluded
    ]
    result = filter_progress(games, mode="in_progress")
    assert len(result) == 1
    assert result[0]["hours_played"] == 3.0


def test_filter_progress_all_returns_everything():
    games = [
        {"hours_played": 0.0, "main_extra": 10},
        {"hours_played": 100.0, "main_extra": 10},
    ]
    assert len(filter_progress(games, mode="all")) == 2


def test_filter_progress_default_hides_over_50_pct():
    games = [
        {"hours_played": 4.0, "main_extra": 10},   # 40%, kept
        {"hours_played": 6.0, "main_extra": 10},   # 60%, hidden
    ]
    result = filter_progress(games, mode="default")
    assert len(result) == 1
    assert result[0]["hours_played"] == 4.0


# --- filter_category ---

def test_filter_category_all_excludes_multiplayer():
    games = [
        {"category": "singleplayer"},
        {"category": "coop_campaign"},
        {"category": "multiplayer"},
    ]
    result = filter_category(games, category="all")
    assert len(result) == 2


def test_filter_category_singleplayer_only():
    games = [{"category": "singleplayer"}, {"category": "coop_campaign"}]
    result = filter_category(games, category="singleplayer")
    assert len(result) == 1


# --- filter_time ---

def test_filter_time_max_hours():
    games = [{"main_extra": 5}, {"main_extra": 20}, {"main_extra": 40}]
    result = filter_time(games, max_hours=20)
    assert len(result) == 2


def test_filter_time_min_hours():
    games = [{"main_extra": 5}, {"main_extra": 20}]
    result = filter_time(games, min_hours=10)
    assert len(result) == 1


# --- apply_filters combines all ---

def test_apply_filters_combines(sample_cache, sample_steam_games):
    rows = build_game_rows(sample_cache, sample_steam_games)
    result = apply_filters(rows, genre=["action"], progress="not_started")
    assert all(r["hours_played"] == 0.0 for r in result)
    assert all("action" in r["genres"] for r in result)
```

- [ ] **Step 2: Rodar pra confirmar falha**

```bash
pytest tests/test_classify.py -v
```

Esperado: `ModuleNotFoundError: No module named 'classify'`

- [ ] **Step 3: Criar `classify.py`**

```python
COOP_TAGS = {"co-op", "online co-op", "local co-op", "co-operative", "co-op campaign"}
MULTIPLAYER_ONLY_TAGS = {"multiplayer", "online multiplayer", "pvp", "mmo"}


def _category(tags: list, main_story: int) -> str:
    tag_set = {t.lower() for t in tags}
    has_coop = bool(tag_set & COOP_TAGS)
    has_single = "singleplayer" in tag_set or "single-player" in tag_set
    is_mp_only = bool(tag_set & MULTIPLAYER_ONLY_TAGS) and not has_single and not has_coop
    if is_mp_only:
        return "multiplayer"
    if has_coop and main_story > 0:
        return "coop_campaign"
    return "singleplayer"


def build_game_rows(cache: dict, steam_games: list) -> list:
    rows = []
    for game in steam_games:
        name = game["name"]
        entry = cache.get(name, {})
        hltb = entry.get("hltb")
        rawg = entry.get("rawg")
        steam = entry.get("steam")
        if not hltb:
            continue
        tags = rawg.get("tags", []) if rawg else []
        rows.append({
            "name": hltb["game_name"],
            "steam_name": name,
            "appid": steam.get("appid") if steam else game.get("appid"),
            "hours_played": game["hours_played"],
            "category": _category(tags, hltb["main_story"]),
            "genres": [g.lower() for g in (rawg.get("genres", []) if rawg else [])],
            "tags": tags,
            "metacritic": rawg.get("metacritic") if rawg else None,
            "steam_pct": steam.get("positive_pct") if steam else None,
            "steam_total_reviews": steam.get("total_reviews") if steam else None,
            "main_story": hltb["main_story"],
            "main_extra": hltb["main_extra"],
            "completionist": hltb["completionist"],
        })
    return rows


def filter_genre(
    games: list,
    must_have: list = None,
    any_of: list = None,
    exclude: list = None,
) -> list:
    result = games
    if must_have:
        lower = [g.lower() for g in must_have]
        result = [g for g in result if all(m in g["genres"] for m in lower)]
    if any_of:
        lower = [g.lower() for g in any_of]
        result = [g for g in result if any(m in g["genres"] for m in lower)]
    if exclude:
        lower = [g.lower() for g in exclude]
        result = [g for g in result if not any(e in g["genres"] for e in lower)]
    return result


def filter_progress(games: list, mode: str = "default") -> list:
    if mode == "all":
        return games
    if mode == "not_started":
        return [g for g in games if g["hours_played"] == 0]
    if mode == "in_progress":
        return [g for g in games if 0 < g["hours_played"] < 0.5 * max(g["main_extra"], 1)]
    return [g for g in games if g["hours_played"] <= 0.5 * max(g["main_extra"], 1)]


def filter_category(games: list, category: str = "all") -> list:
    if category == "all":
        return [g for g in games if g["category"] != "multiplayer"]
    return [g for g in games if g["category"] == category]


def filter_time(games: list, min_hours: float = None, max_hours: float = None) -> list:
    result = games
    if min_hours is not None:
        result = [g for g in result if g["main_extra"] >= min_hours]
    if max_hours is not None:
        result = [g for g in result if g["main_extra"] <= max_hours]
    return result


def apply_filters(
    games: list,
    genre: list = None,
    genre_any: list = None,
    exclude_genre: list = None,
    progress: str = "default",
    category: str = "all",
    min_hours: float = None,
    max_hours: float = None,
) -> list:
    games = filter_genre(games, must_have=genre, any_of=genre_any, exclude=exclude_genre)
    games = filter_progress(games, mode=progress)
    games = filter_category(games, category=category)
    games = filter_time(games, min_hours=min_hours, max_hours=max_hours)
    return games
```

- [ ] **Step 4: Rodar testes**

```bash
pytest tests/test_classify.py -v
```

Esperado: todos passando.

- [ ] **Step 5: Rodar suite completa**

```bash
pytest tests/ -v
```

Esperado: todos os testes passando (fetch + score + classify).

- [ ] **Step 6: Commitar**

```bash
git add classify.py tests/test_classify.py
git commit -m "feat: add classify.py with build_game_rows and all filters"
```

---

## Task 8: `main.py` — modo flags

**Files:**
- Criar: `main.py`

Não há testes unitários para `main.py` — a integração é coberta pelo smoke test da Task 11.

- [ ] **Step 1: Criar `main.py`**

```python
import argparse
import csv
import os
import sys

from fetch import get_api_key, load_cache, build_library
from score import compute_score, SORT_OPTIONS
from classify import build_game_rows, apply_filters

STEAM_USERNAME = "heenett"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Steam game classifier")
    p.add_argument("--username", default=STEAM_USERNAME)
    p.add_argument("--sort", default="hltb_short", choices=SORT_OPTIONS)
    p.add_argument("--genre",         help="Gêneros obrigatórios (vírgula-separados)")
    p.add_argument("--genre-any",     help="Qualquer um desses gêneros (vírgula-separados)")
    p.add_argument("--exclude-genre", help="Gêneros a excluir (vírgula-separados)")

    prog = p.add_mutually_exclusive_group()
    prog.add_argument("--not-started",  action="store_true")
    prog.add_argument("--in-progress",  action="store_true")
    prog.add_argument("--all-progress", action="store_true")

    p.add_argument("--category", default="all", choices=["all", "singleplayer", "coop"])
    p.add_argument("--min-hours", type=float)
    p.add_argument("--max-hours", type=float)
    p.add_argument("--top",    type=int, default=10)
    p.add_argument("--output", default="how_long_to_beat_output")
    p.add_argument("--weight-mc",    type=float, default=0.5)
    p.add_argument("--weight-steam", type=float, default=0.5)
    p.add_argument("--refresh",      action="store_true")
    p.add_argument("--interactive",  action="store_true")
    p.add_argument("--tui",          action="store_true")
    return p.parse_args()


def _progress_mode(args: argparse.Namespace) -> str:
    if args.not_started:
        return "not_started"
    if args.in_progress:
        return "in_progress"
    if args.all_progress:
        return "all"
    return "default"


def _weights(args: argparse.Namespace) -> dict:
    w = {"mc": args.weight_mc, "steam": args.weight_steam}
    total = sum(w.values())
    if abs(total - 1.0) > 0.01:
        print(f"Aviso: pesos somam {total:.2f}, esperado 1.0. Normalizando.", file=sys.stderr)
        w = {k: v / total for k, v in w.items()}
    return w


def _csv_list(value: str | None) -> list | None:
    if not value:
        return None
    return [v.strip() for v in value.split(",") if v.strip()]


def print_table(games: list, sort_by: str) -> None:
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


def save_results(games: list, output_base: str) -> None:
    csv_path = output_base + ".csv"
    md_path  = output_base + ".md"

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "name", "category", "metacritic", "steam_pct", "score",
            "hours_played", "main_story", "main_extra", "completionist",
        ])
        writer.writeheader()
        for g in games:
            writer.writerow({k: g.get(k) for k in writer.fieldnames if k != "score"} | {"score": round(g["_score"], 2)})

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("| # | Nome | MC | Steam | HLTB | Jogadas | Score |\n")
        f.write("|---|------|----|-------|------|---------|-------|\n")
        for i, g in enumerate(games, 1):
            mc    = str(g["metacritic"]) if g["metacritic"] else "-"
            steam = f"{g['steam_pct']}%" if g["steam_pct"] else "-"
            f.write(f"| {i} | {g['name']} | {mc} | {steam} | {g['main_extra']}h | {g['hours_played']}h | {g['_score']:.1f} |\n")

    print(f"\nSalvo em '{csv_path}' e '{md_path}'")


def run(args: argparse.Namespace) -> None:
    steam_key = get_api_key("STEAM_API_KEY", "Steam API key")
    rawg_key  = get_api_key("RAWG_API_KEY",  "RAWG API key")

    cache = load_cache()
    cache, steam_games = build_library(steam_key, rawg_key, args.username, cache, refresh=args.refresh)

    rows = build_game_rows(cache, steam_games)
    rows = apply_filters(
        rows,
        genre=_csv_list(args.genre),
        genre_any=_csv_list(getattr(args, "genre_any", None)),
        exclude_genre=_csv_list(getattr(args, "exclude_genre", None)),
        progress=_progress_mode(args),
        category=args.category,
        min_hours=args.min_hours,
        max_hours=args.max_hours,
    )

    weights = _weights(args)
    for g in rows:
        g["_score"] = compute_score(g, args.sort, weights)

    rows.sort(key=lambda g: g["_score"], reverse=True)
    top = rows[:args.top]

    print(f"\n{'='*60}")
    print(f" TOP {args.top} — sort: {args.sort}")
    print(f"{'='*60}")
    print_table(top, args.sort)
    save_results(rows, args.output)


def main() -> None:
    args = parse_args()
    if args.tui:
        from tui import run_tui
        steam_key = get_api_key("STEAM_API_KEY", "Steam API key")
        rawg_key  = get_api_key("RAWG_API_KEY",  "RAWG API key")
        cache = load_cache()
        cache, steam_games = build_library(steam_key, rawg_key, args.username, cache, refresh=args.refresh)
        rows = build_game_rows(cache, steam_games)
        run_tui(rows)
        return
    if args.interactive:
        from interactive import run_interactive
        run_interactive(args)
        return
    run(args)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verificar que o import funciona**

```bash
python -c "import main; print('OK')"
```

Esperado: `OK` (sem erros de importação).

- [ ] **Step 3: Commitar**

```bash
git add main.py
git commit -m "feat: add main.py with flags mode, print_table, save_results"
```

---

## Task 9: Modo interativo (`interactive.py`)

**Files:**
- Criar: `interactive.py`

- [ ] **Step 1: Criar `interactive.py`**

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
```

- [ ] **Step 2: Verificar import**

```bash
python -c "import interactive; print('OK')"
```

Esperado: `OK`

- [ ] **Step 3: Commitar**

```bash
git add interactive.py
git commit -m "feat: add interactive.py for guided session mode"
```

---

## Task 10: `tui.py` — modo TUI com rich

**Files:**
- Criar: `tui.py`

O modo TUI usa `rich` para renderizar tabela. Como `rich` não tem loop de eventos com teclado, a interação é via prompts de texto após cada ação (print + input). A tela é limpa entre cada render com `Console.clear()`.

- [ ] **Step 1: Criar `tui.py`**

```python
import os
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

    # filtros ativos
    active = []
    if filters["genre"]:       active.append(f"gênero={','.join(filters['genre'])}")
    if filters["genre_any"]:   active.append(f"genre-any={','.join(filters['genre_any'])}")
    if filters["exclude_genre"]: active.append(f"excluir={','.join(filters['exclude_genre'])}")
    if filters["progress"] != "default": active.append(f"progresso={filters['progress']}")
    if filters["category"] != "all": active.append(f"categoria={filters['category']}")
    if filters["min_hours"]:   active.append(f"min={filters['min_hours']}h")
    if filters["max_hours"]:   active.append(f"max={filters['max_hours']}h")
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
    console.print("[bold]\[f][/] filtros  [bold]\[s][/] salvar  [bold]\[q][/] sair")


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
        val = Prompt.ask(f"  {label}", default=str(current) if current else "")
        return val

    genre_raw   = _prompt("Gêneros obrigatórios (vírgula-sep)", ",".join(filters["genre"]) if filters["genre"] else "")
    any_raw     = _prompt("Qualquer gênero (vírgula-sep)", ",".join(filters["genre_any"]) if filters["genre_any"] else "")
    excl_raw    = _prompt("Excluir gêneros (vírgula-sep)", ",".join(filters["exclude_genre"]) if filters["exclude_genre"] else "")
    progress    = _prompt(f"Progresso {SORT_OPTIONS}", filters["progress"])
    category    = _prompt("Categoria [all/singleplayer/coop]", filters["category"])
    min_h       = _prompt("Min horas (vazio=sem)", str(filters["min_hours"]) if filters["min_hours"] else "")
    max_h       = _prompt("Max horas (vazio=sem)", str(filters["max_hours"]) if filters["max_hours"] else "")
    sort_by     = _prompt(f"Sort [{'/'.join(SORT_OPTIONS)}]", filters["sort"])
    top_raw     = _prompt("Top N", str(filters["top"]))

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
            console.print(f"[green]Salvo![/]")

        else:
            _render(games, filters)
```

- [ ] **Step 2: Verificar import**

```bash
python -c "import tui; print('OK')"
```

Esperado: `OK`

- [ ] **Step 3: Commitar**

```bash
git add tui.py interactive.py
git commit -m "feat: add tui.py (rich) and interactive.py"
```

---

## Task 11: Smoke test de integração com cache existente

**Files:**
- Criar: `tests/test_integration.py`

Este teste usa o `games_cache.json` existente (não faz chamadas de rede) pra verificar que o pipeline completo funciona.

- [ ] **Step 1: Criar `tests/test_integration.py`**

```python
import json
import os
import pytest
from classify import build_game_rows, apply_filters
from score import compute_score


CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "games_cache.json")


@pytest.fixture
def real_cache():
    if not os.path.exists(CACHE_FILE):
        pytest.skip("games_cache.json não encontrado — rode o script de fetch primeiro")
    with open(CACHE_FILE, encoding="utf-8") as f:
        return json.load(f)


def test_build_game_rows_produces_valid_rows(real_cache):
    steam_games = [
        {"name": name, "appid": entry.get("steam", {}).get("appid", 0) if entry.get("steam") else 0, "hours_played": 0.0}
        for name, entry in real_cache.items()
    ]
    rows = build_game_rows(real_cache, steam_games)
    assert len(rows) > 0
    for r in rows:
        assert "name" in r
        assert "category" in r
        assert r["category"] in ("singleplayer", "coop_campaign", "multiplayer")


def test_filter_and_score_pipeline(real_cache):
    steam_games = [
        {"name": name, "appid": 0, "hours_played": 0.0}
        for name in real_cache
    ]
    rows = build_game_rows(real_cache, steam_games)
    filtered = apply_filters(rows, progress="all", category="all")
    for g in filtered:
        g["_score"] = compute_score(g, "hltb_short")
    filtered.sort(key=lambda g: g["_score"], reverse=True)
    assert len(filtered) > 0
    scores = [g["_score"] for g in filtered]
    assert scores == sorted(scores, reverse=True)
```

- [ ] **Step 2: Rodar o smoke test**

```bash
pytest tests/test_integration.py -v
```

Esperado: 2 testes passando (ou `skipped` se não houver cache local).

- [ ] **Step 3: Rodar suite completa**

```bash
pytest tests/ -v
```

Esperado: todos passando.

- [ ] **Step 4: Commitar**

```bash
git add tests/test_integration.py
git commit -m "test: add integration smoke test against real cache"
```

---

## Uso rápido após implementação

```bash
# flags
python main.py --genre action --not-started --sort hltb_short --top 15

# composto com pesos customizados
python main.py --sort custom --weight-mc 0.6 --weight-steam 0.4

# modo interativo
python main.py --interactive

# TUI
python main.py --tui

# re-fetch forçado
python main.py --refresh
```
