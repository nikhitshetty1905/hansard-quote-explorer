# debug_1908.py
# Debug why 1908 May 5 didn't yield quotes despite having both terms

from fixed_collector import FixedHansardCollector

def debug_specific_date():
    collector = FixedHansardCollector()
    
    # Test the specific date that should have worked
    url = "https://api.parliament.uk/historic-hansard/commons/1908/may/05"
    
    print(f"=== Debugging {url} ===")
    
    try:
        response = collector.session.get(url, timeout=10)
        if response.status_code != 200:
            print(f"Failed to get content: {response.status_code}")
            return
        
        print(f"Got content: {len(response.text)} chars")
        
        # Extract passages
        passages = collector.extract_passages(response.text)
        print(f"Extracted {len(passages)} passages")
        
        proximity_passed = 0
        for i, passage in enumerate(passages[:10]):  # Check first 10
            word_count = len(passage['text'].split())
            
            # Check individual terms
            has_imm = bool(collector.immigration_terms.search(passage['text']))
            has_lab = bool(collector.labour_terms.search(passage['text']))
            has_proximity = collector.check_proximity(passage['text'])
            
            if has_imm or has_lab:
                print(f"\nPassage {i+1} ({word_count} words):")
                print(f"  Immigration terms: {has_imm}")
                print(f"  Labour terms: {has_lab}")
                print(f"  Proximity passed: {has_proximity}")
                print(f"  Speaker: {passage['speaker']}")
                print(f"  Preview: {passage['text'][:150]}...")
                
                if has_proximity:
                    proximity_passed += 1
        
        print(f"\nSummary: {proximity_passed} passages passed proximity test")
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        collector.close()

if __name__ == "__main__":
    debug_specific_date()