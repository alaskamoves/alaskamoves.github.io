#!/usr/bin/env python3
"""
Rebuild DCF-ready JSONs for all tickers and render per-ticker HTML pages,
then write an index page linking to every ticker.

Default source: tickers/tickers.json (if present). Fallback: db/top_tickers.json.

Usage:
  # Recompute (fetch SEC) and render everything, auto-fill prior close
  python render_all.py --price auto

  # Only render from existing JSONs (skip SEC fetch)
  python render_all.py --no-fetch --price none

  # Specify an explicit list
  python render_all.py --list db/my_list.json
"""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
from typing import List
import dcf_metrics           # batch_precompute, etc.
import render_dcf_html       # render_html(), stooq_prior_close()

CSS = "https://alaskamoves.us/styles/css/dcf.css"


def load_ticker_list(list_arg: str | None) -> List[str]:
    if list_arg:
        p = Path(list_arg)
        if not p.exists():
            raise SystemExit(f"--list file not found: {p}")
        return [str(t).upper().lstrip('$') for t in json.loads(p.read_text())]

    idx = Path("../db/tickers.json")
    if idx.exists():
        try:
            data = json.loads(idx.read_text())
            return [str(row.get("ticker")).upper() for row in data if row.get("ticker")]
        except Exception:
            pass

    fallback = Path("../db/top_tickers.json")
    if fallback.exists():
        return [str(t).upper().lstrip('$') for t in json.loads(fallback.read_text())]

    raise SystemExit("No db/tickers.json or db/top_tickers.json found. Provide --list.")


def precompute_if_needed(tickers: List[str], do_fetch: bool) -> Path:
    out_root = Path("../tickers")
    out_root.mkdir(exist_ok=True)
    if do_fetch:
        dcf_metrics.batch_precompute(tickers, out_root)  # writes tickers/tickers.json
        return out_root / "tickers.json"

    # ensure index exists; if not, synthesize from existing dfc files
    idx = out_root / "tickers.json"
    if idx.exists():
        return idx

    rows = []
    for t in tickers:
        p = out_root / t / f"{t}.json"
        if p.exists():
            try:
                b = json.loads(p.read_text())
                rows.append({
                    "ticker": b.get("ticker", t),
                    "companyName": b.get("companyName"),
                    "cik": b.get("cik"),
                    "latest": b.get("latest", {}),
                    "bundlePath": str(p)
                })
            except Exception:
                continue
    idx.write_text(json.dumps(rows, indent=2))
    return idx


def render_ticker_page(ticker: str, price_mode: str) -> Path:
    t = ticker.upper().lstrip('$')
    in_path = Path("../tickers") / t / f"{t}.json"
    if not in_path.exists():
        alt = Path("../tickers") / f"{t}.json"
        in_path = alt if alt.exists() else in_path
    if not in_path.exists():
        print(f"WARN {t}: missing dcf json: {in_path}")
        return Path()

    bundle = json.loads(in_path.read_text())
    auto_price = render_dcf_html.stooq_prior_close(t) if price_mode == "auto" else None

    out_path = Path("../tickers") / f"{t}" / f"{t}.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    render_dcf_html.render_html(bundle, out_path, auto_price=auto_price)
    print(f"HTML {t}: {out_path}")
    return out_path


def render_index(idx_path: Path) -> Path:
    data = json.loads(idx_path.read_text()) if idx_path.exists() else []

    rows = []
    for row in data:
        t = row.get("ticker")
        name = row.get("companyName", "") or ""
        latest = row.get("latest", {}) or {}
        k = latest.get("10-K") or {}
        q = latest.get("10-Q") or {}
        rows.append((t, name, k.get("filingDate", ""), q.get("filingDate", "")))

    now = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>DCF Dashboard</title>
  <link rel="stylesheet" href="{CSS}" />
</head>
<body>
<div class="container">
<header>
<h1>DCF Dashboard</h1>
<p class="muted">Updated {now}</p>
</header>
<main>
    <table class="table">
    <thead><tr><th>Ticker</th><th>Company</th><th>Latest 10-K</th><th>Latest 10-Q</th></tr></thead>
    <tbody>
    {''.join(f'<tr><td><a href="{t}/{t}.html">{t}</a></td><td>{name}</td><td>{kdate}</td><td>{qdate}</td></tr>' for (t,name,kdate,qdate) in rows)}
    </tbody>
    </table>
    <footer class="site-footer">
        <nav class="footer-nav">
            <a  href="https://alaskamoves.us/index.html">
                &copy; 2025 Alaska Transportation &amp; Trucking L.L.C.
            <br /></a>
            <a href="https://alaskamoves.us/build/index.html">build</a>
            <a href="https://alaskamoves.us/connect/index.html">connect</a>
            <a href="https://alaskamoves.us/dispatch/index.html">dispatch</a>
            <a href="https://alaskamoves.us/exchange/index.html">exchange</a>
            <a href="https://alaskamoves.us/file/index.html">file</a>
        </nav>
    </footer>
</main>
</div>
</body>
</html>"""
    out = Path("../tickers/index.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"Wrote index: {out.resolve()}")
    return out


def main():
    ap = argparse.ArgumentParser(description="Rebuild dcf JSONs and render all ticker pages + an index HTML.")
    ap.add_argument("--list", help="Explicit JSON list of tickers (overrides tickers/tickers.json)")
    ap.add_argument("--no-fetch", action="store_true", help="Skip SEC fetch; render from existing JSONs")
    ap.add_argument("--price", choices=["auto", "none"], default="none", help="Auto-fill prior close on pages")
    args = ap.parse_args()

    tickers = load_ticker_list(args.list)
    idx_path = precompute_if_needed(tickers, do_fetch=not args.no_fetch)

    # Render per-ticker pages
    for t in tickers:
        render_ticker_page(t, price_mode=args.price)

    # Re-read index and render dashboard
    render_index(idx_path)


if __name__ == "__main__":
    main()