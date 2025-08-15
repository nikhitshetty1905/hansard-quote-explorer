# run_openai_historian.py
# Simple script to run OpenAI historian with your API key

from openai_historian import OpenAIHistorian

def run_test_analysis(api_key):
    """Test OpenAI with 3 quotes first"""
    print("=== TESTING OPENAI HISTORIAN ===")
    print("Cost: ~$0.03 for 3 test quotes")
    
    historian = OpenAIHistorian(api_key=api_key)
    
    # Test on 3 quotes first
    processed = historian.regenerate_all_analyses(limit=3, start_id=1)
    
    if processed > 0:
        print(f"✅ Success! Processed {processed} quotes")
        
        # Show results
        import sqlite3
        db = sqlite3.connect("database_updated.db")
        examples = db.execute("SELECT id, quote, historian_analysis FROM quotes WHERE id <= 3").fetchall()
        
        print("\n=== OPENAI ANALYSIS RESULTS ===")
        for quote_id, quote, analysis in examples:
            print(f"Quote {quote_id}: {quote[:80]}...")
            print(f"AI Analysis: {analysis}")
            print("-" * 60)
        
        db.close()
        
        # Ask about full processing
        print(f"\n💰 COST ESTIMATE:")
        print(f"• Test (3 quotes): ~$0.03")
        print(f"• Full analysis (532 quotes): ~$5.32")
        print(f"• Much better than current generic analysis!")
        
        return True
    else:
        print("❌ Test failed. Check your API key.")
        return False

def run_full_analysis(api_key):
    """Run full OpenAI analysis on all quotes"""
    print("=== RUNNING FULL OPENAI ANALYSIS ===")
    print("Processing all 532 quotes...")
    print("Estimated cost: ~$5.32")
    print("Estimated time: ~10 minutes (rate limiting)")
    
    historian = OpenAIHistorian(api_key=api_key)
    
    # Process all quotes
    total_processed = historian.regenerate_all_analyses()
    
    print(f"✅ Complete! Processed {total_processed} quotes")
    print("Database updated with AI-powered historical analysis!")
    
    return total_processed

# Instructions for user
print("""
=== OPENAI HISTORIAN SETUP ===

To run this with your API key:

1. TEST FIRST (recommended):
   python -c "from run_openai_historian import run_test_analysis; run_test_analysis('sk-your-api-key-here')"

2. FULL ANALYSIS (after test works):
   python -c "from run_openai_historian import run_full_analysis; run_full_analysis('sk-your-api-key-here')"

Replace 'sk-your-api-key-here' with your actual OpenAI API key.
""")

if __name__ == "__main__":
    print("Please run with your API key as shown above.")