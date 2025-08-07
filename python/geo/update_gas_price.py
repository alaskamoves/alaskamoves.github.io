import json
from pathlib import Path

DB_DIR = Path("../../geo/db")
ZIP_FIELD = "zipcode"

def _load(zipcode):
    path = DB_DIR / f"{zipcode[:2]}.json"
    with path.open("r", encoding="utf-8") as f:
        return json.load(f), path

def _save(data, path):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def _update(zipcode, key, value):
    data, path = _load(zipcode)
    updated = False
    for row in data:
        if row.get(ZIP_FIELD) == zipcode:
            row[key] = value
            updated = True
            break
    if not updated:
        raise ValueError(f"{zipcode} not found.")
    _save(data, path)
    print(f"✅ {zipcode}: {key} = {value}")

# Public functions
def set_gas_price(zipcode, value: float):
    _update(zipcode, "gas_price", float(value))


# Make edits here.
zip_to_edit = "44070"
avg_gas_price = 2.99
set_gas_price(zip_to_edit, avg_gas_price)