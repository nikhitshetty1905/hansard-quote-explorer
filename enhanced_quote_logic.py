# enhanced_quote_logic.py
# Phase 1: Core logic fixes - word-based filtering + precise token-window proximity

import re
from typing import List, Tuple, Dict, Optional

class EnhancedQuoteExtractor:
    def __init__(self):
        # Immigration terms (MIG)
        self.mig_patterns = [
            r'\bimmig(?:rant|ration)s?\b',
            r'\bmigrants?\b', 
            r'\baliens?\b',
            r'\bforeigners?\b',
            r'\bcolonial\b',
            r'\balien\s+poor\b',
            r'\bundesirable\s+aliens?\b'
        ]
        
        # Labour economics terms (LAB) - excluding bare "Labour" party references
        self.lab_patterns = [
            r'\blabou?r(?!\s+(?:party|member|government|leader|bench))\b',  # Exclude party refs
            r'\bwages?\b',
            r'\bemploy(?:ment|ed|er|ers|ees?)?\b',
            r'\bjobs?\b',
            r'\bunemploy(?:ed|ment)?\b',
            r'\bworkforce\b',
            r'\bstrikes?\b',
            r'\bunions?\b',
            r'\bman-?power\b',
            r'\bdilution\b',
            r'\bsweated\s+labou?r\b',
            r'\bworkers?\b',
            r'\bindustrial\s+(?:action|dispute|unrest)\b'
        ]
        
        # Compile patterns for speed
        self.mig_compiled = [re.compile(pattern, re.IGNORECASE) for pattern in self.mig_patterns]
        self.lab_compiled = [re.compile(pattern, re.IGNORECASE) for pattern in self.lab_patterns]
        
        # Text processing patterns
        self.sentence_splitter = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')
        self.paragraph_splitter = re.compile(r'\n\s*\n')
        self.word_splitter = re.compile(r'\b\w+\b')
        
        # Procedural noise patterns to strip
        self.noise_patterns = [
            re.compile(r'\b(?:hear,?\s*hear|division|question\s+put|order,?\s*order)\b', re.IGNORECASE),
            re.compile(r'\[(?:interruption|laughter|cheers|cries|hon\.\s*members?)\]', re.IGNORECASE),
            re.compile(r'\b(?:mr\.?\s+speaker|madam\s+speaker)\b', re.IGNORECASE)
        ]

    def tokenize_with_positions(self, text: str) -> List[Tuple[str, int, int]]:
        """Tokenize text and return (token, start_pos, end_pos) tuples"""
        tokens = []
        for match in self.word_splitter.finditer(text.lower()):
            tokens.append((match.group(), match.start(), match.end()))
        return tokens

    def find_term_positions(self, tokens: List[Tuple[str, int, int]], patterns: List[re.Pattern]) -> List[int]:
        """Find token positions where any pattern matches"""
        positions = []
        for i, (token, start, end) in enumerate(tokens):
            # Check if any pattern matches at this position in original text
            text_fragment = token  # We already lowercased during tokenization
            for pattern in patterns:
                if pattern.search(token):  # Match on individual token
                    positions.append(i)
                    break
        return positions

    def precise_proximity_test(self, text: str, window_tokens: int = 40) -> Tuple[bool, List[int], List[int]]:
        """
        Precise token-window proximity test
        Returns (passes_test, mig_positions, lab_positions)
        """
        # Tokenize text
        tokens = self.tokenize_with_positions(text)
        
        # Find MIG and LAB term positions
        mig_positions = self.find_term_positions(tokens, self.mig_compiled)
        lab_positions = self.find_term_positions(tokens, self.lab_compiled)
        
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

    def find_paragraph_boundaries(self, text: str, hit_start: int, hit_end: int) -> Tuple[int, int]:
        """Find paragraph boundaries around a hit span"""
        # Find nearest double newlines or document boundaries
        para_start = text.rfind('\n\n', 0, hit_start)
        para_end = text.find('\n\n', hit_end)
        
        # Default to document boundaries if no paragraph breaks found
        if para_start == -1:
            para_start = 0
        else:
            para_start += 2  # Skip the newlines
            
        if para_end == -1:
            para_end = len(text)
        
        return para_start, para_end

    def clean_passage(self, text: str) -> str:
        """Remove procedural noise from passage"""
        cleaned = text
        for noise_pattern in self.noise_patterns:
            cleaned = noise_pattern.sub('', cleaned)
        
        # Clean up extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    def count_words(self, text: str) -> int:
        """Count words in text"""
        return len(self.word_splitter.findall(text))

    def extract_tightest_hit_span(self, text: str, mig_positions: List[int], lab_positions: List[int]) -> Tuple[int, int]:
        """Find the tightest span that contains at least one MIG and one LAB term"""
        tokens = self.tokenize_with_positions(text)
        
        min_span_size = float('inf')
        best_start, best_end = 0, len(text)
        
        # Find tightest MIG-LAB pair
        for mig_pos in mig_positions:
            for lab_pos in lab_positions:
                if abs(mig_pos - lab_pos) <= 40:  # Within window
                    start_token = min(mig_pos, lab_pos)
                    end_token = max(mig_pos, lab_pos)
                    
                    # Convert token positions to character positions
                    char_start = tokens[start_token][1] if start_token < len(tokens) else 0
                    char_end = tokens[end_token][2] if end_token < len(tokens) else len(text)
                    
                    span_size = char_end - char_start
                    if span_size < min_span_size:
                        min_span_size = span_size
                        best_start, best_end = char_start, char_end
        
        return best_start, best_end

    def extract_word_based_quotes(self, text: str, min_words: int = 150, max_words: int = 450) -> List[Dict]:
        """
        Extract quotes using word-based filtering and precise proximity testing
        """
        quotes = []
        
        # First, check if text passes proximity test
        passes, mig_positions, lab_positions = self.precise_proximity_test(text)
        if not passes:
            return quotes
        
        # Find tightest hit span
        hit_start, hit_end = self.extract_tightest_hit_span(text, mig_positions, lab_positions)
        
        # Expand to paragraph boundaries
        para_start, para_end = self.find_paragraph_boundaries(text, hit_start, hit_end)
        
        # Extract initial passage
        passage = text[para_start:para_end].strip()
        passage = self.clean_passage(passage)
        
        word_count = self.count_words(passage)
        
        # If passage is too short, try expanding to include surrounding sentences
        if word_count < min_words:
            # Try expanding sentence by sentence
            sentences = self.sentence_splitter.split(text)
            
            # Find which sentence contains our hit
            hit_sentence = -1
            current_pos = 0
            for i, sentence in enumerate(sentences):
                sentence_end = current_pos + len(sentence)
                if current_pos <= hit_start <= sentence_end:
                    hit_sentence = i
                    break
                current_pos = sentence_end + 1
            
            if hit_sentence >= 0:
                # Expand around hit sentence
                for window_size in [3, 5, 7, 9]:
                    start_sent = max(0, hit_sentence - window_size // 2)
                    end_sent = min(len(sentences), hit_sentence + window_size // 2 + 1)
                    
                    expanded_passage = '. '.join(sentences[start_sent:end_sent]).strip()
                    expanded_passage = self.clean_passage(expanded_passage)
                    expanded_word_count = self.count_words(expanded_passage)
                    
                    if min_words <= expanded_word_count <= max_words:
                        passage = expanded_passage
                        word_count = expanded_word_count
                        break
        
        # Check final word count
        if min_words <= word_count <= max_words:
            # Verify passage still passes proximity test
            final_passes, final_mig, final_lab = self.precise_proximity_test(passage)
            
            if final_passes:
                quotes.append({
                    'text': passage,
                    'word_count': word_count,
                    'mig_term_count': len(final_mig),
                    'lab_term_count': len(final_lab),
                    'hit_start': hit_start,
                    'hit_end': hit_end,
                    'para_start': para_start,
                    'para_end': para_end,
                    'extraction_method': 'paragraph_boundary'
                })
        
        return quotes

    def test_improvements(self, test_text: str):
        """Test the improved extraction logic"""
        print("=== TESTING ENHANCED QUOTE EXTRACTION ===")
        print(f"Input text: {len(test_text)} characters")
        print(f"Word count: {self.count_words(test_text)}")
        
        # Test proximity
        passes, mig_pos, lab_pos = self.precise_proximity_test(test_text)
        print(f"\nProximity test: {'PASS' if passes else 'FAIL'}")
        print(f"MIG positions: {mig_pos}")
        print(f"LAB positions: {lab_pos}")
        
        if passes:
            # Extract quotes
            quotes = self.extract_word_based_quotes(test_text)
            print(f"\nExtracted {len(quotes)} quotes:")
            
            for i, quote in enumerate(quotes):
                print(f"\n--- Quote {i+1} ---")
                print(f"Word count: {quote['word_count']}")
                print(f"MIG terms: {quote['mig_term_count']}, LAB terms: {quote['lab_term_count']}")
                print(f"Method: {quote['extraction_method']}")
                print(f"Text preview: {quote['text'][:200]}...")
        
        return passes, quotes if passes else []

# Test with sample text
if __name__ == "__main__":
    extractor = EnhancedQuoteExtractor()
    
    # Test with a sample passage that should pass
    test_passage = """
    The question of alien immigration and its effect upon the labour market has been 
    much discussed in this House. Hon. Members will recall that the unemployment 
    rate has increased significantly in the East End, where foreign workers have 
    settled in large numbers. These immigrants, while seeking honest employment, 
    have inevitably affected wage rates in certain trades. The tailoring industry, 
    in particular, has seen wages depress as a result of this competition. 
    
    However, we must also acknowledge that many of these aliens have brought new 
    skills and have established industries which did not previously exist in this 
    country. The question before us is whether the benefits to certain sectors 
    outweigh the undoubted hardships caused to British workers in overcrowded trades.
    
    I would argue that proper regulation, rather than exclusion, is the answer to 
    this complex problem affecting both immigration policy and labour conditions.
    """
    
    extractor.test_improvements(test_passage)