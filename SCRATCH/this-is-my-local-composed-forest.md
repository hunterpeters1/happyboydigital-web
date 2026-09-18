## 1.Bible

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


## 2. Per-asset direction (from your Asset Manifest)

| # | Asset | Size | Color rule | Notes |
|---|---|---|---|---|
| 01 | Nav mark & favicon | 22×22 nav / ≥64×64 favicon, SVG | `#4A2C18` flat — always sits on the yellow bar, no light/dark split needed | Replaces the generic Icons8 smiley; this is your clearest "brand mark" moment |
| 02 | Sun/moon toggle | 16×16 in 30×30 button, SVG | `stroke="currentColor"` → auto-resolves to `#4A2C18` in both themes | Keep the `.icon-sun`/`.icon-moon` classes so the existing CSS crossfade keeps working. Simple woodcut sun (disc + rays) and crescent moon — this is the pair to ship now |
| 03 | Atelier app icon | ≥320×320 (640 for retina), PNG/SVG | Ink `#4A2C18` line art, `#F6F1E8` ground, `#F9D93A` as one gold accent | Enough size to afford real engraving detail — a natural spot for a small Happy-Boy-at-the-easel emblem |
| 04 | Blog section icons ×6 | ~24×24, SVG | `stroke="currentColor"` (matches heading ink both themes) — draw as small woodcut emblems: palette+brush, open book, framed picture, lute/note, box camera, quill+thought |
| 05/06 | Social previews (default + Atelier) | 1200×630, PNG | `#F6F1E8` ground / `#4A2C18` ink / `#F9D93A` accent | Seen in social-app chrome, not the site theme — no light/dark pair needed. Biggest canvas you have — the one place a fuller Chronicle-style illustrated scene earns its keep |
| 07 | Site background | 1920×1080 per theme, SVG | Dark: `#1B140F` ground / `#E8DCC0` strokes (in progress). Light: `#F6F1E8` ground / `#4A2C18` or `#6B4226` strokes (not started) | This is `assets/HBDbackground.svg`, already underway — not yet wired into `style.css` (hook point at line 60). Finish the light companion using the same linework, just recolored ink, so both themes match |
| 08 | Comic wordmark | 849×79, PNG | — | Parked/shelved, already at spec, no action needed |

---

