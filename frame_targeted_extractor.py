# frame_targeted_extractor.py
# Extract quotes that clearly demonstrate specific frames with full context

import requests, re, json, csv
from datetime import date
from bs4 import BeautifulSoup

BASE = "https://api.parliament.uk/historic-hansard"

def fetch_html(url):
    r = requests.get(url, timeout=30, headers={"User-Agent":"HansardResearch/1.0"})
    r.raise_for_status()
    return r.text

def find_speaker_boundaries(section_html):
    """Find speaker boundaries in HTML"""
    soup = BeautifulSoup(section_html, 'html.parser')
    text = soup.get_text()
    
    speaker_patterns = [
        r'(Mr\.|Mrs\.|Sir|Lord|Dr\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*:',
        r'(Mr\.|Mrs\.|Sir|Lord|Dr\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:said|asked|replied|continued)',
        r'^([A-Z][A-Z\s]{3,}):\s*',
        r'The\s+(Secretary|Minister|President|Chairman)\s+of\s+State',
    ]
    
    speaker_positions = []
    for pattern in speaker_patterns:
        for match in re.finditer(pattern, text, re.MULTILINE):
            speaker_name = match.group(0).rstrip(':').rstrip()
            speaker_name = re.sub(r'\s+(?:said|asked|replied|continued)$', '', speaker_name)
            
            speaker_positions.append({
                'position': match.start(),
                'speaker': speaker_name
            })
    
    speaker_positions.sort(key=lambda x: x['position'])
    return speaker_positions, text

def extract_frame_specific_quotes(text, min_length=400, max_length=800):
    """Extract quotes that clearly demonstrate specific frames"""
    
    # Split into larger passages for more context
    sentences = re.split(r'[.!?]+\s*(?=[A-Z])', text)
    
    frame_patterns = {
        'LABOUR_NEED': {
            'required_patterns': [
                r'(?:shortage|need|want|require).*(?:labour|labor|workers?|men)',
                r'(?:fill|filling|supply).*(?:vacancy|vacancies|positions?|jobs?)',
                r'essential.*(?:workers?|labour|labor)',
                r'(?:skilled|trained).*(?:workers?|labour|labor).*(?:needed|required|wanted)',
                r'(?:benefit|beneficial|advantage).*(?:employment|labour|labor|work)',
                r'(?:new\s+trades?|skills?).*(?:brought|introduced|taught)',
            ],
            'context_patterns': [
                r'(?:increase|increased|increasing).*(?:demand|employment|work)',
                r'(?:economic|industrial).*(?:benefit|advantage|development)',
            ]
        },
        
        'LABOUR_THREAT': {
            'required_patterns': [
                r'(?:depress|depressing|lower|lowering|reduce|reducing).*wage[s]?',
                r'(?:competition|compete|competing).*(?:with|against).*(?:british|english|our).*(?:workers?|labour|labor)',
                r'(?:unemployment|unemployed).*(?:among|of).*(?:british|english|our)',
                r'(?:under-sell|undersell|undercutting?).*(?:workers?|labour|labor)',
                r'(?:displac|displacing|taking|stolen?).*(?:jobs?|work|employment)',
                r'(?:surplus|excess).*(?:labour|labor)',
            ],
            'context_patterns': [
                r'(?:damage|harm|evil|injur).*(?:done|caused).*(?:by|from)',
                r'(?:suffer|suffering).*(?:from|due\s+to)',
                r'(?:turn.*out|drive.*out).*(?:of|from).*(?:homes?|jobs?)',
            ]
        },
        
        'RACIALISED': {
            'required_patterns': [
                r'(?:undesirable|inferior|degraded?).*aliens?',
                r'(?:racial|race).*(?:problem|question|issue)',
                r'(?:character|quality|type).*(?:of|these).*(?:people|aliens?)',
                r'(?:class|sort|kind).*(?:of|these).*(?:immigrants?|aliens?)',
                r'pauper.*aliens?',
                r'criminal.*aliens?',
            ],
            'context_patterns': [
                r'(?:moral|social|cultural).*(?:standard|level|condition)',
                r'(?:civilization|civilized|barbarous)',
                r'(?:habits|customs|way\s+of\s+life)',
            ]
        },
        
        'MIXED': {
            'required_patterns': [
                r'on\s+the\s+(?:one\s+)?hand.*on\s+the\s+(?:other\s+)?hand',
                r'(?:while|whereas|although).*(?:however|but|nevertheless)',
                r'(?:benefits?|advantages?).*(?:but|however|yet).*(?:harm|damage|problems?)',
                r'(?:some|certain).*(?:good|benefit).*(?:other|some).*(?:harm|damage)',
            ],
            'context_patterns': [
                r'balanced?.*(?:view|approach|consideration)',
                r'(?:both|two).*sides?.*(?:question|argument|issue)',
            ]
        }
    }
    
    targeted_quotes = {}
    
    # Look for passages that clearly demonstrate each frame
    for frame, patterns in frame_patterns.items():
        targeted_quotes[frame] = []
        
        for i in range(len(sentences)):
            for window_size in [4, 6, 8, 10, 12]:  # Longer passages for more context
                if i + window_size > len(sentences):
                    continue
                
                passage = '. '.join(sentences[i:i+window_size]).strip()
                
                if len(passage) < min_length or len(passage) > max_length:
                    continue
                
                passage_lower = passage.lower()
                
                # Check if passage clearly demonstrates this frame
                required_matches = sum(1 for pattern in patterns['required_patterns'] 
                                     if re.search(pattern, passage_lower))
                context_matches = sum(1 for pattern in patterns['context_patterns'] 
                                    if re.search(pattern, passage_lower))
                
                # Must have at least 1 required pattern and ideally some context
                if required_matches >= 1:
                    # Also check for immigration terms
                    has_immigration = bool(re.search(r'(?:immigration|immigrant[s]?|alien[s]?|foreign(?:er|ers)?)', passage_lower))
                    
                    if has_immigration:
                        clarity_score = required_matches * 2 + context_matches
                        
                        # Check this passage doesn't already overlap with existing ones
                        is_new = True
                        for existing in targeted_quotes[frame]:
                            existing_words = set(existing['text'].lower().split())
                            passage_words = set(passage.lower().split())
                            overlap_ratio = len(existing_words & passage_words) / min(len(existing_words), len(passage_words))
                            if overlap_ratio > 0.4:  # 40% overlap
                                is_new = False
                                break
                        
                        if is_new:
                            targeted_quotes[frame].append({
                                'text': passage,
                                'start': i,
                                'window_size': window_size,
                                'clarity_score': clarity_score,
                                'required_matches': required_matches,
                                'context_matches': context_matches
                            })
        
        # Sort by clarity score and take best ones
        targeted_quotes[frame].sort(key=lambda x: -x['clarity_score'])
        targeted_quotes[frame] = targeted_quotes[frame][:3]  # Top 3 per frame
    
    return targeted_quotes

