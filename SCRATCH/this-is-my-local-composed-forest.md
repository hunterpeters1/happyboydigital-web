# Happy Boy Digital — "Nuremberg Chronicles" Style Guide & Asset Plan

## Context

happyboydigital-web is a flat static site (one `style.css`, one font, no build step) with a warm parchment/ink/gold palette already in place. There's a live "Asset Manifest" (a Claude Artifact you already made) tracking 8 graphics still owed to the site — nav mark, theme-toggle sun/moon icons, an app icon, 6 blog emoji replacements, 2 social-preview images, a site background (already in progress in Inkscape as `assets/HBDbackground.svg`), and a parked comic wordmark.

You want the replacements to read as one cohesive, personal illustration style inspired by the *Nuremberg Chronicle* (1493) — dense woodcut/engraving linework, ink-on-vellum feel — built around your existing love of sun/moon imagery, without turning the site into a costume-party pastiche. You'll draw everything yourself in Inkscape; this plan gives you the exact hex values, sizing, and per-asset direction so the art drops straight into the existing code.

**Your calls, confirmed:**
- Style intensity: **accent motif, not full period retheme** — the modern layout stays; the *icons* get woodcut treatment, done intentionally so it reads as "Happy Boy," not generic old-timey.
- Sun/moon: **ship the simple toggle-icon pair now**; a bigger circular "cosmography diagram" motif (echoing the Chronicle's Six Days of Creation page) is a noted future idea, not scoped yet.
- Palette: **keep the current one as-is** — it already reads as parchment/ink/gold leaf.

---

## 1. Hex palette (for Inkscape swatches)

Source of truth: `css/style.css` lines 12–37.

**Light mode**
| Token | Hex | Use |
|---|---|---|
| `--hbd-beige` | `#F6F1E8` | page ground |
| `--hbd-card` | `#FFFDF9` | card/mat surface |
| `--hbd-brown` | `#6B4226` | body ink |
| `--hbd-deep` | `#4A2C18` | headings, primary line-art ink |
| `--hbd-yellow` | `#F9D93A` | accent / "gold leaf" |
| `--hbd-yellow-dark` | `#E0B516` | hover / kicker text |
| border | `rgba(107,66,38,0.15)` | hairlines |
| shadow | `rgba(74,44,18,0.08)` | card drop shadow |

**Dark mode** (`[data-theme="dark"]`)
| Token | Hex |
|---|---|
| `--hbd-beige` | `#1B140F` |
| `--hbd-brown` | `#E8DCC0` |
| `--hbd-deep` | `#F9D93A` (headings *become* the gold) |
| `--hbd-card` | `#241C15` |
| border | `rgba(249,217,58,0.2)` |
| shadow | `rgba(0,0,0,0.45)` |

**Constant across both themes:** `#F9D93A` (yellow) and `#E0B516` (yellow-dark) never flip — they're your one fixed accent.

**Separate "glitch" accent** (logo hover RGB-split effect + 2 stickers only — keep this out of the woodcut illustrations, it's a distinct digital-glitch flourish, not part of the Chronicle world): magenta `#FF00C8`, cyan `#00E7FF`.

---

## 2. The style rule

Draw everything as **single-color ink line art on the parchment**, in the spirit of a woodcut engraving, but simplified for UI scale:

- **One ink color does the drawing** — `#4A2C18` in light mode, and let it auto-flip via `stroke="currentColor"` (the codebase already does this for the toggle icons — `.theme-toggle svg { color: var(--hbd-on-yellow) }`). Reuse that pattern for the blog icons too, so you only draw one file per icon, not a light/dark pair.
- **Yellow (`#F9D93A`) is gold leaf, not a fill color** — use it sparingly as a filled accent (a solid sun disc, a filled star) the way an illuminated manuscript highlights one thing per page, not as broad icon fill.
- **Crosshatch/engraving detail scales with canvas size**: save real crosshatching for the big pieces (og:images, the background, the Atelier icon) where it has room to breathe. At 16–24px (toggle + blog icons), keep it to clean single-weight strokes — fine hatching will just turn to mud at that size.
- **Family resemblance**: your existing hand-drawn stickers (`assets/Stickers/Smiley.svg`, `Pingus.svg`, etc.) already establish a "Happy Boy" line-art hand. Match their line weight/character in the new icons so the whole system reads as one artist's work, not two different icon packs.

---

## 3. Per-asset direction (from your Asset Manifest)

| # | Asset | Size | Color rule | Notes |
|---|---|---|---|---|
| 01 | Nav mark & favicon | 22×22 nav / ≥64×64 favicon, SVG | `#4A2C18` flat — always sits on the yellow bar, no light/dark split needed | Replaces the generic Icons8 smiley; this is your clearest "brand mark" moment |
| 02 | Sun/moon toggle | 16×16 in 30×30 button, SVG | `stroke="currentColor"` → auto-resolves to `#4A2C18` in both themes | Keep the `.icon-sun`/`.icon-moon` classes so the existing CSS crossfade keeps working. Simple woodcut sun (disc + rays) and crescent moon — this is the pair to ship now |
| 03 | Atelier app icon | ≥320×320 (640 for retina), PNG/SVG | Ink `#4A2C18` line art, `#F6F1E8` ground, `#F9D93A` as one gold accent | Enough size to afford real engraving detail — a natural spot for a small Happy-Boy-at-the-easel emblem |
| 04 | Blog section icons ×6 | ~24×24, SVG | `stroke="currentColor"` (matches heading ink both themes) | Replacing 🎨📚🖼️🎵📷💭 — draw as small woodcut emblems: palette+brush, open book, framed picture, lute/note, box camera, quill+thought |
| 05/06 | Social previews (default + Atelier) | 1200×630, PNG | `#F6F1E8` ground / `#4A2C18` ink / `#F9D93A` accent | Seen in social-app chrome, not the site theme — no light/dark pair needed. Biggest canvas you have — the one place a fuller Chronicle-style illustrated scene earns its keep |
| 07 | Site background | 1920×1080 per theme, SVG | Dark: `#1B140F` ground / `#E8DCC0` strokes (in progress). Light: `#F6F1E8` ground / `#4A2C18` or `#6B4226` strokes (not started) | This is `assets/HBDbackground.svg`, already underway — not yet wired into `style.css` (hook point at line 60). Finish the light companion using the same linework, just recolored ink, so both themes match |
| 08 | Comic wordmark | 849×79, PNG | — | Parked/shelved, already at spec, no action needed |

---

## 4. Parked idea (not scoped this round)

You liked the idea of the sun/moon growing into a **circular cosmography-diagram illustration** (echoing the Chronicle's "Six Days of Creation" concentric-circle spread) — e.g. one richer piece reused/cropped across the toggle, nav mark, and maybe a hero/background element. Worth returning to once the base icon set (items 01–04) ships and you've got a feel for the linework at small sizes. Could also be a fun full-page or hero moment later rather than squeezed into a 16px toggle.

---

## 5. Wire-in points (once art exists)

No code changes needed today — this is a style/reference deliverable. When each SVG/PNG is ready, the exact drop-in locations are already documented in your Asset Manifest (file + line links per item), e.g.:
- Nav mark: `css/style.css:112`, referenced on all pages starting `index.html:22`
- Toggle icons: `css/style.css:116`, button markup e.g. `index.html:36`
- Blog icons: `css/style.css:591`, `blog/template.html:79`
- Background hook: `css/style.css:60` (currently just a comment, no rule yet)

I can wire any of these into the code the moment you hand me finished files — just say the word.
