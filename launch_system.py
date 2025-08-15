# launch_system.py
# Simple launcher for the streamlined Hansard system

from simple_collector import SimpleHansardCollector
import subprocess
import sys

def collect_data():
    """Collect data for specified years"""
    print("=== HANSARD QUOTE COLLECTOR ===")
    print("Available years: 1900-1930")
    
    while True:
        try:
            start_year = int(input("Start year (1900-1930): "))
            if 1900 <= start_year <= 1930:
                break
            else:
                print("Please enter a year between 1900 and 1930")
        except ValueError:
            print("Please enter a valid year")
    
    while True:
        try:
            end_year = int(input("End year (1900-1930): "))
            if start_year <= end_year <= 1930:
                break
            else:
                print(f"Please enter a year between {start_year} and 1930")
        except ValueError:
            print("Please enter a valid year")
    
    # Estimate time
    year_range = end_year - start_year + 1
    estimated_hours = year_range * 1.5  # Rough estimate
    
    print(f"\nCollecting quotes for {start_year}-{end_year}")
    print(f"Estimated time: {estimated_hours:.1f} hours")
    
    confirm = input("Continue? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    # Run collection
    collector = SimpleHansardCollector()
    
    try:
        collector.collect_years(start_year, end_year)
        print(f"\n✅ Collection complete!")
        print(f"Database: hansard_simple.db")
        
    except KeyboardInterrupt:
        print(f"\n⏸️  Collection interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        collector.close()

def launch_explorer():
    """Launch the web explorer"""
    print("=== LAUNCHING HANSARD EXPLORER ===")
    
    try:
        import streamlit
        print("Starting web interface...")
        subprocess.run([sys.executable, "-m", "streamlit", "run", "simple_explorer.py"])
    except ImportError:
        print("Streamlit not installed. Install with: pip install streamlit")
    except KeyboardInterrupt:
        print("\nExplorer closed.")

def main():
    print("SIMPLE HANSARD SYSTEM")
    print("=" * 30)
    print("1. Collect quotes from Hansard")
    print("2. Launch web explorer")
    print("3. Exit")
    
    while True:
        choice = input("\nChoice (1-3): ").strip()
        
        if choice == "1":
            collect_data()
            break
        elif choice == "2":
            launch_explorer()
            break
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Please enter 1, 2, or 3")

if __name__ == "__main__":
    main()