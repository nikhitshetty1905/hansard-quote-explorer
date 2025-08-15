# diagnostic.py  
# Test why 1905 had 0 matches - expand search terms and proximity

import requests, re, json, csv, time
from datetime import date, timedelta

BASE = "https://api.parliament.uk/historic-hansard"
START = date(1905, 5, 10)
END   = date(1905, 5, 15)

# Expanded period-appropriate vocabulary
MIG = r"(immigration|immigrant[s]?|migrant[s]?|alien[s]?|aliens|foreign(?:er|ers)?|guest\s*worker[s]?|colonial\s+(?:subjects|workers)|pauper[s]?|undesirable[s]?)"
LAB = r"(labour\s*market|labor\s*market|wage[s]?|pay|employment|unemployment|job[s]?|workforce|manpower|strike[s]?|trade\s*union[s]?|work|working|industry|industrial)"
NEAR = 100  # Increased proximity window

def fetch_json(url):
    for attempt in range(4):
        try:
            r = requests.get(url, timeout=40, headers={"User-Agent":"HansardResearch/1.0"})
            if r.status_code in (429, 502, 503, 504):
                time.sleep(2 ** attempt); continue
            r.raise_for_status()
            return r.json()
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)
    r.raise_for_status()

def words(text): 
    return re.findall(r"\w[\w'-]*", text.lower())

def proximity_hit(text):
    w = words(text)
    mi = [i for i,t in enumerate(w) if re.search(MIG, t)]
    lj = [i for i,t in enumerate(w) if re.search(LAB, t)]
    return any(abs(i-j) <= NEAR for i in mi for j in lj)

def single_term_hit(text, pattern):
    return bool(re.search(pattern, text.lower()))

def iter_days(a, b):
    d = a
    while d <= b:
        yield d
        d += timedelta(days=1)

out = []
alien_only = []
labour_only = []
for d in iter_days(START, END):
    print(f"Processing {d.isoformat()}...")
    mon = d.strftime("%b").lower()
    day_url = f"{BASE}/sittings/{d.year}/{mon}/{d.day}.js"
    try:
        sitting = fetch_json(day_url)
    except requests.HTTPError:
        print(f"  No data for {d.isoformat()}")
        continue

    items = sitting if isinstance(sitting, list) else sitting.get("items", [])
    for it in items:
        href = it.get("href")
        if not href: 
            continue
        deb_url = f"{BASE}{href}.js"

        try:
            deb = fetch_json(deb_url)
        except requests.HTTPError:
            continue

        debate_title = deb.get("title", "")
        house = "commons" if "/commons/" in href else ("lords" if "/lords/" in href else "")
        stack = deb.get("children", [])

        while stack:
            node = stack.pop()
            stack.extend(node.get("children", []))
            text = node.get("text") or node.get("body") or ""
            speaker = (node.get("speaker") or {}).get("name", "")
            party = (node.get("speaker") or {}).get("party", "")
            if not (text and speaker):
                continue
            
            # Test different scenarios
            has_migration = single_term_hit(text, MIG)
            has_labour = single_term_hit(text, LAB)
            has_proximity = proximity_hit(text)
            
            if has_migration and has_labour and has_proximity:
                out.append({
                    "date": d.isoformat(), "house": house, "debate_title": debate_title,
                    "member": speaker, "party": party,
                    "quote": re.sub(r"\s+", " ", text).strip(),
                    "hansard_url": f"https://api.parliament.uk/historic-hansard{href}"
                })
            elif has_migration and not has_labour:
                alien_only.append({"date": d.isoformat(), "debate_title": debate_title, "quote": text[:100]+"..."})
            elif has_labour and not has_migration:
                labour_only.append({"date": d.isoformat(), "debate_title": debate_title, "quote": text[:100]+"..."})
                
    time.sleep(0.2)

print(f"\nRESULTS:")
print(f"Combined matches: {len(out)}")
print(f"Alien-only matches: {len(alien_only)}")
print(f"Labour-only matches: {len(labour_only)}")

if alien_only:
    print("\nSample alien-only quotes:")
    for i, q in enumerate(alien_only[:3]):
        print(f"  {i+1}. {q['date']} - {q['debate_title']}: {q['quote']}")

if labour_only:
    print("\nSample labour-only quotes:")
    for i, q in enumerate(labour_only[:3]):
        print(f"  {i+1}. {q['date']} - {q['debate_title']}: {q['quote']}")