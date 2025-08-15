# check_real_data.py
# Check what real data was collected vs sample data

import sqlite3

# Connect to database
conn = sqlite3.connect("hansard_simple.db")

# Get all quotes
all_quotes = conn.execute("""
    SELECT year, date, speaker, frame, quote, hansard_url
    FROM quotes 
    ORDER BY year, date
""").fetchall()

print("=== ALL QUOTES IN DATABASE ===")
print(f"Total: {len(all_quotes)} quotes\n")

for i, (year, date, speaker, frame, quote, url) in enumerate(all_quotes, 1):
    print(f"Quote {i}:")
    print(f"  Date: {date}")
    print(f"  Speaker: {speaker}")
    print(f"  Frame: {frame}")
    print(f"  URL: {url}")
    print(f"  Quote: {quote[:100]}...")
    print(f"  Full length: {len(quote)} characters")
    
    # Check if URL actually exists
    import requests
    try:
        response = requests.head(url, timeout=10)
        url_status = f"HTTP {response.status_code}"
    except:
        url_status = "UNREACHABLE"
    
    print(f"  URL status: {url_status}")
    print()

conn.close()

print("=== ANALYSIS ===")
print("Sample/fake quotes will have URLs that don't exist or return 404.")
print("Real quotes should have working URLs to actual Hansard pages.")