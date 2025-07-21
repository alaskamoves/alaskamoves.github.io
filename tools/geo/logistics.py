# logistics.py
# ─────────────────────────────────────────────────────────────────────────────
# This is the sovereign core of Alaska Transportation & Trucking's routing logic.
# If you’ve ever asked, “Should I go hard or go home?” — this file answers.
#
# It reads ZIP metadata from geo/db/, makes judgment calls, and talks like a
# seasoned courier after 300 miles of coffee and low fuel warnings.
#
# This module does NOT concern itself with pretty interfaces, only brutal truths.
# ─────────────────────────────────────────────────────────────────────────────
import math
from pathlib import Path
import json
from math import radians, sin, cos, sqrt, atan2

# ─── Global Operational Constants ─────────────────────────────────────────────
FOB_ZIP = "44107"         # Your Forward Operating Base. Your garage. Your home.
MAX_HOURS = 12            # DOT says go home. Your spine agrees.
MAX_MILES = 300           # Approximate range on a full tank.
MPG = 20                  # You drive like you mean it, but not like you're broke.
AVG_SPEED = 25            # mph under working conditions
FUEL_RATE = 3.19          # Default gas price until better intel rolls in.
LOAD_MULTIPLIER = 1.0     # Starts at 1.0 (small package). Bigger loads? Bump it.
DB_DIR = Path("../../geo/db")  # The vault of regional ZIP knowledge.
EARTH_RADIUS_MI = 3958.8  # Radius of Earth in miles

# ─── Derived Metrics ──────────────────────────────────────────────────────────
DAILY_GALLONS = MAX_MILES / MPG                      # ≈ 12 gallons on a 300mi day
MAX_GAS_COST = round(DAILY_GALLONS * FUEL_RATE, 2)   # ≈ $29.88 default budget

# Revenue benchmarks
REVENUE_GOAL = 200.00                                # Target take-home for the day
MIN_MARGIN_PER_GIG = 5.00                            # Don't lift for less

# ─── ZIP Code Utilities ───────────────────────────────────────────────────────
def load_zip(zipcode):
    """
    Load a ZIP code's metadata. Looks it up based on prefix, cracks open the JSON,
    and returns its entry like a CIA agent flipping through dossiers.
    """
    path = DB_DIR / f"{zipcode[:2]}.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for entry in data:
        if entry.get("zipcode") == zipcode:
            return entry
    raise ValueError(f"ZIP {zipcode} not found in {path}")

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculates the crow-flies distance between two GPS coordinates.
    Earth is round, math is magic, mileage is money.
    """
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return 2 * EARTH_RADIUS_MI * atan2(sqrt(a), sqrt(1 - a))

def lookup_distance(zip1, zip2):
    """
    Returns the distance (in miles) between two ZIPs.
    Assumes ZIPs have valid lat/lon fields. No tolls. No traffic. Just vibes.
    """
    z1 = load_zip(zip1)
    z2 = load_zip(zip2)
    return round(haversine(z1["lat"], z1["lon"], z2["lat"], z2["lon"]), 2)

# ─── Core Evaluation Logic ────────────────────────────────────────────────────
def estimate_cost(zip1, zip2, fuel_rate=FUEL_RATE, mpg=MPG, load_multiplier=LOAD_MULTIPLIER):
    """
    Calculate fuel cost for a single-leg trip from zip1 to zip2.
    Assumes you're not flooring it, but also not hypermiling like a coward.
    """
    miles = lookup_distance(zip1, zip2)
    gallons = miles / mpg
    labour = MIN_MARGIN_PER_GIG * estimate_hours(miles)
    return round(((gallons * fuel_rate + labour) * load_multiplier), 2)

def estimate_hours(miles: float, mph: int = AVG_SPEED) -> int:
    """
    Estimate driving time in whole hours, conservatively.
    Rounds up to ensure slack for traffic and gig handling.
    """
    return math.ceil(miles / mph)

def is_viable_route(zip1, zip2, payout, threshold=1.5):
    """
    Determines if the job is worth the squeeze.
    If payout beats cost * threshold, it's a go.
    Threshold exists because you deserve margin, not martyrdom.
    """
    cost = estimate_cost(zip1, zip2)
    return payout >= cost * threshold

def from_fob(zip_dest, **kwargs):
    """
    Shortcut to estimate cost from FOB (44107) to a given ZIP.
    Because that's where your day starts — and sometimes ends.
    """
    return estimate_cost(FOB_ZIP, zip_dest, **kwargs)

# ─── Multi-leg Route Evaluation ──────────────────────────────────────────────
def assess_mission(fob, pickup, dropoff, payout, expected_return=0.0):
    """
    Evaluates a full loop: FOB → Pickup → Dropoff → FOB.
    Returns net gain and a boolean: Was it worth it?

    Used to decide whether to stack a gig or nap in your rig.
    """
    cost = (
        estimate_cost(fob, pickup) +
        estimate_cost(pickup, dropoff) +
        estimate_cost(dropoff, fob)
    )
    net = payout + expected_return - cost
    return round(net, 2), net > 0

# ─── Operational Heuristics ───────────────────────────────────────────────────
def miles_remaining(miles_today):
    """
    Returns miles you can still burn before DOT or your engine calls it quits.
    """
    return MAX_MILES - miles_today

def is_within_radius(zip_dest, max_radius=150):
    """
    Soft ceiling for how far you're willing to stretch from FOB.
    Beyond this, better be a pallet job or a miracle.
    """
    return lookup_distance(FOB_ZIP, zip_dest) <= max_radius

def can_return_to_fob(zip_current, time_left_hr, avg_speed=25):
    """
    Can you still make it home? Don’t guess — use this.
    Good for making sure your last gig doesn’t turn into your next lease.
    """
    miles = lookup_distance(zip_current, FOB_ZIP)
    return (miles / avg_speed) <= time_left_hr

# ─────────────────────────────────────────────────────────────────────────────
# End of logistics.py
# When you read this file, you’re reading the playbook.
# Keep it sharp. Keep it honest. Keep it sovereign.
# ─────────────────────────────────────────────────────────────────────────────