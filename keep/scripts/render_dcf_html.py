#!/usr/bin/env python3
"""
Render a DCF valuation HTML using a precomputed SEC XBRL bundle from dcf_metrics.py.
It fills FCF₀ (CFO - |CapEx|), Shares Outstanding, and Net Debt if available,
then asks the user for current price (or can auto-fill prior close via --price auto
using Stooq's CSV endpoint, no API key required).

Usage:
  # default uses tickers/AAPL/AAPL_xbrl_dump.json and writes tickers/AAPL/dcf_AAPL.html
  python render_dcf_html.py AAPL

  # explicit JSON path and auto-price
  python render_dcf_html.py tickers/MSFT/MSFT_xbrl_dump.json --price auto

  # just build from JSON without auto price
  python render_dcf_html.py tickers/AAPL/AAPL_xbrl_dump.json --out tickers/AAPL/dcf_AAPL.html
"""

import json
import argparse
from pathlib import Path
from typing import Optional, Tuple, Union
import html as _html

try:
    import requests  # optional (only used for --price auto)
except Exception:
    requests = None

# --- Minimal US-GAAP tag sets to derive inputs ---
TAGS = {
    # Cash flow
    "cfo": ["NetCashProvidedByUsedInOperatingActivities"],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"],

    # Balance sheet for net debt
    "cash": ["CashAndCashEquivalentsAtCarryingValue"],
    "st_debt": ["DebtCurrent", "ShortTermBorrowings"],
    "lt_debt": ["LongTermDebtNoncurrent", "LongTermDebt"],

    # Shares
    "shares_out": ["EntityCommonStockSharesOutstanding", "CommonStockSharesOutstanding"],
}


def _pick_latest_FY(facts_tag: dict, unit_hint: Optional[str] = None):
    units = facts_tag.get("units", {})
    unit_order = ([unit_hint] if unit_hint else []) + ["USD", "shares"] + list(units.keys())
    chosen = next((u for u in unit_order if u in units), None)
    if not chosen:
        return None, None, None, None
    pts = units[chosen]
    annual = [p for p in pts if p.get("fp") == "FY" and p.get("qtrs") in (4, 0)] or [p for p in pts if p.get("fp") == "FY"] or pts
    if not annual:
        return None, chosen, None, None
    annual.sort(key=lambda p: (p.get("fy", 0), p.get("end", "")))
    last = annual[-1]
    return last.get("val"), chosen, last.get("fy"), last.get("end")


def _get_tag_value(usgaap: dict, keys: list, unit_hint: Optional[str] = None):
    for tag in keys:
        if tag in usgaap:
            hint = unit_hint or ("shares" if "Shares" in tag else "USD")
            val, unit, fy, end = _pick_latest_FY(usgaap[tag], hint)
            if val is not None:
                return float(val), unit, fy, end, tag
    return None, None, None, None, None


def derive_inputs(bundle: dict):
    usgaap = bundle.get("companyfacts", {}).get("facts", {}).get("us-gaap", {})
    # FCF0
    cfo, *_ = _get_tag_value(usgaap, TAGS["cfo"], "USD")
    capex, *_ = _get_tag_value(usgaap, TAGS["capex"], "USD")
    fcf0 = (cfo - abs(capex)) if (cfo is not None and capex is not None) else None

    # Net debt = (ST debt + LT debt) - cash
    st_debt, *_ = _get_tag_value(usgaap, TAGS["st_debt"], "USD")
    lt_debt, *_ = _get_tag_value(usgaap, TAGS["lt_debt"], "USD")
    cash, *_ = _get_tag_value(usgaap, TAGS["cash"], "USD")
    net_debt = ( (st_debt or 0) + (lt_debt or 0) - (cash or 0) ) if any(v is not None for v in (st_debt, lt_debt, cash)) else None

    shares, *_ = _get_tag_value(usgaap, TAGS["shares_out"], "shares")

    return {
        "fcf0": fcf0,
        "net_debt": net_debt,
        "shares": shares,
    }


