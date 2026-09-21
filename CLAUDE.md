# happyboy.digital

A small static site. **`python build.py` turns the files in `src/` into finished pages in `dist/`**, and `dist/` is what cPanel deploys. Read `README.md` for the everyday guide.

## The rules that matter

- **Edit `src/` (and `css/`, `js/`, `assets/`). Never edit `dist/` by hand.** A rebuild replaces it. `dist/` is committed because the server builds nothing.
- Pages: `src/pages/`. Paintings: one file each in `src/pieces/`. Shared header, nav and footer: `src/partials/`. Page shell: `src/layout.html`. Painting page layout: `src/templates/piece.html`.
- **Prices come from the Curation Log**, not from anywhere in this repo. `python build.py` refreshes `src/content/catalog.json` (title, type, size, price only, never stock counts).
- Cache-busting is automatic: `style.css` and `main.js` are linked with a version taken from a hash of the file. There is nothing to bump.
- Deployed by cPanel Git Version Control using the explicit list in `.cpanel.yml` (`dist/`, `css/`, `js/`, `assets/`, `robots.txt`, `.htaccess`, `inventory.json`). A new top-level folder that must go live needs adding there. `CLAUDE.md`, `README.md`, `src/`, `scripts/` and `build.py` are deliberately not deployed.

## Working in this repo

- **This repo is public.** Never commit anything the owner has said should stay private (pricing nuances, internal notes, business details from chat). When unsure, ask. The owner's private wording list is checked by a tool that lives outside this repo (see below), so read your diff before committing.
- The owner edits the working tree and commits in parallel. Run `git status` first, stage only files you changed, and commit with explicit paths (`git commit -m ... -- path1 path2`) so their staged or uncommitted work is not swept in. Changing a source file means committing its rebuilt `dist/` output too.
- Before committing site changes: `python build.py --check` (broken links and images, structured data), and the owner's preflight `check_site.py` from the Garden's `05 Tools` folder if it is on this machine.
- Commit messages end with `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`.
- Don't remind the owner how to deploy. Just say what was pushed.

## Branches: live site vs redesign rollout

Two folders, two branches, one GitHub repo (the second folder is a `git worktree` of the first):

| Folder (siblings) | Branch | Work that belongs here |
|---|---|---|
| `happyboydigital-web` | `main` | The live site: paintings, blog posts, prices, inventory, bug fixes, page weight. |
| `happyboydigital-web-rollout` | `rollout-ui` | The redesign only (below). Nothing here goes live until the owner says it's rollout day. |

- **First thing in any session: run `git branch --show-current`** and check it matches the folder you are in. If it does not, stop and tell the owner.
- **Never commit redesign work to `main`, and never commit content or fixes to `rollout-ui`.** Content and fixes go to `main` and reach the branch by merging `main` into it. The main folder always stays on `main`; the POS's "Sync to Website" commits `inventory.json` there.
- **Never merge `rollout-ui` into `main`, push it to `main`, or deploy it without the owner's explicit go-ahead.** Before that merge, tag `main` as `pre-rollout`.
- The redesign is: retire the hand-drawn sky; gallery-white ground (`#F7F6F4`), with a per-set colour only when the owner feels inspired by a piece; footer `#1B140F` with yellow text; a short text nav on desktop and the small menu on phones; the border-and-medallion frames kept only on the Blog and Atelier pages; Newsreader (titles) with Space Grotesk (everything else), regular or medium weights; minimal motion. The logo badge, sold seal and blog icons stay. Keep the redesign to `css/`, `src/layout.html`, `src/partials/`, `src/templates/`, small page tweaks it needs and its own assets.
- Every commit on either branch includes its rebuilt `dist/` and passes `python build.py --check`. When merging `main` into `rollout-ui`, `dist/` will conflict: it is generated, so take either side and run `python build.py`. Conflicts in `src/`, `css/` or `js/` need a real look, so ask the owner.
- Preview the branch with `python build.py --serve --port 8001` (the main folder uses 8000). The owner's step-by-step guide is in their Field Guide (`Redesign_Rollout.md`).

## Page weight: painting grids (work.html, index.html)

The paintings are shown about 360 CSS px wide in the grids, so the grids must never load the full-size files. Loading them was 3.5 MB on work.html; the thumbnails bring it to about 1 MB.

- **The build handles this.** The grid cards (`src/partials/card.html`, `home_card.html`) already use the `<picture>` thumbnail markup, with the real width/height read from the files, the first 3 items eager (the first with `fetchpriority="high"`) and the rest lazy. Don't hand-write grid images.
- Thumbnails live in `assets/thumbs/` as `<name>-800.avif` (AVIF q55) and `<name>-800.jpg` (JPEG q78, fallback). `python build.py` makes any that are missing or stale by calling `python scripts/make-thumbs.py [name]` (needs Pillow 11.2+). The source is `assets/<name>.jpeg`.
- **Never** reference `assets/<name>.jpeg`, `assets/large/`, or `assets/originals/` inside a grid. Full-size art belongs to the painting detail pages and their lightbox only.
- **Adding a painting:** `python build.py --new-piece "Title"`, add its row to the Curation Log, put the 1125px file at `assets/NAME.jpeg` (and `assets/large/NAME.jpeg`), fill in the new file in `src/pieces/`, then `python build.py --check`.
- Before committing a change that touches the grids, run `python scripts/check-page-weight.py` (it checks `dist/work.html` and `dist/index.html` by default). It must pass. The budgets are constants at the top of that script.
- Text, SVG and fonts need no page-weight work: the host already serves Brotli and 7-day caching.
