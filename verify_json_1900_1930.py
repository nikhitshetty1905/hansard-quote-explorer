# verify_json_1900_1930.py
# Comprehensive verification of JSON endpoints for 1900-1930 range

import requests
import json
from datetime import date, datetime
import time

class JSONEndpointVerifier:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "HansardResearch/1.0"})
        self.results = {
            "sitting_tests": [],
            "debate_tests": [],
            "structure_analysis": {},
            "coverage_summary": {}
        }
    
    def test_sitting_json(self, year, month, day):
        """Test sitting-day JSON endpoint"""
        # Convert month to abbreviated form (may, apr, etc)
        month_abbrev = datetime(year, month, day).strftime("%b").lower()
        url = f"https://api.parliament.uk/historic-hansard/sittings/{year}/{month_abbrev}/{day:02d}.js"
        
        try:
            start_time = time.time()
            response = self.session.get(url, timeout=30)
            fetch_time = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    result = {
                        "url": url,
                        "status": "success",
                        "fetch_time": fetch_time,
                        "size": len(response.text),
                        "structure": self.analyze_sitting_structure(data),
                        "debate_count": self.count_debates(data),
                        "houses": self.extract_houses(data)
                    }
                except json.JSONDecodeError as e:
                    result = {
                        "url": url,
                        "status": "json_error",
                        "error": str(e),
                        "content_type": response.headers.get("content-type", ""),
                        "content_sample": response.text[:200]
                    }
            else:
                result = {
                    "url": url,
                    "status": "http_error",
                    "status_code": response.status_code,
                    "error": f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            result = {
                "url": url,
                "status": "request_error",
                "error": str(e)
            }
        
        self.results["sitting_tests"].append(result)
        return result
    
    def analyze_sitting_structure(self, data):
        """Analyze the structure of sitting-day JSON"""
        if isinstance(data, list) and data:
            first_item = data[0]
            return {
                "type": "list",
                "length": len(data),
                "first_item_keys": list(first_item.keys()) if isinstance(first_item, dict) else [],
                "has_commons": any("commons" in str(item) for item in data),
                "has_lords": any("lords" in str(item) for item in data)
            }
        elif isinstance(data, dict):
            return {
                "type": "dict", 
                "keys": list(data.keys()),
                "has_debates": "debates" in data or "sections" in data or "sittings" in data
            }
        else:
            return {"type": type(data).__name__, "value": str(data)[:100]}
    
    def count_debates(self, data):
        """Count number of debates in sitting"""
        count = 0
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    # Look for debate indicators
                    if "house_of_commons_sitting" in item:
                        sitting = item["house_of_commons_sitting"]
                        if "top_level_sections" in sitting:
                            count += len(sitting["top_level_sections"])
                    elif "house_of_lords_sitting" in item:
                        sitting = item["house_of_lords_sitting"]
                        if "top_level_sections" in sitting:
                            count += len(sitting["top_level_sections"])
        return count
    
    def extract_houses(self, data):
        """Extract which houses are present"""
        houses = []
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    if "house_of_commons_sitting" in item:
                        houses.append("commons")
                    if "house_of_lords_sitting" in item:
                        houses.append("lords")
        return list(set(houses))
    
    def test_debate_json(self, href_path):
        """Test individual debate JSON endpoint"""
        url = f"https://api.parliament.uk/historic-hansard{href_path}.js"
        
        try:
            start_time = time.time()
            response = self.session.get(url, timeout=30)
            fetch_time = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    result = {
                        "url": url,
                        "status": "success",
                        "fetch_time": fetch_time,
                        "size": len(response.text),
                        "structure": self.analyze_debate_structure(data),
                        "speech_quality": self.assess_speech_quality(data)
                    }
                except json.JSONDecodeError as e:
                    result = {
                        "url": url,
                        "status": "json_error", 
                        "error": str(e)
                    }
            else:
                result = {
                    "url": url,
                    "status": "http_error",
                    "status_code": response.status_code
                }
                
        except Exception as e:
            result = {
                "url": url,
                "status": "request_error",
                "error": str(e)
            }
        
        self.results["debate_tests"].append(result)
        return result
    
    def analyze_debate_structure(self, data):
        """Analyze structure of debate JSON"""
        structure = {"type": type(data).__name__}
        
        if isinstance(data, dict):
            structure["keys"] = list(data.keys())
            
            # Look for common speech-related fields
            speech_indicators = ["speeches", "contributions", "paragraphs", "content", "text"]
            structure["speech_fields"] = [field for field in speech_indicators if field in data]
            
            # Look for speaker information
            speaker_indicators = ["speaker", "member", "members", "attribution"]
            structure["speaker_fields"] = [field for field in speaker_indicators if field in data]
            
            # Check for nested content
            for key, value in data.items():
                if isinstance(value, list) and value:
                    structure[f"{key}_list_sample"] = type(value[0]).__name__
                    if isinstance(value[0], dict):
                        structure[f"{key}_list_keys"] = list(value[0].keys())[:5]
        
        return structure
    
    def assess_speech_quality(self, data):
        """Assess quality and completeness of speech content"""
        assessment = {
            "has_speech_text": False,
            "has_speaker_attribution": False,
            "estimated_content_length": 0,
            "sample_speaker": None,
            "sample_text": None
        }
        
        def extract_text_recursively(obj, path=""):
            text_content = []
            speakers = []
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key in ["text", "content", "speech"] and isinstance(value, str):
                        text_content.append(value)
                    elif key in ["speaker", "member", "attribution"] and isinstance(value, str):
                        speakers.append(value)
                    elif isinstance(value, (dict, list)):
                        sub_text, sub_speakers = extract_text_recursively(value, f"{path}.{key}")
                        text_content.extend(sub_text)
                        speakers.extend(sub_speakers)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    sub_text, sub_speakers = extract_text_recursively(item, f"{path}[{i}]")
                    text_content.extend(sub_text)
                    speakers.extend(sub_speakers)
            
            return text_content, speakers
        
        text_content, speakers = extract_text_recursively(data)
        
        if text_content:
            assessment["has_speech_text"] = True
            assessment["estimated_content_length"] = sum(len(text) for text in text_content)
            assessment["sample_text"] = text_content[0][:200] if text_content else None
        
        if speakers:
            assessment["has_speaker_attribution"] = True
            assessment["sample_speaker"] = speakers[0] if speakers else None
        
        return assessment

def run_comprehensive_test():
    """Run comprehensive test of 1900-1930 range"""
    verifier = JSONEndpointVerifier()
    
    print("=== COMPREHENSIVE JSON VERIFICATION: 1900-1930 ===")
    
    # Test key dates across the range
    test_dates = [
        (1900, 2, 12),  # Early 1900s
        (1905, 5, 2),   # Our known working date - Aliens Bill
        (1910, 1, 15),  # Mid-decade
        (1914, 8, 4),   # WWI start
        (1918, 11, 11), # WWI end
        (1920, 3, 10),  # Post-war
        (1925, 4, 20),  # Mid-1920s
        (1930, 1, 10),  # End of range
    ]
    
    print(f"\nTesting {len(test_dates)} key dates...")
    
    successful_sittings = []
    for year, month, day in test_dates:
        print(f"\n--- Testing {year}-{month:02d}-{day:02d} ---")
        result = verifier.test_sitting_json(year, month, day)
        
        print(f"Status: {result['status']}")
        if result['status'] == 'success':
            print(f"  Debates found: {result['debate_count']}")
            print(f"  Houses: {result['houses']}")
            print(f"  Fetch time: {result['fetch_time']:.2f}s")
            successful_sittings.append(result)
        else:
            print(f"  Error: {result.get('error', 'Unknown error')}")
    
    print(f"\n=== SITTING-DAY SUMMARY ===")
    print(f"Successful: {len(successful_sittings)}/{len(test_dates)}")
    
    # Test individual debates from successful sittings
    if successful_sittings:
        print(f"\n=== TESTING INDIVIDUAL DEBATES ===")
        
        # Get debate hrefs from successful sittings
        debate_hrefs = []
        for sitting in successful_sittings[:3]:  # Test first 3 successful sittings
            # Extract hrefs from the sitting data (this would need to parse the actual structure)
            print(f"Need to extract debate hrefs from: {sitting['url']}")
            
            # For now, test known debates from our 1905 case
            if "1905" in sitting['url']:
                debate_hrefs = [
                    "/commons/1905/may/02/aliens-bill",
                    "/commons/1905/may/02/aliens-bill-1"
                ]
                break
        
        for href in debate_hrefs:
            print(f"\n--- Testing debate: {href} ---")
            result = verifier.test_debate_json(href)
            
            print(f"Status: {result['status']}")
            if result['status'] == 'success':
                speech_quality = result['speech_quality']
                print(f"  Has speech text: {speech_quality['has_speech_text']}")
                print(f"  Has speakers: {speech_quality['has_speaker_attribution']}")
                print(f"  Content length: {speech_quality['estimated_content_length']} chars")
                if speech_quality['sample_speaker']:
                    print(f"  Sample speaker: {speech_quality['sample_speaker']}")
                if speech_quality['sample_text']:
                    print(f"  Sample text: {speech_quality['sample_text']}")
            else:
                print(f"  Error: {result.get('error', 'Unknown error')}")
    
    # Save results
    with open("json_verification_results.json", "w", encoding="utf-8") as f:
        json.dump(verifier.results, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== FINAL ASSESSMENT ===")
    total_sitting_tests = len(verifier.results["sitting_tests"])
    successful_sitting_tests = len([t for t in verifier.results["sitting_tests"] if t["status"] == "success"])
    
    print(f"Sitting-day JSON success rate: {successful_sitting_tests}/{total_sitting_tests} ({successful_sitting_tests/total_sitting_tests*100:.1f}%)")
    
    total_debate_tests = len(verifier.results["debate_tests"])
    successful_debate_tests = len([t for t in verifier.results["debate_tests"] if t["status"] == "success"])
    
    if total_debate_tests > 0:
        print(f"Individual debate JSON success rate: {successful_debate_tests}/{total_debate_tests} ({successful_debate_tests/total_debate_tests*100:.1f}%)")
    
    # Recommendation
    if successful_sitting_tests >= 6 and successful_debate_tests >= 1:  # 75%+ success rate
        print(f"\n✅ RECOMMENDATION: JSON API approach is VIABLE for 1900-1930")
        print(f"   Proceed with JSON-based collector rewrite")
    elif successful_sitting_tests >= 4:  # 50%+ success rate
        print(f"\n⚠️  RECOMMENDATION: HYBRID approach recommended")
        print(f"   Use JSON where available, HTML parsing as fallback")
    else:
        print(f"\n❌ RECOMMENDATION: Stick with HTML parsing approach")
        print(f"   JSON API coverage insufficient for reliable use")

if __name__ == "__main__":
    run_comprehensive_test()