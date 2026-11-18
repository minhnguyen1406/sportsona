# Sportsona design system (brand v3 — "The Rise")

This project carries Sportsona's **brand foundations**: colour tokens, the
Figtree typeface, numeral utilities and guidelines. It does not ship live
components (the app is Svelte), so build layouts from plain HTML/React with the
vocabulary below and everything reads as Sportsona.

**Ignore the retired brand.** Anything in this project showing brand red
`#D63837`, dreamsicle orange, a cocoa gradient, Inter or Alfa Slab One is
pre-v3 exploration, not the current system.

## Setup

- **Fonts and base styles are already applied.** `styles.css` sets the page to
  Figtree on `--background` with `--foreground` text. Do not import other fonts.
- **Dark mode:** add the `dark` class to `<html>` or a wrapping element. Light is
  Sand `#F3EEE2`; dark is flat Grape 900 `#150724`. Design both.

## Four rules

1. **One rose per view.** Rose means "you" or "now". Pick the single element that earns it.
2. **Flat fills only.** No gradients, glows, glass, or shadows for elevation. On dark, depth is the step Grape 900 → 800 → 700.
3. **Figtree only, upright.** No italics, no second typeface.
4. **Numbers get weight.** `.sp-stat` on hero figures, `.sp-fig` in tables.

## Styling idiom

Semantic colours are **bare HSL channel triples**; raw brand colours are hexes.

- Semantic (flip with theme): `color: hsl(var(--foreground))`,
  `background: hsl(var(--card))`, alpha via `hsl(var(--accent) / 0.12)`.
- Raw brand scale (never flips): `background: var(--sp-grape-800)`,
  `color: var(--sp-sand-100)`. Use for always-grape chrome and for
  rose/teal/volt fills.
- If the canvas compiles Tailwind v4, the semantic tokens are utilities:
  `bg-background` `text-foreground` `bg-card` `bg-primary`
  `text-primary-foreground` `bg-accent` `text-accent-foreground` `bg-muted`
  `text-muted-foreground` `border-border` `ring-ring`.

### Token vocabulary (use these exact names)

Surfaces: `--background` `--foreground` `--card` `--card-foreground` `--popover` `--popover-foreground`
Brand: `--primary` `--primary-foreground` (Grape on light, **Rose on dark**) · `--accent` `--accent-foreground` (Rose)
Support: `--secondary` `--secondary-foreground` `--muted` `--muted-foreground`
Status: `--success` `--warning` `--info` `--destructive` (each with `-foreground`)
Lines: `--border` `--input` `--ring`
Series (charts, sport tags — never semantic): `--chart-1` … `--chart-5`
Raw scale: `--sp-grape-900` `--sp-grape-800` `--sp-grape-700` `--sp-grape-600`
`--sp-grape-300` `--sp-grape-200` · `--sp-rose-700` `--sp-rose-500`
`--sp-rose-400` `--sp-rose-100` · `--sp-sand-100` `--sp-sand-500`
`--sp-sand-600` · `--sp-teal-500` `--sp-teal-300` · `--sp-volt-500` ·
`--sp-warning` · `--sp-on-rose` (dark ink for text on a rose fill)
Shape: `--radius` (14px) `--radius-md` (14px) `--radius-lg` (20px, cards) `--radius-xl` (26px); pills use `999px`.

### Classes

- `.sp-stat` — hero numbers, 40px and up (weight 900, tight tracking, tabular).
- `.sp-fig` — any number in a table or column (weight 800, tabular).
- `.text-rose-ink` — rose **text**. Rose 500 on Sand fails contrast (2.8:1), so
  never set `color` to `--sp-rose-500` or `--accent` on a light surface; use
  this class (Rose 700 on light, lifted rose on dark).

### Type scale

Display 800 / 44–56px / −0.04em · Heading 800 / 32–36px / −0.032em ·
Subhead 800 / 20–24px · Body 500 / 13–15px / 1.6 ·
Eyebrow 800 / 11px / +0.14em uppercase.

## The mark

Three ascending bars; the tallest grows a rose head. Bars take the surface's
contrast colour via `currentColor`; the head is always rose.

```html
<svg width="40" height="40" viewBox="0 0 64 64" aria-label="Sportsona">
  <g fill="currentColor">
    <rect x="13" y="39" width="9" height="14" rx="4.5"/>
    <rect x="27" y="30" width="9" height="23" rx="4.5"/>
    <rect x="41" y="25" width="9" height="28" rx="4.5"/>
  </g>
  <circle cx="45.5" cy="14" r="6" fill="#E8607F"/>
</svg>
```

Never stretch, outline, reorder or close the gap under the head.

## Where the truth lives

- `styles.css` — entry stylesheet (fonts, tokens, Tailwind mapping, numeral classes).
- `tokens/tokens.css` — every token, light and dark, commented with hexes.
- `guidelines/brand.md` — palette, contrast rules, type scale, layout patterns, do/don't.

## One idiomatic snippet

```html
<!-- A stat card: the figure is this view's one rose element. -->
<div style="background: hsl(var(--card)); border: 1px solid hsl(var(--border));
            border-radius: var(--radius-lg); padding: 20px; color: hsl(var(--foreground));">
  <p style="font-size: 11px; font-weight: 800; letter-spacing: .14em;
            text-transform: uppercase; color: hsl(var(--muted-foreground)); margin: 0;">
    Stat of the day
  </p>
  <div class="sp-stat text-rose-ink" style="font-size: 64px; margin-top: 12px;">5</div>
  <p style="font-size: 13px; line-height: 1.6; margin: 8px 0 0;">
    Belgian Grand Prix wins for Lewis Hamilton since 2010.
  </p>
  <button style="margin-top: 16px; background: hsl(var(--primary));
                 color: hsl(var(--primary-foreground)); border: 0; border-radius: 999px;
                 font: 800 13px 'Figtree', sans-serif; padding: 11px 19px;">
    See the record
  </button>
</div>
```
