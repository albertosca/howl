# Backlog

- **`--sort composto` is a Portuguese identifier in the public CLI API** (found 2026-08-25 during the i18n work). Users type `howl --sort composto`. Renaming it to `composite` breaks anyone already using it, so it needs a deliberate call: keep it, add an alias, or change it in a major release.
- **`--show-finished` looks for a Portuguese collection name** (found 2026-08-25). `FINISHED_COLLECTION = "Terminados"` is hardcoded in `steam_hltb/sources/collections.py:7`, while `--help` promises "the 'Finished' collection". An English-speaking user's collection is never excluded. Predates the i18n branch. Fixing it changes behaviour, so it needs a decision: match both names, make it configurable, or follow the selected language.
