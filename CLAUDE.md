# happyboy.digital

Static HTML/CSS/JS portfolio and shop for Hunter Peters. No build step. Deployed by cPanel Git Version Control using the explicit file list in `.cpanel.yml`, so a new top-level page or folder must be added there. `CLAUDE.md` and `scripts/` are deliberately not deployed.

## Working in this repo
- The owner edits the working tree and commits in parallel. Run `git status` first, stage only files you changed, and commit with explicit paths (`git commit -m ... -- path1 path2`) so their staged or uncommitted work is not swept in.
- After any change to `css/style.css` or `js/main.js`, bump the `?v=N` query string on every HTML page that links it (cache busting).
- Commit messages end with `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`.

## Page weight: painting grids (work.html, index.html)
The paintings are shown about 360 CSS px wide in the grids, so the grids must never load the full-size files. Loading them was 3.5 MB on work.html; the thumbnails bring it to about 1 MB.

- **Never** reference `assets/<name>.jpeg`, `assets/large/`, or `assets/originals/` inside a grid. Full-size art belongs to the painting detail pages and their lightbox only.
- Every painting has 800 px thumbnails in `assets/thumbs/`: `<name>-800.avif` (AVIF q55) and `<name>-800.jpg` (JPEG q78, fallback). Generate them with `python scripts/make-thumbs.py [name]`. The source is `assets/<name>.jpeg`. Needs Pillow 11.2+.
- Markup for every grid image, with `width`/`height` equal to the thumbnail's real size (the script prints a ready-made snippet):
  ```html
  <picture><source type="image/avif" srcset="/assets/thumbs/NAME-800.avif"><img src="/assets/thumbs/NAME-800.jpg" alt="..." width="800" height="1067" loading="lazy" decoding="async"></picture>
  ```
- The first 3 grid items (first row on desktop) load eagerly, and the first also gets `fetchpriority="high"`. Every item after that gets `loading="lazy"`.
- **Adding a painting:** put the 1125 px file at `assets/NAME.jpeg` (and `assets/large/NAME.jpeg` for the lightbox), run `make-thumbs.py NAME`, paste the snippet into the grid, then run the check below.
- **Before committing any change to `work.html` or `index.html`, run `python scripts/check-page-weight.py work.html` (and `index.html`). It must pass.** The budgets are constants at the top of that script: per-thumbnail size and width, first-row eager and the rest lazy, width/height attributes, and a page total of about 1.15 MB on the AVIF path.
- Text, SVG and fonts need no page-weight work: the host already serves Brotli and 7-day caching.
- `index.html` still uses the full-size files, so the checker fails on it. Convert its grid the same way.
