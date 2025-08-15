# working_collector.py
# Final working collector with correct section URL handling

import requests, re, json, csv, time
from datetime import date, timedelta
from bs4 import BeautifulSoup

BASE = "https://api.parliament.uk/historic-hansard"
START = date(1905, 5, 2)      # Start with date we know works
END   = date(1905, 5, 2)      # Just test one date first

# Era-aware vocab
MIG = r"(immigration|immigrant[s]?|migrant[s]?|alien[s]?|aliens|foreign(?:er|ers)?|guest\s*worker[s]?|colonial\s+(?:subjects|workers))"
LAB = r"(labour\s*market|labor\s*market|wage[s]?|pay|employment|unemployment|job[s]?|workforce|manpower|strike[s]?|trade\s*union[s]?)"
NEAR = 40

def fetch_html(url):
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=30, headers={"User-Agent":"HansardResearch/1.0"})
            r.raise_for_status()
            return r.text
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(1)

def words(text): 
    return re.findall(r"\w[\w'-]*", text.lower())

def proximity_hit(text):
    w = words(text)
    mi = [i for i,t in enumerate(w) if re.search(MIG, t)]
    lj = [i for i,t in enumerate(w) if re.search(LAB, t)]
    return any(abs(i-j) <= NEAR for i in mi for j in lj)

def extract_speaker_from_section(section_html):
    """Try to extract a speaker name from section content"""
    soup = BeautifulSoup(section_html, 'html.parser')
    text = soup.get_text()
    
    # Look for common speaker patterns
    speaker_patterns = [
        r'(Mr\.|Mrs\.|Sir|Lord|Dr\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+\([^)]+\)',  # Name (Constituency)
        r'The\s+(Secretary|Minister|President|Chairman)\s+(?:of\s+State)?',
    ]
    
    for pattern in speaker_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    
    return "Various speakers"

def process_sitting(date_obj, house):
    """Process a single sitting and return matches"""
    matches = []
    
    # Get the sitting index page (with zero-padded day)
    day_str = f"{date_obj.day:02d}"
    month_str = date_obj.strftime('%b').lower()
    sitting_url = f"{BASE}/{house}/{date_obj.year}/{month_str}/{date_obj.day}"
    
    print(f"  Fetching sitting: {sitting_url}")
    
    try:
        sitting_html = fetch_html(sitting_url)
        soup = BeautifulSoup(sitting_html, 'html.parser')
        
        # Find all section links with <a> tags
        section_spans = soup.find_all('span', class_='section-link')
        
        print(f"    Found {len(section_spans)} total sections")
        
        aliens_sections = []
        for span in section_spans:
            # Look for the <a> tag within this span
            link = span.find('a')
            if link:
                href = link.get('href')
                text = link.get_text()
                
                # Check if this section looks relevant
                if any(term in text.lower() for term in ['alien', 'immigration', 'immigrant', 'foreign']):
                    aliens_sections.append((span, link, href, text))
                    print(f"      Found aliens section: {text.strip()}")
        
        print(f"    Processing {len(aliens_sections)} aliens sections")
        
        # Process each aliens section
        for span, link, href, text in aliens_sections:
            # href already contains the full path starting with /historic-hansard
            section_url = f"https://api.parliament.uk{href}"
            section_title = text.strip()
            
            print(f"      Fetching section: {section_title}")
            
            try:
                section_html = fetch_html(section_url)
                
                if section_html:
                    soup_section = BeautifulSoup(section_html, 'html.parser')
                    section_text = soup_section.get_text()
                    
                    print(f"        Section content: {len(section_text)} chars")
                    
                    # Test for our terms
                    mig_matches = re.findall(MIG, section_text.lower())
                    lab_matches = re.findall(LAB, section_text.lower())
                    
                    print(f"        Migration terms: {len(mig_matches)} - {mig_matches[:3]}")
                    print(f"        Labour terms: {len(lab_matches)} - {lab_matches[:3]}")
                    
                    # Test for proximity match
                    if proximity_hit(section_text):
                        print(f"        *** PROXIMITY MATCH FOUND ***")
                        
                        # Extract speaker
                        speaker = extract_speaker_from_section(section_html)
                        
                        # Create a reasonable quote
                        # Find the proximity match area
                        w = words(section_text)
                        mi = [i for i,t in enumerate(w) if re.search(MIG, t)]
                        lj = [i for i,t in enumerate(w) if re.search(LAB, t)]
                        
                        # Find the closest match
                        min_distance = float('inf')
                        best_i, best_j = 0, 0
                        for i in mi:
                            for j in lj:
                                if abs(i-j) <= NEAR and abs(i-j) < min_distance:
                                    min_distance = abs(i-j)
                                    best_i, best_j = i, j
                        
                        # Extract context around the match
                        if min_distance < float('inf'):
                            start_word = max(0, min(best_i, best_j) - 30)
                            end_word = min(len(w), max(best_i, best_j) + 30)
                            quote_words = w[start_word:end_word]
                            quote = ' '.join(quote_words)
                        else:
                            # Fallback
                            quote_words = w[:200]
                            quote = ' '.join(quote_words)
                        
                        matches.append({
                            "date": date_obj.isoformat(),
                            "house": house,
                            "debate_title": section_title,
                            "member": speaker,
                            "party": "",
                            "quote": quote,
                            "hansard_url": section_url
                        })
                        
                        print(f"        Added match: {speaker}")
                        print(f"        Quote: {quote[:100]}...")
                        
                    else:
                        if mig_matches and lab_matches:
                            # Show why no proximity match
                            w = words(section_text)
                            mi = [i for i,t in enumerate(w) if re.search(MIG, t)]
                            lj = [i for i,t in enumerate(w) if re.search(LAB, t)]
                            if mi and lj:
                                min_dist = min(abs(i-j) for i in mi for j in lj)
                                print(f"        No proximity: min distance {min_dist} > {NEAR}")
                        else:
                            print(f"        No proximity: missing terms")
                            
            except Exception as e:
                print(f"        Error fetching section: {e}")
        
    except Exception as e:
        print(f"  Error processing sitting: {e}")
    
    return matches

print("=== WORKING COLLECTOR TEST ===")

d = date(1905, 5, 2)
print(f"Processing {d.isoformat()}...")

matches = process_sitting(d, 'commons')

print(f"\n=== RESULTS ===")
print(f"Found {len(matches)} quotes")

if matches:
    for i, match in enumerate(matches):
        print(f"\n{i+1}. {match['debate_title']}")
        print(f"   Date: {match['date']}")
        print(f"   Speaker: {match['member']}")
        print(f"   Quote: {match['quote']}")
        print(f"   URL: {match['hansard_url']}")
else:
    print("No matches found")