# premium_quote_extractor.py
# High-quality quote extractor based on analysis findings

import requests, re, json, csv
from datetime import date
from bs4 import BeautifulSoup

BASE = "https://api.parliament.uk/historic-hansard"

def fetch_html(url):
    r = requests.get(url, timeout=30, headers={"User-Agent":"HansardResearch/1.0"})
    r.raise_for_status()
    return r.text

def find_speaker_boundaries(section_html):
    """Find precise speaker boundaries in the HTML"""
    soup = BeautifulSoup(section_html, 'html.parser')
    text = soup.get_text()
    
    # Pattern from analysis: "Mr. Hawkey", "Dr. Williams", etc.
    speaker_patterns = [
        r'(Mr\.|Mrs\.|Sir|Lord|Dr\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*:',
        r'(Mr\.|Mrs\.|Sir|Lord|Dr\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:said|asked|replied|continued)',
        r'^([A-Z][A-Z\s]{3,}):\s*',  # ALL CAPS names
        r'The\s+(Secretary|Minister|President|Chairman)\s+of\s+State\s+(?:said|replied)',
    ]
    
    speaker_positions = []
    
    for pattern in speaker_patterns:
        for match in re.finditer(pattern, text, re.MULTILINE):
            speaker_name = match.group(0).rstrip(':').rstrip()
            # Clean up common suffixes
            speaker_name = re.sub(r'\s+(?:said|asked|replied|continued)$', '', speaker_name)
            
            speaker_positions.append({
                'position': match.start(),
                'end': match.end(),
                'speaker': speaker_name,
                'pattern_type': pattern
            })
    
    # Sort by position
    speaker_positions.sort(key=lambda x: x['position'])
    
    return speaker_positions, text

def extract_quality_arguments(text, min_length=250, max_length=600):
    """Extract high-quality argumentative passages"""
    
    # Split by stronger punctuation to get argument segments
    segments = re.split(r'[.!?]+\s*(?=[A-Z])', text)
    
    # Quality indicators based on analysis
    quality_patterns = {
        'EVIDENCE_STRENGTH': [
            r'commission\s+reported\s+that',
            r'evidence\s+(?:shows?|demonstrates?|proves?)',
            r'statistics?\s+(?:show|indicate|prove)',
            r'witness\s+stated\s+that',
            r'figures?\s+(?:show|demonstrate)',
        ],
        'ECONOMIC_REASONING': [
            r'(?:depress|lower|raise|increase)\s+(?:the\s+)?wages?',
            r'compete\s+with.*working\s+(?:men|class|people)',
            r'new\s+trades?.*brought\s+(?:to\s+)?(?:this\s+)?country',
            r'skilled\s+labour.*unskilled\s+labour',
            r'unemployment.*(?:among|of).*(?:british|english|our)',
        ],
        'COMPARATIVE_ANALYSIS': [
            r'(?:like|unlike)\s+the\s+huguenots',
            r'compared\s+(?:with|to).*(?:other\s+countries|our\s+own)',
            r'(?:whereas|while).*(?:these\s+)?aliens?',
            r'on\s+the\s+(?:other\s+)?hand',
        ],
        'LOGICAL_STRUCTURE': [
            r'(?:because|since|as).*(?:therefore|thus|hence)',
            r'if.*then',
            r'not\s+only.*but\s+(?:also|rather)',
            r'(?:however|but|nevertheless).*(?:in\s+fact|actually|indeed)',
            r'(?:first|second|third)ly?.*(?:secondly?|thirdly?|finally)',
        ],
        'STRONG_POSITIONS': [
            r'i\s+(?:argue|submit|contend|maintain)\s+that',
            r'it\s+is\s+(?:clear|evident|obvious)\s+that',
            r'there\s+(?:can\s+)?be\s+no\s+doubt\s+that',
            r'(?:must|should|ought\s+to)\s+(?:be\s+)?(?:clear|evident)',
        ]
    }
    
    quality_arguments = []
    
    # Build passages by combining related segments
    for i in range(len(segments)):
        for window_size in [2, 3, 4, 5]:  # 2-5 segments
            if i + window_size > len(segments):
                continue
            
            passage = '. '.join(segments[i:i+window_size]).strip()
            
            if len(passage) < min_length or len(passage) > max_length:
                continue
            
            # Score this passage
            passage_lower = passage.lower()
            
            # Check for immigration + labour terms
            mig_terms = re.findall(r'(?:immigration|immigrant[s]?|alien[s]?|foreign(?:er|ers)?)', passage_lower)
            lab_terms = re.findall(r'(?:labour|labor|wage[s]?|employment|unemployment|working\s+(?:men|class|people)|job[s]?|trade[s]?)', passage_lower)
            
            if not (mig_terms and lab_terms):
                continue
            
            # Calculate quality score
            quality_score = 0
            matched_patterns = []
            
            for category, patterns in quality_patterns.items():
                category_matches = 0
                for pattern in patterns:
                    if re.search(pattern, passage_lower):
                        category_matches += 1
                        matched_patterns.append(f"{category}:{pattern[:30]}")
                
                if category_matches > 0:
                    # Weight different categories
                    weights = {
                        'EVIDENCE_STRENGTH': 3,
                        'ECONOMIC_REASONING': 2,
                        'COMPARATIVE_ANALYSIS': 2,
                        'LOGICAL_STRUCTURE': 2,
                        'STRONG_POSITIONS': 1
                    }
                    quality_score += category_matches * weights.get(category, 1)
            
            if quality_score >= 3:  # Minimum threshold
                quality_arguments.append({
                    'text': passage,
                    'start_segment': i,
                    'window_size': window_size,
                    'quality_score': quality_score,
                    'migration_terms': len(set(mig_terms)),
                    'labour_terms': len(set(lab_terms)),
                    'matched_patterns': matched_patterns[:5],  # Top 5 matches
                })
    
    # Remove overlaps and sort by quality
    quality_arguments.sort(key=lambda x: (-x['quality_score'], -x['migration_terms'] - x['labour_terms']))
    
    # Remove overlapping arguments
    final_arguments = []
    for arg in quality_arguments:
        overlap = False
        for existing in final_arguments:
            # Check for significant text overlap
            arg_words = set(arg['text'].lower().split())
            existing_words = set(existing['text'].lower().split())
            
            overlap_ratio = len(arg_words & existing_words) / min(len(arg_words), len(existing_words))
            if overlap_ratio > 0.3:  # 30% word overlap
                overlap = True
                break
        
        if not overlap:
            final_arguments.append(arg)
    
    return final_arguments[:5]  # Top 5 non-overlapping arguments

