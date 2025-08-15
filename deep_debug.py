# deep_debug.py
# Deep debug of the extraction logic step by step

from enhanced_quote_logic import EnhancedQuoteExtractor
import requests
from bs4 import BeautifulSoup
import re

def deep_debug_extraction():
    """Step-by-step debugging of extraction process"""
    print("=== DEEP DEBUG: EXTRACTION STEP BY STEP ===")
    
    # Get Aliens Bill text
    url = "https://api.parliament.uk/historic-hansard/commons/1905/may/02/aliens-bill"
    session = requests.Session()
    session.headers.update({"User-Agent": "HansardResearch/1.0"})
    
    try:
        response = session.get(url, timeout=45)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        full_text = soup.get_text()
        
        print(f"Full text: {len(full_text)} characters")
        
        extractor = EnhancedQuoteExtractor()
        
        # Step 1: Proximity test (we know this passes)
        passes, mig_positions, lab_positions = extractor.precise_proximity_test(full_text)
        print(f"\nStep 1 - Proximity: {'PASS' if passes else 'FAIL'}")
        print(f"  MIG positions: {len(mig_positions)} terms found")
        print(f"  LAB positions: {len(lab_positions)} terms found")
        
        if not passes:
            return
        
        # Step 2: Find tightest hit span
        print(f"\nStep 2 - Finding tightest hit span...")
        
        # Manually debug this function
        tokens = extractor.tokenize_with_positions(full_text)
        print(f"  Tokenized into {len(tokens)} tokens")
        
        # Find some sample MIG-LAB pairs within window
        sample_pairs = []
        for mig_pos in mig_positions[:5]:  # Check first 5
            for lab_pos in lab_positions[:5]:  # Check first 5
                if abs(mig_pos - lab_pos) <= 40:
                    sample_pairs.append((mig_pos, lab_pos))
                    if len(sample_pairs) >= 3:
                        break
            if len(sample_pairs) >= 3:
                break
        
        print(f"  Found {len(sample_pairs)} sample MIG-LAB pairs within 40-token window")
        
        if sample_pairs:
            # Show sample pair
            mig_pos, lab_pos = sample_pairs[0]
            mig_token = tokens[mig_pos][0] if mig_pos < len(tokens) else "?"
            lab_token = tokens[lab_pos][0] if lab_pos < len(tokens) else "?"
            print(f"  Sample pair: MIG '{mig_token}' at {mig_pos}, LAB '{lab_token}' at {lab_pos}")
            
            # Get character positions
            try:
                hit_start, hit_end = extractor.extract_tightest_hit_span(full_text, [mig_pos], [lab_pos])
                print(f"  Tightest span: chars {hit_start}-{hit_end} ({hit_end-hit_start} chars)")
                
                # Step 3: Expand to paragraph boundaries
                para_start, para_end = extractor.find_paragraph_boundaries(full_text, hit_start, hit_end)
                print(f"  Paragraph boundaries: chars {para_start}-{para_end} ({para_end-para_start} chars)")
                
                # Step 4: Extract and clean passage
                passage = full_text[para_start:para_end].strip()
                cleaned_passage = extractor.clean_passage(passage)
                word_count = extractor.count_words(cleaned_passage)
                
                print(f"  Raw passage: {len(passage)} chars")
                print(f"  Cleaned passage: {len(cleaned_passage)} chars, {word_count} words")
                print(f"  Sample text: {cleaned_passage[:200]}...")
                
                # Step 5: Check if passes final proximity test
                final_passes, _, _ = extractor.precise_proximity_test(cleaned_passage)
                print(f"  Final proximity test: {'PASS' if final_passes else 'FAIL'}")
                
                # Step 6: Check word count thresholds
                print(f"\n  Word count analysis:")
                print(f"    {word_count} words - would pass 50+ threshold: {'YES' if word_count >= 50 else 'NO'}")
                print(f"    {word_count} words - would pass 80+ threshold: {'YES' if word_count >= 80 else 'NO'}")
                print(f"    {word_count} words - would pass 150+ threshold: {'YES' if word_count >= 150 else 'NO'}")
                
                if word_count < 80:
                    print(f"\n  ISSUE: Passage too short ({word_count} words)")
                    print(f"  Trying sentence expansion...")
                    
                    # Try sentence expansion manually
                    sentences = extractor.sentence_splitter.split(full_text)
                    print(f"    Split into {len(sentences)} sentences")
                    
                    # Find sentence containing our hit
                    hit_sentence = -1
                    current_pos = 0
                    for i, sentence in enumerate(sentences):
                        sentence_end = current_pos + len(sentence)
                        if current_pos <= hit_start <= sentence_end:
                            hit_sentence = i
                            break
                        current_pos = sentence_end + 1
                    
                    print(f"    Hit found in sentence {hit_sentence}")
                    
                    if hit_sentence >= 0:
                        # Try expanding
                        for window in [3, 5, 7, 9]:
                            start_sent = max(0, hit_sentence - window // 2)
                            end_sent = min(len(sentences), hit_sentence + window // 2 + 1)
                            
                            expanded = '. '.join(sentences[start_sent:end_sent]).strip()
                            expanded_clean = extractor.clean_passage(expanded)
                            expanded_words = extractor.count_words(expanded_clean)
                            
                            print(f"    Window {window}: sentences {start_sent}-{end_sent}, {expanded_words} words")
                            
                            if 80 <= expanded_words <= 450:
                                print(f"    ✅ Window {window} passes word count!")
                                
                                # Check if still passes proximity
                                exp_passes, _, _ = extractor.precise_proximity_test(expanded_clean)
                                print(f"    Proximity test: {'PASS' if exp_passes else 'FAIL'}")
                                
                                if exp_passes:
                                    print(f"    ✅ This should produce a valid quote!")
                                    print(f"    Sample: {expanded_clean[:200]}...")
                                break
                        else:
                            print(f"    ❌ No sentence window produces valid quote")
                
                elif final_passes:
                    print(f"  ✅ This passage should be extracted as a quote!")
                else:
                    print(f"  ❌ Failed final proximity test")
                    
            except Exception as e:
                print(f"  Error in span extraction: {e}")
                import traceback
                traceback.print_exc()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    deep_debug_extraction()