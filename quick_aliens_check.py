# quick_aliens_check.py
# Quick check of specific historical dates for aliens content

import requests
from bs4 import BeautifulSoup
import re
from datetime import date

BASE = "https://api.parliament.uk/historic-hansard"

def fetch_html(url):
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent":"HansardResearch/1.0"})
        r.raise_for_status()
        return r.text
    except Exception as e:
        return None

# Historical dates around the Aliens Act 1905
# The Aliens Act 1905 received Royal Assent on August 11, 1905
# Major debates would have been in spring/summer 1905

test_dates = [
    date(1905, 5, 2),   # We know from our original data this had ALIENS BILL content
    date(1905, 5, 4),   # We know this had content too
    date(1905, 5, 8),   
    date(1905, 5, 15),  
    date(1905, 5, 22),
    date(1905, 6, 5),
    date(1905, 6, 12),
    date(1905, 6, 19),
    date(1905, 7, 10),
    date(1905, 7, 24),
]

print("=== QUICK CHECK FOR ALIENS CONTENT ===")

found_dates = []

for d in test_dates:
    print(f"\nChecking {d.isoformat()}...")
    
    # Check Commons
    url = f"{BASE}/commons/{d.year}/{d.strftime('%b').lower()}/{d.day}"
    html_content = fetch_html(url)
    
    if html_content:
        # Quick text search
        text_lower = html_content.lower()
        has_alien = 'alien' in text_lower
        has_aliens = 'aliens' in text_lower
        has_immigration = 'immigration' in text_lower
        has_labour = any(term in text_lower for term in ['labour', 'labor', 'employment', 'job', 'wage'])
        
        print(f"  Commons: alien={has_alien}, aliens={has_aliens}, immigration={has_immigration}, labour={has_labour}")
        
        if (has_alien or has_aliens or has_immigration) and has_labour:
            print(f"  *** POTENTIAL MATCH ***")
            found_dates.append({
                'date': d.isoformat(),
                'house': 'commons',
                'url': url
            })
            
            # Show some context
            if has_aliens:
                # Find aliens context
                for match in re.finditer(r'aliens?', text_lower):
                    start = max(0, match.start() - 50)
                    end = min(len(html_content), match.end() + 50)
                    context = html_content[start:end]
                    try:
                        clean_context = context.encode('ascii', 'replace').decode('ascii')
                        print(f"    Context: ...{clean_context}...")
                        break  # Just show first match
                    except:
                        pass
    else:
        print(f"  Commons: No data")

print(f"\n=== SUMMARY ===")
print(f"Found {len(found_dates)} dates with potential immigration+labour content")

if found_dates:
    print("\nDates to test:")
    for entry in found_dates:
        print(f"  {entry['date']} {entry['house']}")
    
    # Test the first one more thoroughly
    test_date = found_dates[0]
    print(f"\n=== DETAILED TEST: {test_date['date']} ===")
    
    html_content = fetch_html(test_date['url'])
    if html_content:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for section titles that might contain aliens content
        section_links = soup.find_all('span', class_='section-link')
        print(f"Found {len(section_links)} section links")
        
        for i, link in enumerate(section_links):
            link_text = link.get_text().lower()
            if 'alien' in link_text:
                print(f"  Section {i+1}: {link.get_text()}")
                
                # Check if this section link has a parent <a> with href
                parent_a = link.find_parent('a')
                if parent_a:
                    href = parent_a.get('href')
                    if href:
                        section_url = f"{BASE}{href}" if href.startswith('/') else f"{BASE}/{href}"
                        print(f"    URL: {section_url}")
                        
                        # Try to fetch this specific section
                        try:
                            section_html = fetch_html(section_url)
                            if section_html:
                                print(f"    SUCCESS: {len(section_html)} chars")
                                
                                # Quick check for labour terms
                                if any(term in section_html.lower() for term in ['labour', 'employment', 'job', 'wage']):
                                    print(f"    *** CONTAINS LABOUR TERMS ***")
                        except:
                            print(f"    Failed to fetch section")
else:
    print("No promising dates found in the test set")
    print("Try expanding the search or checking different terms")