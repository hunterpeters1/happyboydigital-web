#!/usr/bin/env python3
"""Check that a painting-grid page follows the page-weight rules.

Usage (from the repo root):
    python scripts/check-page-weight.py              # checks work.html
    python scripts/check-page-weight.py index.html   # or any other page(s)

Exits non-zero if a rule is broken, so it can be run before every commit.
The rules and the numbers behind them are in CLAUDE.md ("Page weight").
"""
import sys
from html.parser import HTMLParser
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is not installed. Run: pip install --upgrade pillow")

ROOT = Path(__file__).resolve().parent.parent

# ---- budgets: tweak here, not in the checks below -------------------------
MAX_THUMB_WIDTH = 900            # px; grid columns are ~376 CSS px, so 800 covers 2x screens
MAX_AVIF_BYTES = 220 * 1024      # per thumbnail (current largest is 197 KB)
MAX_JPEG_BYTES = 300 * 1024      # per fallback thumbnail (current largest is 247 KB)
MAX_PAGE_AVIF_BYTES = int(1.15 * 1024 * 1024)   # all thumbnails on one page, AVIF path
MAX_PAGE_JPEG_BYTES = int(1.6 * 1024 * 1024)    # same page on the JPEG fallback path
MAX_OTHER_IMAGE_BYTES = 150 * 1024              # any other raster <img> on the page
EAGER_COUNT = 3                  # first row on desktop loads immediately, the rest lazy
FORBIDDEN = ("/assets/originals/", "/assets/large/")   # full-size art: detail-page lightbox only
RASTER = (".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif")
# ---------------------------------------------------------------------------


class Scan(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []          # open tags, each (tag, classes)
        self.pictures = []       # finished pictures: {"sources": [...], "img": {...}}
        self.imgs = []           # every <img>: attrs + context
        self._pic = None

    def in_class(self, name):
        return any(name in cls for _, cls in self.stack)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = (a.get("class") or "").split()
        if tag == "picture":
            self._pic = {"sources": []}
        if tag == "source" and self._pic is not None:
            self._pic["sources"].append(a)
        if tag == "img":
            rec = {
                "attrs": a,
                "picture": self._pic,
                "thumb": self.in_class("project-thumb") or self.in_class("shelf"),
                "badge": "status-badge" in cls,
            }
            self.imgs.append(rec)
        if tag not in ("img", "source", "br", "meta", "link", "input", "hr"):
            self.stack.append((tag, cls))

    def handle_endtag(self, tag):
        if tag == "picture":
            self._pic = None
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break


def local(path):
    return ROOT / path.lstrip("/").split("?")[0]


def check(page):
    errors, warns = [], []
    scan = Scan()
    scan.feed((ROOT / page).read_text(encoding="utf-8"))

    thumbs = [r for r in scan.imgs if r["thumb"] and not r["badge"] and (r["attrs"].get("src") or "").lower().endswith(RASTER)]
    avif_total = jpeg_total = 0
    seen = set()

    for n, rec in enumerate(thumbs):
        a = rec["attrs"]
        src = a.get("src", "")
        name = src.rsplit("/", 1)[-1]
        pic = rec["picture"]
        if any(f in src for f in FORBIDDEN):
            errors.append(f"{name}: full-size art ({src}) used in a grid; use the thumbnail from assets/thumbs/")
            continue
        if not src.startswith("/assets/thumbs/"):
            errors.append(f"{name}: grid image is not from /assets/thumbs/ (run scripts/make-thumbs.py)")
            continue
        avif = next((s.get("srcset") for s in (pic["sources"] if pic else []) if s.get("type") == "image/avif"), None)
        if not avif:
            errors.append(f"{name}: needs <picture> with an image/avif <source> before the <img>")
        jpg = local(src)
        if not jpg.exists():
            errors.append(f"{name}: file missing ({src})")
            continue
        with Image.open(jpg) as im:
            w, h = im.size
        if w > MAX_THUMB_WIDTH:
            errors.append(f"{name}: {w}px wide, limit is {MAX_THUMB_WIDTH}px")
        size = jpg.stat().st_size
        if size > MAX_JPEG_BYTES:
            errors.append(f"{name}: JPEG fallback is {size // 1024} KB, limit {MAX_JPEG_BYTES // 1024} KB")
        if avif:
            af = local(avif)
            if not af.exists():
                errors.append(f"{name}: AVIF missing ({avif})")
            else:
                asz = af.stat().st_size
                if asz > MAX_AVIF_BYTES:
                    errors.append(f"{name}: AVIF is {asz // 1024} KB, limit {MAX_AVIF_BYTES // 1024} KB")
                if src not in seen:
                    avif_total += asz
        if src not in seen:
            jpeg_total += size
            seen.add(src)
        try:
            aw, ah = int(a.get("width", 0)), int(a.get("height", 0))
        except ValueError:
            aw = ah = 0
        if not aw or not ah:
            errors.append(f"{name}: needs width and height attributes (prevents layout shift)")
        elif abs(aw / ah - w / h) > 0.01:
            errors.append(f"{name}: width/height {aw}x{ah} do not match the file's {w}x{h}")
        lazy = a.get("loading") == "lazy"
        if n < EAGER_COUNT and lazy:
            warns.append(f"{name}: in the first row but loading=lazy; make it eager so it does not pop in")
        if n >= EAGER_COUNT and not lazy:
            errors.append(f"{name}: below the first row, so it needs loading=\"lazy\"")

    for rec in scan.imgs:
        if rec in thumbs or rec["badge"]:
            continue
        src = rec["attrs"].get("src") or ""
        if any(f in src for f in FORBIDDEN):
            errors.append(f"{src}: full-size art on a grid page")
        elif src.lower().endswith(RASTER) and local(src).exists() and local(src).stat().st_size > MAX_OTHER_IMAGE_BYTES:
            warns.append(f"{src}: {local(src).stat().st_size // 1024} KB, over the {MAX_OTHER_IMAGE_BYTES // 1024} KB guide for non-thumbnail images")

    if avif_total > MAX_PAGE_AVIF_BYTES:
        errors.append(f"page total (AVIF path) is {avif_total // 1024} KB, limit {MAX_PAGE_AVIF_BYTES // 1024} KB")
    if jpeg_total > MAX_PAGE_JPEG_BYTES:
        errors.append(f"page total (JPEG fallback path) is {jpeg_total // 1024} KB, limit {MAX_PAGE_JPEG_BYTES // 1024} KB")

    print(f"\n{page}: {len(thumbs)} painting images, {avif_total // 1024} KB on the AVIF path, {jpeg_total // 1024} KB on the JPEG fallback")
    for w in warns:
        print(f"  warn  {w}")
    for e in errors:
        print(f"  FAIL  {e}")
    if not errors:
        print("  ok    follows the page-weight rules")
    return not errors


if __name__ == "__main__":
    pages = sys.argv[1:] or ["work.html"]
    ok = all([check(p) for p in pages])
    sys.exit(0 if ok else 1)
