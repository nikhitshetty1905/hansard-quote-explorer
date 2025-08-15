# explore_json_structure.py
# Deep dive into the JSON structure we found

import requests
import json

def fetch_json(url):
    """Fetch and parse JSON from URL"""
    r = requests.get(url, timeout=30, headers={"User-Agent": "HansardResearch/1.0"})
    r.raise_for_status()
    return r.json()

# Get the sitting data we found
sitting_url = "https://api.parliament.uk/historic-hansard/commons/1905/may/02"
sitting_data = fetch_json(sitting_url)

print("=== SITTING STRUCTURE ===")
print(json.dumps(sitting_data, indent=2)[:2000])

# Extract section information
sitting = sitting_data[0]['house_of_commons_sitting']
sections = sitting['top_level_sections']

print(f"\n=== FOUND {len(sections)} TOP LEVEL SECTIONS ===")

for i, section_wrapper in enumerate(sections):
    section = section_wrapper['section']
    print(f"\nSection {i+1}:")
    print(f"  ID: {section['id']}")
    print(f"  Slug: {section['slug']}")
    print(f"  Title: {section['title']}")
    print(f"  Columns: {section['start_column']}-{section['end_column']}")
    
    # Try to fetch this section as JSON
    section_id = section['id']
    
    # Test different URL patterns for individual sections
    section_patterns = [
        f"https://api.parliament.uk/historic-hansard/sections/{section_id}",
        f"https://api.parliament.uk/historic-hansard/commons/1905/may/02/{section['slug']}",
        f"https://api.parliament.uk/historic-hansard/section/{section_id}",
    ]
    
    found_section_data = False
    for pattern in section_patterns:
        try:
            section_data = fetch_json(pattern)
            print(f"  ✓ JSON available at: {pattern}")
            print(f"  Structure: {list(section_data.keys()) if isinstance(section_data, dict) else type(section_data)}")
            
            # Look for speech content
            if isinstance(section_data, dict):
                if 'speeches' in section_data:
                    print(f"  Contains {len(section_data['speeches'])} speeches")
                if 'content' in section_data:
                    print(f"  Contains content field")
                if 'contributions' in section_data:
                    print(f"  Contains {len(section_data['contributions'])} contributions")
                    
            found_section_data = True
            
            # Save a sample for analysis
            if section['slug'] == 'aliens-bill':
                with open("sample_section.json", "w", encoding="utf-8") as f:
                    json.dump(section_data, f, indent=2, ensure_ascii=False)
                print(f"  Saved aliens-bill section to sample_section.json")
            
            break
            
        except Exception as e:
            print(f"  ✗ {pattern}: {e}")
    
    if not found_section_data:
        print(f"  No JSON endpoint found for this section")

print("\n=== TESTING GENERAL SECTION API ===")

# Test if there's a general sections API pattern
test_section_id = sections[0]['section']['id']  # Use first section ID
general_patterns = [
    f"https://api.parliament.uk/historic-hansard/sections/{test_section_id}",
    f"https://api.parliament.uk/historic-hansard/section/{test_section_id}",
    f"https://hansard.parliament.uk/api/sections/{test_section_id}",
]

for pattern in general_patterns:
    try:
        data = fetch_json(pattern)
        print(f"✓ SUCCESS: {pattern}")
        print(f"  Structure: {list(data.keys()) if isinstance(data, dict) else type(data)}")
        
        # Analyze structure for speech content
        def find_speech_content(obj, path=""):
            """Recursively find speech-like content"""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    if key in ['speech', 'contribution', 'member', 'text', 'content']:
                        print(f"    Found speech-related field: {new_path}")
                    if isinstance(value, (dict, list)):
                        find_speech_content(value, new_path)
            elif isinstance(obj, list) and obj:
                find_speech_content(obj[0], f"{path}[0]")
        
        find_speech_content(data)
        break
        
    except Exception as e:
        print(f"✗ {pattern}: {e}")