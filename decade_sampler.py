# decade_sampler.py
# Sample key years from each decade to assess data availability

from simple_collector import SimpleHansardCollector
import sqlite3

def sample_decades():
    """Sample 2-3 key years from each decade"""
    
    # Key years to sample (years with likely debates on immigration/labour)
    sample_years = {
        '1900s': [1902, 1905, 1908],  # Already have 1905
        '1910s': [1912, 1914, 1918], 
        '1920s': [1922, 1925, 1929]
    }
    
    collector = SimpleHansardCollector()
    
    print("=== DECADE SAMPLING ===")
    print("Collecting from key years to assess data availability\n")
    
    for decade, years in sample_years.items():
        print(f"--- {decade} ---")
        for year in years:
            if year == 1905:
                print(f"  {year}: Already collected (7 quotes)")
                continue
                
            print(f"  Collecting {year}...")
            try:
                collector.collect_years(year, year)
                
                # Check what we got
                conn = sqlite3.connect("hansard_simple.db")
                count = conn.execute("SELECT COUNT(*) FROM quotes WHERE year = ?", (year,)).fetchone()[0]
                print(f"    -> {count} quotes collected")
                conn.close()
                
            except Exception as e:
                print(f"    -> Error: {e}")
        print()
    
    collector.close()
    
    # Final summary
    conn = sqlite3.connect("hansard_simple.db")
    
    total = conn.execute("SELECT COUNT(*) FROM quotes").fetchone()[0]
    print(f"=== SAMPLING COMPLETE ===")
    print(f"Total quotes collected: {total}")
    
    # Year breakdown
    years_data = conn.execute("""
        SELECT year, COUNT(*) 
        FROM quotes 
        GROUP BY year 
        ORDER BY year
    """).fetchall()
    
    print("\nYear distribution:")
    for year, count in years_data:
        print(f"  {year}: {count} quotes")
    
    # Frame breakdown
    frames_data = conn.execute("""
        SELECT frame, COUNT(*) 
        FROM quotes 
        GROUP BY frame 
        ORDER BY COUNT(*) DESC
    """).fetchall()
    
    print("\nFrame distribution:")
    for frame, count in frames_data:
        print(f"  {frame}: {count} quotes")
    
    conn.close()

if __name__ == "__main__":
    sample_decades()