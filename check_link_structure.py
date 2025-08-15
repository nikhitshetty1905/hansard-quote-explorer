# check_link_structure.py
# Check how section links are actually structured in the HTML

import requests
from bs4 import BeautifulSoup

BASE = "https://api.parliament.uk/historic-hansard"

def fetch_html(url):
    r = requests.get(url, timeout=30, headers={"User-Agent":"HansardResearch/1.0"})
    r.raise_for_status()
    return r.text

# Get the sitting page for May 2, 1905
sitting_url = f"{BASE}/commons/1905/may/2"
print(f"=== ANALYZING LINK STRUCTURE ===")
print(f"URL: {sitting_url}")

html_content = fetch_html(sitting_url)

# Look for the specific "Immigration of Aliens" text and see how it's linked
soup = BeautifulSoup(html_content, 'html.parser')

print(f"\n=== RAW HTML SEARCH ===")
# Look for the immigration text in the raw HTML to see the structure
immigration_pos = html_content.lower().find('immigration of aliens')
if immigration_pos >= 0:
    start = max(0, immigration_pos - 200)
    end = min(len(html_content), immigration_pos + 400)
    context = html_content[start:end]
    print(f"Raw HTML context:")
    print(context)

print(f"\n=== LOOKING FOR ALL <A> TAGS ===")
# Find all <a> tags and see if any contain section links
all_links = soup.find_all('a')
print(f"Found {len(all_links)} <a> tags")

for i, link in enumerate(all_links):
    href = link.get('href', '')
    text = link.get_text(strip=True)
    
    if 'alien' in text.lower() or 'alien' in href.lower():
        print(f"  Link {i+1}: href='{href}' text='{text}'")

print(f"\n=== EXAMINING LI STRUCTURE ===")
# Look at the list items that contain section information
ol = soup.find('ol', class_='xoxo')
if ol:
    li_elements = ol.find_all('li', class_='section-line')
    print(f"Found {len(li_elements)} section lines")
    
    for i, li in enumerate(li_elements):
        li_text = li.get_text().lower()
        if 'alien' in li_text:
            print(f"\nSection {i+1} contains 'alien':")
            print(f"  Text: {li.get_text().strip()}")
            print(f"  HTML: {str(li)[:200]}...")
            
            # Look for any links within this li
            links_in_li = li.find_all('a')
            for j, link in enumerate(links_in_li):
                href = link.get('href', '')
                link_text = link.get_text(strip=True)
                print(f"    Link {j+1}: href='{href}' text='{link_text}'")

print(f"\n=== MANUAL URL CONSTRUCTION TEST ===")
# Try to construct URLs manually based on patterns
section_title = "Immigration of Aliens"
# Convert to URL format: lowercase, replace spaces with hyphens, remove punctuation
url_part = section_title.lower().replace(' ', '-').replace('.', '').replace(',', '')
test_url = f"{BASE}/commons/1905/may/2/{url_part}"

print(f"Testing constructed URL: {test_url}")
try:
    test_html = fetch_html(test_url)
    print(f"SUCCESS: Fetched {len(test_html)} chars")
    
    # Quick check for content
    if 'alien' in test_html.lower():
        print("  Contains 'alien' - looks correct!")
    
    # Check for labour terms
    labour_terms = ['labour', 'labor', 'employment', 'job', 'wage', 'work']
    labour_found = [term for term in labour_terms if term in test_html.lower()]
    if labour_found:
        print(f"  Contains labour terms: {labour_found}")
    else:
        print("  No labour terms found")
        
except Exception as e:
    print(f"FAILED: {e}")

# Try other URL patterns
other_patterns = [
    f"{BASE}/commons/1905/may/2/immigration-of-aliens",
    f"{BASE}/commons/1905/may/02/immigration-of-aliens",
]

for pattern in other_patterns:
    print(f"\nTesting: {pattern}")
    try:
        test_html = fetch_html(pattern)
        print(f"SUCCESS: Fetched {len(test_html)} chars")
        break
    except Exception as e:
        print(f"FAILED: {e}")