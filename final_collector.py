# final_collector.py
# Proper collector that fetches individual section content via hrefs

import requests, re, json, csv, time
from datetime import date, timedelta
from bs4 import BeautifulSoup

BASE = "https://api.parliament.uk/historic-hansard"
START = date(1905, 5, 2)      # Start with dates we know have aliens content
END   = date(1905, 7, 31)

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
            time.sleep(2 ** attempt)

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
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+\([^)]+\)',  # Name (Constituency)
        r'The\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # The Secretary, etc.
    ]
    
    for pattern in speaker_patterns:
        match = re.search(pattern, text)
        if match:
            if len(match.groups()) == 2:
                return f"{match.group(1)} {match.group(2)}"
            else:
                return match.group(1)
    
    return "Unknown Speaker"

def process_sitting(date_obj, house):
    """Process a single sitting and return matches"""
    matches = []
    
    # Get the sitting index page
    sitting_url = f"{BASE}/{house}/{date_obj.year}/{date_obj.strftime('%b').lower()}/{date_obj.day}"
    
    try:
        sitting_html = fetch_html(sitting_url)
        soup = BeautifulSoup(sitting_html, 'html.parser')
        
        # Find all section links
        section_links = soup.find_all('span', class_='section-link')
        
        # Look for sections that might contain immigration content
        relevant_sections = []
        for link_span in section_links:
            link_text = link_span.get_text().lower()
            
            # Check if this section looks relevant
            if any(term in link_text for term in ['alien', 'immigration', 'immigrant', 'foreign']):
                relevant_sections.append(link_span)
                print(f"    Found relevant section: {link_span.get_text().strip()}")
        
        # Also check sections that might have labour content combined with general policy discussions
        for link_span in section_links:
            link_text = link_span.get_text().lower()
            if any(term in link_text for term in ['bill', 'act', 'policy', 'trade', 'employment', 'labour', 'labor']):
                # Only add if not already in relevant_sections
                if link_span not in relevant_sections:
                    relevant_sections.append(link_span)
        
        print(f"    Total sections to check: {len(relevant_sections)}")
        
        # Fetch and process each relevant section
        for link_span in relevant_sections:
            # Find the parent <a> tag to get the href
            parent_a = link_span.find_parent('a')
            if not parent_a:
                continue
                
            href = parent_a.get('href')
            if not href:
                continue
            
            # Construct full URL
            section_url = f"{BASE}{href}"
            section_title = link_span.get_text().strip()
            
            try:
                print(f"      Fetching: {section_title}")
                section_html = fetch_html(section_url)
                
                if section_html:
                    soup = BeautifulSoup(section_html, 'html.parser')
                    section_text = soup.get_text()
                    
                    # Test for proximity match
                    if proximity_hit(section_text):
                        # Extract speaker
                        speaker = extract_speaker_from_section(section_html)
                        
                        # Create a reasonable quote (not the entire section)
                        # Try to find the part with the proximity match
                        w = words(section_text)
                        mi = [i for i,t in enumerate(w) if re.search(MIG, t)]
                        lj = [i for i,t in enumerate(w) if re.search(LAB, t)]
                        
                        # Find the closest migration-labour pair
                        min_distance = float('inf')
                        best_i, best_j = 0, 0
                        for i in mi:
                            for j in lj:
                                if abs(i-j) <= NEAR and abs(i-j) < min_distance:
                                    min_distance = abs(i-j)
                                    best_i, best_j = i, j
                        
                        if min_distance < float('inf'):
                            # Extract context around the match (±50 words)
                            start_word = max(0, min(best_i, best_j) - 50)
                            end_word = min(len(w), max(best_i, best_j) + 50)
                            quote_words = w[start_word:end_word]
                            quote = ' '.join(quote_words)
                        else:
                            # Fallback: first 500 words
                            quote_words = w[:500]
                            quote = ' '.join(quote_words)
                        
                        matches.append({
                            "date": date_obj.isoformat(),
                            "house": house,
                            "debate_title": section_title,
                            "member": speaker,
                            "party": "",  # Not easily extractable
                            "quote": quote,
                            "hansard_url": section_url
                        })
                        
                        print(f"        *** MATCH FOUND ***")
                        print(f"        Speaker: {speaker}")
                        print(f"        Quote length: {len(quote)} chars")
                        
            except Exception as e:
                print(f"        Error fetching section: {e}")
                continue
    
    except Exception as e:
        print(f"  Error processing sitting: {e}")
    
    return matches

def iter_days(a, b):
    d = a
    while d <= b:
        yield d
        d += timedelta(days=7)  # Skip weeks to speed up for testing

print("=== FINAL HTML COLLECTOR WITH SECTION FETCHING ===")
out = []
processed_days = 0

for d in iter_days(START, END):
    processed_days += 1
    print(f"\nProcessing {d.isoformat()}... ({processed_days})")
    
    # Check Commons
    matches = process_sitting(d, 'commons')
    out.extend(matches)
    
    time.sleep(0.5)  # Be polite

# Write files
print(f"\n=== RESULTS ===")
print(f"Processed {processed_days} days")
print(f"Found {len(out)} quotes")

if out:
    with open("quotes_final.jsonl","w",encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open("quotes_final.csv","w",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    
    print(f"Saved to quotes_final.jsonl & quotes_final.csv")
    
    # Show samples
    print(f"\nSample quotes:")
    for i, match in enumerate(out[:3]):
        print(f"\n{i+1}. {match['date']} - {match['debate_title']}")
        print(f"   Speaker: {match['member']}")
        print(f"   Quote: {match['quote'][:200]}...")
else:
    print("No quotes found.")