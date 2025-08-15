# structure_explorer.py
# Deep dive into the actual API structure

import requests, json

BASE = "https://api.parliament.uk/historic-hansard"
day_url = f"{BASE}/sittings/1905/may/12.js"

def fetch_json(url):
    r = requests.get(url, timeout=40, headers={"User-Agent":"HansardResearch/1.0"})
    r.raise_for_status()
    return r.json()

def explore_structure(obj, path="", max_depth=3, current_depth=0):
    if current_depth > max_depth:
        return
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            new_path = f"{path}.{key}" if path else key
            print(f"{'  ' * current_depth}{key}: {type(value)}")
            
            if isinstance(value, str) and len(value) > 100:
                print(f"{'  ' * (current_depth + 1)}[TEXT: {len(value)} chars] {value[:100]}...")
            elif isinstance(value, (list, dict)) and key != 'children':
                if isinstance(value, list) and len(value) > 0:
                    print(f"{'  ' * (current_depth + 1)}[{len(value)} items]")
                    if len(value) > 0:
                        explore_structure(value[0], new_path + "[0]", max_depth, current_depth + 1)
                elif isinstance(value, dict):
                    explore_structure(value, new_path, max_depth, current_depth + 1)
            elif key == 'children' and isinstance(value, list):
                print(f"{'  ' * (current_depth + 1)}[CHILDREN: {len(value)} items]")
                if len(value) > 0:
                    explore_structure(value[0], new_path + "[0]", max_depth, current_depth + 1)
    
    elif isinstance(obj, list):
        print(f"{'  ' * current_depth}[LIST: {len(obj)} items]")
        if len(obj) > 0:
            explore_structure(obj[0], path + "[0]", max_depth, current_depth + 1)

print("=== FULL STRUCTURE EXPLORATION ===")
sitting = fetch_json(day_url)
explore_structure(sitting)

# Also check if there are any direct URLs we should be following
print("\n=== LOOKING FOR URLs ===")
if isinstance(sitting, list):
    for i, item in enumerate(sitting):
        print(f"Item {i}:")
        if 'house_of_commons_sitting' in item:
            commons = item['house_of_commons_sitting']
            print(f"  Commons keys: {list(commons.keys())}")
            # Look for URL-like fields
            for key, value in commons.items():
                if isinstance(value, str) and ('/' in value or 'http' in value):
                    print(f"    {key}: {value}")
        if 'house_of_lords_sitting' in item:
            lords = item['house_of_lords_sitting']
            print(f"  Lords keys: {list(lords.keys())}")
            for key, value in lords.items():
                if isinstance(value, str) and ('/' in value or 'http' in value):
                    print(f"    {key}: {value}")