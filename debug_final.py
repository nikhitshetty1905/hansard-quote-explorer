# debug_final.py
# Debug the section fetching to see what content we're getting

import requests, re
from datetime import date
from bs4 import BeautifulSoup

BASE = "https://api.parliament.uk/historic-hansard"

# Era-aware vocab
MIG = r"(immigration|immigrant[s]?|migrant[s]?|alien[s]?|aliens|foreign(?:er|ers)?|guest\s*worker[s]?|colonial\s+(?:subjects|workers))"
LAB = r"(labour\s*market|labor\s*market|wage[s]?|pay|employment|unemployment|job[s]?|workforce|manpower|strike[s]?|trade\s*union[s]?)"
NEAR = 40

def fetch_html(url):
    try:
        r = requests.get(url, timeout=30, headers={"User-Agent":"HansardResearch/1.0"})
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"    Fetch error: {e}")
        return None

def words(text): 
    return re.findall(r"\w[\w'-]*", text.lower())

def proximity_hit(text):
    w = words(text)
    mi = [i for i,t in enumerate(w) if re.search(MIG, t)]
    lj = [i for i,t in enumerate(w) if re.search(LAB, t)]
    return any(abs(i-j) <= NEAR for i in mi for j in lj)

# Test with the first date we know has content
d = date(1905, 5, 2)
house = 'commons'

print(f"=== DEBUGGING SECTION FETCHING FOR {d.isoformat()} ===")

sitting_url = f"{BASE}/{house}/{d.year}/{d.strftime('%b').lower()}/{d.day}"
print(f"Sitting URL: {sitting_url}")

sitting_html = fetch_html(sitting_url)
if not sitting_html:
    print("Failed to fetch sitting HTML")
    exit()

soup = BeautifulSoup(sitting_html, 'html.parser')
section_links = soup.find_all('span', class_='section-link')

# Find the specific aliens sections
aliens_sections = []
for link_span in section_links:
    link_text = link_span.get_text().lower()
    if 'alien' in link_text:
        aliens_sections.append(link_span)

print(f"Found {len(aliens_sections)} aliens sections:")
for i, section in enumerate(aliens_sections):
    print(f"  {i+1}. {section.get_text().strip()}")

# Test fetching the first aliens section
if aliens_sections:
    test_section = aliens_sections[0]  # "Immigration of Aliens"
    print(f"\n=== TESTING SECTION: {test_section.get_text().strip()} ===")
    
    parent_a = test_section.find_parent('a')
    if parent_a:
        href = parent_a.get('href')
        print(f"Href: {href}")
        
        if href:
            section_url = f"{BASE}{href}"
            print(f"Full URL: {section_url}")
            
            section_html = fetch_html(section_url)
            if section_html:
                print(f"Section HTML length: {len(section_html)} chars")
                
                # Parse the content
                soup = BeautifulSoup(section_html, 'html.parser')
                section_text = soup.get_text()
                
                print(f"Section text length: {len(section_text)} chars")
                
                # Show first part of content
                try:
                    preview = section_text[:300].encode('ascii', 'replace').decode('ascii')
                    print(f"Content preview: {preview}...")
                except:
                    print("Content preview: [encoding issues]")
                
                # Test for terms
                mig_matches = re.findall(MIG, section_text.lower())
                lab_matches = re.findall(LAB, section_text.lower())
                has_prox = proximity_hit(section_text)
                
                print(f"Migration matches ({len(mig_matches)}): {mig_matches[:5]}")
                print(f"Labour matches ({len(lab_matches)}): {lab_matches[:5]}")
                print(f"Proximity match: {has_prox}")
                
                if mig_matches and lab_matches and not has_prox:
                    print("\n=== ANALYZING WHY NO PROXIMITY MATCH ===")
                    w = words(section_text)
                    print(f"Total words: {len(w)}")
                    
                    mi = [i for i,t in enumerate(w) if re.search(MIG, t)]
                    lj = [i for i,t in enumerate(w) if re.search(LAB, t)]
                    
                    print(f"Migration word positions: {mi[:5]}")
                    print(f"Labour word positions: {lj[:5]}")
                    
                    if mi and lj:
                        min_dist = min(abs(i-j) for i in mi for j in lj)
                        print(f"Minimum distance between terms: {min_dist} words")
                        if min_dist > NEAR:
                            print(f"Distance {min_dist} > threshold {NEAR}")
                            
                            # Show the closest pair
                            best_pair = None
                            for i in mi:
                                for j in lj:
                                    if abs(i-j) == min_dist:
                                        best_pair = (i, j)
                                        break
                                if best_pair:
                                    break
                            
                            if best_pair:
                                i, j = best_pair
                                start = max(0, min(i, j) - 10)
                                end = min(len(w), max(i, j) + 10)
                                context_words = w[start:end]
                                context = ' '.join(context_words)
                                print(f"Closest pair context: ...{context}...")
                
            else:
                print("Failed to fetch section content")
        else:
            print("No href found")
    else:
        print("No parent <a> tag found")
else:
    print("No aliens sections found")