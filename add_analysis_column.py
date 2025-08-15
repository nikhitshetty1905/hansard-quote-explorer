# add_analysis_column.py
# Safely add historian_analysis column to quotes table

import sqlite3

def add_analysis_column():
    """Add historian_analysis column if it doesn't exist"""
    
    conn = sqlite3.connect("hansard_simple.db")
    
    try:
        # Check if column already exists
        cursor = conn.execute("PRAGMA table_info(quotes)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'historian_analysis' not in columns:
            print("Adding historian_analysis column...")
            conn.execute("ALTER TABLE quotes ADD COLUMN historian_analysis TEXT")
            conn.commit()
            print("✅ Column added successfully")
        else:
            print("✅ Column already exists")
        
        # Create index for performance
        try:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_analysis ON quotes(historian_analysis)")
            conn.commit()
            print("✅ Index created")
        except Exception as e:
            print(f"Index creation: {e}")
        
        # Show current table structure
        cursor = conn.execute("PRAGMA table_info(quotes)")
        print("\nCurrent table structure:")
        for row in cursor.fetchall():
            print(f"  {row[1]} ({row[2]})")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    add_analysis_column()