# run_robust_1925_1930.py
# Use the final_robust_collector for 1925-1930

from final_robust_collector import RobustHansardCollector

def main():
    print("=== USING ROBUST COLLECTOR FOR 1925-1930 ===")
    
    # Initialize the robust collector
    collector = RobustHansardCollector(db_path="hansard_1925_1930_robust.db")
    
    try:
        # Run collection for 1925-1930
        collector.collect_years(1925, 1930)
        
        # Close collector
        collector.close()
        
        print("\n✅ Robust collection completed!")
        
        # Check results
        import sqlite3
        conn = sqlite3.connect("hansard_1925_1930_robust.db")
        result = conn.execute('SELECT COUNT(*) FROM quotes').fetchone()
        year_dist = conn.execute('SELECT year, COUNT(*) FROM quotes GROUP BY year ORDER BY year').fetchall()
        conn.close()
        
        print(f"\n📈 RESULTS:")
        print(f"Total quotes: {result[0]}")
        print("Year distribution:")
        for year, count in year_dist:
            print(f"  {year}: {count} quotes")
            
    except Exception as e:
        print(f"Error: {e}")
        collector.close()

if __name__ == "__main__":
    main()