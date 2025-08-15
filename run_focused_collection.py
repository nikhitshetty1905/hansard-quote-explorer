# run_focused_collection.py
# Run focused collection for 1905-1906 automatically

from hybrid_collector import HybridHansardCollector
from enhanced_tagger import EnhancedTagger
import time

def main():
    print("=== RUNNING FOCUSED COLLECTION: 1905-1906 ===")
    print("Collecting key immigration debates including the Aliens Act")
    print("Estimated time: 30-60 minutes")
    print("Expected output: 5,000-10,000 speeches")
    
    # Initialize collector
    print("\nInitializing hybrid collector...")
    collector = HybridHansardCollector(db_path="hansard_production.db")
    
    try:
        # Run collection
        print("Starting collection...")
        start_time = time.time()
        
        collector.collect_date_range(1905, 1906)
        
        collection_time = time.time() - start_time
        print(f"\n✅ Collection completed in {collection_time/60:.1f} minutes")
        
        # Close collector
        collector.close()
        
        # Run enhanced tagging
        print("\n=== RUNNING FRAME CLASSIFICATION ===")
        tagger = EnhancedTagger(db_path="hansard_production.db")
        
        tagging_start = time.time()
        classified_count = tagger.enhance_speeches_with_frames()
        tagging_time = time.time() - tagging_start
        
        print(f"✅ Classification completed in {tagging_time:.1f} seconds")
        
        if classified_count > 0:
            # Export results
            print("\n=== EXPORTING RESULTS ===")
            tagger.export_classified_speeches("production_speeches.jsonl")
            
            # Show detailed statistics
            tagger.get_frame_statistics()
            
            print(f"\n🎉 SUCCESS! System ready for exploration")
            print(f"📁 Database: hansard_production.db")
            print(f"📄 Export: production_speeches.jsonl") 
            print(f"🌐 Explorer: streamlit run enhanced_explorer.py")
            
        else:
            print("\n⚠️  No speeches found for classification")
            print("This might indicate:")
            print("  - No relevant debates in this period")
            print("  - Connection issues")
            print("  - Need to adjust search terms")
        
        tagger.close()
        
    except KeyboardInterrupt:
        print("\n\n⏸️  Collection interrupted by user")
        collector.close()
        
    except Exception as e:
        print(f"\n❌ Error during collection: {e}")
        print("Check your internet connection and try again")
        collector.close()

if __name__ == "__main__":
    main()