#!/usr/bin/env python3
"""Make grid thumbnails for the painting pages (work.html, index.html).

Every painting in assets/*.jpeg is shown small in the grids (about 376 CSS px
wide on desktop), so the grids load an 800 px copy instead of the full file:

    assets/thumbs/<name>-800.avif   (what modern browsers load)
    assets/thumbs/<name>-800.jpg    (fallback for old browsers)

Usage (from the repo root):
    python scripts/make-thumbs.py              # every painting that is missing or stale
    python scripts/make-thumbs.py roses harry  # just these
    python scripts/make-thumbs.py --force      # redo everything

Needs Pillow 11.2 or newer (native AVIF): pip install --upgrade pillow
The full-size files in assets/ and assets/large/ are untouched -- they are
still what the painting detail pages and the lightbox use.
"""
import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, features
except ImportError:
    sys.exit("Pillow is not installed. Run: pip install --upgrade pillow")

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "assets"
OUT_DIR = SRC_DIR / "thumbs"
WIDTH = 800
AVIF_QUALITY = 55
JPEG_QUALITY = 78


def sources(names):
    if names:
        found = []
        for n in names:
            hits = [p for ext in ("jpeg", "jpg") for p in SRC_DIR.glob(f"{n}.{ext}")]
            if not hits:
                sys.exit(f"No assets/{n}.jpeg or .jpg found.")
            found.append(hits[0])
        return found
    return sorted(list(SRC_DIR.glob("*.jpeg")) + list(SRC_DIR.glob("*.jpg")))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*", help="painting file names without extension (default: all)")
    ap.add_argument("--force", action="store_true", help="rebuild even if the thumbnail is newer than the source")
    args = ap.parse_args()

    if not features.check("avif"):
        sys.exit("This Pillow has no AVIF support. Run: pip install --upgrade pillow (need 11.2+)")

    OUT_DIR.mkdir(exist_ok=True)
    for src in sources(args.names):
        avif = OUT_DIR / f"{src.stem}-{WIDTH}.avif"
        jpg = OUT_DIR / f"{src.stem}-{WIDTH}.jpg"
        fresh = avif.exists() and jpg.exists() and min(avif.stat().st_mtime, jpg.stat().st_mtime) >= src.stat().st_mtime
        with Image.open(src) as im:
            im = im.convert("RGB")
            h = round(im.height * WIDTH / im.width)
            if not args.force and fresh:
                print(f"skip   {src.name} (thumbnails are up to date)")
            else:
                small = im.resize((WIDTH, h), Image.LANCZOS)
                small.save(avif, "AVIF", quality=AVIF_QUALITY)
                small.save(jpg, "JPEG", quality=JPEG_QUALITY, progressive=True, optimize=True)
                print(f"made   {src.name} -> {avif.name} {avif.stat().st_size // 1024} KB, {jpg.name} {jpg.stat().st_size // 1024} KB")
        print(f'''  <picture>
    <source type="image/avif" srcset="/assets/thumbs/{avif.name}">
    <img src="/assets/thumbs/{jpg.name}" alt="ALT TEXT" width="{WIDTH}" height="{h}" loading="lazy" decoding="async">
  </picture>''')


if __name__ == "__main__":
    main()
