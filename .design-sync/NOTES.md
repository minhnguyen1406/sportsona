# Design-sync notes

## Shape: tokens-only (not the converter path)

Sportsona's UI is **Svelte**. Claude Design's runtime renders **React** (or
framework-neutral web components), so the standard component converter does not
apply here. This sync ships **brand foundations only**: color tokens, fonts, and
guidelines. Designs made in Claude Design will look on-brand but are built from
generic components, not Sportsona's own.

## What's in the project (`ds-bundle/`)

- `styles.css` — entry stylesheet; `@import`s fonts + tokens, includes the
  Tailwind v4 `@theme inline` mapping and base defaults.
- `tokens/tokens.css` — all HSL CSS variables, light (`:root`) + dark (`.dark`).
- `fonts/` — self-hosted Inter (variable) + Alfa Slab One woff2 (latin subset),
  fetched from Google Fonts. Self-hosted so they render regardless of CSP.
- `guidelines/brand.md` — palette table (hex), typography, do/don't.
- `README.md` — the conventions header inlined into the design agent's prompt.

## Source of truth

`web/src/app.css` — the Tailwind v4 theme + CSS variables. When the app's tokens
change, re-generate `ds-bundle/tokens/tokens.css` and `ds-bundle/styles.css` from
it, then re-upload (see below).

## Re-sync

No converter/anchor for this shape — re-sync is manual:
1. Update `ds-bundle/` files from `web/src/app.css`.
2. `finalize_plan` (same writes/deletes globs), then `write_files` the changed files.
3. Reconcile deletes for anything removed, then re-arm `_ds_needs_recompile`.

Project id is pinned in `config.json`.

## If we ever want real components in Claude Design

Two options, both real work: (a) port the ~8 UI primitives (Button, Card, Input,
Logo, ResultsTable, …) to a small React package and run the full converter sync;
(b) compile the Svelte primitives to web components — but Svelte custom elements
use shadow DOM by default, which walls them off from the global Tailwind sheet
(needs per-component style injection or `shadow: 'none'`).
