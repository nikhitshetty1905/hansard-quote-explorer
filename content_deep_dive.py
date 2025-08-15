# content_deep_dive.py
# Deep exploration of section content structure

import requests, json, re

BASE = "https://api.parliament.uk/historic-hansard"

def fetch_json(url):
    r = requests.get(url, timeout=40, headers={"User-Agent":"HansardResearch/1.0"})
    r.raise_for_status()
    return r.json()

def explore_all_fields(obj, path="", max_depth=4, current_depth=0):
    """Recursively explore all fields looking for text content"""
    if current_depth > max_depth:
        return []
    
    found_texts = []
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            new_path = f"{path}.{key}" if path else key
            
            # Look for text-like fields
            if isinstance(value, str) and len(value) > 50 and any(word in value.lower() for word in ['the', 'and', 'of', 'to', 'in']):
                # This looks like speech text
                found_texts.append({
                    'path': new_path,
                    'length': len(value),
                    'text': value[:200] + "..." if len(value) > 200 else value,
                    'has_migration': bool(re.search(r'alien|immigration|immigrant|foreign|migrant', value.lower())),
                    'has_labour': bool(re.search(r'labour|labor|employment|wage|job|work|strike|trade.*union', value.lower()))
                })
            
            elif isinstance(value, (dict, list)):
                found_texts.extend(explore_all_fields(value, new_path, max_depth, current_depth + 1))
    
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            new_path = f"{path}[{i}]"
            found_texts.extend(explore_all_fields(item, new_path, max_depth, current_depth + 1))
    
    return found_texts

print("=== DEEP CONTENT EXPLORATION ===")

# Get the sitting data
sitting = fetch_json(f"{BASE}/sittings/1905/may/12.js")
commons = sitting[0]['house_of_commons_sitting']

# Look for ALL text content in the entire structure
print("Searching for text content in the entire sitting data...")
all_texts = explore_all_fields(commons)

print(f"\nFound {len(all_texts)} text fields")

migration_texts = [t for t in all_texts if t['has_migration']]
labour_texts = [t for t in all_texts if t['has_labour']]
both_texts = [t for t in all_texts if t['has_migration'] and t['has_labour']]

print(f"Texts with migration terms: {len(migration_texts)}")
print(f"Texts with labour terms: {len(labour_texts)}")
print(f"Texts with both: {len(both_texts)}")

# Show samples
if migration_texts:
    print("\n=== MIGRATION TEXTS ===")
    for i, text in enumerate(migration_texts[:3]):
        print(f"{i+1}. Path: {text['path']}")
        print(f"   Length: {text['length']} chars")
        print(f"   Content: {text['text']}")
        print()

if labour_texts:
    print("\n=== LABOUR TEXTS ===")
    for i, text in enumerate(labour_texts[:3]):
        print(f"{i+1}. Path: {text['path']}")
        print(f"   Length: {text['length']} chars") 
        print(f"   Content: {text['text']}")
        print()

if both_texts:
    print("\n=== TEXTS WITH BOTH TERMS ===")
    for i, text in enumerate(both_texts):
        print(f"{i+1}. Path: {text['path']}")
        print(f"   Length: {text['length']} chars")
        print(f"   Content: {text['text']}")
        print()
        
# Also sample some general texts to see what kind of content exists
if all_texts:
    print("\n=== SAMPLE GENERAL TEXTS ===")
    for i, text in enumerate(all_texts[:5]):
        print(f"{i+1}. Path: {text['path']}")
        print(f"   Length: {text['length']} chars")
        print(f"   Content: {text['text']}")
        print()