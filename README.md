🇺🇸 **English** · 🇧🇷 [Português](README.pt-BR.md)

# HOWL

**Hoard Optimizer, What to Launch**

[![CI](https://github.com/albertosca/howl/actions/workflows/ci.yml/badge.svg)](https://github.com/albertosca/howl/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/howl-steam-backlog)](https://pypi.org/project/howl-steam-backlog/)
![Coverage](https://raw.githubusercontent.com/albertosca/howl/main/.github/badges/coverage.svg)
![Ruff](https://raw.githubusercontent.com/albertosca/howl/main/.github/badges/ruff.svg)

<!-- Coverage/Ruff são SVGs locais (sem serviço externo). Regenerar com:
       pip install "genbadge[coverage]" anybadge
       pytest --cov-report=xml && genbadge coverage --local -i coverage.xml -o .github/badges/coverage.svg
       anybadge --label="code style" --value=ruff --file=.github/badges/ruff.svg --color="#261230" -o
     O coverage fica sempre correto: o gate --cov-fail-under=100 quebra o CI se cair de 100%. -->

Ranks your Steam library by quality × time invested using data from [HowLongToBeat](https://howlongtobeat.com), Metacritic and Steam Reviews. No more decision paralysis staring at your backlog.

```
  #  Name                                            Year   MC   Steam   HLTB   Played      Score
---  ---------------------------------------------- ----  ----  ------  -----  --------  --------
  1  Hades                                          2020    93     97%    22h        0h      20.3
     ↳ action, roguelike
  2  Hollow Knight                                  2017    87     95%    40h        5h      14.4
     ↳ action, platformer
```

## Requirements

- Python 3.11+
- Steam API Key (free, instructions below)
- Steam account with public profile and library (or private, using your own key)

## Installation

```bash
pip install howl-steam-backlog
```

Or with [pipx](https://pipx.pypa.io/) (recommended for CLI tools — isolated environment):

```bash
pipx install howl-steam-backlog
```

**For development:**

```bash
git clone https://github.com/albertosca/howl.git
cd howl
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

After installing, the `howl` command becomes available:

```bash
howl --help
```

## Configuration

### Quick way: `howl --setup`

```bash
howl --setup
```

The interactive wizard walks you through the required variables, validates them live against the Steam API, and writes them to `~/.config/howl/.env` (loaded automatically, created with `0600` permissions). If you still have a legacy `.env` in the current directory, it offers to migrate it.

### Manual way: environment variables

| Variable | Required | What it is |
|---|---|---|
| `STEAM_API_KEY` | yes | Steam Web API key |
| `STEAM_USERNAME` | yes | Vanity URL of your profile (e.g. `gabelogannewell`) |
| `STEAM_VDF_PATH` | no | Path to `sharedconfig.vdf` (collection filters) |
| `IGDB_CLIENT_ID` | no | Twitch app Client ID (scores for delisted games) |
| `IGDB_CLIENT_SECRET` | no | Twitch app Client Secret |

**STEAM_API_KEY:**
1. Go to https://steamcommunity.com/dev/apikey
2. Log in with your Steam account
3. Fill "Domain Name" with any value (e.g. `localhost`)
4. Copy the generated key

**STEAM_USERNAME:**
The vanity URL of your Steam profile: `steamcommunity.com/id/gabelogannewell` → username is `gabelogannewell`

**IGDB_CLIENT_ID and IGDB_CLIENT_SECRET (optional):**
IGDB complements Metacritic for games where Steam returns no score (delisted, very old, etc.).

1. Go to https://dev.twitch.tv/console and log in with your Twitch account (create one if needed — it's free)
2. Click **Register Your Application**
3. Fill in:
   - **Name:** anything (e.g. `howl-igdb`)
   - **OAuth Redirect URLs:** `http://localhost`
   - **Category:** `Website Integration`
4. Click **Create**
5. In the app list, click **Manage**
6. Copy the **Client ID**
7. Click **New Secret** and copy the **Client Secret** (shown only once)

With the credentials configured, run:
```bash
howl --migrate-igdb
```
The OAuth token is generated and refreshed automatically. You don't need to repeat this process.

**STEAM_VDF_PATH (optional):**
Required to use `--collection` and automatic exclusion of finished games.

| System | Default location |
|---|---|
| macOS | `~/Library/Application Support/Steam/userdata/<steamid>/7/remote/sharedconfig.vdf` |
| Linux | `~/.steam/steam/userdata/<steamid>/7/remote/sharedconfig.vdf` |
| Windows | `C:\Program Files (x86)\Steam\userdata\<steamid>\7\remote\sharedconfig.vdf` |

The `<steamid>` is numeric (different from the vanity URL). Find it in: Steam → Settings → Account → Steam account ID.

Credentials live in `~/.config/howl/.env` (respects `$XDG_CONFIG_HOME`). The wizard writes this file for you; to set it up by hand, create it with one `KEY=value` per line:

```bash
# ~/.config/howl/.env
STEAM_API_KEY=your_key_here
STEAM_USERNAME=your_username
# STEAM_VDF_PATH is optional (collection filters)
STEAM_VDF_PATH=/path/to/sharedconfig.vdf
```

Prefer this over exporting the keys in your shell profile (`~/.zshenv`, `~/.bashrc`): shell exports leak the values to every process on your system.

## Usage

```bash
# First run: populates the cache (may take ~5 min for 300 games)
howl --username my_steam_id --verbose

# Top 10 good and short games (default)
howl --username my_steam_id

# Interactive visual interface
howl --username my_steam_id --tui

# Filter by genre, progress and formula
howl --username my_steam_id --genre "action,rpg" --not-started --sort quick-wins

# Filter by release era
howl --username my_steam_id --era "2010-2015,2015-2020"

# See what's available in the cache
howl --list-genres
howl --list-tags
howl --list-collections
```

With `STEAM_USERNAME` set in the environment, `--username` can be omitted.

## Sort formulas (`--sort`)

| Name | Formula | When to use |
|------|---------|-------------|
| `shortest` | composite / √h | Good and short games — default |
| `longest` | composite × √h | Epics worth every hour |
| `rated` | Metacritic only | Most critically acclaimed |
| `loved` | Steam % positive | Most loved by players |
| `quick-wins` | composite² / h | Maximum quality in less time |
| `hidden-gems` | steam × (1 − mc/100) | Loved by players, ignored by critics |
| `composto` | 0.5×mc + 0.5×steam | Configurable weighted average |

`composite` = weighted average of Metacritic and Steam reviews (tune with `--weight-mc` / `--weight-steam`).

Games without Metacritic or Steam reviews get zero weight on that source (the other takes 100%).

## Available filters

| Flag | Values | Default |
|------|---------|---------|
| `--sort` | see table above | `shortest` |
| `--genre` | comma-separated | — |
| `--genre-any` | comma-separated | — |
| `--exclude-genre` | comma-separated | — |
| `--era` | `pre-2005` `2005-2010` `2010-2015` `2015-2020` `2020+` `unknown` | all |
| `--not-started` | — | — |
| `--in-progress` | — | — |
| `--all-progress` | — | not-finished |
| `--category` | `all` `singleplayer` `coop` | `all` |
| `--min-hours` / `--max-hours` | hours (HLTB) | — |
| `--collection` | Steam collection name | — |
| `--top` | integer | `10` |
| `--show-finished` | — | excluded |

## TUI (visual interface)

```bash
howl --username my_steam_id --tui
```

| Key | Action |
|-------|--------|
| `f` | Open/close filter panel |
| `g` | Toggle genres column |
| `t` | Toggle Steam categories column |
| `s` | Save current result to CSV + Markdown |
| `q` | Quit |

The filter panel applies all changes in real time.

## Cache

HLTB, Steam Reviews and game detail data are cached in `games_cache.json` to avoid repeated requests. To update:

```bash
# Re-fetch everything from scratch
howl --username my_steam_id --refresh

# Fill missing fields in old entries (genres, release_year)
howl --migrate-cache

# Fetch IGDB scores for games without Metacritic (requires IGDB_CLIENT_ID and IGDB_CLIENT_SECRET)
howl --migrate-igdb
```

`--migrate-cache` is useful if you had a cache from earlier versions that didn't have all fields.

`--migrate-igdb` fills critic scores via IGDB for games where Steam returns no Metacritic — especially useful for delisted games (e.g. the original Deus Ex: Human Revolution). It can be re-run at any time; games that already have IGDB data in the cache are skipped.

## Troubleshooting

**"Username not found on Steam"**
Check that the vanity URL is correct. Visit `https://steamcommunity.com/id/your_id/` — if it redirects to your profile, it's right.

**Games without Metacritic or Steam reviews**
Normal — not all games have data. They still show up but with score 0 in some formulas. Use `--sort loved` or `--sort rated` to see only games with data.

**"0 entries to migrate"**
The cache is already complete. If you just built the cache with `howl --verbose`, all games already come with every field.

**Cache with few games**
If the Steam library is set to private, the API returns 0 games. Go to Steam → Profile → Edit → set games to public (you can switch back to private afterwards).

## Development

```bash
pytest                          # run all tests
pytest tests/test_score.py -v   # specific module
```
