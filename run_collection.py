# run_collection.py
# Run the hybrid collection system for a specific date range

from hybrid_collector import HybridHansardCollector
from enhanced_tagger import EnhancedTagger
import time

def run_focused_collection():
    """Run collection for a focused period (1905-1906) to demonstrate the system"""
    
    print("=== RUNNING FOCUSED COLLECTION: 1905-1906 ===")
    print("This period includes major immigration debates like the Aliens Act")
    
    # Initialize collector
    collector = HybridHansardCollector(db_path="hansard_production.db")
    
    try:
        # Collect 1905-1906 (key Aliens Act period)
        start_time = time.time()
        collector.collect_date_range(1905, 1906)
        collection_time = time.time() - start_time
        
        print(f"\nCollection completed in {collection_time/60:.1f} minutes")
        
        # Close collector
        collector.close()
        
        # Run enhanced tagging
        print("\n=== RUNNING ENHANCED TAGGING ===")
        tagger = EnhancedTagger(db_path="hansard_production.db")
        
        start_time = time.time()
        classified_count = tagger.enhance_speeches_with_frames()
        tagging_time = time.time() - start_time
        
        print(f"Tagging completed in {tagging_time:.1f} seconds")
        
        if classified_count > 0:
            # Export results
            tagger.export_classified_speeches("production_speeches.jsonl")
            
            # Show statistics
            tagger.get_frame_statistics()
        
        tagger.close()
        
        print(f"\n=== COLLECTION SUMMARY ===")
        print(f"✅ Collected and classified speeches from 1905-1906")
        print(f"✅ Database: hansard_production.db")
        print(f"✅ Export: production_speeches.jsonl")
        print(f"✅ Ready to explore with: streamlit run enhanced_explorer.py")
        
        return True
        
    except Exception as e:
        print(f"Error during collection: {e}")
        collector.close()
        return False

def run_expanded_collection():
    """Run collection for broader range (1903-1907) around the Aliens Act"""
    
    print("=== RUNNING EXPANDED COLLECTION: 1903-1907 ===")
    print("This covers the full Aliens Act debate period")
    
    collector = HybridHansardCollector(db_path="hansard_expanded.db")
    
    try:
        start_time = time.time()
        collector.collect_date_range(1903, 1907)
        collection_time = time.time() - start_time
        
        print(f"\nExpanded collection completed in {collection_time/60:.1f} minutes")
        
        collector.close()
        
        # Enhanced tagging
        tagger = EnhancedTagger(db_path="hansard_expanded.db")
        classified_count = tagger.enhance_speeches_with_frames()
        
        if classified_count > 0:
            tagger.export_classified_speeches("expanded_speeches.jsonl")
            tagger.get_frame_statistics()
        
        tagger.close()
        return True
        
    except Exception as e:
        print(f"Error during expanded collection: {e}")
        collector.close()
        return False

if __name__ == "__main__":
    print("HANSARD COLLECTION RUNNER")
    print("=" * 50)
    
    # Ask user which collection to run
    print("\nOptions:")
    print("1. Focused Collection (1905-1906) - ~2 hours, ~5,000-10,000 speeches")
    print("2. Expanded Collection (1903-1907) - ~8 hours, ~20,000-30,000 speeches")
    print("3. Custom date range")
    
    choice = input("\nEnter choice (1, 2, or 3): ").strip()
    
    if choice == "1":
        success = run_focused_collection()
    
    elif choice == "2":
        confirm = input("This will take ~8 hours. Continue? (y/N): ").strip().lower()
        if confirm == 'y':
            success = run_expanded_collection()
        else:
            print("Cancelled.")
            success = False
    
    elif choice == "3":
        try:
            start_year = int(input("Start year (1900-1930): "))
            end_year = int(input("End year (1900-1930): "))
            
            if 1900 <= start_year <= end_year <= 1930:
                db_name = f"hansard_{start_year}_{end_year}.db"
                collector = HybridHansardCollector(db_path=db_name)
                
                print(f"\nRunning custom collection: {start_year}-{end_year}")
                start_time = time.time()
                collector.collect_date_range(start_year, end_year)
                collection_time = time.time() - start_time
                
                collector.close()
                
                # Tag and export
                tagger = EnhancedTagger(db_path=db_name)
                classified_count = tagger.enhance_speeches_with_frames()
                
                if classified_count > 0:
                    tagger.export_classified_speeches(f"speeches_{start_year}_{end_year}.jsonl")
                    tagger.get_frame_statistics()
                
                tagger.close()
                
                print(f"\nCustom collection completed in {collection_time/60:.1f} minutes")
                success = True
            else:
                print("Invalid year range. Must be 1900-1930.")
                success = False
                
        except ValueError:
            print("Invalid input. Please enter numbers.")
            success = False
    
    else:
        print("Invalid choice.")
        success = False
    
    if success:
        print(f"\n🎉 Collection completed successfully!")
        print(f"📊 View results with: streamlit run enhanced_explorer.py")
    else:
        print(f"\n❌ Collection failed or cancelled.")