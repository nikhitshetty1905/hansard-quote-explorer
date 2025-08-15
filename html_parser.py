# html_parser.py
# Parse HTML version to extract speech content

import requests, re
from bs4 import BeautifulSoup

BASE = "https://api.parliament.uk/historic-hansard"

def fetch_html(url):
    r = requests.get(url, headers={"User-Agent":"HansardResearch/1.0"})
    r.raise_for_status()
    return r.text

# Test patterns
MIG = r"(immigration|immigrant[s]?|migrant[s]?|alien[s]?|aliens|foreign(?:er|ers)?|guest\s*worker[s]?|colonial\s+(?:subjects|workers))"
LAB = r"(labour\s*market|labor\s*market|wage[s]?|pay|employment|unemployment|job[s]?|workforce|manpower|strike[s]?|trade\s*union[s]?)"

def words(text): 
    return re.findall(r"\w[\w'-]*", text.lower())

def proximity_hit(text):
    w = words(text)
    mi = [i for i,t in enumerate(w) if re.search(MIG, t)]
    lj = [i for i,t in enumerate(w) if re.search(LAB, t)]
    return any(abs(i-j) <= 40 for i in mi for j in lj)

print("=== PARSING HTML CONTENT ===")

html_url = f"{BASE}/commons/1905/may/12"
html_content = fetch_html(html_url)

print(f"HTML content length: {len(html_content)}")

# Try to parse with BeautifulSoup
try:
    soup = BeautifulSoup(html_content, 'html.parser')
    print("Successfully parsed HTML")
    
    # Look for speech content - common patterns in parliamentary transcripts
    possible_speech_selectors = [
        'div.speech',
        'div.contribution', 
        'p.speech',
        'div.member-contribution',
        '.hansard-speech',
        'div[data-member]',
        'blockquote',
    ]
    
    speeches_found = []
    for selector in possible_speech_selectors:
        elements = soup.select(selector)
        if elements:
            print(f"Found {len(elements)} elements with selector: {selector}")
            speeches_found.extend(elements)
    
    # If no specific selectors work, look for any substantial text blocks
    if not speeches_found:
        print("No specific speech elements found, looking for text blocks...")
        # Look for divs or paragraphs with substantial text
        all_elements = soup.find_all(['div', 'p', 'section'])
        for elem in all_elements:
            text = elem.get_text(strip=True)
            if len(text) > 100:  # Substantial text
                speeches_found.append(elem)
    
    print(f"Total text elements found: {len(speeches_found)}")
    
    # Test for our terms
    migration_speeches = 0
    labour_speeches = 0
    combined_speeches = 0
    
    for i, speech_elem in enumerate(speeches_found[:10]):  # Test first 10
        text = speech_elem.get_text()
        
        has_migration = bool(re.search(MIG, text.lower()))
        has_labour = bool(re.search(LAB, text.lower()))
        has_proximity = proximity_hit(text)
        
        if has_migration:
            migration_speeches += 1
        if has_labour:
            labour_speeches += 1
        if has_migration and has_labour and has_proximity:
            combined_speeches += 1
            print(f"\n*** FOUND COMBINED MATCH ***")
            print(f"Element {i}: {len(text)} chars")
            print(f"Content: {text[:300]}...")
    
    print(f"\nResults from first 10 elements:")
    print(f"Migration mentions: {migration_speeches}")
    print(f"Labour mentions: {labour_speeches}")
    print(f"Combined proximity matches: {combined_speeches}")
    
except ImportError:
    print("BeautifulSoup not available, trying basic regex...")
    # Basic approach without BeautifulSoup
    text_content = re.sub(r'<[^>]+>', ' ', html_content)  # Strip HTML tags
    print(f"Text content length: {len(text_content)}")
    
    has_migration = bool(re.search(MIG, text_content.lower()))
    has_labour = bool(re.search(LAB, text_content.lower()))
    has_proximity = proximity_hit(text_content)
    
    print(f"Migration terms found: {has_migration}")
    print(f"Labour terms found: {has_labour}")
    print(f"Proximity match: {has_proximity}")
    
    if has_migration:
        migration_matches = re.findall(MIG, text_content.lower())
        print(f"Migration matches: {migration_matches[:5]}")
    if has_labour:
        labour_matches = re.findall(LAB, text_content.lower())
        print(f"Labour matches: {labour_matches[:5]}")

except Exception as e:
    print(f"Error parsing HTML: {e}")