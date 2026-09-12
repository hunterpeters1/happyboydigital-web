#!/usr/bin/env python3
"""Build the blog: posts/*.md -> blog/*.html, blog.html, sitemap.xml, feed.xml.

Workflow: write a weekly post as posts/YYYY-MM-DD.md (see posts/2026-09-14.md
for the format), then run `python3 build_blog.py` and FTP the changed files
up. No Node, no build system -- just this script and the `markdown` package
(`pip install markdown`; it's not stdlib, despite what older notes here said).

Format of a posts/*.md file:

    ---
    title: Week of Sept 14, 2026
    date: 2026-09-14
    summary: The Week of Stickers
    ---

    ## working_on
    Free text, one or more paragraphs.

    ## learning
    label: What I'm ingesting
    Free text. The "label:" line is optional -- omit it to get the default
    "What I'm learning".

    ## painting
    img: /blog/blogasets/Sept1226/70.jpg
    alt: Wheat fields by Van Gogh
    width: 1400
    height: 1035
    caption: Wheat Fields, Van Gogh. [...]

    ## song
    text: "Tinfoil Hats" by Lamb -- [...]
    link: https://www.youtube.com/watch?v=MjkWlDDWTjQ

    ## snapshot
    (same fields as painting; optional -- omit the whole section to skip it)

    ## random_thought
    label: of many
    Free text. (optional; omit the whole section to skip it)

Sections are optional except working_on -- leave one out of the .md file
and it's simply not rendered, matching how the hand-written template says
"Snapshot and Random thought are fine to leave out some weeks."
"""

import re
import sys
from datetime import datetime
from pathlib import Path

import markdown

ROOT = Path(__file__).parent
POSTS_DIR = ROOT / "posts"
BLOG_DIR = ROOT / "blog"
SITE_URL = "https://happyboy.digital"

SECTION_DEFAULTS = {
    "working_on": ("\U0001F3A8", "What I'm working on"),
    "learning": ("\U0001F4DA", "What I'm learning"),
    "random_thought": ("\U0001F4AD", "Random thought"),
}

STATIC_PAGES = [
    "", "work.html", "stickers.html", "services.html", "atelier.html",
    "about.html", "blog.html",
    "work/happy-boy.html", "work/roses.html", "work/self-portrait.html",
    "work/sunny-field.html", "work/whaleshark.html",
]

LAYOUT = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <script>(function(){try{if(localStorage.getItem("hbd-theme")==="dark"){document.documentElement.setAttribute("data-theme","dark");}}catch(e){}})();</script>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>%%TITLE%% — Happy Boy Digital</title>
  <meta name="description" content="%%SUMMARY%%">

  <meta property="og:type" content="article">
  <meta property="og:site_name" content="Happy Boy Digital">
  <meta property="og:title" content="%%TITLE%% — Happy Boy Digital">
  <meta property="og:description" content="%%SUMMARY%%">
  <meta property="og:image" content="%%SITE_URL%%/assets/og-image.png">
  <meta property="og:url" content="%%POST_URL%%">

  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="%%TITLE%% — Happy Boy Digital">
  <meta name="twitter:description" content="%%SUMMARY%%">
  <meta name="twitter:image" content="%%SITE_URL%%/assets/og-image.png">

  <link rel="icon" type="image/png" href="/assets/favicon.png">
  <link rel="preload" href="/css/SpaceGrotesk-VariableFont_wght.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="/css/style.css?v=5">
</head>
<body>
  <a href="#main" class="skip-link">Skip to content</a>

  <!-- Yellow scroll-away header bar with nav -->
  <div class="yellow-bar" id="yellow-bar">
    <div class="container">
      <nav>
        <div class="logo-group">
          <a href="/index.html" class="logo"><img src="/assets/icons8-happy-48.png" alt="" class="logo-icon">Happy Boy Digital</a>
          <button id="theme-toggle" class="theme-toggle" type="button" aria-label="Toggle dark mode"><svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"></circle><path d="M12 2v3M12 19v3M4.22 4.22l2.12 2.12M17.66 17.66l2.12 2.12M2 12h3M19 12h3M4.22 19.78l2.12-2.12M17.66 6.34l2.12-2.12"></path></svg><svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"></path></svg></button>
        </div>
        <div class="nav-links" id="nav-links">
          <a href="/work.html">Work</a>
          <a href="/services.html">Services</a>
          <a href="/atelier.html">Atelier</a>
          <a href="/about.html">About</a>
          <a href="/blog.html">Blog</a>
        </div>
        <button id="nav-toggle" class="nav-toggle">Menu</button>
      </nav>
    </div>
  </div>

  <main id="main">
    <section class="page-head">
      <div class="container">
        <nav class="breadcrumb" aria-label="Breadcrumb"><a href="/blog.html">Blog</a> / %%BREADCRUMB_TITLE%%</nav>
        <h1 class="lead">%%TITLE%%</h1>
        <p class="sub">%%SUMMARY%%</p>
      </div>
    </section>

    <section>
      <div class="container prose">
