# html_analyzer.py
# Analyze HTML structure differences between working and non-working years

import requests
from bs4 import BeautifulSoup
import re

def analyze_html_structure(url, year, description):
    """Analyze the HTML structure of a Hansard page"""
    print(f"\n=== {description} ({year}) ===")
    print(f"URL: {url}")
    
    try:
        session = requests.Session()
        session.headers.update({"User-Agent": "HansardResearch/1.0"})
        
        response = session.get(url, timeout=10)
        if response.status_code != 200:
            print(f"Failed to get page: {response.status_code}")
            return
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print(f"Page size: {len(response.text)} chars")
        print(f"Title: {soup.title.get_text() if soup.title else 'No title'}")
        
        # Look for different structural elements
        print("\nStructural elements:")
        
        # Check for common parliamentary elements
        elements_to_check = [
            ('blockquote', 'Speech blocks'),
            ('p', 'Paragraphs'),
            ('div', 'Div containers'),
            ('span', 'Span elements'),
            ('a', 'Links'),
            ('h1, h2, h3, h4', 'Headers'),
            ('table', 'Tables'),
            ('ul, ol', 'Lists')
        ]
        
        for selector, description in elements_to_check:
            elements = soup.select(selector)
            print(f"  {description}: {len(elements)} found")
        
        # Look for speaker patterns
        print("\nSpeaker identification patterns:")
        text_content = soup.get_text()
        
        speaker_patterns = [
            (r'Mr\.\s+[A-Z][a-z]+', 'Mr. Speaker'),
            (r'Sir\s+[A-Z][a-z]+', 'Sir Speaker'),
            (r'Lord\s+[A-Z][a-z]+', 'Lord Speaker'),
            (r'The\s+Secretary', 'Secretary'),
            (r'The\s+Minister', 'Minister')
        ]
        
        for pattern, desc in speaker_patterns:
            matches = re.findall(pattern, text_content)
            print(f"  {desc}: {len(matches)} matches")
            if matches and len(matches) <= 5:
                print(f"    Examples: {matches[:3]}")
        
        # Check for immigration/labour terms
        print("\nContent analysis:")
        immigration_terms = re.findall(r'\b(?:immig(?:rant|ration)s?|aliens?|foreigners?)\b', text_content, re.IGNORECASE)
        labour_terms = re.findall(r'\b(?:labou?r|employment|unemploy(?:ed|ment)?|wage[s]?|worker[s]?)\b', text_content, re.IGNORECASE)
        
        print(f"  Immigration terms: {len(immigration_terms)} found")
        print(f"  Labour terms: {len(labour_terms)} found")
        
        # Sample text structure
        print("\nSample text structure (first 500 chars):")
        clean_text = re.sub(r'\s+', ' ', text_content.strip())
        print(f"  {clean_text[:500]}...")
        
        # Look for paragraph breaks and structure
        paragraphs = [p.strip() for p in text_content.split('\n') if p.strip()]
        long_paragraphs = [p for p in paragraphs if len(p) > 100]
        print(f"\nParagraph analysis:")
        print(f"  Total paragraphs: {len(paragraphs)}")
        print(f"  Long paragraphs (>100 chars): {len(long_paragraphs)}")
        
        if long_paragraphs:
            print(f"  Sample long paragraph: {long_paragraphs[0][:200]}...")
        
    except Exception as e:
        print(f"Error analyzing {url}: {e}")

def main():
    """Compare HTML structures between working and non-working years"""
    
    # Test URLs from working years (1900-1906)
    working_urls = [
        ("https://api.parliament.uk/historic-hansard/commons/1905/may/02/aliens-bill", 1905, "Working year - Aliens Bill"),
        ("https://api.parliament.uk/historic-hansard/commons/1904/jul/28", 1904, "Working year - July sitting"),
    ]
    
    # Test URLs from non-working years (1907-1910) 
    non_working_urls = [
        ("https://api.parliament.uk/historic-hansard/commons/1908/may/05", 1908, "Non-working year - May sitting"),
        ("https://api.parliament.uk/historic-hansard/commons/1907/feb/20", 1907, "Non-working year - Feb sitting"),
        ("https://api.parliament.uk/historic-hansard/commons/1909/may/05", 1909, "Non-working year - May sitting"),
    ]
    
    print("ANALYZING HTML STRUCTURE DIFFERENCES")
    print("=" * 50)
    
    for url, year, desc in working_urls:
        analyze_html_structure(url, year, desc)
    
    print("\n" + "=" * 50)
    print("NON-WORKING YEARS:")
    
    for url, year, desc in non_working_urls:
        analyze_html_structure(url, year, desc)

if __name__ == "__main__":
    main()