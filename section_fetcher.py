# section_fetcher.py
# Try to fetch individual section content

import requests, json, re

BASE = "https://api.parliament.uk/historic-hansard"
day_url = f"{BASE}/sittings/1905/may/12.js"

def fetch_json(url):
    r = requests.get(url, timeout=40, headers={"User-Agent":"HansardResearch/1.0"})
    r.raise_for_status()
    return r.json()

sitting = fetch_json(day_url)
commons = sitting[0]['house_of_commons_sitting']
sections = commons['top_level_sections']

print(f"=== TRYING TO FETCH SECTION CONTENT ===")

# Try different URL patterns for sections
for i, section in enumerate(sections[:3]):  # Test first 3 sections
    if 'section' in section:
        sec_data = section['section']
        section_id = sec_data.get('id')
        slug = sec_data.get('slug')
        title = sec_data.get('title', 'No title')
        
        print(f"\nSECTION {i+1}: {title}")
        print(f"  ID: {section_id}, Slug: {slug}")
        
        # Try different URL patterns
        possible_urls = [
            f"{BASE}/sections/{section_id}.js",
            f"{BASE}/commons/1905/may/12/{slug}.js",  
            f"{BASE}/sittings/1905/may/12/{slug}.js",
            f"{BASE}/1905/may/12/{slug}.js"
        ]
        
        for url in possible_urls:
            try:
                print(f"  Trying: {url}")
                content = fetch_json(url)
                print(f"    SUCCESS! Content type: {type(content)}")
                
                # Look for speech content
                if isinstance(content, dict):
                    if 'children' in content:
                        print(f"    Has {len(content['children'])} children")
                        # Check first child for text
                        if content['children']:
                            child = content['children'][0]
                            if 'text' in child:
                                text = child['text']
                                print(f"    First text ({len(text)} chars): {text[:150]}...")
                                # Quick test for our terms
                                if re.search(r"alien|foreign|immigration", text.lower()):
                                    print(f"    *** CONTAINS IMMIGRATION TERMS ***")
                                if re.search(r"labour|labor|employment|wage|job", text.lower()):
                                    print(f"    *** CONTAINS LABOUR TERMS ***")
                    
                    # Show structure
                    print(f"    Keys: {list(content.keys())[:10]}")
                break
                    
            except Exception as e:
                print(f"    Failed: {str(e)[:100]}...")
                continue

# Also check the original approach - maybe the sitting JSON itself contains hrefs
print(f"\n=== CHECKING ORIGINAL ITEMS APPROACH ===")
if 'items' in commons:
    items = commons['items']
    print(f"Found 'items' field with {len(items)} items")
else:
    print("No 'items' field found in commons sitting")