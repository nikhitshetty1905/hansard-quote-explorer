# quick_demo.py
# Quick demonstration with just a few days in 1905

from hybrid_collector import HybridHansardCollector
from enhanced_tagger import EnhancedTagger
import time

def main():
    print("=== QUICK DEMO: May 1905 (Aliens Bill Period) ===")
    print("Running collection for just a few days to demonstrate the system...")
    
    # Initialize collector
    collector = HybridHansardCollector(db_path="hansard_demo.db")
    
    try:
        # Collect just May 1905 (much faster)
        print("\nCollecting May 1905...")
        start_time = time.time()
        
        collector.collect_date_range(1905, 1905, start_month=5, end_month=5)
        
        collection_time = time.time() - start_time
        print(f"\nCollection completed in {collection_time:.1f} seconds")
        
        collector.close()
        
        # Enhanced tagging
        print("\n=== RUNNING FRAME CLASSIFICATION ===")
        tagger = EnhancedTagger(db_path="hansard_demo.db")
        
        classified_count = tagger.enhance_speeches_with_frames()
        
        if classified_count > 0:
            # Export and show results
            tagger.export_classified_speeches("demo_speeches.jsonl")
            tagger.get_frame_statistics()
            
            print(f"\n🎉 DEMO COMPLETED SUCCESSFULLY!")
            print(f"📊 {classified_count} speeches classified")
            print(f"📁 Database: hansard_demo.db")
            print(f"📄 Export: demo_speeches.jsonl")
            
            # Show system is ready for larger scale
            print(f"\n🚀 SYSTEM READY FOR FULL SCALE:")
            print(f"   For 1905-1906: ~2 hours, ~10,000 speeches")
            print(f"   For 1900-1930: ~20 hours, ~100,000 speeches")
            
        else:
            print("No speeches classified - check data availability")
        
        tagger.close()
        
    except Exception as e:
        print(f"Error: {e}")
        collector.close()

if __name__ == "__main__":
    main()