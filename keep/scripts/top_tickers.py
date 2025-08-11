#!/usr/bin/env python3
"""
Output the top-N tickers by transaction magnitude from a ledger CSV, or
fallback to a default JSON list. Optionally write a JSON file with the
selected tickers for downstream batch processing.

Usage examples:
  # from CSV, print to stdout and write db/top_tickers.json
  python top_tickers.py --csv db/fy25_txns.csv -n 10 --json-out db/top_tickers.json

  # use default list when no CSV is provided
  python top_tickers.py --default db/default_tickers.json --json-out db/top_tickers.json

  # just print the JSON list to stdout (newline-delimited tickers also printed)
  python top_tickers.py --list db/top_tickers.json
"""

import argparse
import json
from pathlib import Path
from typing import List
import pandas as pd


def compute_top_tickers(csv_path: str, n: int) -> List[str]:
    df = pd.read_csv(csv_path)

    # Split income vs spend
    income = df[df["amount"] > 0].groupby("account")["amount"].sum()
    spending = df[df["amount"] < 0].groupby("account")["amount"].sum()

    # Combine and compute magnitude
    summary = pd.concat([income, spending], axis=1, keys=["income", "spending"]).fillna(0)
    summary["magnitude"] = summary["income"].abs() + summary["spending"].abs()

    # Rank by magnitude and take top N
    top = summary.sort_values("magnitude", ascending=False).head(n)
    return list(top.index)


def main():
    ap = argparse.ArgumentParser(description="Produce a top-N ticker list (and/or JSON) for downstream processing.")
    ap.add_argument("--csv", help="Path to transactions CSV (expects columns: account, amount)")
    ap.add_argument("-n", "--n", type=int, default=10, help="Number of tickers to select (default: 10)")
    ap.add_argument("--default", default="db/default_tickers.json", help="Fallback JSON file with a default list (array of tickers)")
    ap.add_argument("--list", help="Existing JSON list (array of tickers) to just echo/validate")
    ap.add_argument("--json-out", default="db/top_tickers.json", help="Path to write the resulting JSON array")
    args = ap.parse_args()

    tickers: List[str] = []

    if args.list:
        tickers = json.loads(Path(args.list).read_text())
    elif args.csv:
        tickers = compute_top_tickers(args.csv, args.n)
    else:
        # fallback to a default list
        default_path = Path(args.default)
        if default_path.exists():
            tickers = json.loads(default_path.read_text())
        else:
            raise SystemExit(f"No --csv provided and default list not found: {default_path}")

    # Normalize and de-duplicate, preserve order
    norm = []
    seen = set()
    for t in tickers:
        s = str(t).upper().lstrip("$").strip()
        if s and s not in seen:
            norm.append(s)
            seen.add(s)

    # Write JSON output
    out_path = Path(args.json_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(norm, indent=2))

    # Print results for piping convenience
    for t in norm:
        print(t)

    # Also echo where JSON went
    print(f"\nWrote JSON list: {out_path.resolve()}")


if __name__ == "__main__":
    main()