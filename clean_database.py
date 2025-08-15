# clean_database.py
# Remove sample data, keep only real collected quotes

import sqlite3
import requests

def check_url_real(url):
    """Check if URL returns real content (HTTP 200)"""
    try:
        response = requests.head(url, timeout=10)
        return response.status_code == 200
    except:
        return False

# Connect to database
conn = sqlite3.connect("hansard_simple.db")

# Get all quotes with their IDs
all_quotes = conn.execute("""
    SELECT id, hansard_url, speaker, date 
    FROM quotes 
""").fetchall()

print("=== CLEANING DATABASE ===")
print("Checking which quotes have real Hansard URLs...\n")

real_quotes = []
fake_quotes = []

for quote_id, url, speaker, date in all_quotes:
    if check_url_real(url):
        real_quotes.append((quote_id, speaker, date))
        print(f"REAL: {speaker} ({date})")
    else:
        fake_quotes.append((quote_id, speaker, date))
        print(f"FAKE: {speaker} ({date})")

print(f"\nFound {len(real_quotes)} real quotes, {len(fake_quotes)} fake quotes")

# Remove fake quotes
if fake_quotes:
    fake_ids = [str(quote_id) for quote_id, _, _ in fake_quotes]
    conn.execute(f"DELETE FROM quotes WHERE id IN ({','.join(fake_ids)})")
    conn.commit()
    print(f"Removed {len(fake_quotes)} fake quotes")

# Show final clean data
remaining = conn.execute("SELECT COUNT(*) FROM quotes").fetchone()[0]
print(f"Database now contains {remaining} real quotes")

# Show frame distribution of real data
frames = conn.execute("""
    SELECT frame, COUNT(*) 
    FROM quotes 
    GROUP BY frame 
    ORDER BY COUNT(*) DESC
""").fetchall()

print(f"\nReal quote frames:")
for frame, count in frames:
    print(f"  {frame}: {count}")

conn.close()
print(f"\nDatabase cleaned - only real Hansard quotes remain")