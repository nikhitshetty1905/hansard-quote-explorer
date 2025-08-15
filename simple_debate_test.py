# simple_debate_test.py
# Simple test of debate JSON patterns without emoji characters

import requests
import json

def simple_test():
    """Simple test of debate JSON patterns"""
    
    test_urls = [
        "https://api.parliament.uk/historic-hansard/commons/1905/may/02/aliens-bill.js",
        "https://api.parliament.uk/historic-hansard/sections/351228.js",  # aliens-bill section ID
        "https://api.parliament.uk/historic-hansard/section/351228.js",
        "https://hansard-api.parliament.uk/sections/351228.js",
        "https://api.parliament.uk/historic-hansard/commons/1905/may/02/aliens-bill",  # No .js
    ]
    
    session = requests.Session()
    session.headers.update({"User-Agent": "HansardResearch/1.0"})
    
    for url in test_urls:
        print(f"\nTesting: {url}")
        
        try:
            response = session.get(url, timeout=30)
            print(f"  Status: {response.status_code}")
            print(f"  Content-Type: {response.headers.get('content-type', 'None')}")
            print(f"  Size: {len(response.text)}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'json' in content_type:
                    try:
                        data = response.json()
                        print(f"  SUCCESS: Got JSON data")
                        print(f"  Type: {type(data)}")
                        if isinstance(data, dict):
                            print(f"  Keys: {list(data.keys())[:5]}")
                        elif isinstance(data, list):
                            print(f"  List length: {len(data)}")
                        
                        # Save successful result
                        with open("successful_debate.json", "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        print(f"  Saved to successful_debate.json")
                        break  # Stop after first success
                        
                    except json.JSONDecodeError:
                        print(f"  JSON parse failed")
                else:
                    print(f"  Not JSON response")
            
            elif response.status_code == 404:
                print(f"  404 - endpoint doesn't exist")
                if response.text:
                    print(f"  Error content: {response.text}")
            
            else:
                print(f"  HTTP {response.status_code}")
                
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    print("=== SIMPLE DEBATE JSON TEST ===")
    simple_test()
    
    # If no JSON works, let's also check what the HTML contains
    print(f"\n=== CHECKING HTML VERSION FOR COMPARISON ===")
    html_url = "https://api.parliament.uk/historic-hansard/commons/1905/may/02/aliens-bill"
    
    try:
        response = requests.get(html_url, headers={"User-Agent": "HansardResearch/1.0"})
        print(f"HTML Status: {response.status_code}")
        print(f"HTML Size: {len(response.text)}")
        
        if response.status_code == 200:
            # Look for any JSON-related hints in the HTML
            html_content = response.text.lower()
            json_hints = [".js", "json", "api"]
            
            for hint in json_hints:
                if hint in html_content:
                    # Find context
                    pos = html_content.find(hint)
                    context = html_content[max(0, pos-100):pos+100]
                    print(f"Found '{hint}' in HTML: ...{context}...")
                    break
    
    except Exception as e:
        print(f"HTML test error: {e}")