def extract_speaker_for_argument(speaker_positions, text, argument_text, argument_start_pos):
    """Find the speaker for a specific argument"""
    
    # Find where this argument appears in the full text
    arg_position = text.lower().find(argument_text[:50].lower())
    if arg_position == -1:
        return "Unknown Speaker"
    
    # Find the last speaker before this argument
    relevant_speaker = "Unknown Speaker"
    for speaker_info in reversed(speaker_positions):
        if speaker_info['position'] < arg_position:
            relevant_speaker = speaker_info['speaker']
            break
    
    return relevant_speaker

# Test with our known sections
test_sections = [
    ("https://api.parliament.uk/historic-hansard/commons/1905/may/02/aliens-bill", "ALIENS BILL"),
    ("https://api.parliament.uk/historic-hansard/commons/1905/may/02/aliens-bill-1", "ALIENS BILL (continued)"),
]

print("=== PREMIUM QUOTE EXTRACTION ===")

all_premium_quotes = []

for section_url, section_title in test_sections:
    print(f"\n=== {section_title} ===")
    
    try:
        section_html = fetch_html(section_url)
        speaker_positions, full_text = find_speaker_boundaries(section_html)
        
        print(f"  Content: {len(full_text)} chars")
        print(f"  Found {len(speaker_positions)} speaker boundaries")
        
        # Show found speakers
        speakers = [sp['speaker'] for sp in speaker_positions]
        unique_speakers = list(dict.fromkeys(speakers))  # Preserve order, remove duplicates
        print(f"  Speakers: {', '.join(unique_speakers[:5])}")
        
        # Extract quality arguments
        quality_args = extract_quality_arguments(full_text)
        print(f"  Found {len(quality_args)} quality arguments")
        
        for i, arg in enumerate(quality_args):
            # Find speaker for this argument
            speaker = extract_speaker_for_argument(speaker_positions, full_text, arg['text'], 0)
            
            all_premium_quotes.append({
                "date": "1905-05-02",
                "house": "commons",
                "debate_title": section_title,
                "member": speaker,
                "party": "",
                "quote": arg['text'],
                "quality_score": arg['quality_score'],
                "migration_terms": arg['migration_terms'],
                "labour_terms": arg['labour_terms'],
                "matched_patterns": arg['matched_patterns'],
                "hansard_url": section_url
            })
            
            print(f"\n    Argument {i+1} (Score: {arg['quality_score']}) - {speaker}")
            print(f"      Migration terms: {arg['migration_terms']}, Labour terms: {arg['labour_terms']}")
            print(f"      Patterns: {', '.join(arg['matched_patterns'][:3])}")
            print(f"      Text: {arg['text'][:200]}...")
        
    except Exception as e:
        print(f"  Error: {e}")

# Save premium quotes
print(f"\n=== RESULTS ===")
print(f"Total premium quotes: {len(all_premium_quotes)}")

if all_premium_quotes:
    with open("quotes_premium.jsonl","w",encoding="utf-8") as f:
        for r in all_premium_quotes:
            # Remove analysis fields for final output
            output_quote = {k:v for k,v in r.items() if k not in ['quality_score', 'migration_terms', 'labour_terms', 'matched_patterns']}
            f.write(json.dumps(output_quote, ensure_ascii=False) + "\n")
    
    print(f"Saved to quotes_premium.jsonl")
    
    # Show top quotes by quality
    sorted_quotes = sorted(all_premium_quotes, key=lambda x: -x['quality_score'])
    print(f"\n=== TOP 3 PREMIUM QUOTES ===")
    for i, quote in enumerate(sorted_quotes[:3]):
        print(f"\n{i+1}. Quality Score: {quote['quality_score']} - {quote['member']}")
        print(f"   {quote['quote']}")
        print(f"   Patterns: {', '.join(quote['matched_patterns'][:2])}")
        print(f"   URL: {quote['hansard_url']}")
else:
    print("No premium quotes found")