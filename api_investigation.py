# api_investigation.py
# Try to understand the correct API usage

import requests, json, re

BASE = "https://api.parliament.uk/historic-hansard"

def fetch_json(url):
    r = requests.get(url, timeout=40, headers={"User-Agent":"HansardResearch/1.0"})
    r.raise_for_status()
    return r.json()

print("=== TESTING DIFFERENT API APPROACHES ===")

# 1. Try the original format that the collector expected
print("\n1. Testing original expected format:")
try:
    # The original collector expected /commons/1905/may/12/aliens-bill format
    # Let's see what URLs are available by testing known historical events
    test_urls = [
        f"{BASE}/commons/1905/may/12.js",  # Just the date
        f"{BASE}/lords/1905/may/12.js",    # Lords for the same date
        f"{BASE}/commons/1905.js",         # Whole year
        f"{BASE}/commons/1905/may.js",     # Whole month
    ]
    
    for url in test_urls:
        try:
            print(f"  Trying: {url}")
            result = fetch_json(url)
            print(f"    SUCCESS! Type: {type(result)}")
            if isinstance(result, dict):
                print(f"    Keys: {list(result.keys())[:10]}")
                if 'items' in result:
                    items = result['items']
                    print(f"    Items: {len(items)}")
                    if items:
                        first_item = items[0]
                        print(f"    First item keys: {list(first_item.keys())}")
                        if 'href' in first_item:
                            print(f"    First href: {first_item['href']}")
            elif isinstance(result, list):
                print(f"    List length: {len(result)}")
                if result:
                    print(f"    First item keys: {list(result[0].keys())}")
        except Exception as e:
            print(f"    Failed: {str(e)[:80]}...")
            
except Exception as e:
    print(f"Error in section 1: {e}")

# 2. Check if there are actual debate URLs we can construct
print("\n2. Looking for debate-specific content:")
sitting = fetch_json(f"{BASE}/sittings/1905/may/12.js")
commons = sitting[0]['house_of_commons_sitting']
sections = commons['top_level_sections']

# Look for sections that might contain aliens/immigration debates
immigration_sections = []
for section in sections:
    if 'section' in section:
        sec_data = section['section']
        title = sec_data.get('title', '').lower()
        if any(term in title for term in ['alien', 'immigration', 'foreign', 'bill']):
            immigration_sections.append(section)
            print(f"  Found relevant section: {sec_data.get('title')}")
            print(f"    ID: {sec_data.get('id')}, Slug: {sec_data.get('slug')}")

if not immigration_sections:
    print("  No immigration-related sections found by title")
    print("  Sample section titles:")
    for i, section in enumerate(sections[:10]):
        if 'section' in section:
            title = section['section'].get('title', 'No title')
            print(f"    {i+1}. {title}")

# 3. Try a known historical URL format
print("\n3. Testing known historical format:")
# The Aliens Act 1905 was debated - let's try some known URL patterns
known_patterns = [
    f"{BASE}/commons/1905/may/aliens-bill.js",
    f"{BASE}/commons/1905/aliens-act.js", 
    f"{BASE}/1905/aliens-bill.js"
]

for url in known_patterns:
    try:
        print(f"  Trying: {url}")
        result = fetch_json(url)
        print(f"    SUCCESS!")
        break
    except Exception as e:
        print(f"    Failed: {str(e)[:60]}...")