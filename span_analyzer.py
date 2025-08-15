# span_analyzer.py
# Look at the span structure to understand segmentation

import requests
from bs4 import BeautifulSoup
import re

BASE = "https://api.parliament.uk/historic-hansard"

def fetch_html(url):
    r = requests.get(url, headers={"User-Agent":"HansardResearch/1.0"})
    r.raise_for_status()
    return r.text

html_url = f"{BASE}/commons/1905/may/12"
html_content = fetch_html(html_url)
soup = BeautifulSoup(html_content, 'html.parser')

print("=== ANALYZING SPAN ELEMENTS ===")

# Get all spans with their classes
spans = soup.find_all('span')
print(f"Total spans: {len(spans)}")

# Group by class
span_classes = {}
for span in spans:
    classes = span.get('class', [])
    for cls in classes:
        if cls not in span_classes:
            span_classes[cls] = []
        span_classes[cls].append(span)

for cls, cls_spans in span_classes.items():
    print(f"\n{cls}: {len(cls_spans)} spans")
    for i, span in enumerate(cls_spans[:3]):  # Show first 3
        text = span.get_text(strip=True)
        try:
            clean_text = text.encode('ascii', 'replace').decode('ascii')
            print(f"  {i+1}: {clean_text[:80]}")
        except:
            print(f"  {i+1}: [encoding issues]")

print("\n=== EXAMINING CONTENT DIV STRUCTURE ===")

# Get the main content div
content_div = soup.find('div', id='content')
if content_div:
    print("Found content div")
    
    # Look at its direct children
    children = list(content_div.children)
    print(f"Direct children: {len(children)}")
    
    text_children = [child for child in children if hasattr(child, 'get_text')]
    print(f"Text-bearing children: {len(text_children)}")
    
    for i, child in enumerate(text_children[:5]):
        if hasattr(child, 'name') and child.name:
            attrs = dict(child.attrs) if hasattr(child, 'attrs') else {}
            print(f"  Child {i+1}: {child.name} - {attrs}")
            text = child.get_text(strip=True)
            try:
                clean_text = text[:100].encode('ascii', 'replace').decode('ascii')
                print(f"    Text: {clean_text}...")
            except:
                print(f"    Text: [encoding issues]")
        else:
            # Text node
            text = str(child).strip()
            if text and len(text) > 10:
                try:
                    clean_text = text[:50].encode('ascii', 'replace').decode('ascii')
                    print(f"  Text node {i+1}: {clean_text}...")
                except:
                    print(f"  Text node {i+1}: [encoding issues]")

print("\n=== LOOKING FOR SECTION BOUNDARIES ===")

# Try to find section boundaries using the span elements
major_sections = soup.find_all('span', class_='major-section')
minor_sections = soup.find_all('span', class_='minor-section')

print(f"Major sections: {len(major_sections)}")
print(f"Minor sections: {len(minor_sections)}")

# Show major sections
for i, section in enumerate(major_sections[:5]):
    text = section.get_text(strip=True)
    try:
        clean_text = text.encode('ascii', 'replace').decode('ascii')
        print(f"  Major {i+1}: {clean_text}")
    except:
        print(f"  Major {i+1}: [encoding issues]")

# Show minor sections  
for i, section in enumerate(minor_sections[:10]):
    text = section.get_text(strip=True)
    try:
        clean_text = text.encode('ascii', 'replace').decode('ascii')
        print(f"  Minor {i+1}: {clean_text}")
    except:
        print(f"  Minor {i+1}: [encoding issues]")

print("\n=== TRYING TO PARSE SECTION STRUCTURE ===")

# Try to extract sections by looking at the structure
# It seems like the content might be structured as:
# Major section title -> content -> minor sections -> content

# Get all text from content div and try to segment it
content_text = content_div.get_text() if content_div else ""
print(f"Total content length: {len(content_text)}")

# Look for patterns that might indicate speech boundaries
speech_indicators = [
    r'[A-Z][a-z]+\s+\([^)]+\)',  # Name with constituency
    r'(Mr\.|Mrs\.|Sir|Lord|Dr\.)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s*:',  # Title Name:
    r'^[A-Z\s]{3,}:',  # ALL CAPS:
    r'said\s*:',  # said:
]

print("Potential speech boundaries:")
for pattern in speech_indicators:
    matches = re.finditer(pattern, content_text, re.MULTILINE | re.IGNORECASE)
    match_list = list(matches)
    if match_list:
        print(f"  Pattern '{pattern}': {len(match_list)} matches")
        for match in match_list[:3]:
            start_pos = max(0, match.start() - 20)
            end_pos = min(len(content_text), match.end() + 50)
            context = content_text[start_pos:end_pos]
            try:
                clean_context = context.encode('ascii', 'replace').decode('ascii')
                print(f"    {clean_context}")
            except:
                print(f"    [encoding issues]")