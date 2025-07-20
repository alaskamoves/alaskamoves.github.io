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
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Route Evaluation</title>
  <link rel="stylesheet" href="../assets/css/core.css">
</head>
<body>
  <header>
    <h1>📍 Route Evaluator</h1>
    <p>Assess whether the next gig stacks or stalls — in real time.</p>
  </header>
  <main>
    <section>
      <form method="GET" action="#">
        <label for="pickup">Pickup ZIP:</label>
        <input type="text" id="pickup" name="pickup" required><br>

        <label for="dropoff">Dropoff ZIP:</label>
        <input type="text" id="dropoff" name="dropoff" required><br>

        <label for="payout">Payout ($):</label>
        <input type="number" step="0.01" id="payout" name="payout" required><br>

        <input type="submit" value="Evaluate Gig">
      </form>
    </section>
    <section id="results">
      <p>No gig evaluated yet. Enter details above.</p>
    </section>
  </main>
  <footer>
    <p>&copy; 2025 Alaska Transportation &amp; Trucking L.L.C.</p>
  </footer>
</body>
</html>
"""

def write_index():
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(HEADER, encoding="utf-8")
    print(f"✅ index.html written to: {INDEX_FILE.resolve()}")

if __name__ == "__main__":
    write_index()