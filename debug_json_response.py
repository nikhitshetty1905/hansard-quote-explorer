# debug_json_response.py
# Check what we're actually getting from the endpoint

import requests

def check_response(url):
    """Check what we get from URL"""
    r = requests.get(url, timeout=30, headers={"User-Agent": "HansardResearch/1.0"})
    print(f"URL: {url}")
    print(f"Status: {r.status_code}")
    print(f"Content-Type: {r.headers.get('content-type', 'None')}")
    print(f"Content-Length: {len(r.text)}")
    print(f"First 500 chars: {repr(r.text[:500])}")
    
    if r.headers.get('content-type', '').startswith('application/json'):
        try:
            data = r.json()
            print(f"JSON parsed successfully")
            return data
        except Exception as e:
            print(f"JSON parse error: {e}")
    
    return None

# Check the sitting URL that seemed to work
sitting_url = "https://api.parliament.uk/historic-hansard/commons/1905/may/02"
data = check_response(sitting_url)

if data:
    print(f"\n=== JSON STRUCTURE ===")
    import json
    print(json.dumps(data, indent=2)[:1000])