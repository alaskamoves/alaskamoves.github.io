import json
from datetime import datetime
from jinja2 import Template

# Load posts.json
with open("../../dispatch/db/posts.json", "r") as f:
    posts = json.load(f)

# Sort posts by publish_date descending
def parse_date(post):
    try:
        return datetime.strptime(post["publish_date"], "%Y-%m-%d")
    except ValueError:
        return datetime.min

posts.sort(key=parse_date, reverse=True)

# HTML template with inline [medium] citation
html_template = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Dispatch</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
<div class="container">
  <h1>../dispatch/</h1>
  <p><em>selected writings filed in operational order</em></p>

  <div class="links">
    {% for post in posts %}
    <li>
        <a href="{{ post.dispatch_url | replace('https://alaskamoves.us/dispatch/', '') }}" target="_self">
          {{ post.title }}
        </a>
        <div class="mirror-links">
            {% if post.medium_url %}
                <a href="{{ post.medium_url }}" target="_self">[MEDIUM]</a>
            {% endif %}
            {% if post.substack_url %}
                <a href="{{ post.substack_url }}" target="_self">[SUBSTACK]</a>
            {% endif %}
        </div>
    </li>
    {% endfor %}
  </div>

  <div class="footer-nav" style="margin-top: 2rem;">
    <a href="../index.html" target="_self" rel="noopener noreferrer">return.(self) ↩︎</a>
  </div>
</div>

<footer class="site-footer">
    &copy; 2025 Alaska Transportation &amp; Trucking L.L.C.
    <nav class="footer-nav">
        <a href="../terms.html">onlyCrumbs</a>
        <a href="../pricing.html">pricing</a>
        <a href="../dispatch.html">dispatch</a>
    </nav>
</footer>
  
</body>
</html>"""

# Render HTML
template = Template(html_template)
rendered_html = template.render(posts=posts)

# Save to index.html
with open("../../dispatch/index.html", "w", encoding="utf-8") as f:
    f.write(rendered_html)

print("✔️ index.html generated successfully.")