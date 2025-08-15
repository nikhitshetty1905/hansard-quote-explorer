# fixed_quote_logic.py
# Fixed version of the enhanced quote logic with proper token matching

import re
from typing import List, Tuple, Dict, Optional

class FixedQuoteExtractor:
    def __init__(self):
        # Immigration terms (MIG)
        self.mig_patterns = [
            r'immig(?:rant|ration)s?',
            r'migrants?', 
            r'aliens?',
            r'foreigners?',
            r'colonial',
            r'alien\s+poor',
            r'undesirable\s+aliens?'
        ]
        
        # Labour economics terms (LAB) - excluding bare "Labour" party references
        self.lab_patterns = [
            r'labou?r(?!\s+(?:party|member|government|leader|bench))',  # Exclude party refs
            r'wages?',
            r'employ(?:ment|ed|er|ers|ees?)?',
            r'jobs?',
            r'unemploy(?:ed|ment)?',
            r'workforce',
            r'strikes?',
            r'unions?',
            r'man-?power',
            r'dilution',
            r'sweated\s+labou?r',
            r'workers?',
            r'industrial\s+(?:action|dispute|unrest)'
        ]
        
        # Compile patterns for speed - note: no word boundaries in individual patterns
        self.mig_compiled = [re.compile(pattern, re.IGNORECASE) for pattern in self.mig_patterns]
        self.lab_compiled = [re.compile(pattern, re.IGNORECASE) for pattern in self.lab_patterns]
        
        # Combined patterns for full-text search (with word boundaries)
        self.mig_combined = re.compile(r'\b(?:' + '|'.join(self.mig_patterns) + r')\b', re.IGNORECASE)
        self.lab_combined = re.compile(r'\b(?:' + '|'.join(self.lab_patterns) + r')\b', re.IGNORECASE)
        
        # Text processing patterns
        self.sentence_splitter = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')
        self.paragraph_splitter = re.compile(r'\n\s*\n')
        self.word_tokenizer = re.compile(r'\b\w+\b')
        
        # Procedural noise patterns
        self.noise_patterns = [
            re.compile(r'\b(?:hear,?\s*hear|division|question\s+put|order,?\s*order)\b', re.IGNORECASE),
            re.compile(r'\[(?:interruption|laughter|cheers|cries|hon\.\s*members?)\]', re.IGNORECASE),
            re.compile(r'\b(?:mr\.?\s+speaker|madam\s+speaker)\b', re.IGNORECASE)
        ]

    def tokenize_text(self, text: str) -> List[str]:
        """Simple word tokenization"""
        return self.word_tokenizer.findall(text.lower())

    def find_term_positions_fixed(self, text: str) -> Tuple[List[int], List[int]]:
        """
        Fixed version: Find word positions of MIG and LAB terms
        Returns (mig_positions, lab_positions) as word indices
        """
        words = self.tokenize_text(text)
        
        mig_positions = []
        lab_positions = []
        
        # Check each word position
        for i, word in enumerate(words):
            # Check if this word matches any MIG pattern
            for pattern in self.mig_compiled:
                if pattern.search(word):
                    mig_positions.append(i)
                    break
            
            # Check if this word matches any LAB pattern  
            for pattern in self.lab_compiled:
                if pattern.search(word):
                    lab_positions.append(i)
                    break
        
        return mig_positions, lab_positions

    def precise_proximity_test(self, text: str, window_tokens: int = 40) -> Tuple[bool, List[int], List[int]]:
        """
        Fixed proximity test using proper tokenization
        """
        mig_positions, lab_positions = self.find_term_positions_fixed(text)
        
        # Check if any MIG-LAB pair is within window
        passes = False
        if mig_positions and lab_positions:
            for mig_pos in mig_positions:
                for lab_pos in lab_positions:
                    if abs(mig_pos - lab_pos) <= window_tokens:
                        passes = True
                        break
                if passes:
                    break
        
        return passes, mig_positions, lab_positions

    def extract_passage_around_terms(self, text: str, mig_positions: List[int], lab_positions: List[int], 
                                   min_words: int = 80, max_words: int = 450) -> List[Dict]:
        """
        Extract passages around MIG-LAB term pairs
        """
        words = self.tokenize_text(text)
        quotes = []
        
        # Find best MIG-LAB pairs (closest together)
        best_pairs = []
        for mig_pos in mig_positions:
            for lab_pos in lab_positions:
                distance = abs(mig_pos - lab_pos)
                if distance <= 40:  # Within proximity window
                    best_pairs.append((mig_pos, lab_pos, distance))
        
        # Sort by distance (closest first)
        best_pairs.sort(key=lambda x: x[2])
        
        # Extract passages around best pairs
        used_ranges = []  # Track used word ranges to avoid overlaps
        
        for mig_pos, lab_pos, distance in best_pairs[:5]:  # Max 5 quotes
            # Find word range around this pair
            center = (mig_pos + lab_pos) // 2
            
            # Try different window sizes
            for half_window in [40, 60, 80, 120]:  # Different passage sizes
                start_word = max(0, center - half_window)
                end_word = min(len(words), center + half_window)
                
                passage_words = words[start_word:end_word]
                word_count = len(passage_words)
                
                if min_words <= word_count <= max_words:
                    # Check for overlap with existing passages
                    overlap = False
                    for used_start, used_end in used_ranges:
                        if not (end_word <= used_start or start_word >= used_end):
                            overlap = True
                            break
                    
                    if not overlap:
                        # Reconstruct passage from words
                        passage_text = ' '.join(passage_words)
                        
                        # Clean passage
                        cleaned_passage = self.clean_passage_fixed(passage_text)
                        
                        # Verify still passes proximity test
                        passes, final_mig, final_lab = self.precise_proximity_test(cleaned_passage)
                        
                        if passes:
                            quotes.append({
                                'text': cleaned_passage,
                                'word_count': len(cleaned_passage.split()),
                                'mig_term_count': len(final_mig),
                                'lab_term_count': len(final_lab),
                                'start_word': start_word,
                                'end_word': end_word,
                                'extraction_method': 'word_window',
                                'mig_pos': mig_pos,
                                'lab_pos': lab_pos,
                                'distance': distance
                            })
                            
                            used_ranges.append((start_word, end_word))
                            break  # Found good quote for this pair
        
        return quotes

    def clean_passage_fixed(self, text: str) -> str:
        """Clean passage text"""
        cleaned = text
        for noise_pattern in self.noise_patterns:
            cleaned = noise_pattern.sub('', cleaned)
        
        # Clean up extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Ensure proper sentence structure
        cleaned = re.sub(r'([.!?])\s*([a-z])', r'\1 \2'.title(), cleaned)
        
        return cleaned

    def extract_word_based_quotes(self, text: str, min_words: int = 80, max_words: int = 450) -> List[Dict]:
        """
        Main extraction method using fixed logic
        """
        # First check proximity
        passes, mig_positions, lab_positions = self.precise_proximity_test(text)
        
        if not passes:
            return []
        
        # Extract passages around term pairs
        quotes = self.extract_passage_around_terms(text, mig_positions, lab_positions, 
                                                 min_words, max_words)
        
        return quotes

    def test_fixed_logic(self, text: str):
        """Test the fixed extraction logic"""
        print("=== TESTING FIXED EXTRACTION LOGIC ===")
        print(f"Input text: {len(text)} characters, {len(text.split())} words")
        
        # Test proximity
        passes, mig_pos, lab_pos = self.precise_proximity_test(text)
        print(f"\nProximity test: {'PASS' if passes else 'FAIL'}")
        print(f"MIG positions: {len(mig_pos)} found - {mig_pos[:10]}...")
        print(f"LAB positions: {len(lab_pos)} found - {lab_pos[:10]}...")
        
        if passes:
            # Show sample nearby pairs
            nearby_pairs = []
            for m in mig_pos[:5]:
                for l in lab_pos[:5]:
                    if abs(m - l) <= 40:
                        nearby_pairs.append((m, l, abs(m - l)))
            
            nearby_pairs.sort(key=lambda x: x[2])
            print(f"Sample nearby pairs: {nearby_pairs[:3]}")
            
            # Extract quotes
            quotes = self.extract_word_based_quotes(text, min_words=80, max_words=450)
            print(f"\nExtracted {len(quotes)} quotes:")
            
            for i, quote in enumerate(quotes):
                print(f"\n--- Quote {i+1} ---")
                print(f"Word count: {quote['word_count']}")
                print(f"Terms: {quote['mig_term_count']} MIG, {quote['lab_term_count']} LAB")
                print(f"Distance: {quote['distance']} tokens")
                print(f"Method: {quote['extraction_method']}")
                print(f"Text: {quote['text'][:200]}...")
        
        return quotes if passes else []

# Test the fixed logic
if __name__ == "__main__":
    import requests
    from bs4 import BeautifulSoup
    
    extractor = FixedQuoteExtractor()
    
    # Test with Aliens Bill
    url = "https://api.parliament.uk/historic-hansard/commons/1905/may/02/aliens-bill"
    session = requests.Session()
    session.headers.update({"User-Agent": "HansardResearch/1.0"})
    
    try:
        response = session.get(url, timeout=45)
        soup = BeautifulSoup(response.text, 'html.parser')
        full_text = soup.get_text()
        
        quotes = extractor.test_fixed_logic(full_text)
        
        print(f"\n=== RESULTS SUMMARY ===")
        print(f"Successfully extracted {len(quotes)} quotes using fixed logic")
        
        if quotes:
            avg_words = sum(q['word_count'] for q in quotes) / len(quotes)
            print(f"Average quote length: {avg_words:.0f} words")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()