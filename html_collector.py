# html_collector.py  
# Corrected collector using HTML parsing for actual speech content

import requests, re, json, csv, time
from datetime import date, timedelta
from bs4 import BeautifulSoup

BASE = "https://api.parliament.uk/historic-hansard"
START = date(1905, 5, 1)      # Two month test period 
END   = date(1905, 6, 30)

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

def extract_speeches(html_content):
    """Extract individual speeches from HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Look for substantial text blocks that could be speeches
    speeches = []
    
    # Try different approaches to find speech content
    # 1. Look for common parliamentary HTML patterns
    for element in soup.find_all(['div', 'p', 'section', 'blockquote']):
        text = element.get_text(strip=True)
        if len(text) > 100:  # Substantial text
            # Try to find speaker name (often in preceding elements or attributes)
            speaker = "Unknown"
            
            # Check for member names in various formats
            for prev in [element.find_previous_sibling(), element.parent]:
                if prev:
                    prev_text = prev.get_text(strip=True)
                    # Look for patterns like "Mr. Smith:", "LORD JONES said:", etc.
                    speaker_match = re.search(r'(Mr\.|Mrs\.|Lord|Sir|Dr\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', prev_text)
                    if speaker_match:
                        speaker = speaker_match.group(0)
                        break
                    elif re.match(r'^[A-Z\s]+:', prev_text):  # ALL CAPS name with colon
                        speaker = prev_text.rstrip(':')
                        break
            
            speeches.append({
                'text': text,
                'speaker': speaker,
                'element': element
            })
    
    return speeches

def iter_days(a, b):
    d = a
    while d <= b:
        yield d
        d += timedelta(days=1)

print("=== HTML-BASED HANSARD COLLECTOR ===")
out = []
processed_days = 0
successful_days = 0

for d in iter_days(START, END):
    processed_days += 1
    print(f"Processing {d.isoformat()}... ({processed_days})")
    
    # Try both Commons and Lords
    for house in ['commons', 'lords']:
        html_url = f"{BASE}/{house}/{d.year}/{d.strftime('%b').lower()}/{d.day}"
        
        try:
            html_content = fetch_html(html_url)
            speeches = extract_speeches(html_content)
            
            if speeches:
                successful_days += 1
                print(f"  {house.title()}: Found {len(speeches)} speech blocks")
                
                for speech in speeches:
                    text = speech['text']
                    speaker = speech['speaker']
                    
                    if proximity_hit(text):
                        # Extract title/debate context from page
                        soup = BeautifulSoup(html_content, 'html.parser')
                        title_elem = soup.find('title') or soup.find('h1')
                        debate_title = title_elem.get_text(strip=True) if title_elem else f"{house.title()} sitting"
                        
                        out.append({
                            "date": d.isoformat(),
                            "house": house,
                            "debate_title": debate_title,
                            "member": speaker,
                            "party": "",  # Not easily extractable from HTML
                            "quote": re.sub(r"\s+", " ", text).strip(),
                            "hansard_url": html_url
                        })
                        print(f"    *** FOUND MATCH: {speaker} ***")
            
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                continue  # No sitting that day
            else:
                print(f"  Error fetching {house}: {e}")
        except Exception as e:
            print(f"  Error processing {house}: {e}")
    
    # Progress update every 10 days
    if processed_days % 10 == 0:
        print(f"  Progress: {processed_days} days processed, {successful_days} with content, {len(out)} matches")
    
    time.sleep(0.3)  # Be polite

# Write files
print(f"\n=== RESULTS ===")
print(f"Processed {processed_days} days")
print(f"Found content on {successful_days} days")
print(f"Found {len(out)} proximity matches")

if out:
    with open("quotes_html.jsonl","w",encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open("quotes_html.csv","w",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    
    print(f"Saved to quotes_html.jsonl & quotes_html.csv")
    
    # Show samples
    print(f"\nFirst few matches:")
    for i, match in enumerate(out[:3]):
        print(f"{i+1}. {match['date']} - {match['member']}: {match['quote'][:100]}...")
else:
    print("No matches found. Consider:")
    print("1. Expanding date range")  
    print("2. Reducing proximity window")
    print("3. Checking if the terms appear individually")