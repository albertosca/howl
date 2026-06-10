# Design: TODO Fixes — steam-howlongtobeat

**Data:** 2026-06-10  
**Escopo:** 5 itens do TODO.md (item 3 — coleções Steam — adiado até Alberto fornecer o VDF)

---

## Itens em escopo

### 1. Top N bugado

**Problema:**
- TUI ignora `--top` passado via CLI (sempre inicia com `DEFAULT_FILTERS["top"] = 10`)
- No modo flags, se os filtros descartam mais jogos que o esperado, nenhum aviso é dado

**Solução:**
- `main()` passa `args.top` (e os demais filtros do CLI) como filtros iniciais ao chamar `run_tui()`
- No modo flags (`run()`), após montar `top`, exibir: `"Mostrando X de Y jogos filtrados"` se `X < args.top`

**Arquivos:** `main.py`, `tui.py` (novo, Textual)

---

### 2. `--help` confuso

**Solução:**
- Adicionar `description` e `epilog` com exemplos ao `ArgumentParser`
- Melhorar os `help=` de cada argumento (português, claro sobre formato de input)
- Grupo de exemplos no epilog:

```
Exemplos:
  python main.py --top 25 --sort metacritic
  python main.py --genre "action,rpg" --not-started --top 10
  python main.py --tui --top 25 --sort hltb_short
  python main.py --collection "Finalizados" --sort composto
```

**Arquivo:** `main.py`

---

### 3. Coleções Steam *(ADIADO)*

Aguardando Alberto fornecer o arquivo `sharedconfig.vdf` do Windows.  
Caminho: `C:\Program Files (x86)\Steam\userdata\{steamid}\7\remote\sharedconfig.vdf`

Abordagem planejada: leitura do VDF via lib `vdf`, export para `collections.json`, flag `--collection <nome>`.

---

### 4. Dados faltando na tabela

**Problema:** gêneros e tags não aparecem na saída do modo flags.

**Solução (estilo B — linha extra):**

Após cada linha de jogo no modo flags (`print_table`), imprimir uma linha recuada com gêneros e (opcionalmente) tags:

```
  1  Hades                                          93    96%   22h      0.5h      42.1
     ↳ action, roguelike, rpg  ·  tags: indie, great soundtrack
```

- Gêneros: até 4, separados por `, `
- Tags: até 4 primeiras, só se `--show-tags` for passado (evitar poluição por padrão)
- No TUI Textual: colunas `Gêneros` e `Tags` toggleáveis com teclas `g` e `t`

**Arquivo:** `main.py` (`print_table`), `tui.py` (novo)

---

### 5. TUI htop-like com Textual

**Substitui** o `tui.py` atual (baseado em `rich.Prompt`) por implementação `textual`.

**Layout:**

```
┌─ Steam HLTB ─────────────────────────────────────────────────────────┐
│ Sort: [hltb_short ▾]  Top: [25]  Progress: [default ▾]   q=sair     │
├─────┬──────────────────────────────────────┬────┬──────┬─────┬──────┤
│  #  │ Nome                                 │ MC │ HLTB │ Jog │Score │
├─────┼──────────────────────────────────────┼────┼──────┼─────┼──────┤
│  1  │ Hades                                │ 93 │  22h │ 0h  │ 42.1 │
│  2  │ Hollow Knight                        │ 87 │  40h │ 0h  │ 38.6 │
└─────┴──────────────────────────────────────┴────┴──────┴─────┴──────┘
 f=filtros  g=gêneros  t=tags  s=salvar  ↑↓=navega  Enter=detalhes
```

**Componentes Textual:**
- `DataTable` para a lista principal (reativo, ordenável com clique)
- Painel de filtros (toggle com `f`): `Input` widgets para genre, sort, top, min/max hours; `Select` para progress/category
- Painel de detalhes (toggle com `Enter`): exibe todos os campos do jogo selecionado
- Colunas `Gêneros` e `Tags` ocultadas por padrão, `g`/`t` toggleam

**Comportamento:**
- Inicia com valores do CLI (`--top`, `--sort`, `--genre`, etc.)
- Filtros aplicam em tempo real (reactive binding)
- `s` abre prompt de filename e chama `save_results()`

**Arquivo:** `tui.py` (reescrita completa)  
**Nova dependência:** `textual` (adicionar a `requirements.txt`)

---

### 6. Print verboso do scan

**Problema:** `build_library()` em `fetch.py` imprime cada jogo scaneado; na prática inútil pois quase todos vêm do cache.

**Solução:**
- Adicionar `verbose: bool = False` a `build_library()`
- Flag `--verbose` / `-v` em `main.py` passada para `build_library()`
- Default silencioso: só imprime jogos **novos** (não encontrados no cache)
- Com `--verbose`: comportamento atual (imprime todos)

**Arquivos:** `fetch.py`, `main.py`

---

## Arquivos tocados

| Arquivo | Mudança |
|---------|---------|
| `main.py` | help melhorado, `--verbose`, `--show-tags`, passa args pro TUI, aviso top < N |
| `fetch.py` | `build_library(verbose=False)` |
| `tui.py` | reescrita completa com Textual |
| `requirements.txt` | + `textual` |
| `tests/` | novos testes para verbose, show-tags, top warning |

## Fora de escopo

- Item 3 (coleções Steam) — adiado
- Mudanças em `score.py`, `classify.py`, `fetch.py` (além do verbose)
- Novos critérios de score
