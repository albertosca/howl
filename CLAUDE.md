# howl — development standards

## Mandatory cycle

Before any change: `./venv/bin/pytest` to establish a green baseline.
Before reporting done: `./venv/bin/pytest` again. Never say "done" without running the suite.

## Quality gate

```bash
./venv/bin/ruff check --fix steam_hltb/ tests/
./venv/bin/ruff format steam_hltb/ tests/
./venv/bin/mypy steam_hltb
./venv/bin/pytest
```

All four must pass before committing. In the order above.

## Language

Everything in English — code, comments, docstrings, commits, docs, user-facing output.
Exception: `README.pt-BR.md` stays in Portuguese (explicit bilingual copy).

## Comments and docstrings

**Rule**: only comment when the WHY is non-obvious. Never explain the WHAT.

```python
# GOOD — non-obvious WHY
_TOKEN_EXPIRY_MARGIN_S = 60  # renews token 60s before expiry (clock skew buffer)
# external_games.category = 1 is the Steam platform code in the IGDB API.

# BAD — WHAT (the name already says it)
def _load_token():
    """Reads the token from disk."""  # ← delete

def get_token():
    """
    Returns a valid token.
    - If absent: None
    - If cached: uses cache
    """  # ← delete; the code already shows this
```

Single-line docstrings: only when the function has surprising behaviour that doesn't fit an inline comment. Concrete examples in the docstring are allowed when the transform is non-obvious (e.g. `_normalize_for_igdb` with before/after result).

Multi-line docstrings with bullet-points describing the flow: **never**.

## Coverage

100% mandatory, gate active (`--cov-fail-under=100`).

`# pragma: no cover` only on genuinely unreachable branches. Never to escape a hard test.

## Type annotations

mypy strict. `dict[str, Any]` where the schema is heterogeneous (cache entries). Aliases in `core/types.py`:
- `Game = dict[str, Any]` — ranking row (has score, hours, etc.)
- `Filters = dict[str, Any]` — filter parameters from the UI

`steam_games: list[dict[str, Any]]` — raw dicts from the Steam API, **not** `list[Game]`.

## No defensive code

Don't validate what can't happen. Don't add fallbacks for internally impossible scenarios. Validate only at system boundaries (user input, external APIs).

## No drive-by

Bug fix doesn't authorize cleanup around it. Refactor doesn't authorize adding a feature. If something bad is spotted out of scope, mention it as a follow-up and leave it for later.

## Named constants for magic values

```python
# BAD
if count < 3:
if sim < 0.6:

# GOOD
if count < MIN_RATING_COUNT:
if sim < _IGDB_MIN_SIMILARITY:
```

## Mocks in tests

Lambdas simulating functions with `**kwargs` must reflect the real signature:
```python
# When the real function has verbose=False as default:
lambda c, t, name, **kw: result   # accepts extra kwargs without breaking
```

## Package structure

```
steam_hltb/
  core/      — score, classify, selection, types
  sources/   — fetch (Steam/HLTB), igdb, collections
  config/    — paths, prompts, setup
  ui/        — args, report, tui, interactive
  main.py
tests/       # mirrors steam_hltb/
```

## CLI flags

- `--verbose` / `-v`: controls detailed output in long operations (`--migrate-igdb`, `--migrate-cache`, `--refresh`)
- Never hardcode `verbose=True` in main — always `verbose=args.verbose`
- `--refresh`: fetches new games only (same as default behaviour)
- `--refresh-all`: re-fetches all games including cached ones (slow)

## Commits

Propose message before executing. Wait for explicit OK. HEREDOC to preserve formatting:
```bash
git commit -m "$(cat <<'EOF'
type(scope): short description

Body explaining the WHY if relevant.
EOF
)"
```
