import json
from pathlib import Path
from tools.geo.logistics import haversine, FOB_ZIP, DB_DIR

RADIUS = 100  # miles
STATE_PREFIX = FOB_ZIP[:2]
STATE_FILE = DB_DIR / f"{STATE_PREFIX}.json"
OUTPUT_FILE = Path("../../route/db/44107.js")

def main():
    with open(STATE_FILE) as f:
        zips = json.load(f)

    # Find FOB coordinates
    fob = next(z for z in zips if z["zipcode"] == FOB_ZIP)
    flat = {}

    for z in zips:
        dist = haversine(fob["lat"], fob["lon"], z["lat"], z["lon"])
        if dist <= RADIUS:
            flat[z["zipcode"]] = {
                "lat": z["lat"],
                "lon": z["lon"]
            }

    # Save as JS object
    with open(OUTPUT_FILE, "w") as out:
        out.write("const zipCoords = ")
        json.dump(flat, out, indent=2)
        out.write(";\n")

    print(f"✅ Wrote {len(flat)} ZIPs to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()