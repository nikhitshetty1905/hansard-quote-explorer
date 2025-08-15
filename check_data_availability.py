# check_data_availability.py
# Check data availability across decades to understand coverage gaps

import requests
import calendar

def check_year_availability(year):
    """Check how many sittings are available for a given year"""
    print(f"\n=== Checking {year} ===")
    
    session = requests.Session()
    session.headers.update({"User-Agent": "HansardResearch/1.0"})
    
    available_sittings = 0
    checked_dates = 0
    
    # Check a sample of dates throughout the year
    for month in range(1, 13, 2):  # Check every other month
        month_names = {
            1: "jan", 3: "mar", 5: "may", 7: "jul", 9: "sep", 11: "nov"
        }
        
        if month not in month_names:
            continue
            
        month_name = month_names[month]
        days_in_month = calendar.monthrange(year, month)[1]
        
        # Check first, middle, and last day of each month
        test_days = [1, days_in_month // 2, days_in_month]
        
        for day in test_days:
            checked_dates += 1
            
            # Try different URL patterns
            url_patterns = [
                f"https://api.parliament.uk/historic-hansard/commons/{year}/{month_name}/{day:02d}",
                f"https://api.parliament.uk/historic-hansard/sittings/{year}/{month_name}/{day:02d}",
                f"https://api.parliament.uk/historic-hansard/lords/{year}/{month_name}/{day:02d}"
            ]
            
            for url in url_patterns:
                try:
                    response = session.get(url, timeout=5)
                    if response.status_code == 200 and len(response.text) > 1000:
                        available_sittings += 1
                        break
                except:
                    continue
    
    availability_rate = (available_sittings / checked_dates) * 100
    print(f"  Available sittings: {available_sittings}/{checked_dates} ({availability_rate:.1f}%)")
    
    return {
        'year': year,
        'available': available_sittings,
        'checked': checked_dates,
        'rate': availability_rate
    }

def main():
    """Check data availability across all three decades"""
    
    print("CHECKING DATA AVAILABILITY ACROSS 1900-1930")
    print("=" * 50)
    
    # Sample years from each decade
    test_years = [
        # 1900s
        1902, 1905, 1908,
        # 1910s  
        1912, 1915, 1918,
        # 1920s
        1922, 1925, 1928
    ]
    
    results = []
    
    for year in test_years:
        try:
            result = check_year_availability(year)
            results.append(result)
        except Exception as e:
            print(f"Error checking {year}: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    if results:
        decades = {
            '1900s': [r for r in results if 1900 <= r['year'] <= 1909],
            '1910s': [r for r in results if 1910 <= r['year'] <= 1919],
            '1920s': [r for r in results if 1920 <= r['year'] <= 1929]
        }
        
        for decade, decade_results in decades.items():
            if decade_results:
                avg_rate = sum(r['rate'] for r in decade_results) / len(decade_results)
                total_available = sum(r['available'] for r in decade_results)
                total_checked = sum(r['checked'] for r in decade_results)
                
                print(f"\n{decade}:")
                print(f"  Average availability: {avg_rate:.1f}%")
                print(f"  Total available: {total_available}/{total_checked}")
                
                for result in decade_results:
                    print(f"    {result['year']}: {result['rate']:.1f}%")
        
        # Recommendations
        print(f"\nRecommendations:")
        
        low_availability_decades = []
        for decade, decade_results in decades.items():
            if decade_results:
                avg_rate = sum(r['rate'] for r in decade_results) / len(decade_results)
                if avg_rate < 20:
                    low_availability_decades.append(decade)
        
        if low_availability_decades:
            print(f"- Low data availability in: {', '.join(low_availability_decades)}")
            print("- May need to adjust collection strategy for these periods")
        else:
            print("- Data availability looks good across all decades")

if __name__ == "__main__":
    main()