def extract_speaker_for_quote(speaker_positions, text, quote_text):
    """Find speaker for a specific quote"""
    quote_pos = text.lower().find(quote_text[:50].lower())
    if quote_pos == -1:
        return "Unknown Speaker"
    
    relevant_speaker = "Unknown Speaker"
    for speaker_info in reversed(speaker_positions):
        if speaker_info['position'] < quote_pos:
            relevant_speaker = speaker_info['speaker']
            break
    
    return relevant_speaker

# Extract frame-targeted quotes
print("=== FRAME-TARGETED QUOTE EXTRACTION ===")

test_sections = [
    ("https://api.parliament.uk/historic-hansard/commons/1905/may/02/aliens-bill", "ALIENS BILL"),
    ("https://api.parliament.uk/historic-hansard/commons/1905/may/02/aliens-bill-1", "ALIENS BILL (continued)"),
]

all_frame_quotes = []

for section_url, section_title in test_sections:
    print(f"\n=== {section_title} ===")
    
    try:
        section_html = fetch_html(section_url)
        speaker_positions, full_text = find_speaker_boundaries(section_html)
        
        print(f"  Content: {len(full_text)} chars")
        
        # Extract frame-specific quotes
        frame_quotes = extract_frame_specific_quotes(full_text)
        
        for frame, quotes in frame_quotes.items():
            print(f"\n  --- {frame} QUOTES ({len(quotes)}) ---")
            
            for i, quote in enumerate(quotes):
                speaker = extract_speaker_for_quote(speaker_positions, full_text, quote['text'])
                
                all_frame_quotes.append({
                    "date": "1905-05-02",
                    "house": "commons",
                    "debate_title": section_title,
                    "member": speaker,
                    "party": "",
                    "quote": quote['text'],
                    "frame": frame,
                    "clarity_score": quote['clarity_score'],
                    "hansard_url": section_url
                })
                
                print(f"    Quote {i+1} (Clarity: {quote['clarity_score']}) - {speaker}")
                print(f"      Required: {quote['required_matches']}, Context: {quote['context_matches']}")
                print(f"      {quote['text'][:200]}...")
                print()
    
    except Exception as e:
        print(f"  Error: {e}")

# Save frame-targeted quotes
print(f"\n=== RESULTS ===")
print(f"Total frame-targeted quotes: {len(all_frame_quotes)}")

if all_frame_quotes:
    # Remove analysis fields for final output
    final_quotes = []
    for quote in all_frame_quotes:
        final_quote = {k:v for k,v in quote.items() if k not in ['clarity_score']}
        final_quotes.append(final_quote)
    
    with open("quotes_frame_targeted.jsonl","w",encoding="utf-8") as f:
        for r in final_quotes:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    
    print(f"Saved to quotes_frame_targeted.jsonl")
    
    # Show distribution by frame
    frame_counts = {}
    for quote in all_frame_quotes:
        frame = quote['frame']
        if frame not in frame_counts:
            frame_counts[frame] = 0
        frame_counts[frame] += 1
    
    print(f"\n=== FRAME DISTRIBUTION ===")
    for frame, count in frame_counts.items():
        print(f"  {frame}: {count} quotes")
        
        # Show best quote for this frame
        frame_quotes = [q for q in all_frame_quotes if q['frame'] == frame]
        if frame_quotes:
            best_quote = max(frame_quotes, key=lambda x: x['clarity_score'])
            print(f"    Best example ({best_quote['member']}):")
            print(f"    {best_quote['quote'][:300]}...")
            print()
else:
    print("No frame-targeted quotes found")