def stooq_prior_close(ticker: str) -> Optional[float]:
    """Fetch prior close from Stooq daily CSV (no key). Ticker is assumed US if it lacks a suffix.
    We try <TICKER>.US first, then the raw ticker. Returns close as float or None on error.
    """
    if requests is None:
        return None
    candidates = []
    t = ticker.upper().lstrip("$")
    if "." not in t:
        candidates.append(f"{t}.US")
    candidates.append(t)
    for sym in candidates:
        url = f"https://stooq.com/q/d/l/?s={sym.lower()}&i=d"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200 or not r.text.strip():
                continue
            lines = [ln.strip() for ln in r.text.splitlines() if ln.strip()]
            if len(lines) < 2:
                continue
            # CSV header: Date,Open,High,Low,Close,Volume
            last = lines[-1].split(',')
            if len(last) >= 5:
                return float(last[4])
        except Exception:
            continue
    return None


HTML_HEAD = """<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>DCF Valuation Calculator</title>
  <link rel=\"stylesheet\" href=\"https://alaskamoves.us/styles/css/dcf.css\" />
  <script src=\"https://cdn.jsdelivr.net/npm/chart.js\"></script>
</head>
<body>
  <div class=\"container\">"""

HTML_TAIL = """  
    <footer class="site-footer">\n
    <nav class="footer-nav">\n
        <a  href="https://alaskamoves.us/index.html">\n
            &copy; 2025 Alaska Transportation &amp; Trucking L.L.C.\n
            <br /></a>\n
        <a href="https://alaskamoves.us/build/index.html">build</a>\n
        <a href="https://alaskamoves.us/connect/index.html">connect</a>\n
        <a href="https://alaskamoves.us/dispatch/index.html">dispatch</a>\n
        <a href="https://alaskamoves.us/exchange/index.html">exchange</a>\n
        <a href="https://alaskamoves.us/file/index.html">file</a>\n
    </nav>\n
    </footer>\n
</div>\n   
<script>\n    
    const $ = (id) => document.getElementById(id);\n    
    const fmt = new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 });\n    
    const fmtMoney = (x) => (isFinite(x) ? (x < 0 ? '-' : '') + new Intl.NumberFormat(undefined, 
        { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(Math.abs(x)) : '—');\n    
    const fmtPrice = (x) => (isFinite(x) ? new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD', maximumFractionDigits: 2 }).format(x) : '—');\n
    const clamp = (v, min, max) => Math.min(Math.max(v, min), max);\n\n    
    function parseNum(input) {\n      if (!input) return NaN;\n      
    const v = parseFloat(String(input).replace(/[\\,\\s]/g, ''));\n      
    return isNaN(v) ? NaN : v;\n    }\n\n    
    function dcf({ fcf0, years, growth, terminalGrowth, discount, netDebt, shares }) {\n      
    const r = discount / 100;\n      const g = growth / 100;\n      const gt = terminalGrowth / 100;\n      
    if (r <= gt) return { error: 'Discount rate must exceed terminal growth.' };\n\n      
    let pvCashflows = 0;\n      
    let fcf_t = fcf0;\n      
    for (let t = 1; t <= years; t++) {\n        
    fcf_t = fcf_t * (1 + g);\n        
    pvCashflows += fcf_t / Math.pow(1 + r, t);\n      }\n      
    const fcf_n1 = fcf_t * (1 + gt);\n      
    const terminalValue = fcf_n1 / (r - gt);\n      
    const pvTerminal = terminalValue / Math.pow(1 + r, years);\n      
    const enterprise = pvCashflows + pvTerminal;\n      
    const equity = enterprise - netDebt;\n      
    return { pvCashflows, pvTerminal, enterprise, equity };\n    }\n\n    
    function computeAndRender() {\n      
    const fcf0 = parseNum($("fcf0").value);\n      
    const years = Math.round(parseNum($("years").value));\n      
    const growth = parseNum($("growth").value);\n      
    const terminalGrowth = parseNum($("terminalGrowth").value);\n      
    const discount = parseNum($("discountBox").value);\n      
    const netDebt = parseNum($("netDebt").value);\n      
    const shares = parseNum($("shares").value);\n      
    const currentPrice = parseNum($("currentPrice").value);\n\n      
    if ([fcf0, years, growth, terminalGrowth, discount, netDebt, shares].some(v => !isFinite(v))) {\n        
    alert('Please fill all required numeric fields.');\n        return;\n      }\n\n      
    const res = dcf({ fcf0, years, growth, terminalGrowth, discount, netDebt, shares });\n      
    if (res.error) { alert(res.error); return; }\n\n      const ivps = res.equity / shares;\n      
    $("ivps").textContent = fmtPrice(ivps);\n      
    $("ev").textContent = fmtMoney(res.enterprise);\n      
    $("equity").textContent = fmtMoney(res.equity);\n\n      
    if (isFinite(currentPrice)) {\n        const upside = (ivps / currentPrice - 1) * 100;\n        
    const sign = upside >= 0 ? '+' : '';\n        $("upside").textContent = sign + fmt.format(upside) + '%';\n
    } else {\n        $("upside").textContent = '—';\n      }\n\n      
    updateChartSensitivity({ fcf0, years, growth, terminalGrowth, netDebt, shares });\n    }\n\n    
    $("discount").addEventListener('input', (e) => {\n      $("discountBox").value = e.target.value;\n      
    $("discountLabel").textContent = parseFloat(e.target.value).toFixed(1) + '%';\n    });\n    
    $("discountBox").addEventListener('input', (e) => {\n      
    const v = clamp(parseNum(e.target.value), 0.1, 60);\n      $("discount").value = v;\n      
    $("discountLabel").textContent = parseFloat(v).toFixed(1) + '%';\n    });\n    
    document.querySelectorAll('[data-bump]').forEach(btn => btn.addEventListener('click', () => {\n      
    const delta = parseFloat(btn.dataset.bump);\n      
    const v = clamp(parseNum($("discountBox").value) + delta, 0.1, 60);\n      
    $("discountBox").value = v.toFixed(1);\n      $("discount").value = v;\n      
    $("discountLabel").textContent = v.toFixed(1) + '%';\n    }));\n\n    
    $("calcBtn").addEventListener('click', computeAndRender);\n    
    $("resetBtn").addEventListener('click', () => { document.querySelectorAll('input').forEach(i => i.value = ''); $("discount").value = 10; $("discountBox").value = 10; $("discountLabel").textContent = '10.0%'; clearOutputs(); });\n
    $("downloadBtn").addEventListener('click', () => {\n      const payload = {\n        
    ticker: $("ticker").value || null,\n        currentPrice: parseNum($("currentPrice").value) || null,\n
    fcf0: parseNum($("fcf0").value) || null,\n        years: parseNum($("years").value) || null,\n        
    growth: parseNum($("growth").value) || null,\n        
    terminalGrowth: parseNum($("terminalGrowth").value) || null,\n        
    discount: parseNum($("discountBox").value) || null,\n        
    netDebt: parseNum($("netDebt").value) || null,\n        
    shares: parseNum($("shares").value) || null,\n        
    timestamp: new Date().toISOString()\n      };\n      
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });\n      
    const url = URL.createObjectURL(blob);\n      const a = document.createElement('a');\n      
    a.href = url; a.download = (payload.ticker || 'dcf') + '_assumptions.json';\n      
    document.body.appendChild(a); a.click(); a.remove();\n      URL.revokeObjectURL(url);\n    });\n\n    
    function clearOutputs() {\n      $("ivps").textContent = '—';\n      $("upside").textContent = '—';\n      
    $("ev").textContent = '—';\n      $("equity").textContent = '—';\n      if (chart) chart.destroy();\n      
    initChart();\n    }\n\n    let chart;\n    function initChart() {\n      
    const ctx = document.getElementById('chart').getContext('2d');\n      
    chart = new Chart(ctx, {\n        type: 'line',\n        data: {\n          labels: [],\n          
    datasets: [{ label: 'Intrinsic Value / Share', data: [], tension: 0.25, pointRadius: 0 }]\n        },\n
    options: {\n          responsive: true,\n          
    plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => '$' + Number(ctx.parsed.y).toFixed(2) } } },\n
    scales: {\n            x: { title: { display: true, text: 'Discount Rate (%)' } },\n            
    y: { title: { display: true, text: 'Value / Share (USD)' }, beginAtZero: false }\n          
    }\n        }\n    });\n    }\n\n    
    function updateChartSensitivity({ fcf0, years, growth, terminalGrowth, netDebt, shares }) {\n      
    const xs = [];\n      const ys = [];\n      for (let r = 4; r <= 20.01; r += 0.25) {\n        
    const res = dcf({ fcf0, years, growth, terminalGrowth, discount: r, netDebt, shares });\n        
    if (res.error) { continue; }\n        const ivps = res.equity / shares;\n        
    xs.push(r.toFixed(2));\n        ys.push(ivps);\n      }\n      chart.data.labels = xs;\n      
    chart.data.datasets[0].data = ys;\n      chart.update();\n    }\n\n    initChart();\n  
    </script>\n    
    </body>\n</html>\n"""