%%SECTIONS_HTML%%
        <p style="margin-top:32px;">That's the week. <a href="mailto:petershunter45@gmail.com">Say hi</a> if any of it landed.</p>

        <p style="margin-top:24px;"><a href="/blog.html" class="btn btn-secondary">&larr; All posts</a></p>

      </div>
    </section>
  </main>

  <footer>
    <div class="container">
      <p style="margin-bottom:8px;">Say hi: <a href="mailto:petershunter45@gmail.com">petershunter45@gmail.com</a><button type="button" class="copy-email-btn" data-email="petershunter45@gmail.com" aria-label="Copy email address">Copy</button></p>
      <p class="small">Happy Boy Digital.</p>
    </div>
  </footer>

  <script src="/js/main.js?v=6"></script>
</body>
</html>
"""


def parse_frontmatter(text):
    """Split a posts/*.md file into (frontmatter dict, body text)."""
    m = re.match(r"^---\s*\n(.*?\n)---\s*\n(.*)$", text, re.DOTALL)
    if not m:
        raise ValueError("missing --- frontmatter block")
    meta = {}
    for line in m.group(1).splitlines():
        if not line.strip():
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta, m.group(2)


def parse_sections(body):
    """Split the body into {section_name: raw_text} on '## name' markers."""
    sections = {}
    current, buf = None, []
    for line in body.splitlines():
        header = re.match(r"^##\s+(\w+)\s*$", line)
        if header:
            if current:
                sections[current] = "\n".join(buf).strip("\n")
            current, buf = header.group(1), []
        elif current:
            buf.append(line)
    if current:
        sections[current] = "\n".join(buf).strip("\n")
    return sections


def parse_kv_block(text):
    """Parse a 'key: value' per line block (used by painting/snapshot/song)."""
    kv = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        key, _, value = line.partition(":")
        kv[key.strip()] = value.strip()
    return kv


def inline_html(text):
    """Render markdown but unwrap a single resulting <p> for inline use
    (figcaptions, one-line song blurbs) -- multi-paragraph text is returned
    with its <p> tags intact."""
    rendered = markdown.markdown(text.strip())
    m = re.match(r"^<p>(.*)</p>\s*$", rendered, re.DOTALL)
    return m.group(1) if m else rendered


def render_prose_section(name, raw):
    """working_on / learning / random_thought: optional 'label: ...' first
    line, then one or more paragraphs of free text.

    For "learning" the label *replaces* the default header text (matching
    the existing post's "What I'm ingesting" swap for "What I'm learning").
    For "random_thought" it's appended as a dim <em> suffix instead (e.g.
    "Random thought *of many*"), since that section's header text doesn't
    change -- only working_on has no label override at all.
    """
    emoji, default_label = SECTION_DEFAULTS[name]
    lines = raw.splitlines()
    label = None
    body_lines = lines
    if lines and lines[0].startswith("label:"):
        label = lines[0].partition(":")[2].strip()
        body_lines = lines[1:]
    body = markdown.markdown("\n".join(body_lines).strip())

    if name == "random_thought":
        header = default_label
        if label:
            header += f' <em style="font-weight:400; opacity:0.6;">{label}</em>'
    else:
        header = label or default_label

    return (
        f'        <h2><span class="section-emoji">{emoji}</span>{header}</h2>\n'
        f"        {body}\n"
    )


def render_image_section(emoji, label, raw):
    kv = parse_kv_block(raw)
    caption = inline_html(kv["caption"]) if "caption" in kv else ""
    html = (
        f'        <h2><span class="section-emoji">{emoji}</span>{label}</h2>\n'
        f'        <img src="{kv["img"]}" alt="{kv["alt"]}" width="{kv["width"]}" '
        f'height="{kv["height"]}" loading="lazy" decoding="async">\n'
    )
    if caption:
        html += f"        <figcaption>{caption}</figcaption>\n"
    return html


def render_song_section(raw):
    kv = parse_kv_block(raw)
    html = (
        '        <h2><span class="section-emoji">\U0001F3B5</span>Song of the week</h2>\n'
        f"        <p>{inline_html(kv['text'])}</p>\n"
    )
    if kv.get("link"):
        html += (
            f'        <a href="{kv["link"]}" class="btn btn-sm" target="_blank" '
            'rel="noopener" style="margin-top:8px;">&#9654; Watch on YouTube</a>\n'
        )
    return html


def render_sections(sections):
    order = ["working_on", "learning", "painting", "song", "snapshot", "random_thought"]
    out = []
    for name in order:
        if name not in sections:
            continue
        raw = sections[name]
        if name in ("working_on", "learning", "random_thought"):
            out.append(render_prose_section(name, raw))
        elif name == "painting":
            out.append(render_image_section("\U0001F5BC️", "Painting of the week", raw))
        elif name == "snapshot":
            out.append(render_image_section("\U0001F4F7", "Snapshot", raw))
        elif name == "song":
            out.append(render_song_section(raw))
    return "\n".join(out)


def human_dates(date_str):
    d = datetime.strptime(date_str, "%Y-%m-%d")
    short = d.strftime("%b ") + str(d.day) + d.strftime(", %Y")
    long = d.strftime("%B ") + str(d.day) + d.strftime(", %Y")
    return short, long


def build_post(md_path):
    meta, body = parse_frontmatter(md_path.read_text(encoding="utf-8"))
    sections = parse_sections(body)
    slug = md_path.stem  # e.g. "2026-09-14"
    short_date, long_date = human_dates(meta.get("date", slug))
    title = meta.get("title", f"Week of {short_date}")
    summary = meta.get("summary", "")
    post_url = f"{SITE_URL}/blog/{slug}.html"

    html = (
        LAYOUT
        .replace("%%TITLE%%", title)
        .replace("%%BREADCRUMB_TITLE%%", f"Week of {long_date}")
        .replace("%%SUMMARY%%", summary)
        .replace("%%SITE_URL%%", SITE_URL)
        .replace("%%POST_URL%%", post_url)
        .replace("%%SECTIONS_HTML%%", render_sections(sections))
    )

    out_path = BLOG_DIR / f"{slug}.html"
    out_path.write_text(html, encoding="utf-8")
    return {
        "slug": slug,
        "date": meta.get("date", slug),
        "title": title,
        "summary": summary,
        "url": post_url,
        "path": f"blog/{slug}.html",
    }


def rebuild_post_list(posts):
    """Replace the <ul class="post-list"> contents in blog.html, newest first."""
    blog_html = ROOT / "blog.html"
    text = blog_html.read_text(encoding="utf-8")
    items = []
    for p in posts:
        list_title = f'{p["title"]} — {p["summary"]}' if p["summary"] else p["title"]
        items.append(
            f'          <li>\n            <a href="/{p["path"]}">\n'
            f'              <span class="post-date">{human_dates(p["date"])[0]}</span>\n'
            f'              <span class="post-title">{list_title}</span>\n'
            "            </a>\n          </li>"
        )
    new_list = '<ul class="post-list">\n' + "\n".join(items) + "\n        </ul>"
    text = re.sub(r'<ul class="post-list">.*?</ul>', new_list, text, flags=re.DOTALL)
    blog_html.write_text(text, encoding="utf-8")


def rebuild_sitemap(posts):
    urls = [f"{SITE_URL}/{p}" if p else f"{SITE_URL}/" for p in STATIC_PAGES]
    urls += [p["url"] for p in posts]
    body = "\n".join(f"  <url><loc>{u}</loc></url>" for u in urls)
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n</urlset>\n"
    )
    (ROOT / "sitemap.xml").write_text(xml, encoding="utf-8")


def rebuild_feed(posts):
    items = []
    for p in posts:
        pub_date = datetime.strptime(p["date"], "%Y-%m-%d").strftime("%a, %d %b %Y 00:00:00 +0000")
        items.append(
            "    <item>\n"
            f"      <title>{p['title']}</title>\n"
            f"      <link>{p['url']}</link>\n"
            f"      <guid>{p['url']}</guid>\n"
            f"      <pubDate>{pub_date}</pubDate>\n"
            f"      <description>{p['summary']}</description>\n"
            "    </item>"
        )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0"><channel>\n'
        "  <title>Happy Boy Digital — Blog</title>\n"
        f"  <link>{SITE_URL}/blog.html</link>\n"
        "  <description>Weekly notes from Hunter Peters.</description>\n"
        "  <language>en-us</language>\n"
        + "\n".join(items) + "\n"
        "</channel></rss>\n"
    )
    (ROOT / "feed.xml").write_text(xml, encoding="utf-8")


def main():
    md_files = sorted(POSTS_DIR.glob("*.md"), reverse=True)  # newest date first
    if not md_files:
        print("No posts found in posts/", file=sys.stderr)
        return
    posts = [build_post(p) for p in md_files]
    rebuild_post_list(posts)
    rebuild_sitemap(posts)
    rebuild_feed(posts)
    print(f"Built {len(posts)} post(s), refreshed blog.html, sitemap.xml, feed.xml.")


if __name__ == "__main__":
    main()
