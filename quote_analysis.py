# quote_analysis.py
# Analyze the types and quality of quotes we're extracting

import requests, re, json
from datetime import date
from bs4 import BeautifulSoup
from collections import Counter

def fetch_html(url):
    r = requests.get(url, timeout=30, headers={"User-Agent":"HansardResearch/1.0"})
    r.raise_for_status()
    return r.text

def analyze_quote_types(quotes):
    """Analyze what types of arguments/content we're extracting"""
    
    argument_patterns = {
        'EVIDENCE_BASED': [
            r'evidence\s+(?:shows?|demonstrates?)',
            r'commission\s+reported',
            r'statistics?\s+(?:show|indicate)',
            r'figures?\s+(?:show|prove)',
            r'witness\s+stated',
            r'report\s+(?:says|shows|indicates)',
        ],
        'ECONOMIC_CLAIMS': [
            r'(?:depress|lower|raise|increase)\s+(?:the\s+)?wages?',
            r'(?:under-sell|compete\s+with|competition\s+(?:from|with))',
            r'(?:unemployment|employment)',
            r'labour\s+market',
            r'new\s+trades?',
            r'skilled\s+(?:labour|workers?)',
            r'unskilled\s+(?:labour|workers?)',
        ],
        'POLICY_ARGUMENTS': [
            r'this\s+bill\s+(?:will|would|should)',
            r'measure\s+(?:will|would|should)',
            r'policy\s+(?:of|which)',
            r'(?:support|oppose)\s+(?:this\s+)?(?:bill|measure)',
            r'vote\s+(?:with|against)',
            r'amendment\s+to',
        ],
        'COMPARATIVE': [
            r'unlike\s+(?:the\s+)?(?:aliens?|immigrants?)',
            r'compared\s+(?:with|to)',
            r'(?:like|unlike)\s+the\s+huguenots',
            r'other\s+countries',
            r'british\s+(?:working\s+)?(?:men|classes?|workers?)',
        ],
        'IDEOLOGICAL': [
            r'right\s+of\s+asylum',
            r'free\s+trade',
            r'protection(?:ist)?',
            r'national\s+(?:interest|character)',
            r'principle\s+of',
            r'liberty\s+of',
        ],
        'RHETORICAL': [
            r'i\s+(?:argue|submit|contend|maintain)',
            r'it\s+is\s+(?:said|claimed|argued)',
            r'(?:hon\.?\s+)?(?:members?|gentlemen)\s+(?:will\s+)?(?:agree|disagree)',
            r'let\s+me\s+(?:say|tell|ask)',
            r'the\s+question\s+is',
        ],
    }
    
    results = {}
    
    for quote in quotes:
        text = quote['quote'].lower()
        quote_patterns = []
        
        for category, patterns in argument_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    quote_patterns.append(category)
                    break  # Only count each category once per quote
        
        quote['argument_types'] = quote_patterns
        
        # Analyze argument completeness
        completeness_indicators = [
            r'because\s+',  # Causal reasoning
            r'therefore\s+',  # Conclusions
            r'however\s+',  # Counter-arguments
            r'but\s+',  # Contrasts
            r'if\s+.*then',  # Conditional logic
            r'not\s+only.*but\s+also',  # Complex arguments
        ]
        
        completeness_score = sum(1 for pattern in completeness_indicators if re.search(pattern, text))
        quote['completeness_score'] = completeness_score
        
        # Analyze rhetorical strength
        strength_indicators = [
            r'(?:strong|powerful|compelling)\s+(?:evidence|argument)',
            r'(?:clearly|obviously|evidently)',
            r'(?:must|should|ought\s+to)',
            r'(?:cannot|can\s+never)',
            r'(?:always|never|all|none)',  # Absolute claims
        ]
        
        strength_score = sum(1 for pattern in strength_indicators if re.search(pattern, text))
        quote['rhetorical_strength'] = strength_score
    
    # Aggregate results
    all_types = []
    for quote in quotes:
        all_types.extend(quote['argument_types'])
    
    type_counts = Counter(all_types)
    
    return quotes, type_counts

