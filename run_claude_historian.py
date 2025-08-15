# run_claude_historian.py
# Simple script to run Claude historian with your API key

from claude_historian import ClaudeHistorian

def run_claude_test(api_key):
    """Test Claude with 3 quotes first"""
    print("=== TESTING CLAUDE HISTORIAN ===")
    print("Cost: ~$0.01 for 3 test quotes (much cheaper than OpenAI!)")
    
    historian = ClaudeHistorian(api_key=api_key)
    
    # Test on 3 quotes first
    processed = historian.regenerate_all_analyses(limit=3, start_id=1)
    
    if processed > 0:
        print(f"✅ Success! Processed {processed} quotes")
        
        # Show results
        import sqlite3
        db = sqlite3.connect("database_updated.db")
        examples = db.execute("SELECT id, quote, historian_analysis FROM quotes WHERE id <= 3").fetchall()
        
        print("\n=== CLAUDE ANALYSIS RESULTS ===")
        for quote_id, quote, analysis in examples:
            print(f"Quote {quote_id}: {quote[:80]}...")
            print(f"Claude Analysis: {analysis}")
            print("-" * 70)
        
        db.close()
        
        # Ask about full processing
        print(f"\n💰 CLAUDE COST COMPARISON:")
        print(f"• Claude test (3 quotes): ~$0.01")
        print(f"• Claude full (532 quotes): ~$1.60")
        print(f"• OpenAI would cost: ~$5.32")
        print(f"• 70% CHEAPER than OpenAI!")
        print(f"• Better at historical analysis!")
        
        return True
    else:
        print("❌ Test failed. Check your Claude API key.")
        return False

def run_full_claude_analysis(api_key):
    """Run full Claude analysis on all quotes"""
    print("=== RUNNING FULL CLAUDE ANALYSIS ===")
    print("Processing all 532 quotes...")
    print("Estimated cost: ~$1.60 (70% cheaper than OpenAI!)")
    print("Estimated time: ~5 minutes (faster than OpenAI)")
    
    historian = ClaudeHistorian(api_key=api_key)
    
    # Process all quotes
    total_processed = historian.regenerate_all_analyses()
    
    print(f"✅ Complete! Processed {total_processed} quotes")
    print("Database updated with Claude's superior historical analysis!")
    
    return total_processed

def show_sample_prompt():
    """Show what prompts we send to Claude"""
    historian = ClaudeHistorian()
    
    sample_quote = "The right policy with regard to undesirable aliens is the policy of expulsion. We cannot blame the Australasians for the attitude they have adopted."
    
    prompt = historian.create_claude_prompt(sample_quote, "Sir Kenelm Digby", 1905, "LABOUR_THREAT")
    
    print("=== SAMPLE CLAUDE PROMPT ===")
    print(prompt)
    print("\n" + "="*50)

# Instructions for user
print("""
=== CLAUDE HISTORIAN SETUP ===

To get your Claude API key:
1. Go to: https://console.anthropic.com/
2. Sign up/sign in
3. Get API key (usually starts with 'sk-ant-')

To run:

1. TEST FIRST (recommended):
   python -c "from run_claude_historian import run_claude_test; run_claude_test('sk-ant-your-key-here')"

2. FULL ANALYSIS (after test works):
   python -c "from run_claude_historian import run_full_claude_analysis; run_full_claude_analysis('sk-ant-your-key-here')"

3. SEE SAMPLE PROMPT:
   python -c "from run_claude_historian import show_sample_prompt; show_sample_prompt()"

Claude Benefits:
- 70% cheaper than OpenAI (~$1.60 vs $5.32)
- Better at historical analysis
- Faster processing
- More nuanced understanding
""")

if __name__ == "__main__":
    show_sample_prompt()