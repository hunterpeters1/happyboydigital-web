# happyboy.digital

The website for Happy Boy Digital. It is a static site: a small Python script turns the files in `src/` into finished pages in `dist/`, and `dist/` is what gets deployed.

**The whole idea:** you edit files in `src/`, run `python build.py`, and commit. You never edit `dist/` by hand, because the next build replaces it.

---

## One-time setup

You need Python 3.10+ (you already have it). Then, once:

```
pip install -r requirements.txt
```

## Everyday commands

Run these from this folder.

| I want to... | Run |
|---|---|
| Build the site | `python build.py` |
| See it in my browser | `python build.py --serve`, then open http://localhost:8000. It rebuilds whenever you save a file, so just refresh the page. |
| Build and check everything | `python build.py --check` (finds broken links, missing images, invalid structured data) |
| Start a new painting page | `python build.py --new-piece "Title"` |
| Start a new blog post | `python build.py --new-post 2026-09-28` |

If something is wrong, the build stops and says what and where in plain English. Nothing is half-written: fix it and run it again.

---

## Where things live

```
src/pages/        one file per page (home, services, about, ...)
src/pages/blog/   the blog posts
src/pieces/       one small file per painting
src/layout.html   the wrapper every page shares (head, header, footer)
src/partials/     the shared header, nav, footer and the painting card
src/templates/    how a painting's page is laid out
src/scaffolds/    the starter files that --new-piece and --new-post copy
css/  js/  assets/    styles, scripts, images (used as they are)
dist/             the finished site (generated. Don't edit)
```

The header, navigation and footer exist **once** (in `src/partials/`). Change one and every page changes.

---

## Add a painting

1. Run `python build.py --new-piece "Title"`. It creates `src/pieces/title.md`.
2. Add a row to the **Curation Log** with the same Title. That row sets the price and size (this is the only place a price is typed).
3. Put the painting at `assets/<image>.jpeg` (about 1125px wide) and the bigger zoom image at `assets/large/<image>.jpeg`. The `image` line in the new file says the name it expects.
4. Open `src/pieces/title.md` and fill in the artist's notes and the grid position.
5. Run `python build.py --check`. The 800px thumbnails are made for you.

The painting page, the grid on the Work page, the sitemap and the structured data for search engines all update from that one file.

## Retire a painting

Delete its file in `src/pieces/` and its row in the Curation Log, then run `python build.py`. The build lists any files that no longer exist. Deploys don't delete anything, so remove those from `public_html` by hand.

## Mark a painting as sold

In its file in `src/pieces/`, change `status: available` to `status: sold`, add a `size:` line if it isn't in the Curation Log, and rebuild.

## Write a blog post

1. Run `python build.py --new-post 2026-09-28` (use the Monday of that week).
2. Fill in the `[bracketed]` prompts in `src/pages/blog/2026-09-28.html` and delete sections you skip.
3. Remove the `draft: true` line when it's ready to go out. Drafts are never built, listed or deployed.
4. Rebuild. The blog list and sitemap update themselves.

Put post photos in `assets/blog/`, resized to about 1400px on the long edge.

## Edit an existing page

Open its file in `src/pages/`. The top block between the `---` lines holds the page title and description. Everything below it is the page content. Save, then refresh the preview.

---

## Prices

Prices come from the Curation Log, not from anywhere in this folder. Each build refreshes `src/content/catalog.json` from it (only title, type, size and price, never stock). On a computer that doesn't have the Log, the build just uses that saved file.

## CSS and JavaScript versions

Pages link `style.css` and `main.js` with a version that is worked out from the file itself, so browsers always fetch a changed file. There's nothing to bump by hand.

## Deploying

`.cpanel.yml` copies `dist/` (the pages), plus `css/`, `js/`, `assets/`, `robots.txt`, `.htaccess` and `inventory.json`, into `public_html`. Commit `dist/` along with your changes, because the server doesn't build anything.

## Images

Grids use the 800px thumbnails in `assets/thumbs/`, never the full-size files. `python build.py` makes any that are missing. See `CLAUDE.md` for the page-weight rules and `python scripts/check-page-weight.py` for the check.

## If something goes wrong

| You see | Fix |
|---|---|
| `Jinja2 is not installed` | Run `pip install -r requirements.txt` |
| `... is marked 'available' but there's no row titled exactly ...` | Add the row to the Curation Log, and make the Title match exactly |
| `The painting file for '...' is missing` | Put `assets/<image>.jpeg` in place, or fix the `image:` line |
| `expected 'key: value'` | A line at the top of a file (between the `---`) is missing its colon |
| Preview shows "Build problem" | Read the message, fix the file, save. The page recovers by itself |
