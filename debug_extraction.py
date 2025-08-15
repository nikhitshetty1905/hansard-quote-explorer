# debug_extraction.py
# Debug the enhanced extraction to understand why we get 0 results

from updated_hybrid_collector import UpdatedHybridCollector
from enhanced_quote_logic import EnhancedQuoteExtractor
import requests
from bs4 import BeautifulSoup

def debug_aliens_bill():
    """Debug extraction on the known Aliens Bill text"""
    print("=== DEBUGGING ALIENS BILL EXTRACTION ===")
    
    # Fetch the actual Aliens Bill HTML
    url = "https://api.parliament.uk/historic-hansard/commons/1905/may/02/aliens-bill"
    
    session = requests.Session()
    session.headers.update({"User-Agent": "HansardResearch/1.0"})
    
    try:
        response = session.get(url, timeout=45)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        full_text = soup.get_text()
        
        print(f"Full text length: {len(full_text)} characters")
        
        # Test with enhanced extractor
        extractor = EnhancedQuoteExtractor()
        
        # Step 1: Proximity test
        passes, mig_pos, lab_pos = extractor.precise_proximity_test(full_text)
        print(f"\nStep 1 - Proximity test: {'PASS' if passes else 'FAIL'}")
        print(f"MIG term positions found: {len(mig_pos)}")
        print(f"LAB term positions found: {len(lab_pos)}")
        
        if not passes:
            print("❌ Proximity test failed - no quotes will be extracted")
            
            # Debug: Show actual terms found
            print("\n=== DEBUGGING TERM DETECTION ===")
            
            # Test individual patterns
            for i, pattern in enumerate(extractor.mig_compiled):
                matches = pattern.findall(full_text.lower())
                if matches:
                    print(f"MIG pattern {i} ({pattern.pattern}): {len(matches)} matches")
                    print(f"  Examples: {matches[:5]}")
            
            for i, pattern in enumerate(extractor.lab_compiled):
                matches = pattern.findall(full_text.lower())
                if matches:
                    print(f"LAB pattern {i} ({pattern.pattern}): {len(matches)} matches")
                    print(f"  Examples: {matches[:5]}")
            
            return
        
        # Step 2: Quote extraction
        quotes = extractor.extract_word_based_quotes(full_text)
        print(f"\nStep 2 - Quote extraction: {len(quotes)} quotes found")
        
        if not quotes:
            print("❌ No quotes extracted despite proximity test passing")
            
            # Debug: Try lower word count threshold
            print("\n=== TESTING WITH LOWER THRESHOLDS ===")
            
            # Try 100-450 words instead of 150-450
            quotes_lower = extractor.extract_word_based_quotes(full_text, min_words=100, max_words=450)
            print(f"With 100-450 word threshold: {len(quotes_lower)} quotes")
            
            # Try 50-600 words
            quotes_relaxed = extractor.extract_word_based_quotes(full_text, min_words=50, max_words=600)
            print(f"With 50-600 word threshold: {len(quotes_relaxed)} quotes")
            
            if quotes_relaxed:
                print(f"\n=== SAMPLE RELAXED QUOTE ===")
                sample = quotes_relaxed[0]
                print(f"Word count: {sample['word_count']}")
                print(f"MIG terms: {sample['mig_term_count']}, LAB terms: {sample['lab_term_count']}")
                print(f"Text: {sample['text'][:300]}...")
        
        else:
            print("✅ Quotes successfully extracted!")
            for i, quote in enumerate(quotes):
                print(f"\n--- Quote {i+1} ---")
                print(f"Word count: {quote['word_count']}")
                print(f"MIG terms: {quote['mig_term_count']}, LAB terms: {quote['lab_term_count']}")
                print(f"Method: {quote['extraction_method']}")
                print(f"Preview: {quote['text'][:200]}...")
    
    except Exception as e:
        print(f"Error: {e}")

def compare_with_old_system():
    """Compare results with old character-based system"""
    print("\n=== COMPARING WITH OLD SYSTEM ===")
    
    # Load old results
    try:
        import sqlite3
        old_conn = sqlite3.connect("hansard_demo.db")
        old_quotes = old_conn.execute("""
            SELECT quote, LENGTH(quote) as char_length
            FROM speeches 
            WHERE debate_title LIKE '%ALIENS BILL%'
        """).fetchall()
        
        print(f"Old system found: {len(old_quotes)} quotes")
        
        # Convert to word counts
        extractor = EnhancedQuoteExtractor()
        for i, (quote, char_len) in enumerate(old_quotes):
            word_count = extractor.count_words(quote)
            print(f"  Quote {i+1}: {char_len} chars = {word_count} words")
            
            if word_count < 150:
                print(f"    ❌ Below 150-word threshold")
            else:
                print(f"    ✅ Would pass word count filter")
        
        old_conn.close()
        
    except Exception as e:
        print(f"Error comparing with old system: {e}")

if __name__ == "__main__":
    debug_aliens_bill()
    compare_with_old_system()