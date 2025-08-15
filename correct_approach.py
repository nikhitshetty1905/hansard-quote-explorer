# correct_approach.py
# Try to find the correct way to get actual speech content

import requests, json

BASE = "https://api.parliament.uk/historic-hansard"

def fetch_json(url):
    r = requests.get(url, timeout=40, headers={"User-Agent":"HansardResearch/1.0"})
    r.raise_for_status()
    return r.json()

print("=== FINDING THE CORRECT API APPROACH ===")

# The original collector expected items with href - let me try different date formats and years
# Maybe 1905 isn't fully digitized, or we need a different approach

test_dates = [
    ("1920", "jan", "15"),  # Try a later date
    ("1910", "feb", "10"),  # Try 1910
    ("1895", "mar", "05"),  # Try earlier
]

for year, month, day in test_dates:
    print(f"\n=== Testing {year}-{month}-{day} ===")
    
    # Try the sitting format
    sitting_url = f"{BASE}/sittings/{year}/{month}/{day}.js"
    try:
        sitting = fetch_json(sitting_url)
        print(f"Sitting data exists: {len(sitting)} items")
        
        # Check if this date has items with href
        for item in sitting:
            if 'house_of_commons_sitting' in item:
                commons = item['house_of_commons_sitting']
                print(f"Commons keys: {list(commons.keys())}")
                
                # Check if this has items or different structure
                if 'items' in commons:
                    items = commons['items']
                    print(f"  Found items field with {len(items)} items!")
                    if items:
                        first_item = items[0]
                        print(f"  First item keys: {list(first_item.keys())}")
                        if 'href' in first_item:
                            print(f"  First href: {first_item['href']}")
                            # Try to fetch this content
                            content_url = f"{BASE}{first_item['href']}.js"
                            try:
                                content = fetch_json(content_url)
                                print(f"  Content fetch SUCCESS! Keys: {list(content.keys())}")
                                if 'children' in content and content['children']:
                                    child = content['children'][0]
                                    if 'text' in child:
                                        text = child['text']
                                        print(f"  Found speech text! Length: {len(text)}")
                                        print(f"  Sample: {text[:200]}...")
                                        break
                            except Exception as e:
                                print(f"  Content fetch failed: {e}")
                        break
                break
        break  # If we found success, stop testing other dates
                
    except Exception as e:
        print(f"Failed: {str(e)[:60]}...")

print("\n=== ALTERNATIVE APPROACH: WEB SCRAPING ===")
# If the API doesn't have the full content, maybe we need to scrape the HTML version
html_url = "https://api.parliament.uk/historic-hansard/commons/1905/may/12"  # Without .js
print(f"HTML version might be at: {html_url}")

try:
    import requests
    response = requests.get(html_url, headers={"User-Agent":"HansardResearch/1.0"})
    print(f"HTML response status: {response.status_code}")
    if response.status_code == 200:
        content = response.text
        print(f"HTML content length: {len(content)}")
        # Look for aliens/immigration terms
        content_lower = content.lower()
        if 'alien' in content_lower or 'immigration' in content_lower:
            print("HTML version contains immigration-related terms!")
        if 'labour' in content_lower or 'employment' in content_lower:
            print("HTML version contains labour-related terms!")
except Exception as e:
    print(f"HTML fetch failed: {e}")