# diagnostic_collector.py
# Diagnose why collection is yielding few results

from simple_collector import SimpleHansardCollector
import requests
import json

def diagnose_year(year):
    """Diagnose collection issues for a specific year"""
    
    print(f"=== DIAGNOSING {year} ===")
    
    collector = SimpleHansardCollector()
    
    # Get sitting data for the year
    url = f"https://api.parliament.uk/historic-hansard/sittings/{year}.js"
    
    try:
        response = collector.session.get(url)
        if response.status_code != 200:
            print(f"Failed to get sittings data: {response.status_code}")
            return
        
        sitting_data = response.json()
        print(f"Got sitting data: {len(sitting_data)} sittings")
        
        # Extract debates
        debates = collector.extract_relevant_debates(sitting_data)
        print(f"Found {len(debates)} relevant debates")
        
        if len(debates) == 0:
            print("No debates found matching immigration/labour patterns")
            return
        
        # Sample a few debates to see what happens
        sample_debates = debates[:3]  # First 3 debates
        
        for i, debate in enumerate(sample_debates):
            print(f"\nDebate {i+1}: {debate['title']}")
            print(f"  URL: {debate['url']}")
            
            # Try to get content
            try:
                html_response = collector.session.get(debate['url'])
                if html_response.status_code != 200:
                    print(f"  Failed to get HTML: {html_response.status_code}")
                    continue
                
                print(f"  Got HTML content: {len(html_response.text)} chars")
                
                # Extract passages
                passages = collector.extract_passages(html_response.text)
                print(f"  Extracted {len(passages)} passages")
                
                proximity_count = 0
                for passage in passages[:5]:  # Check first 5 passages
                    if collector.check_proximity(passage['text']):
                        proximity_count += 1
                
                print(f"  Passages passing proximity test: {proximity_count}")
                
            except Exception as e:
                print(f"  Error processing debate: {e}")
    
    except Exception as e:
        print(f"Error getting sittings data: {e}")
    
    finally:
        collector.close()

def main():
    """Diagnose a few key years"""
    test_years = [1902, 1908, 1914]
    
    for year in test_years:
        diagnose_year(year)
        print("-" * 50)

if __name__ == "__main__":
    main()