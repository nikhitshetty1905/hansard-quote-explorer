# structure_debug.py
# Debug the actual API response structure

import requests, json
from datetime import date

BASE = "https://api.parliament.uk/historic-hansard"
d = date(1905, 5, 12)
mon = d.strftime("%b").lower()
day_url = f"{BASE}/sittings/{d.year}/{mon}/{d.day}.js"

def fetch_json(url):
    r = requests.get(url, timeout=40, headers={"User-Agent":"HansardResearch/1.0"})
    r.raise_for_status()
    return r.json()

print(f"Fetching: {day_url}")
sitting = fetch_json(day_url)

print(f"Type: {type(sitting)}")
print(f"Keys (if dict): {sitting.keys() if isinstance(sitting, dict) else 'Not a dict'}")

if isinstance(sitting, list):
    print(f"List length: {len(sitting)}")
    for i, item in enumerate(sitting):
        print(f"\nItem {i}:")
        print(f"  Type: {type(item)}")
        if isinstance(item, dict):
            print(f"  Keys: {list(item.keys())}")
            # Print first few key-value pairs
            for k, v in list(item.items())[:5]:
                print(f"  {k}: {str(v)[:100]}...")
elif isinstance(sitting, dict):
    print(f"Dict keys: {list(sitting.keys())}")
    for k, v in list(sitting.items())[:5]:
        print(f"{k}: {str(v)[:100]}...")