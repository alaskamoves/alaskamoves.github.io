# tools/route/evaluate.py
# ─────────────────────────────────────────────────────────────────────────────
# Offline evaluator: Should you take the gig, or head home?
# Compares cost to complete a delivery (pickup → dropoff → FOB) vs. cost to go
# straight home from pickup. Verdict is based on which yields higher net value.
# ─────────────────────────────────────────────────────────────────────────────

import json
from pathlib import Path
from tools.geo.logistics import estimate_cost, FOB_ZIP

INPUTS_FILE = Path("../../route/db/inputs.json")


def go_or_no(pickup, dropoff, payout):
    """
    Compare cost of completing a delivery vs. heading home.
    Returns a dict with costs, gain, and verdict.
    """
    cost_if_accepted = estimate_cost(pickup, dropoff) + estimate_cost(dropoff, FOB_ZIP)
    cost_if_home = estimate_cost(pickup, FOB_ZIP)

    net_gain = payout - cost_if_accepted
    savings_if_home = -cost_if_home

    verdict = "✅ TAKE IT" if net_gain > savings_if_home else "❌ SKIP IT"

    return {
        "pickup": pickup,
        "dropoff": dropoff,
        "payout": payout,
        "cost_if_accepted": round(cost_if_accepted, 2),
        "net_gain": round(net_gain, 2),
        "cost_to_just_go_home": round(cost_if_home, 2),
        "verdict": verdict
    }


def main():
    if not INPUTS_FILE.exists():
        print("❌ inputs.json not found.")
        return

    with open(INPUTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    pickup = data.get("pickup")
    dropoff = data.get("dropoff")
    payout = float(data.get("payout", 0))

    if not pickup or not dropoff:
        print("❌ Please specify both pickup and dropoff ZIPs.")
        return

    result = go_or_no(pickup, dropoff, payout)

    print("\n🧭 Route Evaluation:")
    print(f"  From {result['pickup']} to {result['dropoff']}, ending at FOB ({FOB_ZIP})")
    print(f"  Payout Offered: ${result['payout']:.2f}")
    print(f"  Cost to Complete: ${result['cost_if_accepted']:.2f}")
    print(f"  Cost to Go Home Instead: ${result['cost_to_just_go_home']:.2f}")
    print(f"  Net Gain if Taken: ${result['net_gain']:.2f}")
    print(f"\n{result['verdict']}")


if __name__ == "__main__":
    main()
