# tools/route/generate_index.py
# ─────────────────────────────────────────────────────────────────────────────
# Script to generate the index.html page for the route/ directory.
# Pulls from logistics.py and creates a landing page for gig evaluation.
# This is the frontend driveway, paved by backend facts.
# ─────────────────────────────────────────────────────────────────────────────

from pathlib import Path
from datetime import datetime

ROUTE_DIR = Path("../../route/")
INDEX_FILE = ROUTE_DIR / "index.html"

HEADER = """<!DOCTYPE html>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Could Alaska Move?</title>
  <link rel="stylesheet" href="dispatch.styles">
</head>
<body>
  <div class="container">
  <h1>Could Alaska Move?</h1>

  <form id="routeForm">
  <label for="src">Pickup ZIP:</label>
  <input id="src" type="text" value="44111" required />

  <label for="dest">Dropoff ZIP:</label>
  <input id="dest" type="text" value="44106" required />

  <label for="payout">Payout ($):</label>
  <input id="payout" type="number" value="71" required />

  <button id="submit">Evaluate Route</button>
  </form>
  <pre id="output"></pre>

  <script src="db/44107.js"></script>
  <script type="module" src="logistics.js"></script>

  <footer class="site-footer">
    &copy; 2025 Alaska Transportation &amp; Trucking L.L.C.
    <nav class="footer-nav">
      <a href="index.html">onlyCrumbs</a>
      <a href="index.html">pricing</a>
      <a href="dispatch.html">dispatch</a>
    </nav>
  </footer>
  </div>
</body>
</html>
"""

def write_index():
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(HEADER, encoding="utf-8")
    print(f"✅ index.html written to: {INDEX_FILE.resolve()}")

if __name__ == "__main__":
    write_index()