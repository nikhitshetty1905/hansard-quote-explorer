# collect_1925_1930.py
# Collect missing years 1925-1930 to complete the dataset

from hybrid_collector import HybridHansardCollector
from enhanced_tagger import EnhancedTagger
import time

def main():
    print("=== COLLECTING MISSING YEARS: 1925-1930 ===")
    print("Completing the dataset to match CLAUDE.md specifications")
    print("Estimated time: 2-3 hours")
    
    # Initialize collector for the missing years
    db_path = "hansard_1925_1930.db"
    print(f"\nInitializing collector... Database: {db_path}")
    collector = HybridHansardCollector(db_path=db_path)
    
    try:
        # Run collection for missing years
        print("Starting collection for 1925-1930...")
        start_time = time.time()
        
        collector.collect_date_range(1925, 1930)
        
        collection_time = time.time() - start_time
        print(f"\n✅ Collection completed in {collection_time/60:.1f} minutes")
        
        # Close collector
        collector.close()
        
        # Run enhanced tagging
        print("\n=== RUNNING FRAME CLASSIFICATION ===")
        tagger = EnhancedTagger(db_path=db_path)
        
        tagging_start = time.time()
        classified_count = tagger.enhance_speeches_with_frames()
        tagging_time = time.time() - tagging_start
        
        print(f"✅ Classification completed in {tagging_time:.1f} seconds")
        print(f"📊 Classified {classified_count} speeches")
        
        if classified_count > 0:
            # Export results
            print("\n=== EXPORTING RESULTS ===")
            export_file = "speeches_1925_1930.jsonl"
            tagger.export_classified_speeches(export_file)
            
            # Show statistics
            tagger.get_frame_statistics()
            
            print(f"\n🎉 SUCCESS! 1925-1930 data collection complete")
            print(f"📁 Database: {db_path}")
            print(f"📄 Export: {export_file}")
            print(f"🔄 Next: Merge with hansard_simple.db to complete 1900-1930 dataset")
            
        else:
            print("\n⚠️  No speeches found for classification in 1925-1930")
            print("This might indicate limited immigration-labour debates in this period")
        
        tagger.close()
        
        # Check what we collected
        import sqlite3
        conn = sqlite3.connect(db_path)
        result = conn.execute('SELECT COUNT(*) FROM quotes').fetchone()
        year_dist = conn.execute('SELECT year, COUNT(*) FROM quotes GROUP BY year ORDER BY year').fetchall()
        conn.close()
        
        print(f"\n📈 COLLECTION SUMMARY:")
        print(f"Total quotes: {result[0]}")
        print("Year distribution:")
        for year, count in year_dist:
            print(f"  {year}: {count} quotes")
        
    except KeyboardInterrupt:
        print("\n\n⏸️  Collection interrupted by user")
        collector.close()
        
    except Exception as e:
        print(f"\n❌ Error during collection: {e}")
        print("Check your internet connection and try again")
        collector.close()

if __name__ == "__main__":
    main()