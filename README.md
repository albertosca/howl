# HOWL

**Hoard Optimizer, What to Launch**

Ranqueia sua biblioteca Steam por qualidade × tempo investido, usando dados do HowLongToBeat, Metacritic e Steam Reviews. Nunca mais fique paralisado na frente da backlog.

## Instalação

```bash
pip install -e ".[dev]"
```

Isso cria o comando `howl` disponível globalmente no ambiente.

## Uso rápido

```bash
# Top 10 jogos bons e curtos (padrão)
howl

# Interface visual interativa (htop-style)
howl --tui

# Filtrar por gênero e progresso
howl --genre "action,rpg" --not-started --top 20

# Ordenar por fórmula diferente
howl --sort quick-wins
howl --sort hidden-gems

# Filtrar por época de lançamento
howl --era "2010-2015,2015-2020"

# Ver coleções Steam disponíveis
howl --list-collections

# Mostrar apenas jogos da coleção "Jogando"
howl --collection Jogando
```

## Fórmulas de ordenação

| Nome | Fórmula | Quando usar |
|------|---------|-------------|
| `shortest` | composite / √h | Jogos bons e curtos |
| `longest` | composite × √h | Épicos que valem o tempo |
| `rated` | Metacritic puro | Aclamados pela crítica |
| `loved` | Steam % positivo | Favoritos dos jogadores |
| `quick-wins` | composite² / h | Qualidade máxima, tempo mínimo |
| `hidden-gems` | steam × (1 − mc/100) | Amados pelos players, ignorados pela crítica |
| `composto` | 0.5×mc + 0.5×steam | Média ponderada configurável |

O `composite` de cada fórmula é a média ponderada de Metacritic e Steam reviews (configurável com `--weight-mc` / `--weight-steam`).

## Filtros disponíveis

| Flag | Opções | Default |
|------|--------|---------|
| `--sort` | ver tabela acima | `shortest` |
| `--genre` | vírgula-separado | — |
| `--genre-any` | vírgula-separado | — |
| `--exclude-genre` | vírgula-separado | — |
| `--era` | `pre-2005`, `2005-2010`, `2010-2015`, `2015-2020`, `2020+`, `unknown` | todas |
| `--not-started` / `--in-progress` / `--all-progress` | — | não-zerados |
| `--category` | `all`, `singleplayer`, `coop` | `all` |
| `--min-hours` / `--max-hours` | horas HLTB | — |
| `--collection` | nome da coleção Steam | — |
| `--top` | inteiro | `10` |

## Coleções Steam

A ferramenta lê suas coleções do arquivo `sharedconfig.vdf` do Steam. Jogos marcados como **Terminados** são excluídos de todas as views por padrão (use `--show-finished` para incluí-los).

```bash
# Ver coleções disponíveis e contagem
howl --list-collections

# Filtrar só o que está "Jogando"
howl --collection Jogando
```

## Cache e migração

Os dados são cacheados em `games_cache.json`. Para popular gêneros e ano de lançamento em entradas antigas:

```bash
howl --migrate-cache   # ~15-30 min dependendo do tamanho da biblioteca
```

Para rebuscar tudo do zero:

```bash
howl --refresh
```

## TUI

```bash
howl --tui
```

| Tecla | Ação |
|-------|------|
| `f` | Abrir/fechar painel de filtros |
| `g` | Toggle coluna de gêneros |
| `t` | Toggle coluna de tags/categorias |
| `s` | Salvar resultado atual em CSV + Markdown |
| `q` | Sair |

## Variáveis de ambiente

```bash
export STEAM_API_KEY=sua_chave_aqui
```

Sem a variável, a ferramenta pede a chave interativamente.

## Desenvolvimento

```bash
# Rodar testes
pytest

# Rodar um arquivo específico
pytest tests/test_score.py -v
```
