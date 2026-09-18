# Catalog Rotation Checklist

Manual steps for adding a painting to the catalog, or retiring one. Nothing
automates this yet — follow every step in order. Skipped steps go unnoticed
until someone hits a stale link or a wrong badge (sitemap.xml was missing
3 of 8 work pages before this checklist existed — that's the failure mode
this guards against).

## Adding a painting

1. Produce three image sizes:
   - `/assets/<name>.jpeg` — grid thumbnail
   - `/assets/large/<name>.jpeg` — lightbox zoom
   - `/assets/originals/<name>.jpeg` — full-res source (gitignored, not deployed)
2. Create `/work/<slug>.html` — copy an existing painting page (e.g.
   `work/roses.html`) as the template. Update: `<title>`, meta description,
   og:*/twitter:* tags, breadcrumb, h1, artist's notes, image srcs, the
   Product JSON-LD `offers` block (original + 3 print tiers), the price
   table, and the buy-box painting name.
3. Add a `.project-thumb` card to `work.html`'s grid, with
   `data-item-title="<Title>"` if it should track sold/in-stock status.
4. Optional: add/swap a featured card on `index.html`'s "Selected Work"
   preview.
5. Add the new page's URL to `sitemap.xml`.
6. Add a row to `Curation_Log_Excel.csv` (`04 Ledger/`). Title must match
   `data-item-title` exactly — it's the join key. Count = 1 for a
   one-of-a-kind original.
7. Commit + push. Click **Sync to Website** in the Receipt Generator GUI if
   the CSV changed. Then deploy from cPanel (Git Version Control > Update
   from Remote > Deploy HEAD Commit).

## Retiring a painting (decision: full removal, not archived)

1. Delete `/work/<slug>.html`.
2. Remove its `.project-thumb` card from `work.html`.
3. Remove its featured card from `index.html`, if present.
4. Remove its URL from `sitemap.xml`.
5. Remove its row from `Curation_Log_Excel.csv` (or set Count to 0 first if
   you want a brief sold-out badge before it disappears).
6. Delete its three image files under `/assets`, `/assets/large`,
   `/assets/originals`.
7. Commit + push, deploy from cPanel — **then manually delete the old files
   from `public_html`** (File Manager or SSH). The `.cpanel.yml` deploy
   script only copies/overwrites; it never deletes anything except
   `originals/`/`paintings.zip`. A retired page and its images keep serving
   live from `public_html` until removed by hand, even after the repo and
   GitHub are clean.

## Why the title match matters

Title is the join key used everywhere: the CSV, `inventory.json`, and every
`data-item-title` attribute. If a retired painting's exact title is ever
reused for an unrelated future piece, the inventory sync will incorrectly
treat them as the same item. Give a returning subject a new title (or at
least a new slug) rather than reusing an old one.
