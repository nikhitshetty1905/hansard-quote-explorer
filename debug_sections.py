# debug_sections.py
# Debug what sections are being extracted

import requests, re
from datetime import date
from bs4 import BeautifulSoup

BASE = "https://api.parliament.uk/historic-hansard"

# Era-aware vocab
MIG = r"(immigration|immigrant[s]?|migrant[s]?|alien[s]?|aliens|foreign(?:er|ers)?|guest\s*worker[s]?|colonial\s+(?:subjects|workers))"
LAB = r"(labour\s*market|labor\s*market|wage[s]?|pay|employment|unemployment|job[s]?|workforce|manpower|strike[s]?|trade\s*union[s]?)"
NEAR = 40

def fetch_html(url):
    r = requests.get(url, timeout=40, headers={"User-Agent":"HansardResearch/1.0"})
    r.raise_for_status()
    return r.text

def words(text): 
    return re.findall(r"\w[\w'-]*", text.lower())

def proximity_hit(text):
    w = words(text)
    mi = [i for i,t in enumerate(w) if re.search(MIG, t)]
    lj = [i for i,t in enumerate(w) if re.search(LAB, t)]
    return any(abs(i-j) <= NEAR for i in mi for j in lj)

def extract_debate_sections(html_content, date_str, house):
    """Extract individual debate sections from HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    sections = []
    
    # Get the main content
    content_div = soup.find('div', id='content')
    if not content_div:
        return sections
    
    # Find section boundaries using the span structure
    major_sections = soup.find_all('span', class_='major-section')
    minor_sections = soup.find_all('span', class_='minor-section')
    all_sections = major_sections + minor_sections
    
    print(f"  Found {len(major_sections)} major + {len(minor_sections)} minor sections")
    
    # For each section, try to extract its content
    for i, section_span in enumerate(all_sections):
        section_title = section_span.get_text(strip=True)
        
        print(f"    Section {i+1}: {section_title}")
        
        # Skip procedural sections that are unlikely to contain debates
        if any(skip in section_title.upper() for skip in ['PREAMBLE', 'SPEAKER', 'BUSINESS', 'PETITIONS', 'RETURNS']):
            print(f"      -> SKIPPED (procedural)")
            continue
        
        # Try to find the actual content for this section
        section_content = ""
        
        # Find the parent li element that contains this section
        parent_li = section_span.find_parent('li')
        if parent_li:
            # Get all text from this li
            section_content = parent_li.get_text()
            
            # Clean up the content
            section_content = re.sub(r'\d+\s+words?', '', section_content)
            section_content = re.sub(r'c{1,2}\d+(?:-\d+)?', '', section_content)
            section_content = re.sub(r'\s+', ' ', section_content).strip()
        
        print(f"      Content length: {len(section_content)} chars")
        if section_content:
            # Show first bit of content
            try:
                preview = section_content[:150].encode('ascii', 'replace').decode('ascii')
                print(f"      Preview: {preview}...")
            except:
                print(f"      Preview: [encoding issues]")
            
            # Test for our terms
            has_mig = bool(re.search(MIG, section_content.lower()))
            has_lab = bool(re.search(LAB, section_content.lower()))
            has_prox = proximity_hit(section_content)
            
            print(f"      Migration: {has_mig}, Labour: {has_lab}, Proximity: {has_prox}")
            
            if has_mig:
                mig_matches = re.findall(MIG, section_content.lower())
                print(f"        Migration matches: {mig_matches[:3]}")
            if has_lab:
                lab_matches = re.findall(LAB, section_content.lower())
                print(f"        Labour matches: {lab_matches[:3]}")
        
        # Only include sections with substantial content
        if len(section_content) > 100:
            sections.append({
                'title': section_title,
                'content': section_content,
                'date': date_str,
                'house': house
            })
        print()
    
    return sections

# Test on a single day we know has data
d = date(1905, 5, 12)
print(f"=== DEBUGGING SECTIONS FOR {d.isoformat()} ===")

html_url = f"{BASE}/commons/{d.year}/{d.strftime('%b').lower()}/{d.day}"
print(f"URL: {html_url}")

try:
    html_content = fetch_html(html_url)
    sections = extract_debate_sections(html_content, d.isoformat(), 'commons')
    
    print(f"\nFinal result: {len(sections)} sections extracted")
    
    matches = 0
    for section in sections:
        if proximity_hit(section['content']):
            matches += 1
            print(f"  MATCH: {section['title']}")
    
    print(f"Total proximity matches: {matches}")
    
except Exception as e:
    print(f"Error: {e}")