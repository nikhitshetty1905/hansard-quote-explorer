# content_explorer.py
# See what's actually in the 1905 debates

import requests, re, json
from datetime import date, timedelta

BASE = "https://api.parliament.uk/historic-hansard"
START = date(1905, 5, 12)  # Focus on one day we know has data
END   = date(1905, 5, 12)

def fetch_json(url):
    r = requests.get(url, timeout=40, headers={"User-Agent":"HansardResearch/1.0"})
    r.raise_for_status()
    return r.json()

def iter_days(a, b):
    d = a
    while d <= b:
        yield d
        d += timedelta(days=1)

for d in iter_days(START, END):
    print(f"=== {d.isoformat()} ===")
    mon = d.strftime("%b").lower()
    day_url = f"{BASE}/sittings/{d.year}/{mon}/{d.day}.js"
    
    try:
        sitting = fetch_json(day_url)
        print(f"Sitting data structure: {type(sitting)}")
        
        items = sitting if isinstance(sitting, list) else sitting.get("items", [])
        print(f"Found {len(items)} items for this day")
        
        for i, it in enumerate(items[:2]):  # Just check first 2 debates
            href = it.get("href")
            title = it.get("title", "No title")
            print(f"\nDEBATE {i+1}: {title}")
            print(f"URL: {href}")
            
            if href:
                deb_url = f"{BASE}{href}.js"
                try:
                    deb = fetch_json(deb_url)
                    print(f"Debate has {len(deb.get('children', []))} child nodes")
                    
                    # Sample the first few speeches
                    stack = deb.get("children", [])[:3]  # Just first 3 for sampling
                    speech_count = 0
                    
                    while stack and speech_count < 3:
                        node = stack.pop(0)
                        stack.extend(node.get("children", [])[:2])  # Limit expansion
                        text = node.get("text") or node.get("body") or ""
                        speaker = (node.get("speaker") or {}).get("name", "")
                        
                        if text and speaker:
                            speech_count += 1
                            print(f"\nSPEECH {speech_count} by {speaker}:")
                            print(f"Length: {len(text)} chars")
                            print(f"First 200 chars: {text[:200]}...")
                            
                            # Check for key terms
                            text_lower = text.lower()
                            has_alien = "alien" in text_lower
                            has_labour = any(term in text_lower for term in ["labour", "labor", "employment", "job", "wage", "work"])
                            print(f"Contains 'alien': {has_alien}")
                            print(f"Contains labour terms: {has_labour}")
                            
                except Exception as e:
                    print(f"Error fetching debate: {e}")
                    
    except Exception as e:
        print(f"Error fetching sitting: {e}")