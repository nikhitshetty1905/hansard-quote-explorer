# analyze_all_decades.py
# Analyze HTML formats across all three decades to prevent parsing issues

import requests
from bs4 import BeautifulSoup
import re

def analyze_decade_html(year, month, day, description):
    """Analyze HTML structure for a specific date"""
    print(f"\n=== {description} ({year}) ===")
    
    session = requests.Session()
    session.headers.update({"User-Agent": "HansardResearch/1.0"})
    
    # Try different URL patterns
    url_patterns = [
        f"https://api.parliament.uk/historic-hansard/commons/{year}/{month}/{day:02d}",
        f"https://api.parliament.uk/historic-hansard/sittings/{year}/{month}/{day:02d}",
        f"https://api.parliament.uk/historic-hansard/lords/{year}/{month}/{day:02d}"
    ]
    
    working_url = None
    for url in url_patterns:
        try:
            response = session.get(url, timeout=10)
            if response.status_code == 200 and len(response.text) > 5000:
                working_url = url
                break
        except:
            continue
    
    if not working_url:
        print(f"  No accessible sitting found for {day}/{month}/{year}")
        return
    
    print(f"  URL: {working_url}")
    
    try:
        response = session.get(working_url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print(f"  Page size: {len(response.text)} chars")
        print(f"  Title: {soup.title.get_text() if soup.title else 'No title'}")
        
        # Analyze structure
        blockquotes = soup.find_all('blockquote')
        spans = soup.find_all('span')
        paragraphs = soup.find_all('p')
        divs = soup.find_all('div')
        
        print(f"  Structure:")
        print(f"    Blockquotes: {len(blockquotes)}")
        print(f"    Spans: {len(spans)}")
        print(f"    Paragraphs: {len(paragraphs)}")
        print(f"    Divs: {len(divs)}")
        
        # Determine likely format
        if len(blockquotes) > 10:
            format_type = "Classic (blockquote-based)"
        elif len(spans) > 50:
            format_type = "Modern (span-based)"
        else:
            format_type = "Unknown/Mixed"
        
        print(f"  Likely format: {format_type}")
        
        # Check for content
        text_content = soup.get_text().lower()
        immigration_count = len(re.findall(r'\b(?:immig(?:rant|ration)s?|aliens?|foreigners?)\b', text_content))
        labour_count = len(re.findall(r'\b(?:labou?r|employment|unemploy(?:ed|ment)?|wage[s]?|worker[s]?)\b', text_content))
        
        print(f"  Content relevance:")
        print(f"    Immigration terms: {immigration_count}")
        print(f"    Labour terms: {labour_count}")
        
        # Test speaker patterns
        speaker_patterns = [
            r'Mr\.\s+[A-Z][a-z]+',
            r'Sir\s+[A-Z][a-z]+',
            r'Lord\s+[A-Z][a-z]+'
        ]
        
        total_speakers = 0
        for pattern in speaker_patterns:
            matches = len(re.findall(pattern, text_content))
            total_speakers += matches
        
        print(f"    Speaker mentions: {total_speakers}")
        
        return {
            'year': year,
            'format': format_type,
            'blockquotes': len(blockquotes),
            'spans': len(spans),
            'immigration_terms': immigration_count,
            'labour_terms': labour_count,
            'speakers': total_speakers
        }
        
    except Exception as e:
        print(f"  Error analyzing: {e}")
        return None

def main():
    """Analyze HTML formats across all three decades"""
    
    print("ANALYZING HTML FORMATS ACROSS 1900-1930")
    print("=" * 60)
    
    # Sample dates from each decade
    test_dates = [
        # 1900s decade
        (1903, "mar", 15, "Early 1900s"),
        (1905, "may", 2, "Mid 1900s - Aliens Act"),
        (1908, "jul", 10, "Late 1900s"),
        
        # 1910s decade  
        (1912, "apr", 20, "Early 1910s"),
        (1914, "aug", 15, "Mid 1910s - WWI start"),
        (1918, "nov", 11, "Late 1910s - WWI end"),
        
        # 1920s decade
        (1922, "jan", 25, "Early 1920s"),
        (1925, "jun", 10, "Mid 1920s"),
        (1929, "oct", 15, "Late 1920s - Stock crash"),
    ]
    
    results = []
    
    for year, month, day, description in test_dates:
        result = analyze_decade_html(year, month, day, description)
        if result:
            results.append(result)
    
    # Summary analysis
    print("\n" + "=" * 60)
    print("SUMMARY ANALYSIS")
    print("=" * 60)
    
    if results:
        print("\nFormat distribution by decade:")
        
        # Group by decade
        decades = {
            '1900s': [r for r in results if 1900 <= r['year'] <= 1909],
            '1910s': [r for r in results if 1910 <= r['year'] <= 1919], 
            '1920s': [r for r in results if 1920 <= r['year'] <= 1929]
        }
        
        for decade, decade_results in decades.items():
            if decade_results:
                print(f"\n{decade}:")
                formats = [r['format'] for r in decade_results]
                for fmt in set(formats):
                    count = formats.count(fmt)
                    print(f"  {fmt}: {count} samples")
                
                # Average structure elements
                avg_blockquotes = sum(r['blockquotes'] for r in decade_results) / len(decade_results)
                avg_spans = sum(r['spans'] for r in decade_results) / len(decade_results)
                print(f"  Avg blockquotes: {avg_blockquotes:.1f}")
                print(f"  Avg spans: {avg_spans:.1f}")
        
        print("\nRecommendations:")
        
        # Check if our parser will handle all formats
        classic_count = sum(1 for r in results if 'Classic' in r['format'])
        modern_count = sum(1 for r in results if 'Modern' in r['format'])
        unknown_count = sum(1 for r in results if 'Unknown' in r['format'])
        
        print(f"- Classic format (blockquote): {classic_count} samples")
        print(f"- Modern format (span): {modern_count} samples") 
        print(f"- Unknown/Mixed format: {unknown_count} samples")
        
        if unknown_count > 0:
            print("⚠️  WARNING: Some samples have unknown format - may need additional parsing logic")
        else:
            print("✅ All samples use known formats - current parser should handle them")

if __name__ == "__main__":
    main()