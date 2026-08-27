# Backlog

All four items recorded during the 2026-08 outreach work are resolved. Kept here as
context for the decisions rather than deleted outright.

- ~~**`--sort composto` is a Portuguese identifier**~~ — resolved 2026-08-27. `composite` is
  canonical; `composto` and the undocumented `custom` resolve to it through `normalize_sort`
  and are dropped at 1.0. Flag values are API identifiers, so they stay English and the i18n
  catalogs never touch them.
- ~~**`--show-finished` looks for a Portuguese collection name**~~ — resolved 2026-08-27. It was
  never a language problem: `"Terminados"` was one person's collection name hardcoded as a
  constant. Now `HOWL_FINISHED_COLLECTION` / `--finished-collection`, with no default, since
  any default is wrong for everyone who did not pick it.
- ~~**Duplicate rows for the same game**~~ — resolved 2026-08-27. Deduplicated on appid, and on
  name only when release year and Metacritic agree, so a remake sharing a title with its
  original is not swallowed.
- ~~**Mock-based tests cannot detect IGDB schema drift**~~ — partially resolved 2026-08-27. Two
  guards pin the field names the queries depend on and fail when a query is edited. **They do
  not prove the names are still correct upstream** — only a credentialed call does that, and
  that remains a manual check before releases. Reopen this if IGDB announces API changes.
