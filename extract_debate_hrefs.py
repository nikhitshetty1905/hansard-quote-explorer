# extract_debate_hrefs.py
# Extract actual debate hrefs from sitting JSON to test individual debate endpoints

import requests
import json

def fetch_sitting_json(year, month, day):
    """Fetch sitting JSON and extract debate hrefs"""
    from datetime import datetime
    
    month_abbrev = datetime(year, month, day).strftime("%b").lower()
    url = f"https://api.parliament.uk/historic-hansard/sittings/{year}/{month_abbrev}/{day:02d}.js"
    
    response = requests.get(url, headers={"User-Agent": "HansardResearch/1.0"})
    response.raise_for_status()
    
    return response.json(), url

def extract_hrefs_from_sitting(sitting_data):
    """Extract all debate hrefs from sitting JSON"""
    hrefs = []
    
    if isinstance(sitting_data, list):
        for item in sitting_data:
            if isinstance(item, dict):
                # Check Commons sitting
                if "house_of_commons_sitting" in item:
                    sitting = item["house_of_commons_sitting"]
                    if "top_level_sections" in sitting:
                        for section in sitting["top_level_sections"]:
                            if "section" in section and "slug" in section["section"]:
                                # Construct href from sitting info
                                date_parts = sitting.get("date", "").split("-")
                                if len(date_parts) == 3:
                                    year, month, day = date_parts
                                    month_name = {
                                        "01": "jan", "02": "feb", "03": "mar", "04": "apr",
                                        "05": "may", "06": "jun", "07": "jul", "08": "aug", 
                                        "09": "sep", "10": "oct", "11": "nov", "12": "dec"
                                    }.get(month, month)
                                    
                                    href = f"/commons/{year}/{month_name}/{int(day):02d}/{section['section']['slug']}"
                                    hrefs.append(href)
                
                # Check Lords sitting  
                if "house_of_lords_sitting" in item:
                    sitting = item["house_of_lords_sitting"]
                    if "top_level_sections" in sitting:
                        for section in sitting["top_level_sections"]:
                            if "section" in section and "slug" in section["section"]:
                                date_parts = sitting.get("date", "").split("-")
                                if len(date_parts) == 3:
                                    year, month, day = date_parts
                                    month_name = {
                                        "01": "jan", "02": "feb", "03": "mar", "04": "apr",
                                        "05": "may", "06": "jun", "07": "jul", "08": "aug", 
                                        "09": "sep", "10": "oct", "11": "nov", "12": "dec"
                                    }.get(month, month)
                                    
                                    href = f"/lords/{year}/{month_name}/{int(day):02d}/{section['section']['slug']}"
                                    hrefs.append(href)
    
    return hrefs

def test_debate_json(href):
    """Test individual debate JSON endpoint"""
    url = f"https://api.parliament.uk/historic-hansard{href}.js"
    
    try:
        response = requests.get(url, headers={"User-Agent": "HansardResearch/1.0"}, timeout=30)
        
        if response.status_code == 200:
            try:
                data = response.json()
                return {
                    "status": "success",
                    "url": url,
                    "size": len(response.text),
                    "data": data
                }
            except json.JSONDecodeError:
                return {
                    "status": "json_error",
                    "url": url,
                    "content_type": response.headers.get("content-type"),
                    "sample": response.text[:200]
                }
        else:
            return {
                "status": "http_error", 
                "url": url,
                "status_code": response.status_code
            }
    except Exception as e:
        return {
            "status": "request_error",
            "url": url,
            "error": str(e)
        }

# Test our known working date: 1905-05-02
print("=== EXTRACTING DEBATE HREFS FROM 1905-05-02 ===")

try:
    sitting_data, sitting_url = fetch_sitting_json(1905, 5, 2)
    print(f"Successfully fetched: {sitting_url}")
    
    # Save the sitting data for inspection
    with open("sitting_1905_05_02.json", "w", encoding="utf-8") as f:
        json.dump(sitting_data, f, indent=2, ensure_ascii=False)
    print("Saved sitting data to sitting_1905_05_02.json")
    
    # Show structure
    print(f"\nSitting data structure:")
    if isinstance(sitting_data, list):
        print(f"  Type: list with {len(sitting_data)} items")
        for i, item in enumerate(sitting_data):
            if isinstance(item, dict):
                print(f"  Item {i}: {list(item.keys())}")
                if "house_of_commons_sitting" in item:
                    commons = item["house_of_commons_sitting"]
                    print(f"    Commons sections: {len(commons.get('top_level_sections', []))}")
                    if "top_level_sections" in commons:
                        for j, section in enumerate(commons["top_level_sections"][:3]):  # First 3
                            if "section" in section:
                                print(f"      Section {j}: {section['section'].get('slug', 'no-slug')} - {section['section'].get('title', 'no-title')}")
    
    # Extract hrefs
    hrefs = extract_hrefs_from_sitting(sitting_data)
    print(f"\nExtracted {len(hrefs)} debate hrefs:")
    for href in hrefs[:5]:  # Show first 5
        print(f"  {href}")
    
    # Test first few debate JSON endpoints
    print(f"\n=== TESTING INDIVIDUAL DEBATE JSON ===")
    for i, href in enumerate(hrefs[:3]):  # Test first 3
        print(f"\n--- Testing {href} ---")
        result = test_debate_json(href)
        
        print(f"Status: {result['status']}")
        if result['status'] == 'success':
            print(f"  Size: {result['size']} chars")
            print(f"  Data type: {type(result['data'])}")
            if isinstance(result['data'], dict):
                print(f"  Keys: {list(result['data'].keys())}")
                
            # Save sample for analysis
            if i == 0:  # Save first successful one
                with open("debate_sample.json", "w", encoding="utf-8") as f:
                    json.dump(result['data'], f, indent=2, ensure_ascii=False)
                print(f"  Saved sample to debate_sample.json")
                
        else:
            print(f"  Error: {result.get('error', result.get('status_code', 'Unknown'))}")
    
except Exception as e:
    print(f"Error: {e}")

# Also test a few other successful dates
print(f"\n=== TESTING OTHER SUCCESSFUL DATES ===")

other_dates = [
    (1900, 2, 12),
    (1914, 8, 4), 
    (1918, 11, 11)
]

for year, month, day in other_dates:
    try:
        print(f"\n--- {year}-{month:02d}-{day:02d} ---")
        sitting_data, sitting_url = fetch_sitting_json(year, month, day)
        hrefs = extract_hrefs_from_sitting(sitting_data)
        print(f"Found {len(hrefs)} debates")
        
        if hrefs:
            # Test first debate
            result = test_debate_json(hrefs[0])
            print(f"  First debate ({hrefs[0]}): {result['status']}")
            
    except Exception as e:
        print(f"  Error: {e}")