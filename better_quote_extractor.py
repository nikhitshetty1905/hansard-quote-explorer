# better_quote_extractor.py
# Extract more meaningful, longer quotes from the sections we found

import requests, re, json, csv
from datetime import date
from bs4 import BeautifulSoup

BASE = "https://api.parliament.uk/historic-hansard"

# More comprehensive patterns for substantial arguments
MIG = r"(immigration|immigrant[s]?|migrant[s]?|alien[s]?|aliens|foreign(?:er|ers)?|guest\s*worker[s]?|colonial\s+(?:subjects|workers))"
LAB = r"(labour\s*market|labor\s*market|wage[s]?|pay|employment|unemployment|job[s]?|workforce|manpower|strike[s]?|trade\s*union[s]?|working\s+(?:people|men|class)|sweating|competition)"
NEAR = 100  # Increased proximity for more substantial arguments

def fetch_html(url):
    r = requests.get(url, timeout=30, headers={"User-Agent":"HansardResearch/1.0"})
    r.raise_for_status()
    return r.text

def words(text): 
    return re.findall(r"\w[\w'-]*", text.lower())

def find_substantial_quotes(text, min_length=150, max_length=500):
    """Find substantial quotes that discuss both immigration and labour"""
    
    # Split text into sentences (roughly)
    sentences = re.split(r'[.!?]+', text)
    quotes = []
    
    # Look for substantial passages
    for i in range(len(sentences)):
        # Try different window sizes
        for window_size in [3, 5, 7, 10]:  # 3-10 sentences
            if i + window_size > len(sentences):
                continue
                
            passage = ' '.join(sentences[i:i+window_size]).strip()
            
            if len(passage) < min_length or len(passage) > max_length:
                continue
            
            # Check if this passage has both terms
            passage_lower = passage.lower()
            has_mig = bool(re.search(MIG, passage_lower))
            has_lab = bool(re.search(LAB, passage_lower))
            
            if has_mig and has_lab:
                # Check for substantive content (not just procedural)
                substantive_indicators = [
                    r'evidence\s+to\s+show',
                    r'argument[s]?\s+(?:in\s+support|against)',
                    r'ground[s]?\s+for\s+this\s+bill',
                    r'result\s+of\s+their\s+coming',
                    r'(?:increase|decrease)\s+(?:in\s+)?wage[s]?',
                    r'competition\s+(?:with|from)',
                    r'(?:depress|raise|affect)\s+(?:the\s+)?wage[s]?',
                    r'new\s+trades',
                    r'working\s+(?:people|men|class)',
                    r'sweating',
                    r'unemployment',
                    r'(?:benefit|harm|evil)\s+(?:done|caused)',
                ]
                
                if any(re.search(pattern, passage_lower) for pattern in substantive_indicators):
                    quotes.append({
                        'text': passage,
                        'start_sentence': i,
                        'length': len(passage),
                        'window_size': window_size
                    })
    
    # Remove overlapping quotes (prefer longer ones)
    final_quotes = []
    quotes.sort(key=lambda x: (-x['length'], x['start_sentence']))  # Longer first, then earlier
    
    for quote in quotes:
        # Check if this overlaps significantly with existing quotes
        overlap = False
        for existing in final_quotes:
            # Check sentence overlap
            existing_end = existing['start_sentence'] + existing['window_size']
            quote_end = quote['start_sentence'] + quote['window_size']
            
            overlap_start = max(quote['start_sentence'], existing['start_sentence'])
            overlap_end = min(quote_end, existing_end)
            
            if overlap_end > overlap_start:  # There's overlap
                overlap_sentences = overlap_end - overlap_start
                if overlap_sentences >= 2:  # 2+ sentence overlap
                    overlap = True
                    break
        
        if not overlap:
            final_quotes.append(quote)
    
    return final_quotes[:3]  # Return top 3 non-overlapping quotes

def extract_speaker_context(section_html, quote_text):
    """Try to extract speaker for this specific quote"""
    soup = BeautifulSoup(section_html, 'html.parser')
    
    # Look for the quote text and find preceding speaker indicators
    page_text = soup.get_text()
    
    # Find where this quote appears
    quote_start = page_text.lower().find(quote_text[:50].lower())
    if quote_start > 0:
        # Look backwards for speaker name
        preceding_text = page_text[max(0, quote_start - 500):quote_start]
        
        # Common speaker patterns
        speaker_patterns = [
            r'(Mr\.|Mrs\.|Sir|Lord|Dr\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][A-Z\s]+):',  # ALL CAPS NAME:
            r'The\s+(Secretary|Minister|President|Chairman)',
        ]
        
        # Find the last speaker mention before the quote
        last_speaker = "Unknown Speaker"
        for pattern in speaker_patterns:
            matches = list(re.finditer(pattern, preceding_text))
            if matches:
                last_match = matches[-1]
                if len(last_match.groups()) == 2:
                    last_speaker = f"{last_match.group(1)} {last_match.group(2)}"
                else:
                    last_speaker = last_match.group(0)
        
        return last_speaker
    
    return "Unknown Speaker"

# Test with the sections we know work
test_sections = [
    "https://api.parliament.uk/historic-hansard/commons/1905/may/02/immigration-of-aliens",
    "https://api.parliament.uk/historic-hansard/commons/1905/may/02/aliens-bill",
    "https://api.parliament.uk/historic-hansard/commons/1905/may/02/aliens-bill-1"
]

print("=== EXTRACTING BETTER QUOTES ===")

all_quotes = []

for i, section_url in enumerate(test_sections):
    print(f"\nSection {i+1}: {section_url.split('/')[-1]}")
    
    try:
        section_html = fetch_html(section_url)
        soup = BeautifulSoup(section_html, 'html.parser')
        section_text = soup.get_text()
        
        # Extract title from URL
        section_title = section_url.split('/')[-1].replace('-', ' ').title()
        
        print(f"  Content length: {len(section_text)} chars")
        
        # Find substantial quotes
        quotes = find_substantial_quotes(section_text)
        print(f"  Found {len(quotes)} substantial quotes")
        
        for j, quote in enumerate(quotes):
            speaker = extract_speaker_context(section_html, quote['text'])
            
            # Clean up the quote text
            clean_quote = re.sub(r'\s+', ' ', quote['text']).strip()
            
            all_quotes.append({
                "date": "1905-05-02",
                "house": "commons", 
                "debate_title": section_title,
                "member": speaker,
                "party": "",
                "quote": clean_quote,
                "hansard_url": section_url
            })
            
            print(f"    Quote {j+1} ({quote['length']} chars) - {speaker}:")
            print(f"      {clean_quote[:150]}...")
            
    except Exception as e:
        print(f"  Error: {e}")

# Save the better quotes
print(f"\n=== RESULTS ===")
print(f"Total substantial quotes: {len(all_quotes)}")

if all_quotes:
    with open("quotes_substantial.jsonl","w",encoding="utf-8") as f:
        for r in all_quotes:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open("quotes_substantial.csv","w",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(all_quotes[0].keys()))
        w.writeheader()
        w.writerows(all_quotes)
    
    print(f"Saved to quotes_substantial.jsonl & quotes_substantial.csv")
    
    # Show full quotes
    print(f"\n=== FULL SUBSTANTIAL QUOTES ===")
    for i, quote in enumerate(all_quotes):
        print(f"\n{i+1}. {quote['debate_title']} - {quote['member']}")
        print(f"   {quote['quote']}")
        print(f"   URL: {quote['hansard_url']}")
else:
    print("No substantial quotes found")