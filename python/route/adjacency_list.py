import json
from python.geo.logistics import haversine
from pathlib import Path

# Constants
FOB_LAT, FOB_LON = 41.4822, -81.7995  # Lakewood, OH
RADIUS_MILES = 100
INPUT_FILE = Path("../../geo/db/44.json")
OUTPUT_FILE = Path("../../route/db/44107.json")

# Load ZIP code data
with INPUT_FILE.open("r") as f:
    zip_data = json.load(f)

# Filter ZIP codes within the desired radius
nearby_zips = []
for z in zip_data:
    if "lat" in z and "lon" in z:
        dist = haversine(FOB_LAT, FOB_LON, z["lat"], z["lon"])
        if dist <= RADIUS_MILES:
            z["distance"] = round(dist, 2)
            nearby_zips.append(z)

# Write filtered data to output file
with OUTPUT_FILE.open("w") as f:
    json.dump(nearby_zips, f, indent=2)

print(f"✅ Saved {len(nearby_zips)} ZIP codes within {RADIUS_MILES}mi of 44107 to {OUTPUT_FILE}")