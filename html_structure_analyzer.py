# html_structure_analyzer.py
# Examine HTML structure to find individual speeches

import requests
from bs4 import BeautifulSoup

BASE = "https://api.parliament.uk/historic-hansard"

def fetch_html(url):
    r = requests.get(url, headers={"User-Agent":"HansardResearch/1.0"})
    r.raise_for_status()
    return r.text

# Get a sample HTML page
html_url = f"{BASE}/commons/1905/may/12"
html_content = fetch_html(html_url)

soup = BeautifulSoup(html_content, 'html.parser')

print("=== HTML STRUCTURE ANALYSIS ===")
print(f"Page title: {soup.title.get_text() if soup.title else 'No title'}")

# Look for common parliamentary HTML patterns
print("\n=== SEARCHING FOR SPEECH PATTERNS ===")

# Check for various structural elements
patterns_to_check = [
    ('div', 'class'),
    ('p', 'class'), 
    ('blockquote', None),
    ('div', 'id'),
    ('span', 'class'),
    ('section', None),
]

for tag, attr in patterns_to_check:
    elements = soup.find_all(tag)
    print(f"\n{tag.upper()} elements: {len(elements)}")
    
    # Show unique classes/attributes
    if attr and elements:
        attrs = set()
        for elem in elements:
            attr_val = elem.get(attr)
            if attr_val:
                if isinstance(attr_val, list):
                    attrs.update(attr_val)
                else:
                    attrs.add(attr_val)
        if attrs:
            print(f"  Unique {attr}s: {sorted(list(attrs))[:10]}")
    
    # Show sample content
    if elements:
        for i, elem in enumerate(elements[:3]):
            text = elem.get_text(strip=True)
            if len(text) > 50:
                # Handle encoding issues
                try:
                    clean_text = text[:100].encode('ascii', 'replace').decode('ascii')
                    print(f"  Sample {i+1}: {clean_text}...")
                except:
                    print(f"  Sample {i+1}: [encoding issues]")

# Look for speaker names specifically
print("\n=== LOOKING FOR SPEAKER PATTERNS ===")

# Common patterns for speaker names in parliamentary transcripts
speaker_patterns = [
    r'(Mr\.|Mrs\.|Sir|Lord|Dr\.|The|Hon\.)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*',
    r'^[A-Z\s]{3,}:',  # ALL CAPS names with colon
    r'[A-Z][a-z]+\s+\([^)]+\)',  # Name with constituency
]

import re
full_text = soup.get_text()

print("Looking for speaker name patterns in full text:")
for pattern in speaker_patterns:
    matches = re.findall(pattern, full_text)
    if matches:
        unique_matches = list(set(matches))[:10]
        print(f"  Pattern '{pattern}': {len(matches)} matches, samples: {unique_matches}")

# Also look at the raw HTML structure around potential speeches
print("\n=== EXAMINING SPECIFIC SECTIONS ===")

# Look for elements that might contain individual speeches
potential_speech_elements = []

# Try to find elements with substantial text that might be individual speeches
for elem in soup.find_all(['div', 'p', 'blockquote', 'section']):
    text = elem.get_text(strip=True)
    if 100 < len(text) < 2000:  # Reasonable speech length
        potential_speech_elements.append(elem)

print(f"Found {len(potential_speech_elements)} elements with 100-2000 chars")

# Examine the first few
for i, elem in enumerate(potential_speech_elements[:5]):
    print(f"\nElement {i+1}:")
    print(f"  Tag: {elem.name}")
    print(f"  Attributes: {dict(elem.attrs)}")
    print(f"  Text length: {len(elem.get_text(strip=True))}")
    try:
        clean_text = elem.get_text(strip=True)[:150].encode('ascii', 'replace').decode('ascii')
        print(f"  Text sample: {clean_text}...")
    except:
        print(f"  Text sample: [encoding issues]")
    
    # Check if previous/next siblings might contain speaker info
    if elem.previous_sibling:
        prev_text = elem.previous_sibling.get_text(strip=True) if hasattr(elem.previous_sibling, 'get_text') else str(elem.previous_sibling).strip()
        if prev_text and len(prev_text) < 100:
            try:
                clean_prev = prev_text.encode('ascii', 'replace').decode('ascii')
                print(f"  Previous sibling: {clean_prev}")
            except:
                print(f"  Previous sibling: [encoding issues]")
    
    # Check parent element
    if elem.parent and elem.parent.name != 'body':
        parent_attrs = dict(elem.parent.attrs)
        print(f"  Parent: {elem.parent.name} {parent_attrs}")

print("\n=== SEARCHING FOR HANSARD-SPECIFIC PATTERNS ===")

# Look for column references (c123, cc123-4) which are common in Hansard
column_refs = re.findall(r'c{1,2}\d+(?:-\d+)?', full_text)
if column_refs:
    print(f"Found {len(column_refs)} column references: {column_refs[:10]}")

# Look for "said" patterns which indicate speech
said_patterns = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+said', full_text, re.IGNORECASE)
if said_patterns:
    unique_said = list(set(said_patterns))[:10]
    print(f"Found 'said' patterns: {unique_said}")