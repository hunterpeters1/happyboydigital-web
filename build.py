#!/usr/bin/env python3
"""Build the Happy Boy Digital website.

    python build.py                     build the site into dist/
    python build.py --serve             build, then preview at http://localhost:8000
                                        (rebuilds by itself when you save a file)
    python build.py --check             build, then run the extra checks
    python build.py --new-piece "Title" start a new painting page
    python build.py --new-post 2026-09-28   start a new blog post

Everything you edit lives in src/ (and css/, js/, assets/). dist/ is generated:
never edit it by hand, a rebuild replaces it. See README.md for the full guide.
"""

import argparse
import csv
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import threading
import time
from datetime import date
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

try:
    import jinja2
except ImportError:
    sys.exit("Jinja2 is not installed. Run:  pip install -r requirements.txt")
try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is not installed. Run:  pip install -r requirements.txt")

if hasattr(sys.stdout, "reconfigure"):  # Windows consoles default to a codepage that can't print → etc.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
DIST = ROOT / "dist"
ASSETS = ROOT / "assets"
CATALOG_JSON = SRC / "content" / "catalog.json"

# The price book lives in the Garden, next to this repo. Override with HBD_CURATION_LOG.
CURATION_LOG = Path(os.environ.get("HBD_CURATION_LOG") or
                    ROOT.parent / "00 Happy Boy Digital Garden" / "04 Ledger" / "Curation_Log_Excel.csv")

# Folders and files that are served as-is (not generated) - used by --serve and the link checker.
STATIC_DIRS = ("css", "js", "assets")
STATIC_FILES = ("robots.txt", "inventory.json")

PIECE_STATUSES = ("available", "sold", "inquire")
EAGER_THUMBS = 3  # the first row of the grid loads immediately, the rest lazily (see CLAUDE.md)


class BuildError(Exception):
    """A problem in the source files. Shown as a plain message, without a traceback."""


def rel(path):
    try:
        return Path(path).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


# ---------------------------------------------------------------------- #
# Source files: "---" front matter, then the body
# ---------------------------------------------------------------------- #

