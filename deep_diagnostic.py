# deep_diagnostic.py
# Comprehensive diagnosis of why we're not finding matches

import requests, re, json
from datetime import date, timedelta

BASE = "https://api.parliament.uk/historic-hansard"
START = date(1905, 5, 12)  # Known Aliens Act date
END   = date(1905, 5, 12)

# Test patterns
MIG = r"(immigration|immigrant[s]?|migrant[s]?|alien[s]?|aliens|foreign(?:er|ers)?|guest\s*worker[s]?|colonial\s+(?:subjects|workers))"
LAB = r"(labour\s*market|labor\s*market|wage[s]?|pay|employment|unemployment|job[s]?|workforce|manpower|strike[s]?|trade\s*union[s]?)"
NEAR = 40

def fetch_json(url):
    r = requests.get(url, timeout=40, headers={"User-Agent":"HansardResearch/1.0"})
    r.raise_for_status()
    return r.json()

def words(text): 
    return re.findall(r"\w[\w'-]*", text.lower())

def proximity_hit(text):
    w = words(text)
    mi = [i for i,t in enumerate(w) if re.search(MIG, t)]
    lj = [i for i,t in enumerate(w) if re.search(LAB, t)]
    return any(abs(i-j) <= NEAR for i in mi for j in lj)

def iter_days(a, b):
    d = a
    while d <= b:
        yield d
        d += timedelta(days=1)

print("=== COMPREHENSIVE DIAGNOSTIC ===")
total_speeches = 0
migration_speeches = 0
labour_speeches = 0
combined_speeches = 0

for d in iter_days(START, END):
    print(f"\n=== {d.isoformat()} ===")
    mon = d.strftime("%b").lower()
    day_url = f"{BASE}/sittings/{d.year}/{mon}/{d.day}.js"
    
    try:
        sitting = fetch_json(day_url)
        print(f"Raw data type: {type(sitting)}")
        
        if isinstance(sitting, list):
            print(f"Found {len(sitting)} items")
            
            for item_idx, item in enumerate(sitting):
                print(f"\nITEM {item_idx}:")
                if 'house_of_commons_sitting' in item:
                    house_data = item['house_of_commons_sitting']
                    house_name = "commons"
                    print(f"  House: Commons")
                elif 'house_of_lords_sitting' in item:
                    house_data = item['house_of_lords_sitting']
                    house_name = "lords"
                    print(f"  House: Lords")
                else:
                    print(f"  Keys: {list(item.keys())}")
                    continue
                
                print(f"  Title: {house_data.get('title', 'No title')}")
                print(f"  Children: {len(house_data.get('children', []))}")
                
                # Process all speeches in this house
                stack = house_data.get('children', [])
                house_speech_count = 0
                
                while stack:
                    node = stack.pop()
                    if 'children' in node:
                        stack.extend(node.get("children", []))
                    
                    text = node.get("text") or node.get("body") or ""
                    speaker = (node.get("speaker") or {}).get("name", "")
                    
                    if text and speaker:
                        house_speech_count += 1
                        total_speeches += 1
                        
                        # Test individual patterns
                        has_migration = bool(re.search(MIG, text.lower()))
                        has_labour = bool(re.search(LAB, text.lower()))
                        has_proximity = proximity_hit(text)
                        
                        if has_migration:
                            migration_speeches += 1
                        if has_labour:
                            labour_speeches += 1
                        if has_migration and has_labour and has_proximity:
                            combined_speeches += 1
                            
                        # Show first few speeches for debugging
                        if house_speech_count <= 3:
                            print(f"\n    SPEECH {house_speech_count} by {speaker}:")
                            print(f"      Length: {len(text)} chars")
                            print(f"      Migration terms: {has_migration}")
                            print(f"      Labour terms: {has_labour}")
                            print(f"      Proximity match: {has_proximity}")
                            print(f"      First 150 chars: {text[:150]}")
                            
                            # Show specific term matches
                            if has_migration:
                                migration_matches = re.findall(MIG, text.lower())
                                print(f"      Migration matches: {migration_matches}")
                            if has_labour:
                                labour_matches = re.findall(LAB, text.lower())
                                print(f"      Labour matches: {labour_matches}")
                
                print(f"  Total speeches in {house_name}: {house_speech_count}")
    
    except Exception as e:
        print(f"Error: {e}")

print(f"\n=== SUMMARY ===")
print(f"Total speeches processed: {total_speeches}")
print(f"Speeches with migration terms: {migration_speeches}")
print(f"Speeches with labour terms: {labour_speeches}")
print(f"Speeches with both (proximity): {combined_speeches}")

print(f"\n=== PATTERN TESTS ===")
test_texts = [
    "These aliens are taking jobs from British workers",
    "Immigration of foreign labour depresses wages", 
    "The alien question affects employment in our factories",
    "Foreign workers create unemployment problems"
]

for i, text in enumerate(test_texts):
    print(f"Test {i+1}: '{text}'")
    print(f"  Migration: {bool(re.search(MIG, text.lower()))}")
    print(f"  Labour: {bool(re.search(LAB, text.lower()))}")
    print(f"  Proximity: {proximity_hit(text)}")
    print()