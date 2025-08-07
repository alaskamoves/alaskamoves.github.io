# python/route/write_inputs.py
# ─────────────────────────────────────────────────────────────────────────────
# CLI mimic of a web form to collect pickup, dropoff, and payout.
# Writes inputs.json to the current directory for evaluate.py to consume.
# Use this script offline while on the road.
# ─────────────────────────────────────────────────────────────────────────────

import json
from pathlib import Path
from datetime import datetime

OUTPUT_FILE = Path("../../route/db/inputs.json")

def prompt_zip(prompt):
    while True:
        val = input(prompt).strip()
        if len(val) == 5 and val.isdigit():
            return val
        print("❌ Please enter a valid 5-digit ZIP code.")

def prompt_float(prompt):
    while True:
        try:
            return float(input(prompt).strip())
        except ValueError:
            print("❌ Please enter a valid number.")

def main():
    print("\n📋 Enter route details:")
    pickup = prompt_zip("Pickup ZIP: ")
    dropoff = prompt_zip("Dropoff ZIP: ")
    payout = prompt_float("Payout Offered ($): ")

    data = {
        "pickup": pickup,
        "dropoff": dropoff,
        "payout": payout,
        "timestamp": datetime.now().isoformat(timespec="seconds")
    }

    OUTPUT_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"\n✅ Saved route to {OUTPUT_FILE.resolve()}")
    print("Run `evaluate.py` to assess viability.")

if __name__ == "__main__":
    main()
