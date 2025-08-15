# find_json_api.py  
# Try different approaches to get JSON from Hansard API

import requests
import json

def try_json_variations(base_url):
    """Try different ways to get JSON"""
    
    variations = [
        # Different headers
        (base_url, {"Accept": "application/json"}),
        (base_url, {"Accept": "application/json", "Content-Type": "application/json"}),
        
        # Different parameters  
        (base_url + "?format=json", {}),
        (base_url + "?output=json", {}),
        (base_url + ".json", {}),
        (base_url + "/json", {}),
        
        # Different paths
        (base_url.replace("/historic-hansard/", "/historic-hansard/api/"), {}),
        (base_url.replace("/historic-hansard/", "/api/historic-hansard/"), {}),
        
        # Check if there's a modern API
        ("https://hansard-api.parliament.uk/commons/1905/05/02", {}),
        ("https://api.parliament.uk/hansard/commons/1905/05/02", {}),
    ]
    
    for url, headers in variations:
        try:
            default_headers = {"User-Agent": "HansardResearch/1.0"}
            default_headers.update(headers)
            
            r = requests.get(url, timeout=30, headers=default_headers)
            
            print(f"\n--- {url} ---")
            print(f"Status: {r.status_code}")
            print(f"Content-Type: {r.headers.get('content-type', 'None')}")
            
            if r.status_code == 200:
                content_type = r.headers.get('content-type', '')
                if 'json' in content_type:
                    try:
                        data = r.json()
                        print(f"✓ SUCCESS! Got JSON data")
                        print(f"Structure: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                        return url, data
                    except:
                        print(f"JSON parse failed")
                else:
                    print(f"Got HTML/other content ({len(r.text)} chars)")
            else:
                print(f"Failed: {r.status_code}")
                
        except Exception as e:
            print(f"Error: {e}")
    
    return None, None

# Try the sitting URL
base_url = "https://api.parliament.uk/historic-hansard/commons/1905/may/02"
success_url, data = try_json_variations(base_url)

if data:
    print(f"\n=== FOUND JSON API ===")
    print(f"URL: {success_url}")
    with open("hansard_json_sample.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("Saved sample to hansard_json_sample.json")
else:
    print(f"\n=== NO JSON API FOUND ===")
    print("Will need to stick with HTML parsing approach")

# Let's also check if there are any API documentation hints in the HTML
print(f"\n=== CHECKING HTML FOR API HINTS ===")
r = requests.get(base_url, headers={"User-Agent": "HansardResearch/1.0"})
html = r.text.lower()

api_hints = [
    "api", "json", "rest", "endpoint", "/v1/", "/api/",
    "application/json", "data-api", "xhr", "ajax"
]

for hint in api_hints:
    if hint in html:
        # Find context around the hint
        pos = html.find(hint)
        context = html[max(0, pos-50):pos+100]
        print(f"Found '{hint}': ...{context}...")
        break