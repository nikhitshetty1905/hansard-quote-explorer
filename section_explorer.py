# section_explorer.py
# Examine the top_level_sections structure

import requests, json

BASE = "https://api.parliament.uk/historic-hansard"
day_url = f"{BASE}/sittings/1905/may/12.js"

def fetch_json(url):
    r = requests.get(url, timeout=40, headers={"User-Agent":"HansardResearch/1.0"})
    r.raise_for_status()
    return r.json()

sitting = fetch_json(day_url)
commons = sitting[0]['house_of_commons_sitting']
sections = commons['top_level_sections']

print(f"=== TOP LEVEL SECTIONS ({len(sections)}) ===")

for i, section in enumerate(sections[:3]):  # Just first 3 for examination
    print(f"\nSECTION {i+1}:")
    print(f"  Keys: {list(section.keys())}")
    
    if 'section' in section:
        sec_data = section['section']
        print(f"  Section keys: {list(sec_data.keys())}")
        
        if 'title' in sec_data:
            print(f"  Title: {sec_data.get('title', 'No title')}")
        
        if 'href' in sec_data:
            print(f"  Href: {sec_data.get('href', 'No href')}")
        
        # Look for children or content
        if 'children' in sec_data:
            children = sec_data['children']
            print(f"  Children: {len(children)}")
            
            if len(children) > 0:
                first_child = children[0]
                print(f"  First child keys: {list(first_child.keys())}")
                
                # Look for text/body
                if 'text' in first_child:
                    text = first_child['text']
                    print(f"  First child text ({len(text)} chars): {text[:200]}...")
                if 'body' in first_child:
                    body = first_child['body']
                    print(f"  First child body ({len(body)} chars): {body[:200]}...")

# Also check if we need to fetch individual sections
print(f"\n=== CHECKING FOR HREF PATTERNS ===")
for i, section in enumerate(sections[:5]):
    if 'section' in section:
        sec_data = section['section']
        if 'href' in sec_data:
            href = sec_data['href']
            title = sec_data.get('title', 'No title')
            print(f"Section {i+1}: {title} -> {href}")
            
            # Check if this looks like aliens/immigration related
            if any(term in title.lower() for term in ['alien', 'immigration', 'foreign']):
                print(f"  *** POTENTIALLY RELEVANT SECTION ***")