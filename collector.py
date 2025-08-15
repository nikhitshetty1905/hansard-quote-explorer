2# collector.py
# Pulls Historic Hansard (no API key), extracts exact quotes about immigration x labour.

import requests, re, json, csv, time
from datetime import date, timedelta

BASE = "https://api.parliament.uk/historic-hansard"
START = date(1890, 1, 1)      # Full historical range with fixed structure
END   = date(1950, 12, 31)

# Era-aware vocab: start small; expand later per decade.
MIG = r"(immigration|immigrant[s]?|migrant[s]?|alien[s]?|aliens|foreign(?:er|ers)?|guest\s*worker[s]?|colonial\s+(?:subjects|workers))"
LAB = r"(labour\s*market|labor\s*market|wage[s]?|pay|employment|unemployment|job[s]?|workforce|manpower|strike[s]?|trade\s*union[s]?)"
NEAR = 40  # words proximity window

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

def iter_days(a, b):
    d = a
    while d <= b:
        yield d
        d += timedelta(days=1)

out = []
for d in iter_days(START, END):
    print(f"Processing {d.isoformat()}...")
    mon = d.strftime("%b").lower()
    day_url = f"{BASE}/sittings/{d.year}/{mon}/{d.day}.js"
    try:
        sitting = fetch_json(day_url)
    except requests.HTTPError:
        print(f"  No data for {d.isoformat()}")
        continue

    # Handle the actual API structure: list of house sittings
    if isinstance(sitting, list):
        for item in sitting:
            if 'house_of_commons_sitting' in item:
                house_data = item['house_of_commons_sitting']
                house_name = "commons"
            elif 'house_of_lords_sitting' in item:
                house_data = item['house_of_lords_sitting']
                house_name = "lords"
            else:
                continue
                
            # Process speeches directly from the sitting data
            stack = house_data.get('children', [])
            debate_title = house_data.get('title', '')
            
            while stack:
                node = stack.pop()
                stack.extend(node.get("children", []))
                text = node.get("text") or node.get("body") or ""
                speaker = (node.get("speaker") or {}).get("name", "")
                party = (node.get("speaker") or {}).get("party", "")
                if not (text and speaker):
                    continue
                if proximity_hit(text):
                    out.append({
                        "date": d.isoformat(),
                        "house": house_name,
                        "debate_title": debate_title,
                        "member": speaker,
                        "party": party,
                        "quote": re.sub(r"\s+", " ", text).strip(),
                        "hansard_url": f"https://api.parliament.uk/historic-hansard/sittings/{d.year}/{mon}/{d.day}"
                    })
    time.sleep(0.2)  # be polite

# write files
with open("quotes.jsonl","w",encoding="utf-8") as f:
    for r in out:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

with open("quotes.csv","w",newline="",encoding="utf-8") as f:
    import csv
    w = csv.DictWriter(f, fieldnames=list(out[0].keys()) if out else 
        ["date","house","debate_title","member","party","quote","hansard_url"])
    w.writeheader(); w.writerows(out)

print(f"Saved {len(out)} quotes -> quotes.jsonl & quotes.csv")