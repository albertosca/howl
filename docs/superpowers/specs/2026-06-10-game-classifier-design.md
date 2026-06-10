# Game Classifier — Design Spec

**Data:** 2026-06-10  
**Status:** aprovado

## Objetivo

Substituir o script monolítico atual por um classificador modular que ajuda o usuário a escolher o próximo jogo da biblioteca Steam, com múltiplas fontes de dados, filtros ricos por gênero/progresso/tempo, múltiplos critérios de ordenação, e interface CLI com modo flags, interativo e TUI.

---

## Arquitetura

```
steam-howlongtobeat/
├── fetch.py       # coleta de dados: Steam, HLTB, RAWG
├── score.py       # fórmulas de score e normalização
├── classify.py    # filtros: gênero, progresso, categoria, tempo
├── tui.py         # modo TUI com rich
└── main.py        # entrypoint CLI: flags + --interactive + --tui
```

Scripts antigos (`how_long_to_beat.py`, `how_long_to_beat_minus_played_games.py`) ficam intactos para referência.

---

## Dados e Cache (`fetch.py`)

### Schema do cache (`games_cache.json`)

Extensão retrocompatível — entradas antigas permanecem válidas; campos ausentes tratados como `None`.

```json
"Half-Life 2": {
  "hltb": {
    "game_name": "Half-Life 2",
    "main_story": 12,
    "main_extra": 15,
    "completionist": 19
  },
  "rawg": {
    "metacritic": 96,
    "genres": ["action", "shooter"],
    "tags": ["singleplayer", "fps", "atmospheric", "..."]
  },
  "steam": {
    "appid": 220,
    "positive_pct": 97,
    "total_reviews": 158000
  }
}
```

`genres` é o campo `genres` da RAWG API (lista limpa de gêneros canônicos), separado das `tags` livres. O `appid` vem da Steam API (já retornado junto com o nome do jogo em `GetOwnedGames`).

### Funções

- `fetch_hltb(name)` — sem mudança
- `fetch_rawg(rawg_key, name)` — adiciona `genres` ao retorno existente; remove `rawg_user_score`
- `fetch_steam_reviews(appid)` — chama `ISteamUserStats` pra pegar `positive_pct` e `total_reviews`
- `load_cache()` / `save_cache(cache)` — sem mudança
- Flag `--refresh` no `main.py` força re-fetch de todas as entradas (ignora cache)

---

## Scoring (`score.py`)

Todos os scores são normalizados para 0–100 antes de ordenar.

Quando uma fonte está ausente, o peso dela é redistribuído proporcionalmente entre as demais — o jogo não é descartado.

### Fórmulas prontas

| `--sort` | Fórmula | Foco |
|---|---|---|
| `hltb_short` *(default)* | `metacritic / sqrt(main_extra)` | Bom e curto |
| `hltb_long` | `metacritic * sqrt(main_extra)` | Bom e longo |
| `metacritic` | `metacritic` direto | Crítica pura |
| `steam` | `steam_positive_pct` | Comunidade Steam |
| `composto` | `0.5 * metacritic + 0.5 * steam_pct` | Críticos + usuários |
| `custom` | pesos via flags | Livre |

### Score customizado

```bash
python main.py --sort custom --weight-mc 0.6 --weight-steam 0.4
```

Os pesos devem somar 1.0; o programa valida e avisa se não somarem.

---

## Filtros (`classify.py`)

### Gênero

```bash
--genre fps,action        # jogos que têm TODOS esses gêneros
--genre-any fps,action    # jogos que têm QUALQUER um desses gêneros
--exclude-genre rpg,mmo   # remove jogos com qualquer um desses gêneros
```

Matching case-insensitive contra o campo `genres` do cache.

### Progresso

```bash
--not-started    # hours_played == 0
--in-progress    # 0 < hours_played < 50% do main_extra
--all            # sem filtro de progresso
# sem flag      # comportamento atual: esconde >50% do main_extra jogados
```

### Categoria

```bash
--category singleplayer   # só single-player
--category coop           # só co-op com campanha
--category all            # ambos (default)
```

A lógica de classificação singleplayer/coop/multiplayer permanece igual à atual (baseada em tags RAWG).

### Tempo

```bash
--max-hours 20    # main_extra <= 20h
--min-hours 5     # main_extra >= 5h
```

### Output

```bash
--top 10              # quantos jogos exibir (default: 10)
--output nome_base    # salva nome_base.csv e nome_base.md
```

Se `--output` não for passado, salva em `how_long_to_beat_output` (mesmo nome atual).

---

## Interface

### Modo flags (default)

```bash
python main.py --genre fps --not-started --sort hltb_short --top 15
python main.py --exclude-genre rpg --all --sort composto --weight-mc 0.6 --weight-steam 0.4
```

Roda, imprime tabela no terminal, salva CSV + Markdown, sai.

### Modo interativo (`--interactive`)

Sessão guiada: o programa pergunta gênero, exclusões, progresso, sort e número de resultados, um por vez. Estilo do script atual. Ao final exibe e salva igual ao modo flags.

### Modo TUI (`--tui`)

Dependência: `rich` (sem curses nativo — mais simples de manter).

Layout:
```
┌─ Filtros ──────────────────────────────────────────────┐
│ Gênero: [fps]  Excluir: []  Progresso: [not-started]  │
│ Sort: [hltb_short]  Top: [10]                          │
├─ Resultados ───────────────────────────────────────────┤
│  # │ Nome              │ MC │ Steam │ HLTB │ Jogadas   │
│  1 │ Half-Life 2       │ 96 │  97%  │  15h │  0.0h     │
│  2 │ Portal 2          │ 95 │  98%  │  10h │  0.0h     │
└────────────────────────────────────────────────────────┘
[q] sair  [s] salvar  [f] editar filtros  [↑↓] navegar
```

- Filtros editáveis ao vivo com `f`; resultado atualiza imediatamente
- `s` salva CSV + Markdown com nome padrão ou pedido
- Opera sobre o cache já carregado — sem re-fetch durante a TUI

---

## Compatibilidade

- Python 3.8+
- Dependências: `requests`, `howlongtobeatpy`, `beautifulsoup4`, `rich`
- Variáveis de ambiente: `STEAM_API_KEY`, `RAWG_API_KEY` (fallback para input interativo)
- Cache existente é preservado; novos campos são adicionados incrementalmente
