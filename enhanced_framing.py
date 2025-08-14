# enhanced_framing.py
# Robust framing system with linkage patterns and confidence scoring

import re
import sqlite3
from typing import Dict, List, Tuple, Optional

class EnhancedFraming:
    """Advanced framing system with linkage detection and confidence scoring"""
    
    def __init__(self):
        # Core term patterns
        self.immigration_terms = re.compile(r'\b(?:immig(?:rant|ration)s?|aliens?|foreigners?|migrants?|colonial)\b', re.IGNORECASE)
        self.labour_terms = re.compile(r'\b(?:labou?r|employment|unemploy(?:ed|ment)?|wage[s]?|worker[s]?|job[s]?|workforce|union[s]?|strike[s]?)\b', re.IGNORECASE)
        
        # Linkage patterns - prove immigration→labour connection
        self.linkage_patterns = [
            # Causal patterns
            re.compile(r'(aliens?|foreigners?|immig\w+).*?(?:because|therefore|hence|so that|will|would|must|shall|tends? to).{0,25}(depress|lower|increas|creat|affect).{0,20}(wage|employ|job|unemploy)', re.IGNORECASE),
            re.compile(r'(wage|employ|job|unemploy).*?(?:because|due to|owing to|result of).{0,20}(aliens?|foreigners?|immig\w+)', re.IGNORECASE),
            
            # Contrast patterns  
            re.compile(r'(aliens?|foreigners?|immig\w+).*?(?:although|yet|however|on the other hand).{0,30}(wage|employ|job|labou?r)', re.IGNORECASE),
            re.compile(r'(labou?r|wage|employ|job).*?(?:but|however|although|whilst).{0,30}(aliens?|foreigners?|immig\w+)', re.IGNORECASE),
            
            # Attribution patterns
            re.compile(r'(aliens?|foreigners?|immig\w+).{0,20}(?:will|would|must|shall|tends? to).{0,15}(compete|threaten|benefit|help|assist).{0,20}(wage|employ|job|labou?r)', re.IGNORECASE),
        ]
        
        # Enhanced frame patterns
        self.frame_patterns = {
            'LABOUR_NEED': re.compile(r'(?:shortage|scarcity|need|want|require|fill|vacan|essential.*work|benefit|advantage|employment.*increase|man-?power.*need)', re.IGNORECASE),
            'LABOUR_THREAT': re.compile(r'(?:depress|lower|compete|competition|unemployment|surplus|suffer|mischief|casual.*labour|unskilled.*labour|over-?supply|strike-?break)', re.IGNORECASE), 
            'RACIALISED': re.compile(r'(?:undesirable.*aliens?|aliens?.*undesirable|character.*aliens?|aliens?.*character|exclude.*aliens?|pauper.*immig|colou?red.*labou?r)', re.IGNORECASE),
            'MIXED': re.compile(r'(?:on.*hand.*other.*hand|while.*but|although.*however|benefit.*but.*(?:harm|threat)|advantage.*but.*(?:danger|risk))', re.IGNORECASE)
        }
        
        # Claim and policy indicators
        self.claim_verbs = re.compile(r'\b(?:argue|maintain|contend|assert|claim|believe|urge|propose|submit|declare|state)\b', re.IGNORECASE)
        self.policy_terms = re.compile(r'\b(?:bill|act|clause|amendment|order|regulation|measure|committee|second reading|legislation)\b', re.IGNORECASE)
        
        # Negative guards
        self.procedural_noise = re.compile(r'^\s*(?:hear,? hear|order|division|adjourn(?:ed)?|schedule)\b', re.MULTILINE | re.IGNORECASE)
        self.hedge_words = re.compile(r'\b(?:perhaps|may be|might|not necessarily|possibly|allegedly|reportedly)\b', re.IGNORECASE)
        
        # Party filter guard
        self.labour_party_pattern = re.compile(r'\bLabour (?:Party|Member|Government)\b', re.IGNORECASE)
        self.economics_terms = re.compile(r'\b(?:wage|employ|job|strike|market|unemploy|man-?power|workforce|union)\b', re.IGNORECASE)

    def tokenize_and_find_positions(self, text: str) -> Tuple[List[str], List[int], List[int]]:
        """Tokenize text and find immigration/labour term positions"""
        words = re.findall(r'[A-Za-z0-9\'-]+', text.lower())
        
        imm_positions = []
        lab_positions = []
        
        for i, word in enumerate(words):
            if self.immigration_terms.search(word):
                imm_positions.append(i)
            if self.labour_terms.search(word):
                lab_positions.append(i)
        
        return words, imm_positions, lab_positions

    def check_linkage(self, text: str) -> Tuple[bool, List[str]]:
        """Check for explicit linkage patterns between immigration and labour"""
        fired_patterns = []
        
        for pattern in self.linkage_patterns:
            matches = pattern.findall(text)
            if matches:
                # Store the matched text for transparency
                for match in matches:
                    if isinstance(match, tuple):
                        fired_patterns.append(" ... ".join(match))
                    else:
                        fired_patterns.append(match)
        
        return len(fired_patterns) > 0, fired_patterns

    def check_proximity(self, text: str, window_words: int = 40) -> Tuple[bool, int]:
        """Enhanced proximity check with Labour Party guard"""
        
        # Guard against Labour Party false positives
        if self.labour_party_pattern.search(text):
            if not self.economics_terms.search(text):
                return False, 999  # High distance indicates filtered out
        
        words, imm_positions, lab_positions = self.tokenize_and_find_positions(text)
        
        if not imm_positions or not lab_positions:
            return False, 999
        
        # Find minimum distance
        min_distance = float('inf')
        for imm_pos in imm_positions:
            for lab_pos in lab_positions:
                distance = abs(imm_pos - lab_pos)
                min_distance = min(min_distance, distance)
        
        return min_distance <= window_words, int(min_distance)

    def compute_features(self, text: str) -> Dict:
        """Compute all features for confidence scoring"""
        words, imm_positions, lab_positions = self.tokenize_and_find_positions(text)
        has_linkage, linkage_patterns = self.check_linkage(text)
        has_proximity, min_distance = self.check_proximity(text)
        
        # Count frame cue hits
        r_hits = len(self.frame_patterns['RACIALISED'].findall(text))
        n_hits = len(self.frame_patterns['LABOUR_NEED'].findall(text))
        t_hits = len(self.frame_patterns['LABOUR_THREAT'].findall(text))
        m_hits = len(self.frame_patterns['MIXED'].findall(text))
        
        # Other indicators
        claim_hits = len(self.claim_verbs.findall(text))
        policy_hits = len(self.policy_terms.findall(text))
        procedural_hits = len(self.procedural_noise.findall(text))
        hedge_hits = len(self.hedge_words.findall(text))
        
        total_words = len(words)
        hedge_ratio = hedge_hits / max(total_words, 1)
        
        return {
            'mig_count': len(imm_positions),
            'lab_count': len(lab_positions),
            'min_distance': min_distance,
            'has_linkage': has_linkage,
            'linkage_patterns': linkage_patterns,
            'has_proximity': has_proximity,
            'claim_hits': claim_hits,
            'policy_hits': policy_hits,
            'procedural_hits': procedural_hits,
            'hedge_ratio': hedge_ratio,
            'r_hits': r_hits,
            'n_hits': n_hits,
            't_hits': t_hits,
            'm_hits': m_hits,
            'total_words': total_words
        }

    def assign_frame(self, features: Dict) -> str:
        """Assign frame based on enhanced rules"""
        r_hits = features['r_hits']
        n_hits = features['n_hits'] 
        t_hits = features['t_hits']
        m_hits = features['m_hits']
        
        # Require linkage OR tight proximity
        if not (features['has_linkage'] or features['min_distance'] <= 20):
            return 'OTHER'
        
        # Frame decision logic
        if r_hits >= 1 and (n_hits >= 1 or t_hits >= 1):
            return 'RACIALISED'
        elif m_hits >= 1 or (n_hits >= 1 and t_hits >= 1):
            return 'MIXED'
        elif n_hits >= 1:
            return 'LABOUR_NEED'
        elif t_hits >= 1:
            return 'LABOUR_THREAT'
        else:
            return 'OTHER'

    def compute_confidence(self, features: Dict) -> int:
        """Compute confidence score 0-10"""
        confidence = 0
        
        # Token counts
        if features['mig_count'] >= 2 and features['lab_count'] >= 2:
            confidence += 3
        
        # Distance bonus
        if features['min_distance'] <= 20:
            confidence += 2
        elif features['min_distance'] <= 30:
            confidence += 1
        
        # Linkage bonus
        if features['has_linkage']:
            confidence += 1
        
        # Claim verbs bonus
        if features['claim_hits'] > 0:
            confidence += 2
        
        # Policy terms bonus
        if features['policy_hits'] > 0:
            confidence += 1
        
        # Penalties
        if features['procedural_hits'] > 0:
            confidence -= 2
        
        if features['hedge_ratio'] > 0.1:
            confidence -= 1
        
        # Clamp to [0, 10]
        return max(0, min(10, confidence))

    def analyze_quote(self, text: str) -> Dict:
        """Full analysis of a quote with frame, confidence, and reasoning"""
        features = self.compute_features(text)
        frame = self.assign_frame(features)
        confidence = self.compute_confidence(features)
        
        # Build explanation
        explanation = {
            'frame': frame,
            'confidence': confidence,
            'features': features,
            'reasoning': {
                'linkage_found': features['has_linkage'],
                'linkage_patterns': features['linkage_patterns'],
                'min_distance': features['min_distance'], 
                'mig_terms': features['mig_count'],
                'lab_terms': features['lab_count'],
                'claim_verbs': features['claim_hits'] > 0,
                'policy_terms': features['policy_hits'] > 0,
                'procedural_filtered': features['procedural_hits'] > 0,
                'hedge_penalty': features['hedge_ratio'] > 0.1
            }
        }
        
        return explanation

def test_enhanced_framing():
    """Test the enhanced framing system"""
    framing = EnhancedFraming()
    
    test_quotes = [
        # High confidence - clear linkage
        "The aliens will therefore depress wages and create unemployment among British workers in our factories.",
        
        # Medium confidence - proximity only  
        "These foreign workers and our employment situation require careful consideration of wages.",
        
        # Low confidence - hedge words
        "Perhaps aliens might possibly affect labour, though it is not necessarily the case.",
        
        # Filtered out - Labour Party without economics
        "The Labour Party member spoke about constitutional reform and voting rights."
    ]
    
    print("=== TESTING ENHANCED FRAMING ===\n")
    
    for i, quote in enumerate(test_quotes, 1):
        result = framing.analyze_quote(quote)
        print(f"Quote {i}: {quote[:60]}...")
        print(f"Frame: {result['frame']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Linkage: {result['reasoning']['linkage_found']}")
        print(f"Distance: {result['reasoning']['min_distance']}")
        print("-" * 60)

if __name__ == "__main__":
    test_enhanced_framing()