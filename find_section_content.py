# find_section_content.py
# Try to find where the actual section content is stored

import requests
from bs4 import BeautifulSoup
import re

BASE = "https://api.parliament.uk/historic-hansard"

def fetch_html(url):
    r = requests.get(url, timeout=40, headers={"User-Agent":"HansardResearch/1.0"})
    r.raise_for_status()
    return r.text

# Test on May 12, 1905 - we know this has aliens content from our original test
html_url = f"{BASE}/commons/1905/may/12"
print(f"=== ANALYZING CONTENT STRUCTURE ===")
print(f"URL: {html_url}")

html_content = fetch_html(html_url)
soup = BeautifulSoup(html_content, 'html.parser')

# Look at the full text to see if aliens/immigration content exists
full_text = soup.get_text()
print(f"Total page length: {len(full_text)} characters")

# Search for our terms in the full content
mig_matches = re.findall(r"alien[s]?|immigration|immigrant[s]?", full_text.lower())
lab_matches = re.findall(r"labour|labor|employment|wage[s]?|job[s]?", full_text.lower())

print(f"Migration terms found: {len(mig_matches)} - {set(mig_matches)}")
print(f"Labour terms found: {len(lab_matches)} - {set(lab_matches[:10])}")

if mig_matches:
    print(f"\n=== LOOKING FOR ALIENS CONTENT ===")
    # Find where "alien" appears in the content
    for match in re.finditer(r"alien[s]?", full_text.lower()):
        start = max(0, match.start() - 100)
        end = min(len(full_text), match.end() + 100)
        context = full_text[start:end]
        try:
            clean_context = context.encode('ascii', 'replace').decode('ascii')
            print(f"Context: ...{clean_context}...")
            print()
        except:
            print("Context: [encoding issues]")

print(f"\n=== EXAMINING ORDERED LIST STRUCTURE ===")

# Look at the ordered list more carefully
ol_element = soup.find('ol', class_='xoxo')
if ol_element:
    print("Found ordered list")
    li_elements = ol_element.find_all('li', recursive=False)  # Direct children only
    print(f"Direct li children: {len(li_elements)}")
    
    for i, li in enumerate(li_elements[:5]):  # First 5
        print(f"\nLI {i+1}:")
        print(f"  Attributes: {dict(li.attrs)}")
        
        # Get text length
        li_text = li.get_text()
        print(f"  Text length: {len(li_text)} chars")
        
        # Look for spans within this li
        spans = li.find_all('span')
        print(f"  Contains {len(spans)} spans")
        
        # Show span classes
        span_classes = []
        for span in spans:
            classes = span.get('class', [])
            span_classes.extend(classes)
        unique_classes = list(set(span_classes))
        print(f"  Span classes: {unique_classes}")
        
        # If this li contains alien content, show more detail
        if 'alien' in li_text.lower():
            print(f"  *** CONTAINS ALIENS CONTENT ***")
            # Show structure
            direct_children = list(li.children)
            print(f"  Direct children: {len(direct_children)}")
            for j, child in enumerate(direct_children[:3]):
                if hasattr(child, 'name'):
                    print(f"    Child {j+1}: {child.name} - {dict(child.attrs) if hasattr(child, 'attrs') else {}}")
                else:
                    child_text = str(child).strip()
                    if child_text and len(child_text) > 10:
                        try:
                            clean_text = child_text[:50].encode('ascii', 'replace').decode('ascii')
                            print(f"    Text child {j+1}: {clean_text}...")
                        except:
                            print(f"    Text child {j+1}: [encoding issues]")

print(f"\n=== CHECKING FOR INDIVIDUAL SECTION URLs ===")

# Maybe sections have individual URLs we need to fetch?
section_links = soup.find_all('span', class_='section-link')
print(f"Found {len(section_links)} section links")

for i, link in enumerate(section_links[:5]):
    print(f"  Link {i+1}: {link.get_text(strip=True)}")
    
    # Check if this span has href or is inside a link
    parent_a = link.find_parent('a')
    if parent_a:
        href = parent_a.get('href')
        print(f"    -> href: {href}")
        
        # Try to construct full URL and fetch
        if href and not href.startswith('http'):
            section_url = f"{BASE}{href}" if href.startswith('/') else f"{BASE}/{href}"
            print(f"    Full URL: {section_url}")
            
            # If this looks like aliens/immigration related, try to fetch it
            if 'alien' in link.get_text().lower():
                try:
                    section_content = fetch_html(section_url)
                    print(f"    *** SUCCESS: Fetched {len(section_content)} chars")
                    
                    # Quick check for our terms
                    if 'alien' in section_content.lower() and any(term in section_content.lower() for term in ['labour', 'employment', 'job', 'wage']):
                        print(f"    *** CONTAINS BOTH TERMS ***")
                        
                except Exception as e:
                    print(f"    Failed to fetch: {e}")