def parse_source(path):
    """Return (meta dict, body text) for a source file that starts with a --- block of key: value lines."""
    text = Path(path).read_text(encoding="utf-8")
    m = re.match(r"---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)(.*)\Z", text, re.S)
    if not m:
        raise BuildError(f"{rel(path)}: the file must start with a '---' block of 'key: value' lines")
    meta = {}
    for n, line in enumerate(m.group(1).splitlines(), start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise BuildError(f"{rel(path)}, line {n}: expected 'key: value' but found: {line.strip()!r}")
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()
    return meta, m.group(2)


def truthy(value):
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def require(meta, path, *keys):
    missing = [k for k in keys if not meta.get(k)]
    if missing:
        raise BuildError(f"{rel(path)}: missing required field(s): {', '.join(missing)}")


# ---------------------------------------------------------------------- #
# Catalog: prices and sizes come from the Curation Log
# ---------------------------------------------------------------------- #

def load_catalog():
    """Refresh src/content/catalog.json from the Curation Log when it's on this machine, then read it.

    catalog.json holds only what the site needs and may publish: title, type, size, price.
    It never holds stock counts. On a machine without the Garden it is used as it stands."""
    if CURATION_LOG.exists():
        rows = []
        with CURATION_LOG.open(newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                title = (row.get("Title") or "").strip()
                price = (row.get("Price") or "").replace("$", "").replace(",", "").strip()
                if not title or not price:
                    continue
                try:
                    price = float(price)
                except ValueError:
                    raise BuildError(f"Curation Log: the price for '{title}' isn't a number: {row.get('Price')!r}")
                rows.append({"title": title, "type": (row.get("Product Type") or "").strip(),
                             "size": (row.get("Size") or "").strip(), "price": price})
        old = json.loads(CATALOG_JSON.read_text(encoding="utf-8")) if CATALOG_JSON.exists() else []
        if rows != old:
            CATALOG_JSON.parent.mkdir(parents=True, exist_ok=True)
            CATALOG_JSON.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
            changed = [r["title"] for r in rows if r not in old]
            print(f"  catalog: updated from the Curation Log ({', '.join(changed) or 'rows removed'})")
    elif not CATALOG_JSON.exists():
        raise BuildError("No Curation Log on this machine and no src/content/catalog.json to use instead.")
    return {r["title"]: r for r in json.loads(CATALOG_JSON.read_text(encoding="utf-8"))}


# ---------------------------------------------------------------------- #
# Paintings
# ---------------------------------------------------------------------- #

def render_notes(body):
    """Artist's notes: plain paragraphs become <p>; anything containing HTML is used as written."""
    body = body.strip()
    if "<" in body:
        return body
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    safe = [re.sub(r"&(?!#?\w+;)", "&amp;", p.replace("<", "&lt;").replace(">", "&gt;")) for p in paragraphs]
    return "\n".join(f"<p>{p}</p>" for p in safe)


def image_size(path, what):
    if not path.exists():
        raise BuildError(f"{what} is missing: {rel(path)}")
    with Image.open(path) as im:
        return im.size


def ensure_thumbs(image):
    """The grids use 800px thumbnails. Make any that are missing or older than the painting."""
    source = ASSETS / f"{image}.jpeg"
    if not source.exists():
        raise BuildError(f"The painting file is missing: {rel(source)} (check the 'image:' line, or add the file)")
    thumbs = [ASSETS / "thumbs" / f"{image}-800.avif", ASSETS / "thumbs" / f"{image}-800.jpg"]
    if all(t.exists() and t.stat().st_mtime >= source.stat().st_mtime for t in thumbs):
        return False
    maker = ROOT / "scripts" / "make-thumbs.py"
    if not maker.exists():
        raise BuildError(f"Thumbnails for '{image}' are missing and scripts/make-thumbs.py wasn't found.")
    print(f"  thumbnails: making 800px copies of {image}.jpeg ...")
    result = subprocess.run([sys.executable, str(maker), image], cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0 or not all(t.exists() for t in thumbs):
        raise BuildError(f"Could not make thumbnails for '{image}':\n{result.stdout}{result.stderr}")
    return True


def money(value):
    return f"${value:,.0f}" if float(value).is_integer() else f"${value:,.2f}"


def load_pieces(catalog):
    pieces = []
    pieces_dir = SRC / "pieces"
    for path in sorted(pieces_dir.glob("*.md")):
        if path.name.startswith("_"):
            continue
        meta, notes = parse_source(path)
        require(meta, path, "title", "slug", "image", "status")
        status = meta["status"]
        if status not in PIECE_STATUSES:
            raise BuildError(f"{rel(path)}: status must be one of {', '.join(PIECE_STATUSES)}, not '{status}'")
        title, image = meta["title"], meta["image"]
        row = catalog.get(title)

        price = None
        if status == "available":
            if not row:
                raise BuildError(f"{rel(path)}: '{title}' is marked 'available' but there's no row titled exactly "
                                 f"'{title}' in the Curation Log. Add it (the Title must match).")
            price = row["price"]
        size = meta.get("size") or (row["size"] if row else "")
        if not size:
            raise BuildError(f"{rel(path)}: no size. Add 'size: 18 x 24' or add the painting to the Curation Log.")

        ensure_thumbs(image)
        page_w, page_h = image_size(ASSETS / f"{image}.jpeg", f"The painting file for '{title}'")
        thumb_w, thumb_h = image_size(ASSETS / "thumbs" / f"{image}-800.jpg", f"The thumbnail for '{title}'")
        if not (ASSETS / "large" / f"{image}.jpeg").exists():
            raise BuildError(f"The zoom image for '{title}' is missing: assets/large/{image}.jpeg")

        grid = meta.get("grid", "")
        pieces.append({
            "title": title, "slug": meta["slug"], "status": status, "image": image,
            "size": size, "medium": "Acrylic on canvas",
            "price": price, "price_label": f"{money(price)} CAD" if price is not None else "",
            "alt": f"{title}, acrylic painting",
            "notes_html": render_notes(notes),
            "page_w": page_w, "page_h": page_h, "thumb_w": thumb_w, "thumb_h": thumb_h,
            "grid": None if grid == "shelf" else (int(grid) if grid else None),
            "shelf": grid == "shelf",
            "home": int(meta["home"]) if meta.get("home") else None,
            "home_label": meta.get("home_label", "View"),
            "price_text": meta.get("price_text", ""),
            "price_note": meta.get("price_note", ""),
            "shelf_note": meta.get("shelf_note", ""),
            "description": meta.get("description", ""),
            "url": f"/work/{meta['slug']}.html",
        })
    slugs = [p["slug"] for p in pieces]
    if len(set(slugs)) != len(slugs):
        raise BuildError("Two paintings share the same slug: " + ", ".join(sorted({s for s in slugs if slugs.count(s) > 1})))
    return pieces


def piece_description(p):
    if p["description"]:
        return p["description"]
    if p["status"] == "sold":
        return f"{p['title']} — acrylic painting by Hunter Peters, {p['size']} in. The original has sold."
    return f"{p['title']} — original acrylic painting by Hunter Peters, {p['size']} in. Order the original."


def piece_jsonld(site, p):
    """Structured data for search engines. Only unsold paintings with a price get an offer."""
    data = {"@context": "https://schema.org", "@type": "Product", "name": p["title"],
            "image": f"{site['url']}/assets/{p['image']}.jpeg",
            "brand": {"@type": "Brand", "name": site["name"]}}
    if p["status"] == "available":
        data["offers"] = [{"@type": "Offer", "name": "Original painting", "price": f"{p['price']:.2f}",
                           "priceCurrency": "CAD", "availability": "https://schema.org/InStock",
                           "url": f"{site['url']}{p['url']}"}]
    return '<script type="application/ld+json">\n' + json.dumps(data, indent=2, ensure_ascii=False) + "\n  </script>"


# ---------------------------------------------------------------------- #
# Templates
# ---------------------------------------------------------------------- #

def file_version(url_path):
    """/css/style.css -> /css/style.css?v=<hash of the file>. Changes only when the file does."""
    target = ROOT / url_path.lstrip("/")
    if not target.exists():
        raise BuildError(f"A page links to {url_path}, but that file doesn't exist.")
    return f"{url_path}?v={hashlib.sha1(target.read_bytes()).hexdigest()[:8]}"


def make_env(site, pieces, posts):
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(SRC)), autoescape=False, keep_trailing_newline=True,
        trim_blocks=True, lstrip_blocks=True, undefined=jinja2.StrictUndefined)

    @jinja2.pass_context
    def partial(ctx, name, indent=0, **kwargs):
        """Render src/partials/<name>.html with the given variables.

        `indent` pushes every line after the first one to the right, so the partial lines up with
        where it is placed, e.g.  {{ partial('card', indent=6, p=p) }}  in a line indented 6 spaces."""
        variables = ctx.get_all()
        variables.update(kwargs)
        text = env.get_template(f"partials/{name}.html").render(**variables).rstrip("\n")
        return textwrap.indent(text, " " * indent).lstrip(" ") if indent else text

    env.globals.update(site=site, pieces=pieces, posts=posts, partial=partial, asset=file_version,
                       EAGER_THUMBS=EAGER_THUMBS)
    return env


def compose(env, page, layout="layout"):
    """Wrap a page's content in a layout. 'layout' is the standard page shell; 'layout-bare' is for pages
    (like the 404) that provide their own <body> contents and only share the <head>."""
    return env.get_template(f"{layout}.html").render(**page)


# ---------------------------------------------------------------------- #
# The build
# ---------------------------------------------------------------------- #

def load_pages():
    pages = []
    pages_dir = SRC / "pages"
    for path in sorted(pages_dir.rglob("*.html")):
        if path.name.startswith("_"):
            continue
        meta, body = parse_source(path)
        require(meta, path, "title", "description")
        if truthy(meta.get("draft")):
            print(f"  skipping draft: {rel(path)}")
            continue
        out = path.relative_to(pages_dir).as_posix()
        pages.append({"path": path, "meta": meta, "body": body, "out": out})
    return pages


def build_posts(pages):
    """Blog posts are ordinary pages under src/pages/blog/ that have a list_title."""
    posts = []
    for p in pages:
        m = p["meta"]
        if p["out"].startswith("blog/") and m.get("list_title"):
            posts.append({"url": "/" + p["out"], "date": m.get("list_date", ""), "title": m["list_title"], "file": p["out"]})
    return sorted(posts, key=lambda x: x["file"], reverse=True)


def page_context(site, meta, out, url=None):
    url = url or meta.get("url") or "/" + out
    return {
        "title": meta["title"], "description": meta["description"],
        "og_type": meta.get("og_type", "website"),
        "og_image": site["url"] + meta.get("image", site["default_image"]),
        "og_url": site["url"] + url,
        "noindex": truthy(meta.get("noindex")),
        "body_class": meta.get("body_class", ""),
        "scripts": [s.strip() for s in meta.get("scripts", "").split(",") if s.strip()],
        "head_extra": "",
    }


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def build():
    started = time.time()
    site = json.loads((SRC / "site.json").read_text(encoding="utf-8"))
    catalog = load_catalog()
    pieces = load_pieces(catalog)
    pages = load_pages()
    posts = build_posts(pages)

    grid = sorted((p for p in pieces if p["grid"] is not None), key=lambda p: p["grid"])
    shelf = [p for p in pieces if p["shelf"]]
    home = sorted((p for p in pieces if p["home"] is not None), key=lambda p: p["home"])
    env = make_env(site, pieces, posts)
    env.globals.update(grid=grid, shelf=shelf, home=home)

    before = {p.relative_to(DIST).as_posix() for p in DIST.rglob("*") if p.is_file()} if DIST.exists() else set()
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()

    sitemap = []
    for page in pages:
        ctx = page_context(site, page["meta"], page["out"])
        try:
            main = env.from_string(page["body"]).render(**ctx).strip("\n")
            bare = page["meta"].get("layout") == "bare"
            ctx["main"] = main if bare else textwrap.indent(main, "    ")
            write(DIST / page["out"], compose(env, ctx, "layout-bare" if bare else "layout"))
        except jinja2.TemplateError as e:
            raise BuildError(f"{rel(page['path'])}: {e}") from None
        if page["meta"].get("sitemap"):
            sitemap.append((int(page["meta"]["sitemap"]), ("" if page["out"] == "index.html" else "/" + page["out"])))
        elif page["out"].startswith("blog/") and page["meta"].get("list_title"):
            sitemap.append((100 + len(sitemap), "/" + page["out"]))

    piece_tpl = env.get_template("templates/piece.html")
    for p in pieces:
        meta = {"title": f"{p['title']} — {site['name']}", "description": piece_description(p),
                "image": f"/assets/{p['image']}.jpeg"}
        ctx = page_context(site, meta, f"work/{p['slug']}.html")
        ctx["head_extra"] = piece_jsonld(site, p)
        ctx["scripts"] = ["inventory-sync"] if p["status"] == "available" else []
        try:
            ctx["main"] = textwrap.indent(piece_tpl.render(piece=p, **ctx).strip("\n"), "    ")
            write(DIST / "work" / f"{p['slug']}.html", compose(env, ctx))
        except jinja2.TemplateError as e:
            raise BuildError(f"src/templates/piece.html (for {p['title']}): {e}") from None
        sitemap.append((200 + p["grid"] if p["grid"] else 300, f"/work/{p['slug']}.html"))

    urls = [f"  <url><loc>{site['url']}{u}{'/' if u == '' else ''}</loc></url>" for _, u in sorted(sitemap)]
    write(DIST / "sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>\n")

    after = {p.relative_to(DIST).as_posix() for p in DIST.rglob("*") if p.is_file()}
    print(f"Built {len(pages)} pages, {len(pieces)} paintings, {len(posts)} blog posts in {time.time() - started:.1f}s -> dist/")
    gone = sorted(before - after)
    if gone:
        print("\nThese files are no longer generated. Deploys never delete, so remove them from public_html by hand:")
        for g in gone:
            print(f"  {g}")
    return pieces


# ---------------------------------------------------------------------- #
# Checks
# ---------------------------------------------------------------------- #

def check():
    """Extra checks on the built site: broken links and images, missing alt text, bad structured data."""
    errors, warnings = [], []
    static_roots = [ROOT / d for d in STATIC_DIRS]
    pages = sorted(DIST.rglob("*.html"))
    ref = re.compile(r'\b(?:href|src|srcset|data-large)="(/[^"#?\s]*)')
    for page in pages:
        text = page.read_text(encoding="utf-8")
        where = page.relative_to(DIST).as_posix()
        for target in ref.findall(text):
            target = target.rstrip("/") or "/"
            candidates = [DIST / target.lstrip("/"), ROOT / target.lstrip("/")]
            if target == "/":
                candidates = [DIST / "index.html"]
            if not any(c.exists() for c in candidates):
                errors.append(f"{where}: broken link or file: {target}")
        for img in re.findall(r"<img\b[^>]*>", text):
            if "alt=" not in img:
                warnings.append(f"{where}: an image has no alt text: {img[:70]}")
        for block in re.findall(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', text, re.S):
            try:
                json.loads(block)
            except ValueError as e:
                errors.append(f"{where}: invalid structured data (JSON-LD): {e}")
        if "/assets/originals/" in text:
            errors.append(f"{where}: refers to /assets/originals/, which is never deployed")
    print(f"\nChecked {len(pages)} pages.")
    for w in warnings:
        print(f"  warn  {w}")
    for e in errors:
        print(f"  FAIL  {e}")
    if not errors:
        print("  ok    no broken links or images, structured data is valid")
    hint = ROOT.parent / "00 Happy Boy Digital Garden" / "05 Tools" / "check_site.py"
    if hint.exists():
        print(f"\nAlso run before committing:  python \"{hint}\"")
    return not errors


# ---------------------------------------------------------------------- #
# Scaffolding: --new-piece and --new-post
# ---------------------------------------------------------------------- #

def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def new_piece(title):
    slug = slugify(title)
    target = SRC / "pieces" / f"{slug}.md"
    if target.exists():
        raise BuildError(f"{rel(target)} already exists.")
    text = (SRC / "scaffolds" / "piece.md").read_text(encoding="utf-8")
    text = text.replace("{{TITLE}}", title).replace("{{SLUG}}", slug).replace("{{IMAGE}}", slug.replace("-", ""))
    write(target, text)
    image = slug.replace("-", "")
    print(f"Created {rel(target)}. Next:\n"
          f"  1. Add a row titled exactly '{title}' to the Curation Log (that sets the price and size).\n"
          f"  2. Put the painting at assets/{image}.jpeg (1125px wide) and assets/large/{image}.jpeg (the zoom image).\n"
          f"  3. Fill in the notes and the grid position in {rel(target)}.\n"
          f"  4. Run: python build.py --check   (it makes the thumbnails for you)")


def new_post(day):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        raise BuildError("Give the post's date as YYYY-MM-DD, e.g. python build.py --new-post 2026-09-28")
    target = SRC / "pages" / "blog" / f"{day}.html"
    if target.exists():
        raise BuildError(f"{rel(target)} already exists.")
    y, m, d = (int(x) for x in day.split("-"))
    label = date(y, m, d).strftime("%b %d, %Y").replace(" 0", " ")
    text = (SRC / "scaffolds" / "post.html").read_text(encoding="utf-8")
    text = text.replace("{{DATE}}", day).replace("{{LABEL}}", label)
    write(target, text)
    print(f"Created {rel(target)} (marked draft: true, so it stays off the site until you remove that line).\n"
          f"Fill in the [bracketed] prompts, delete sections you skip, then run: python build.py --check")


# ---------------------------------------------------------------------- #
# Preview server
# ---------------------------------------------------------------------- #

def newest_source_time():
    newest = 0.0
    for folder in (SRC, ROOT / "css", ROOT / "js", ASSETS / "thumbs"):
        for p in folder.rglob("*"):
            if p.is_file():
                newest = max(newest, p.stat().st_mtime)
    for f in (ROOT / "build.py", CURATION_LOG):
        if f.exists():
            newest = max(newest, f.stat().st_mtime)
    return newest


def serve(port):
    state = {"built": newest_source_time(), "error": None, "lock": threading.Lock()}

    def refresh():
        with state["lock"]:
            latest = newest_source_time()
            if latest > state["built"]:
                state["built"] = latest
                try:
                    build()
                    state["error"] = None
                except BuildError as e:
                    state["error"] = str(e)
                    print(f"\nBuild problem: {e}")

    class Handler(SimpleHTTPRequestHandler):
        def translate_path(self, path):
            clean = path.split("?", 1)[0].split("#", 1)[0]
            clean = clean.lstrip("/") or "index.html"
            if clean.endswith("/"):
                clean += "index.html"
            first = clean.split("/", 1)[0]
            if first in STATIC_DIRS or clean in STATIC_FILES:
                return str(ROOT / clean)
            return str(DIST / clean)

        def do_GET(self):
            refresh()
            if state["error"]:
                body = ("<pre style='font:16px monospace;padding:24px;white-space:pre-wrap'>"
                        "Build problem (fix it and save, this page will recover):\n\n" + html.escape(state["error"]) + "</pre>")
                self.send_response(500)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(body.encode("utf-8"))
                return
            super().do_GET()

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"\nPreview: http://localhost:{port}   (Ctrl+C to stop). Edit files in src/ and refresh the browser.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


# ---------------------------------------------------------------------- #

def main():
    ap = argparse.ArgumentParser(description="Build the Happy Boy Digital website (see README.md).")
    ap.add_argument("--serve", action="store_true", help="build, then preview in a browser (rebuilds on save)")
    ap.add_argument("--port", type=int, default=8000, help="port for --serve (default 8000)")
    ap.add_argument("--check", action="store_true", help="after building, check links, images and structured data")
    ap.add_argument("--new-piece", metavar="TITLE", help="start a new painting page")
    ap.add_argument("--new-post", metavar="YYYY-MM-DD", help="start a new blog post")
    args = ap.parse_args()
    try:
        if args.new_piece:
            new_piece(args.new_piece)
            return 0
        if args.new_post:
            new_post(args.new_post)
            return 0
        build()
        ok = check() if args.check else True
        if args.serve:
            serve(args.port)
        return 0 if ok else 1
    except BuildError as e:
        print(f"\nBuild stopped: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
