# howl — padrões de desenvolvimento

## Ciclo obrigatório

Antes de qualquer mudança: `./venv/bin/pytest` pra estabelecer baseline verde.
Antes de reportar pronto: `./venv/bin/pytest` de novo. Nunca dizer "feito" sem rodar a suite.

## Gate de qualidade

```bash
./venv/bin/ruff check --fix steam_hltb/ tests/
./venv/bin/ruff format steam_hltb/ tests/
./venv/bin/mypy steam_hltb
./venv/bin/pytest
```

Todos os quatro têm que passar antes de commitar. Na ordem acima.

## Comentários e docstrings

**Regra**: só comentar quando o WHY é não-óbvio. Nunca explicar o WHAT.

```python
# BOM — WHY não-óbvio
_TOKEN_EXPIRY_MARGIN_S = 60  # renova 60s antes de expirar (folga de relógio)
# external_games.category = 1 é o código Steam na API do IGDB.

# RUIM — WHAT (o nome já diz)
def _load_token():
    """Lê o token do disco."""  # ← delete

def get_token():
    """
    Retorna token válido.
    - Se ausente: None
    - Se em cache: usa cache
    """  # ← delete; o código já mostra isso
```

Docstrings de uma linha: só quando a função tem comportamento surpreendente que não cabe em comentário inline. Exemplos concretos no docstring são permitidos quando o transform não é óbvio (ex: `_normalize_for_igdb` com o resultado antes/depois).

Docstrings multi-linha com bullet-points descrevendo o fluxo: **nunca**.

## Cobertura

100% obrigatório, gate ativo (`--cov-fail-under=100`).

`# pragma: no cover` só em ramos genuinamente inalcançáveis. Nunca pra fugir de teste difícil.

## Type annotations

mypy strict. `dict[str, Any]` onde o schema é heterogêneo (entradas de cache). Aliases em `core/types.py`:
- `Game = dict[str, Any]` — linha do ranking (tem score, horas, etc.)
- `Filters = dict[str, Any]` — parâmetros de filtro da UI

`steam_games: list[dict[str, Any]]` — dicts crus da API Steam, **não** `list[Game]`.

## Sem código defensivo

Não validar o que não pode acontecer. Não adicionar fallbacks para cenários impossíveis internamente. Validação só na fronteira com o usuário ou APIs externas.

## Sem drive-by

Bug fix não autoriza cleanup ao redor. Refactor não autoriza adicionar feature. Se notar algo ruim fora do escopo, mencionar como follow-up e deixar pra depois.

## Constantes nomeadas para magic values

```python
# RUIM
if count < 3:
if sim < 0.6:

# BOM
if count < MIN_RATING_COUNT:
if sim < _IGDB_MIN_SIMILARITY:
```

## Mocks em testes

Lambdas que simulam funções com `**kwargs` devem refletir a assinatura real:
```python
# Quando a função real tem verbose=False como default:
lambda c, t, name, **kw: result   # aceita kwargs extras sem quebrar
```

## Estrutura do pacote

```
steam_hltb/
  core/      — score, classify, selection, types
  sources/   — fetch (Steam/HLTB), igdb, collections
  config/    — paths, prompts, setup
  ui/        — args, report, tui, interactive
  main.py
tests/       # espelha steam_hltb/
```

## Flags CLI

- `--verbose` / `-v`: controla output detalhado em operações longas (`--migrate-igdb`, `--migrate-cache`, `--refresh`)
- Nunca hardcodar `verbose=True` no main — sempre `verbose=args.verbose`

## Commits

Propor mensagem antes de executar. Esperar OK explícito. HEREDOC para preservar formatação:
```bash
git commit -m "$(cat <<'EOF'
tipo(escopo): descrição curta

Corpo explicando o WHY se relevante.
EOF
)"
```
