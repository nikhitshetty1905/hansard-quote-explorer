# find_aliens_dates.py
# Search for dates that actually contain aliens/immigration content

import requests
from bs4 import BeautifulSoup
import re
from datetime import date, timedelta

BASE = "https://api.parliament.uk/historic-hansard"

def fetch_html(url):
    try:
        r = requests.get(url, timeout=30, headers={"User-Agent":"HansardResearch/1.0"})
        r.raise_for_status()
        return r.text
    except:
        return None

def has_immigration_content(html_content):
    """Check if HTML contains immigration/aliens terms"""
    if not html_content:
        return False, []
    
    soup = BeautifulSoup(html_content, 'html.parser')
    full_text = soup.get_text().lower()
    
    # Look for immigration terms
    immigration_terms = ['alien', 'aliens', 'immigration', 'immigrant', 'foreign worker', 'foreign labour']
    found_terms = []
    
    for term in immigration_terms:
        if term in full_text:
            found_terms.append(term)
    
    return len(found_terms) > 0, found_terms

def iter_days(start_date, end_date):
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)

# Search around the Aliens Act period more broadly
start_date = date(1905, 4, 1)
end_date = date(1905, 7, 31)

print("=== SEARCHING FOR IMMIGRATION CONTENT ===")
print(f"Date range: {start_date} to {end_date}")

immigration_dates = []
checked = 0

for d in iter_days(start_date, end_date):
    checked += 1
    if checked % 10 == 0:
        print(f"Checked {checked} days, found {len(immigration_dates)} with immigration content")
    
    # Check both Commons and Lords
    for house in ['commons', 'lords']:
        url = f"{BASE}/{house}/{d.year}/{d.strftime('%b').lower()}/{d.day}"
        html_content = fetch_html(url)
        
        if html_content:
            has_content, terms = has_immigration_content(html_content)
            if has_content:
                immigration_dates.append({
                    'date': d.isoformat(),
                    'house': house,
                    'terms': terms,
                    'url': url
                })
                print(f"  FOUND: {d.isoformat()} {house} - Terms: {terms}")

print(f"\n=== RESULTS ===")
print(f"Checked {checked} days")
print(f"Found {len(immigration_dates)} sittings with immigration content")

if immigration_dates:
    print("\n=== DATES WITH IMMIGRATION CONTENT ===")
    for entry in immigration_dates[:10]:  # Show first 10
        print(f"{entry['date']} {entry['house']}: {entry['terms']}")
    
    # Test our parser on the first date with content
    test_entry = immigration_dates[0]
    print(f"\n=== TESTING PARSER ON {test_entry['date']} ===")
    
    test_html = fetch_html(test_entry['url'])
    if test_html:
        soup = BeautifulSoup(test_html, 'html.parser')
        full_text = soup.get_text()
        
        # Look for both immigration AND labour terms
        mig_matches = re.findall(r"alien[s]?|immigration|immigrant[s]?|foreign.*(?:worker[s]?|labour)", full_text.lower())
        lab_matches = re.findall(r"labour|labor|employment|wage[s]?|job[s]?|work", full_text.lower())
        
        print(f"Migration terms: {mig_matches[:5]}")
        print(f"Labour terms: {lab_matches[:5]}")
        
        # Test proximity
        from debug_sections import proximity_hit
        if proximity_hit(full_text):
            print("*** PROXIMITY MATCH FOUND ***")
        else:
            print("No proximity match in full text")
    
else:
    print("No dates with immigration content found!")
    print("This suggests:")
    print("1. The search terms might be wrong for this period")
    print("2. The dates might be outside the 1905 range")
    print("3. The content might be structured differently")