# Design-sync notes

## Shape: tokens-only (not the converter path)

Sportsona's UI is **Svelte**. Claude Design's runtime renders **React** (or
framework-neutral web components), so the standard component converter does not
apply here. This sync ships **brand foundations only**: color tokens, fonts, and
guidelines. Designs made in Claude Design will look on-brand but are built from
generic components, not Sportsona's own.

## What's in the bundle (`.design-sync/ds-bundle/`, committed)

- `styles.css` — entry stylesheet; `@import`s fonts + tokens, carries the
  Tailwind v4 `@theme inline` mapping, base defaults, and the `.sp-stat`,
  `.sp-fig`, `.text-rose-ink` utilities.
- `tokens/tokens.css` — every CSS variable: semantic HSL triples for light
  (`:root`) + dark (`.dark`), and the raw `--sp-*` brand scale.
- `fonts/` — self-hosted Figtree variable woff2 (latin + latin-ext) from Google
  Fonts. Self-hosted so it renders regardless of CSP.
- `guidelines/brand.md` — brand v3 palette, contrast rules, type scale, mark,
  layout patterns, do/don't.
- `README.md` — the conventions header inlined into the design agent's prompt.

The bundle is committed so a re-sync works from any machine (the pre-v3 bundle
was never committed, and the project sat on the retired red/dreamsicle brand
until 2026-11-17).

## Source of truth

`web/src/app.css` — the Tailwind v4 theme + CSS variables. `tokens/tokens.css`
and the `@theme` block in `styles.css` are extracted from it verbatim; the
guidelines and README are hand-written from the v3 handoff
(`design_handoff_rebrand/README.md` in the project).

## Re-sync

No converter/anchor for this shape — re-sync is manual:
1. Regenerate `ds-bundle/tokens/tokens.css` and `ds-bundle/styles.css` from
   `web/src/app.css`; update `guidelines/brand.md` + `README.md` if rules changed.
2. Check every token/class named in `README.md` exists in the bundle CSS.
3. `finalize_plan` with `localDir: .design-sync/ds-bundle`, writes limited to
   `styles.css`, `README.md`, `tokens/**`, `fonts/**`, `guidelines/**`,
   `_ds_needs_recompile`; deletes only for bundle files that were removed.
4. `write_files` (sentinel first and last), then `delete_files`.

**Never touch anything else in the project** — the root-level `Sportsona *.html`
explorations, `design_handoff_rebrand/`, and the loose `sportsona-*.css` files
are the owner's own design work, not sync output.

Project id is pinned in `config.json`.

## If we ever want real components in Claude Design

Two options, both real work: (a) port the ~8 UI primitives (Button, Card, Input,
Logo, ResultsTable, …) to a small React package and run the full converter sync;
(b) compile the Svelte primitives to web components — but Svelte custom elements
use shadow DOM by default, which walls them off from the global Tailwind sheet
(needs per-component style injection or `shadow: 'none'`).