def render_html(bundle: dict, out_path: Path, auto_price: Optional[float] = None):
    tkr = bundle.get("ticker", "—")
    name = bundle.get("companyName", "—")

    derived = bundle.get("derived") or {}
    fcf0 = derived.get("fcf0")
    net_debt = derived.get("net_debt")
    shares = derived.get("shares")
    if fcf0 is None or net_debt is None or shares is None:
        # Fallback to compute from full companyfacts if present
        _fallback = derive_inputs(bundle)
        fcf0 = fcf0 if fcf0 is not None else _fallback.get("fcf0")
        net_debt = net_debt if net_debt is not None else _fallback.get("net_debt")
        shares = shares if shares is not None else _fallback.get("shares")
    fcf0 = fcf0 or 0
    net_debt = net_debt or 0
    shares = shares or 1

    header = f"""
    <header class=\"flex flex-col md:flex-row md:items-end md:justify-between gap-4 mb-6\">
      <div>
        <h1 class=\"text-3xl md:text-4xl font-bold tracking-tight\">DCF – { _html.escape(tkr) }</h1>
        <p class=\"text-zinc-600 dark:text-zinc-300 mt-1\">{ _html.escape(name or '—') } · Pre-filled from SEC XBRL (companyfacts).</p>
      </div>
    </header>
    """

    inputs = f"""
    <div class=\"grid grid-cols-1 lg:grid-cols-3 gap-6\">
      <section class=\"card p-5 lg:col-span-2\">
        <div class=\"grid grid-cols-1 md:grid-cols-2 gap-4\">
          <div>
            <label class=\"label\">Ticker</label>
            <input id=\"ticker\" class=\"input\" value=\"{_html.escape(tkr)}\" />
          </div>
          <div>
            <label class=\"label\">Current Share Price</label>
            <input id=\"currentPrice\" class=\"number-input\" inputmode=\"decimal\" placeholder=\"{(auto_price or 0):.2f}\" value=\"{(auto_price or '')}\" />
            <p class=\"hint mt-1\">{ 'Auto-filled from Stooq prior close' if auto_price else 'Enter latest price (prior close is fine)' }.</p>
          </div>

          <div>
            <label class=\"label\">Starting Free Cash Flow (FCF₀)</label>
            <input id=\"fcf0\" class=\"number-input\" inputmode=\"decimal\" value=\"{int(round(fcf0))}\" />
            <p class=\"hint mt-1\">Derived as CFO − |Capex| from latest FY.</p>
          </div>
          <div>
            <label class=\"label\">Projection Years (N)</label>
            <input id=\"years\" class=\"number-input\" inputmode=\"numeric\" value=\"5\" />
          </div>

          <div>
            <label class=\"label\">FCF Growth Rate (annual, %)</label>
            <input id=\"growth\" class=\"number-input\" inputmode=\"decimal\" value=\"5\" />
          </div>
          <div>
            <label class=\"label\">Terminal Growth (g, %)</label>
            <input id=\"terminalGrowth\" class=\"number-input\" inputmode=\"decimal\" value=\"2.5\" />
            <p class=\"hint mt-1\">Conservative long‑run growth (≤ GDP).</p>
          </div>

          <div class=\"md:col-span-2\">
            <label class=\"label flex items-center justify-between\"> <span>Discount Rate (WACC, %)</span> <span id=\"discountLabel\" class=\"font-semibold\">10.0%</span> </label>
            <input id=\"discount\" type=\"range\" min=\"3\" max=\"25\" step=\"0.1\" value=\"10\" class=\"w-full\" />
            <div class=\"mt-2 grid grid-cols-3 gap-2\">
              <input id=\"discountBox\" class=\"number-input\" inputmode=\"decimal\" value=\"10\" />
              <button class=\"btn-ghost\" data-bump=\"-1\">–1%</button>
              <button class=\"btn-ghost\" data-bump=\"1\">+1%</button>
            </div>
          </div>

          <div>
            <label class=\"label\">Net Debt (Debt – Cash)</label>
            <input id=\"netDebt\" class=\"number-input\" inputmode=\"decimal\" value=\"{int(round(net_debt))}\" />
          </div>
          <div>
            <label class=\"label\">Shares Outstanding</label>
            <input id=\"shares\" class=\"number-input\" inputmode=\"decimal\" value=\"{int(round(shares))}\" />
          </div>
        </div>

        <div class=\"mt-6 flex gap-2\">
          <button id=\"calcBtn\" class=\"btn\">Calculate</button>
          <button id=\"downloadBtn\" class=\"btn-ghost\">Download Assumptions</button>
          <button id=\"resetBtn\" class=\"btn-ghost\">Reset</button>
        </div>
      </section>

      <section class=\"card p-5 flex flex-col gap-4\">
        <div>
          <h2 class=\"text-xl font-semibold mb-2\">Results</h2>
          <div class=\"grid grid-cols-2 gap-4\">
            <div class=\"p-3 rounded-xl bg-zinc-50 dark:bg-zinc-800\"><div class=\"hint\">Intrinsic Value / Share</div><div id=\"ivps\" class=\"kpi\">—</div></div>
            <div class=\"p-3 rounded-xl bg-zinc-50 dark:bg-zinc-800\"><div class=\"hint\">Upside vs. Current</div><div id=\"upside\" class=\"kpi\">—</div></div>
            <div class=\"p-3 rounded-xl bg-zinc-50 dark:bg-zinc-800\"><div class=\"hint\">Enterprise Value (DCF)</div><div id=\"ev\" class=\"font-semibold\">—</div></div>
            <div class=\"p-3 rounded-xl bg-zinc-50 dark:bg-zinc-800\"><div class=\"hint\">Equity Value</div><div id=\"equity\" class=\"font-semibold\">—</div></div>
          </div>
        </div>
        <div class=\"h-px bg-zinc-200 dark:bg-zinc-800\"></div>
        <div><h3 class=\"font-semibold mb-2\">DCF Sensitivity (Value/Share vs Discount Rate)</h3><canvas id=\"chart\" height=\"200\"></canvas></div>
        <details class=\"mt-2\"><summary class=\"cursor-pointer select-none font-medium\">Methodology</summary><div class=\"mt-2 text-sm text-zinc-600 dark:text-zinc-300 space-y-1\"><p>We project FCF for N years with constant growth <em>g</em> and discount at rate <em>r</em>. Terminal value uses Gordon Growth: TV = FCF<sub>N+1</sub> / (r − g<sub>term</sub>). Enterprise value is PV of projected FCFs plus PV(TV). Equity value = Enterprise value − Net Debt. Intrinsic value per share = Equity / Shares.</p><p>Inputs are auto-derived from SEC XBRL where available; you can override any field. Price is the prior close if auto-filled, otherwise enter manually.</p></div></details>
      </section>
    </div>
    """

    html = HTML_HEAD + header + inputs + HTML_TAIL
    out_path.write_text(html, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Render a DCF HTML from an XBRL bundle, pre-filled with FCF/share/net debt.")
    ap.add_argument("json_or_ticker", nargs="?", help="Path to <TICKER>_xbrl_dump.json or a ticker symbol (default AAPL)")
    ap.add_argument("--out", help="Output HTML path (default: tickers/<TICKER>/dcf_<TICKER>.html)")
    ap.add_argument("--price", choices=["auto", "none"], default="none", help="Auto-fill prior close via Stooq (default: none)")
    args = ap.parse_args()

    if not args.json_or_ticker:
        ticker = "AAPL"
    else:
        candidate = Path(args.json_or_ticker)
        if candidate.exists() and candidate.suffix.lower() == ".json":
            in_path = candidate
            ticker = in_path.stem.split("_")[0].upper()
        else:
            ticker = args.json_or_ticker.upper().lstrip("$")
    # default locations under tickers/
    if 'in_path' not in locals():
        in_path = Path("../tickers") / f"{ticker}.json"
        if not in_path.exists():
            alt = Path("../tickers") / f"{ticker}.json"
            in_path = alt

    if not in_path.exists():
        print(f"JSON file {in_path} not found — run dcf_metrics.py to create tickers/{ticker}_dfc.json (or provide a path).")
        raise SystemExit(2)

    bundle = json.loads(in_path.read_text())

    auto_price = None
    if args.price == "auto":
        auto_price = stooq_prior_close(ticker)

    out_path = Path(args.out) if args.out else (Path("../tickers") / f"{ticker}.html")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    render_html(bundle, out_path, auto_price=auto_price)
    print(f"Wrote {out_path.resolve()}")


if __name__ == "__main__":
    main()