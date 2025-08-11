#!/usr/bin/env python3
import sys, json, time, re
from pathlib import Path
from typing import Optional, Union
import requests

UA = "Your Name YourSite your.email@example.com"

SEC_BASE = "https://data.sec.gov"
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

def http_get(url):
    r = requests.get(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip, deflate"})
    r.raise_for_status()
    return r

def load_ticker_map(cache_path: Path) -> dict:
    if cache_path.exists():
        return json.loads(cache_path.read_text())
    time.sleep(0.2)
    data = http_get(TICKERS_URL).json()
    cache_path.write_text(json.dumps(data))
    return data

def ticker_to_cik(ticker: str, mapping: dict) -> str:
    t = ticker.upper().lstrip("$")
    for _, row in mapping.items():
        if row["ticker"].upper() == t:
            return f'{int(row["cik_str"]):010d}'
    raise ValueError(f"Ticker not found in SEC mapping: {ticker}")

def get_company_facts(cik: str) -> dict:
    time.sleep(0.2)
    return http_get(f"{SEC_BASE}/api/xbrl/companyfacts/CIK{cik}.json").json()

def get_submissions(cik: str) -> dict:
    time.sleep(0.2)
    return http_get(f"{SEC_BASE}/submissions/CIK{cik}.json").json()

def latest_filing_accessions(subs_json: dict) -> dict:
    """Return {'10-K': (accession, date), '10-Q': (accession, date)} for the most recent of each."""
    recent = subs_json.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    accns = recent.get("accessionNumber", [])
    dates = recent.get("filingDate", [])
    latest = {}
    for form, accn, dt in zip(forms, accns, dates):
        if form in ("10-K", "10-Q") and form not in latest:
            latest[form] = (accn, dt)
        if "10-K" in latest and "10-Q" in latest:
            break
    return latest

# --- Batch precompute and index support ---
def build_bundle(ticker: str, mapping: dict, out_root: Path) -> Path:
    ticker = ticker.upper().lstrip("$")
    out_root.mkdir(exist_ok=True)
    out_dir = out_root / ticker
    out_dir.mkdir(exist_ok=True)

    cik = ticker_to_cik(ticker, mapping)

    subs = get_submissions(cik)
    facts = get_company_facts(cik)

    latest = latest_filing_accessions(subs)
    latest_10k = latest.get("10-K")
    latest_10q = latest.get("10-Q")

    usgaap = facts.get("facts", {}).get("us-gaap", {})
    def _latest(tag_names, unit_hint=None):
        def pick_latest_FY(facts_tag, unit_hint=None):
            units = facts_tag.get("units", {})
            unit_order = ([unit_hint] if unit_hint else []) + ["USD", "shares"] + list(units.keys())
            chosen = next((u for u in unit_order if u in units), None)
            if not chosen:
                return None
            pts = units[chosen]
            annual = [p for p in pts if p.get("fp") == "FY" and p.get("qtrs") in (4, 0)] or [p for p in pts if p.get("fp") == "FY"] or pts
            if not annual:
                return None
            annual.sort(key=lambda p: (p.get("fy", 0), p.get("end", "")))
            return annual[-1].get("val")
        for tg in tag_names:
            if tg in usgaap:
                val = pick_latest_FY(usgaap[tg], unit_hint or ("shares" if "Shares" in tg else "USD"))
                if val is not None:
                    return float(val)
        return None

    cfo = _latest(["NetCashProvidedByUsedInOperatingActivities"], "USD")
    capex = _latest(["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"], "USD")
    fcf0 = (cfo - abs(capex)) if (cfo is not None and capex is not None) else None

    st_debt = _latest(["DebtCurrent", "ShortTermBorrowings"], "USD")
    lt_debt = _latest(["LongTermDebtNoncurrent", "LongTermDebt"], "USD")
    cash = _latest(["CashAndCashEquivalentsAtCarryingValue"], "USD")
    net_debt = ((st_debt or 0) + (lt_debt or 0) - (cash or 0)) if any(v is not None for v in (st_debt, lt_debt, cash)) else None

    shares = _latest(["EntityCommonStockSharesOutstanding", "CommonStockSharesOutstanding"], "shares")

    bundle = {
        "ticker": ticker,
        "cik": cik,
        "companyName": subs.get("name"),
        "latest": {
            "10-K": {"accession": latest_10k[0], "filingDate": latest_10k[1]} if latest_10k else None,
            "10-Q": {"accession": latest_10q[0], "filingDate": latest_10q[1]} if latest_10q else None,
        },
        "derived": {
            "fcf0": fcf0,
            "net_debt": net_debt,
            "shares": shares,
        },
        "sources": {
            "submissions": f"{SEC_BASE}/submissions/CIK{cik}.json",
            "companyfacts": f"{SEC_BASE}/api/xbrl/companyfacts/CIK{cik}.json",
        }
    }

    out_path = out_dir / f"{ticker}.json"
    out_path.write_text(json.dumps(bundle, indent=2))
    return out_path

def batch_precompute(tickers, out_root: Path):
    cache_dir = Path("../db"); cache_dir.mkdir(exist_ok=True)
    mapping = load_ticker_map(cache_dir / "company_tickers.json")

    index = []
    for t in tickers:
        try:
            p = build_bundle(t, mapping, out_root)
            bundle = json.loads(p.read_text())
            index.append({
                "ticker": bundle.get("ticker"),
                "companyName": bundle.get("companyName"),
                "cik": bundle.get("cik"),
                "latest": bundle.get("latest", {}),
                "bundlePath": str(p)
            })
            print(f"OK {t}: {p}")
        except Exception as e:
            print(f"FAIL {t}: {e}")

    idx_path = out_root / "tickers.json"
    idx_path.write_text(json.dumps(index, indent=2))
    print(f"Wrote index: {idx_path.resolve()}")
    return idx_path

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Fetch SEC submissions + XBRL companyfacts. Single ticker or batch from JSON list.")
    ap.add_argument("ticker", nargs="?", help="Ticker symbol (e.g., AAPL)")
    ap.add_argument("--list", help="Path to JSON array of tickers for batch precompute (e.g., db/top_tickers.json)")
    ap.add_argument("--out-root", default="tickers", help="Output directory root (default: tickers)")
    args = ap.parse_args()

    out_root = Path(args.out_root)

    if args.list:
        tickers = json.loads(Path(args.list).read_text())
        batch_precompute(tickers, out_root)
        return

    # Single ticker path (backwards compatible)
    ticker = (args.ticker or "AAPL").upper().lstrip("$")
    cache_dir = Path("../db"); cache_dir.mkdir(exist_ok=True)
    mapping = load_ticker_map(cache_dir / "company_tickers.json")
    p = build_bundle(ticker, mapping, out_root)
    print(f"Wrote {p.resolve()}")

if __name__ == "__main__":
    main()