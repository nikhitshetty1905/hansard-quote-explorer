# proper_html_collector.py
# Corrected collector that extracts debate sections, not entire sittings

import requests, re, json, csv, time
from datetime import date, timedelta
from bs4 import BeautifulSoup

BASE = "https://api.parliament.uk/historic-hansard"
START = date(1905, 5, 10)      # Small test range
END   = date(1905, 5, 15)

# Era-aware vocab
MIG = r"(immigration|immigrant[s]?|migrant[s]?|alien[s]?|aliens|foreign(?:er|ers)?|guest\s*worker[s]?|colonial\s+(?:subjects|workers))"
LAB = r"(labour\s*market|labor\s*market|wage[s]?|pay|employment|unemployment|job[s]?|workforce|manpower|strike[s]?|trade\s*union[s]?)"
NEAR = 40

def fetch_html(url):
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=40, headers={"User-Agent":"HansardResearch/1.0"})
            r.raise_for_status()
            return r.text
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)

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
    
    # For each section, try to extract its content
    for section_span in all_sections:
        section_title = section_span.get_text(strip=True)
        
        # Skip procedural sections that are unlikely to contain debates
        if any(skip in section_title.upper() for skip in ['PREAMBLE', 'SPEAKER', 'BUSINESS', 'PETITIONS', 'RETURNS']):
            continue
        
        # Try to find the actual content for this section
        # Look for the section in the ordered list structure
        section_content = ""
        
        # Find the parent li element that contains this section
        parent_li = section_span.find_parent('li')
        if parent_li:
            # Get all text from this li, excluding the nested structure
            section_content = parent_li.get_text()
            
            # Clean up the content - remove section headers, word counts, etc.
            # Remove patterns like "123 words", "c123", "cc123-4"
            section_content = re.sub(r'\d+\s+words?', '', section_content)
            section_content = re.sub(r'c{1,2}\d+(?:-\d+)?', '', section_content)
            section_content = re.sub(r'\s+', ' ', section_content).strip()
        
        # Only include sections with substantial content
        if len(section_content) > 100:  # At least 100 characters
            sections.append({
                'title': section_title,
                'content': section_content,
                'date': date_str,
                'house': house
            })
    
    return sections

def iter_days(a, b):
    d = a
    while d <= b:
        yield d
        d += timedelta(days=1)

print("=== PROPER HTML-BASED HANSARD COLLECTOR ===")
out = []
processed_days = 0

for d in iter_days(START, END):
    processed_days += 1
    print(f"Processing {d.isoformat()}... ({processed_days})")
    
    # Try both Commons and Lords
    for house in ['commons', 'lords']:
        html_url = f"{BASE}/{house}/{d.year}/{d.strftime('%b').lower()}/{d.day}"
        
        try:
            html_content = fetch_html(html_url)
            sections = extract_debate_sections(html_content, d.isoformat(), house)
            
            if sections:
                print(f"  {house.title()}: Found {len(sections)} debate sections")
                
                for section in sections:
                    content = section['content']
                    title = section['title']
                    
                    if proximity_hit(content):
                        # Extract a reasonable quote from the section (not the entire thing)
                        quote_text = content[:2000] + "..." if len(content) > 2000 else content
                        
                        out.append({
                            "date": d.isoformat(),
                            "house": house,
                            "debate_title": title,
                            "member": "Multiple speakers",  # Sections contain multiple speakers
                            "party": "",
                            "quote": quote_text,
                            "hansard_url": html_url
                        })
                        print(f"    *** FOUND MATCH: {title} ***")
                        print(f"        Content length: {len(content)} chars")
            
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                continue  # No sitting that day
            else:
                print(f"  Error fetching {house}: {e}")
        except Exception as e:
            print(f"  Error processing {house}: {e}")
    
    time.sleep(0.3)  # Be polite

# Write files
print(f"\n=== RESULTS ===")
print(f"Processed {processed_days} days")
print(f"Found {len(out)} section matches")

if out:
    with open("quotes_sections.jsonl","w",encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open("quotes_sections.csv","w",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    
    print(f"Saved to quotes_sections.jsonl & quotes_sections.csv")
    
    # Show samples
    print(f"\nFound sections:")
    for i, match in enumerate(out):
        print(f"{i+1}. {match['date']} - {match['debate_title']}")
        print(f"   {len(match['quote'])} chars: {match['quote'][:150]}...")
        print()
else:
    print("No matches found.")