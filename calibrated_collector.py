# calibrated_collector.py
# Calibrate word count thresholds based on actual Hansard data

from updated_hybrid_collector import UpdatedHybridCollector
from enhanced_quote_logic import EnhancedQuoteExtractor
import requests
from bs4 import BeautifulSoup

class CalibratedCollector(UpdatedHybridCollector):
    """Collector with calibrated word count thresholds"""
    
    def __init__(self, db_path="hansard_calibrated.db", cache_dir="hansard_cache"):
        super().__init__(db_path, cache_dir)
        
        # Calibrated word count thresholds based on Hansard speech patterns
        self.min_words = 80   # Reduced from 150 based on actual data
        self.max_words = 450  # Keep upper limit from spec
    
    def process_debate_html(self, debate_info, sitting_url):
        """Process debate HTML with calibrated thresholds"""
        url = debate_info["url"]
        
        try:
            response = self.session.get(url, timeout=45)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            full_text = soup.get_text()
            
            # Quick proximity check
            passes, _, _ = self.quote_extractor.precise_proximity_test(full_text)
            if not passes:
                return []
            
            print(f"    Processing: {debate_info['title']} ({len(full_text)} chars)")
            
            # Find speakers
            speaker_positions = self.find_speaker_boundaries(full_text)
            
            # Extract quotes with calibrated thresholds
            quotes = self.quote_extractor.extract_word_based_quotes(
                full_text, 
                min_words=self.min_words, 
                max_words=self.max_words
            )
            
            print(f"      Found {len(quotes)} quotes with {self.min_words}-{self.max_words} word filter")
            
            speeches = []
            for quote_data in quotes:
                # Find speaker for this quote
                quote_text = quote_data['text']
                quote_pos = full_text.find(quote_text[:50])
                speaker = "Unknown Speaker"
                
                for speaker_info in reversed(speaker_positions):
                    if speaker_info['position'] < quote_pos:
                        speaker = speaker_info['speaker']
                        break
                
                # Generate dedup key
                dedup_key = self.generate_dedup_key(url, speaker, quote_text)
                
                # Calculate quality score with calibrated metrics
                quality = self.calculate_calibrated_quality(quote_data)
                
                speeches.append({
                    'dedup_key': dedup_key,
                    'date': debate_info['date'],
                    'house': debate_info['house'],
                    'debate_title': debate_info['title'],
                    'member': speaker,
                    'party': '',
                    'quote': quote_text,
                    'word_count': quote_data['word_count'],
                    'mig_term_count': quote_data['mig_term_count'],
                    'lab_term_count': quote_data['lab_term_count'],
                    'extraction_method': quote_data['extraction_method'],
                    'url': url,
                    'sitting_url': sitting_url,
                    'extraction_quality': quality
                })
            
            return speeches
            
        except Exception as e:
            print(f"    Error processing {url}: {e}")
            return []
    
    def calculate_calibrated_quality(self, quote_data):
        """Calculate quality score calibrated for actual Hansard patterns"""
        score = 0
        
        word_count = quote_data['word_count']
        mig_count = quote_data['mig_term_count'] 
        lab_count = quote_data['lab_term_count']
        quote_text = quote_data['text'].lower()
        
        # Calibrated word count scoring
        if 150 <= word_count <= 300:
            score += 3  # Ideal length
        elif 100 <= word_count <= 149:
            score += 2  # Good length 
        elif 80 <= word_count <= 99:
            score += 1  # Acceptable length
        elif 301 <= word_count <= 450:
            score += 2  # Long but acceptable
        # Anything outside 80-450 gets 0 points
        
        # Enhanced term density scoring
        if mig_count >= 3 and lab_count >= 3:
            score += 4  # Very high density
        elif mig_count >= 2 and lab_count >= 2:
            score += 3  # High density
        elif mig_count >= 1 and lab_count >= 2:
            score += 2  # Good density
        elif mig_count >= 2 and lab_count >= 1:
            score += 2  # Good density
        elif mig_count >= 1 and lab_count >= 1:
            score += 1  # Minimum density
        
        # Argument structure indicators
        argument_patterns = [
            r'\b(argue|maintain|contend|assert|claim|believe|submit|urge|propose)\b',
            r'\b(I\s+(?:think|believe|maintain|argue|submit))\b',
            r'\b(it\s+is\s+(?:clear|evident|obvious|certain))\b'
        ]
        for pattern in argument_patterns:
            if re.search(pattern, quote_text):
                score += 1
                break
        
        # Policy/legislative context
        policy_patterns = [
            r'\b(bill|act|legislation|measure|policy|government|committee)\b',
            r'\b(second\s+reading|third\s+reading|amendment|clause)\b',
            r'\b(house|parliament|member|hon\.?\s+member)\b'
        ]
        for pattern in policy_patterns:
            if re.search(pattern, quote_text):
                score += 1
                break
        
        # Economic indicators (numbers, statistics, economic terms)
        if re.search(r'\b\d+(?:[,%]\d+)*\s*(?:%|per\s+cent|pounds?|£)\b', quote_text):
            score += 1
        
        # Direct speech/debate indicators
        if re.search(r'\b(hon\.?\s+member|right\s+hon\.?\s+gentleman|minister)\b', quote_text):
            score += 1
        
        return score

def test_calibrated_thresholds():
    """Test different word count thresholds to find optimal balance"""
    print("=== TESTING CALIBRATED WORD COUNT THRESHOLDS ===")
    
    # Test different thresholds
    thresholds_to_test = [
        (50, 400),    # Very permissive
        (80, 450),    # Calibrated based on debug
        (100, 450),   # Slightly stricter
        (150, 450),   # Original spec
    ]
    
    # Use Aliens Bill as test case
    extractor = EnhancedQuoteExtractor()
    
    url = "https://api.parliament.uk/historic-hansard/commons/1905/may/02/aliens-bill"
    session = requests.Session()
    session.headers.update({"User-Agent": "HansardResearch/1.0"})
    
    try:
        response = session.get(url, timeout=45)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        full_text = soup.get_text()
        
        print(f"Testing on Aliens Bill debate ({len(full_text)} chars)")
        
        for min_words, max_words in thresholds_to_test:
            quotes = extractor.extract_word_based_quotes(full_text, min_words=min_words, max_words=max_words)
            
            print(f"\nThreshold {min_words}-{max_words} words: {len(quotes)} quotes found")
            
            if quotes:
                word_counts = [q['word_count'] for q in quotes]
                avg_words = sum(word_counts) / len(word_counts)
                min_found = min(word_counts)
                max_found = max(word_counts)
                
                print(f"  Word counts: avg {avg_words:.0f}, range {min_found}-{max_found}")
                
                # Show first quote as sample
                sample = quotes[0]
                print(f"  Sample quote ({sample['word_count']} words):")
                print(f"    MIG: {sample['mig_term_count']}, LAB: {sample['lab_term_count']} terms")
                print(f"    Text: {sample['text'][:150]}...")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # First test thresholds
    test_calibrated_thresholds()
    
    print("\n" + "="*60)
    print("TESTING CALIBRATED COLLECTOR")
    print("="*60)
    
    # Test calibrated collector
    collector = CalibratedCollector()
    collector.collect_date_range(1905, 1905, start_month=5, end_month=5)
    collector.close()