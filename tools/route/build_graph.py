import json
from pathlib import Path
from tools.geo.logistics import haversine

# File paths
INPUT_FILE = Path("../../route/db/44107.json")
OUTPUT_FILE = Path("../../route/db/graph.json")

# Load node list
with INPUT_FILE.open("r") as f:
    nodes = json.load(f)

# Build adjacency graph within LOCAL_HOP_RADIUS
LOCAL_HOP_RADIUS = 25
adj_graph = {}

for i, zip_a in enumerate(nodes):
    a_code = zip_a["zipcode"]
    a_lat, a_lon = zip_a["lat"], zip_a["lon"]
    adj_graph[a_code] = {}

    for j, zip_b in enumerate(nodes):
        if i == j:
            continue
        b_code = zip_b["zipcode"]
        b_lat, b_lon = zip_b["lat"], zip_b["lon"]
        dist = haversine(a_lat, a_lon, b_lat, b_lon)
        if dist <= LOCAL_HOP_RADIUS:
            adj_graph[a_code][b_code] = round(dist, 2)

# Write adjacency graph
with OUTPUT_FILE.open("w") as f:
    json.dump(adj_graph, f, indent=2)

print(f"✅ Adjacency graph saved with {len(adj_graph)} nodes to {OUTPUT_FILE}")