def analyze_speaker_patterns(section_html):
    """Analyze how speakers are indicated in the HTML structure"""
    
    soup = BeautifulSoup(section_html, 'html.parser')
    text = soup.get_text()
    
    # Look for different speaker indication patterns
    speaker_patterns = [
        (r'(Mr\.|Mrs\.|Sir|Lord|Dr\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*:', 'TITLE_NAME_COLON'),
        (r'^([A-Z][A-Z\s]{3,}):\s*', 'ALL_CAPS_COLON'),
        (r'(Mr\.|Mrs\.|Sir|Lord|Dr\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+\([^)]+\)', 'TITLE_NAME_CONSTITUENCY'),
        (r'The\s+(Secretary|Minister|President|Chairman)\s+of\s+State', 'OFFICIAL_TITLE'),
        (r'(Mr\.|Mrs\.|Sir|Lord|Dr\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:said|asked|replied)', 'TITLE_NAME_VERB'),
    ]
    
    found_patterns = {}
    
    for pattern, pattern_name in speaker_patterns:
        matches = re.findall(pattern, text, re.MULTILINE)
        if matches:
            found_patterns[pattern_name] = matches[:5]  # First 5 examples
    
    return found_patterns

print("=== ANALYZING QUOTE TYPES AND QUALITY ===")

# Load our current substantial quotes
with open("quotes_substantial.jsonl", "r", encoding="utf-8") as f:
    quotes = [json.loads(line) for line in f]

print(f"Analyzing {len(quotes)} quotes...")

# Analyze argument types
analyzed_quotes, type_counts = analyze_quote_types(quotes)

print(f"\n=== ARGUMENT TYPE DISTRIBUTION ===")
for arg_type, count in type_counts.most_common():
    print(f"  {arg_type}: {count} quotes ({count/len(quotes)*100:.1f}%)")

print(f"\n=== QUOTE QUALITY ANALYSIS ===")

# Show examples of each type
for arg_type in type_counts.keys():
    print(f"\n--- {arg_type} EXAMPLES ---")
    examples = [q for q in analyzed_quotes if arg_type in q['argument_types']]
    for i, quote in enumerate(examples[:2]):  # Show top 2
        print(f"{i+1}. Completeness: {quote['completeness_score']}, Strength: {quote['rhetorical_strength']}")
        print(f"   {quote['quote'][:200]}...")
        print()

print(f"\n=== COMPLETENESS AND STRENGTH SCORES ===")
completeness_scores = [q['completeness_score'] for q in analyzed_quotes]
strength_scores = [q['rhetorical_strength'] for q in analyzed_quotes]

print(f"Completeness scores: min={min(completeness_scores)}, max={max(completeness_scores)}, avg={sum(completeness_scores)/len(completeness_scores):.1f}")
print(f"Rhetorical strength scores: min={min(strength_scores)}, max={max(strength_scores)}, avg={sum(strength_scores)/len(strength_scores):.1f}")

# Identify highest quality quotes
high_quality = sorted(analyzed_quotes, key=lambda q: q['completeness_score'] + q['rhetorical_strength'], reverse=True)

print(f"\n=== TOP 3 HIGHEST QUALITY QUOTES ===")
for i, quote in enumerate(high_quality[:3]):
    print(f"\n{i+1}. Score: {quote['completeness_score'] + quote['rhetorical_strength']} (C:{quote['completeness_score']}, S:{quote['rhetorical_strength']})")
    print(f"   Types: {quote['argument_types']}")
    print(f"   {quote['quote'][:300]}...")

print(f"\n=== SPEAKER PATTERN ANALYSIS ===")

# Analyze speaker patterns in one of the section HTMLs
test_url = "https://api.parliament.uk/historic-hansard/commons/1905/may/02/aliens-bill"
try:
    section_html = fetch_html(test_url)
    speaker_patterns = analyze_speaker_patterns(section_html)
    
    print("Found speaker indication patterns:")
    for pattern_type, examples in speaker_patterns.items():
        print(f"  {pattern_type}: {len(examples)} instances")
        for example in examples[:3]:
            if isinstance(example, tuple):
                print(f"    {' '.join(example)}")
            else:
                print(f"    {example}")
except Exception as e:
    print(f"Error analyzing speaker patterns: {e}")

print(f"\n=== RECOMMENDATIONS ===")
print("1. Focus on EVIDENCE_BASED and ECONOMIC_CLAIMS quotes (highest value)")
print("2. Improve speaker identification using found HTML patterns")
print("3. Prioritize quotes with completeness_score >= 2")
print("4. Look for more COMPARATIVE and IDEOLOGICAL arguments")
print("5. Extract longer passages that include 'because/therefore/however' reasoning")