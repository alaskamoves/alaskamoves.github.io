import geopandas as gpd
import json
from collections import defaultdict
from pathlib import Path

# Input and output paths
INPUT = Path("../../assets/geo/tiger_zcta_2024/tl_2024_us_zcta520.shp")
OUTPUT_DIR = Path("../../geo/db")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load shapefile using GeoPandas
gdf = gpd.read_file(INPUT)

# Rename the ZIP code field
gdf = gdf.rename(columns={"ZCTA5CE20": "zipcode"})
gdf["zipcode"] = gdf["zipcode"].astype(str)

# Reproject to EPSG:5070 for U.S.-wide consistency
gdf = gdf.to_crs(epsg=5070)

# Compute geographic centroids for frontend mapping (lat/lon in degrees)
gdf["lat"] = gdf.centroid.to_crs(epsg=4326).y.round(6)
gdf["lon"] = gdf.centroid.to_crs(epsg=4326).x.round(6)

# Compute internal points (projected meters) for backend routing logic
gdf["lat_p"] = gdf.geometry.representative_point().y.round(6)
gdf["lon_p"] = gdf.geometry.representative_point().x.round(6)

# Assign default gas price
gdf["gas_price"] = 3.19

# Group ZIPs by prefix and export
records_by_prefix = defaultdict(list)

for _, row in gdf.iterrows():
    zcta = row["zipcode"]
    if not zcta.isdigit() or len(zcta) != 5:
        continue

    prefix = zcta[:2]
    entry = {
        "zipcode": zcta,
        "lat": row["lat"],
        "lon": row["lon"],
        "lat_p": row["lat_p"],
        "lon_p": row["lon_p"],
        "gas_price": row["gas_price"]
    }

    records_by_prefix[prefix].append(entry)

# Write JSON for each prefix
for prefix, entries in records_by_prefix.items():
    out_path = OUTPUT_DIR / f"{prefix}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)