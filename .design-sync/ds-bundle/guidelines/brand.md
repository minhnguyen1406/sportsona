# Sportsona brand guidelines — v3, "The Rise"

Sportsona is a personalised, multi-sport companion app — F1-first. The brand is
**Electric Grape + Rose on warm Sand**, set in **Figtree only**, with **no
gradients**. Source of truth for values: `web/src/app.css` in the app repo
(mirrored in `tokens/tokens.css`).

## Four rules, if nothing else survives

1. **The head stays.** The logo is three ascending bars where the tallest grows a head. No head, no logo.
2. **One rose per view.** Rose means *you*, or *now*. Two rose things on a screen and it means neither.
3. **Flat fills only.** No gradients, glows, glass or elevation shadows. Depth comes from the grape scale.
4. **Numbers get 900 and tight tracking.** It is how one typeface sounds like sport.

## Palette

| Role | Name | Hex | Use |
|---|---|---|---|
| Primary | Electric Grape (Grape 700) | `#2A1247` | Dark surfaces, headers, primary actions on light |
| Accent | Rose 500 | `#E8607F` | "You" and "now": logo head, the one CTA, your row in a table |
| Series 2 | Court Teal | `#16B8A3` | Second data series, sport tags. Never means good/bad |
| Series 3 | Volt | `#C8E63C` | Streaks, records, highlights on grape. Unusable on light |
| Ground (light) | Sand 100 | `#F3EEE2` | Page background — warm, never white or cool grey |
| Card (light) | Sand 50 | `#FBF7EF` | Cards and panels on Sand |
| Text (light) | Ink | `#211228` | Body text on Sand (15.4:1) |

Grape scale (dark surfaces step 900 → 800 → 700): 900 `#150724` page ground ·
800 `#1F0D35` chrome and cards · 700 `#2A1247` card surfaces · 600 `#3A2159`
borders and hover · 300 `#9B7FC0` secondary text on dark (min 13px) ·
200 `#C9BADD` body/caption text on dark.

Rose tints: 700 `#B0304F` (rose **text** on light) · 500 `#E8607F` · 400 `#F0839B` · 100 `#FCE4EA`.
Sand: 50 `#FBF7EF` · 100 `#F3EEE2` · 200 `#E9E1CE` (borders, muted fills) · 500 `#8A7A60` (swatches only, never text) · 600 `#5F5443` (secondary text on light).

Semantic: Success `#1F9E5A` · Danger / Flag Red `#C42B3E` · Warning `#E39A0B` · Info `#3B7FC4`.
Rose and Flag Red both read "pink-red" at a glance — danger always carries an icon or the word, never colour alone.

### Contrast rules (measured)

- **Never Rose 500 text on Sand** (2.8:1). Use Rose 700, or the `.text-rose-ink` class.
- Volt and Teal 500 are safe on grape, not as text on light.
- Grape 300 on grape only at 13px and up; use Grape 200 for small text on dark.

### Balance

Roughly by area: Grape 55% · Sand 30% · Rose 8% · Teal 4% · Volt 3%.

### One role flips between themes

On light, `--primary` is Grape and `--accent` is Rose. On dark, Grape *is* the
surface, so `--primary` becomes Rose. Don't hard-code grape buttons.

## Typography

**Figtree Variable, 300–900. Upright only — no italics, no second typeface.**

| Role | Weight | Size | Tracking |
|---|---|---|---|
| Stat | 900 | 40–96px | −0.045em, tabular |
| Display | 800 | 44–56px | −0.04em |
| Heading | 800 | 32–36px | −0.032em |
| Subhead | 800 | 20–24px | −0.024em |
| Label | 700 | 16–18px | −0.015em |
| Body large | 500 | 15px / 1.6 | — |
| Body | 500 | 13px / 1.6 | — |
| Eyebrow | 800 | 11px | +0.14em, uppercase |

Numerals: `.sp-stat` on hero figures (40px+), `.sp-fig` on anything in a table
or column (tabular figures are non-negotiable there). Numbers inside a sentence
inherit normally.

## The mark — "The Rise"

Three ascending bars; the tallest grows a head. A performance chart and a
person are the same object. On a 64-unit grid: bars `x=13 y=39 w=9 h=14`,
`x=27 y=30 w=9 h=23`, `x=41 y=25 w=9 h=28` (all `rx=4.5`), head `cx=45.5 cy=14 r=6`.
The 5 units of air between head and bar is what reads as a person — never close it.

- On Grape: Sand bars, Rose head. On Sand: Grape bars, Rose head. On Rose: Grape bars, Sand head.
- Minimum 16px. Never stretch, mirror, reorder, outline, or apply a gradient.
- Wordmark: "Sportsona" in Figtree 800 at −0.028em, followed by a rose period (a real glyph).

## Layout patterns

- **Cards:** radius 20px. On light, `1px solid hsl(var(--border))`; on dark, no border — the surface step separates.
- **Buttons:** pill, weight 800, 13px, `11px 19px` padding. Primary = rose fill with `#3A0C1C` text; ghost = transparent with a 1px inset ring.
- **Pills / chips:** `border-radius: 999px`.
- **Nav:** the active item is a filled pill, not an underline.
- **Your own row** in a standings table: Rose 100 background, Rose 700 position number, 800-weight name. That is the view's one rose element.
- **Transitions:** 0.16s `cubic-bezier(.2,.7,.3,1)`.

## Do / Don't

- **Do** keep page grounds Sand (light) or Grape 900 (dark).
- **Do** spend rose once per view.
- **Don't** use gradients, glows, glass, or shadows for elevation.
- **Don't** use Inter, Alfa Slab One, italics, brand red `#D63837`, dreamsicle orange or the cocoa gradient — that is the retired pre-v3 brand.
- **Don't** let Teal or Volt mean good or bad, or use them as a page background.
