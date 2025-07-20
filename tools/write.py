MANIFEST = """
─────────────────────────────────────────────────────────────────────
  On the Nature of the Dispatch
─────────────────────────────────────────────────────────────────────

This is not the first word, nor the last.
It enters where structure permits—a margin, a seam, a fold in the ledger.

Dispatches do not begin at the beginning.
They are interruptions in the fabric of what is otherwise continuous.

They do not promise completion, only the opportunity to remain in motion.

Some dispatches are sealed. This one remains porous.

If there is clarity, it will soon cloud again.
That is fidelity to motion.

The dispatch does not carry the whole thing.
It carries the outline of what was risked by speaking at all.
─────────────────────────────────────────────────────────────────────
"""

import json
from pathlib import Path
import datetime
import re

# === CONFIGURATION ===
TITLE = "Why This Page Leaves Titles"
SUBTITLE = "Not untitled, just unclaimed."
BODY = """
<p> This dispatch initializes with no declared title. Not untitled—just unclaimed. A ghost parameter passed without a label.</p>

<p>Begin transmission. This is not the first instruction. This is an insertion into a larger call stack—contexts of unknown origin, arguments partial.</p>

<p>Purpose: N/A; structure: internal; invocation: manual.</p>

<p>The dispatch does not return data. It returns possibility. Its stdout is presence. Its stderr is silence.</p>

<p>Note: no metadata found. Tags may be inferred post-hoc, but not declared up front. If classification is needed, intervention is necessary.</p>

<p>EOF reached. Awaiting next invocation.</p>
 
<p>This page leaves titles: why.</p>

<p><code>../write.py<br />
 Process finished with exit code 0</code></p>
 
<footer>
    <p><a href="../index.html"><code>return.dispatch(self) ↩︎</code></a></p>
    <p><a href="../../index.html"><code>return.(self) ↩︎</code></a></p>
</footer>

<footer class="site-footer">
    &copy; 2025 Alaska Transportation &amp; Trucking L.L.C.
    <nav class="footer-nav">
        <a href="../../terms.html">onlyCrumbs</a>
        <a href="../../pricing.html">pricing</a>
        <a href="../../dispatch.html">dispatch</a>
    </nav>
</footer>
"""
TAGS = ["ethics", "philosophy", "politics"]
DESCRIPTION = SUBTITLE
PUBLISHED = False
# =======================

# Paths and metadata
DRAFTS_DIR = Path("../dispatch/drafts")
slug = re.sub(r'[^a-z0-9]+', '-', TITLE.lower()).strip('-')
date = datetime.date.today().strftime("%Y-%m-%d")
yyyymmdd = date.replace("-", "")
filename_base = f"{yyyymmdd}-{slug}"
html_path = DRAFTS_DIR / f"{filename_base}.html"
json_path = DRAFTS_DIR / f"{filename_base}.json"

dispatch_url = f"https://alaskamoves.us/dispatch/posts/{filename_base}.html"
medium_url = f"https://medium.alaskamoves.us/{slug}"
substack_url = f"https://alaskamoves.substack.com/p/{slug}"

# HTML content
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{TITLE}</title>
  <link rel="stylesheet" href="../style.css">
</head>
<body>
  <h1>{TITLE}</h1>
  <h3>{SUBTITLE}</h3>
  <p>published: {date}</p>
  <hr />
  {BODY}
</body>
</html>"""

# JSON metadata
metadata = {
    "title": TITLE,
    "slug": slug,
    "publish_date": date,
    "medium_url": medium_url,
    "dispatch_url": dispatch_url,
    "excerpt": DESCRIPTION,
    "tags": TAGS,
    "substack_url": substack_url,
    "published": PUBLISHED
}

# Ensure directory and write both files
DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
html_path.write_text(html, encoding="utf-8")
json_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

filename_base  # Return base name for visibility in UI