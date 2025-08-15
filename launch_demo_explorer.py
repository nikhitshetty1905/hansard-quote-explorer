# launch_demo_explorer.py
# Launch the explorer pointing to our demo database

import subprocess
import sys
from pathlib import Path

def launch_explorer():
    print("=== LAUNCHING ENHANCED EXPLORER ===")
    print("Using demo database: hansard_demo.db")
    
    # Check if database exists
    if not Path("hansard_demo.db").exists():
        print("Demo database not found. Run quick_demo.py first.")
        return
    
    # Update explorer to use demo database
    explorer_content = """# demo_explorer.py
# Enhanced explorer pointing to demo database

import streamlit as st
import sqlite3
import pandas as pd
import json
from pathlib import Path

st.set_page_config(
    page_title="Demo Hansard Quote Bank", 
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def get_database_connection():
    db_path = "hansard_demo.db"
    if not Path(db_path).exists():
        st.error(f"Database not found: {db_path}")
        st.stop()
    return sqlite3.connect(db_path, check_same_thread=False)

def main():
    st.title("Demo Hansard Quote Bank")
    st.markdown("*Demonstration using May 1905 Aliens Bill debates*")
    
    # Get database connection
    conn = get_database_connection()
    
    # Show database stats
    stats = conn.execute('''
        SELECT 
            COUNT(*) as total_speeches,
            COUNT(DISTINCT debate_title) as debates,
            COUNT(DISTINCT member) as members,
            COUNT(CASE WHEN frame IS NOT NULL THEN 1 END) as classified
        FROM speeches
    ''').fetchone()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Speeches", stats[0])
    col2.metric("Debates", stats[1])
    col3.metric("Members", stats[2])
    col4.metric("Classified", stats[3])
    
    # Frame distribution
    frame_stats = conn.execute('''
        SELECT frame, COUNT(*) as count 
        FROM speeches 
        WHERE frame IS NOT NULL 
        GROUP BY frame 
        ORDER BY count DESC
    ''').fetchall()
    
    st.subheader("Frame Distribution")
    if frame_stats:
        frame_df = pd.DataFrame(frame_stats, columns=['Frame', 'Count'])
        st.bar_chart(frame_df.set_index('Frame'))
    
    # Search interface
    st.subheader("Search Speeches")
    search_term = st.text_input("Search within speeches")
    
    # Get speeches
    if search_term:
        query = '''
            SELECT s.date, s.member, s.debate_title, s.frame, s.quote, s.extraction_quality
            FROM speeches s
            JOIN speeches_fts fts ON s.id = fts.rowid
            WHERE speeches_fts MATCH ?
            ORDER BY s.extraction_quality DESC
        '''
        speeches = conn.execute(query, (search_term,)).fetchall()
    else:
        speeches = conn.execute('''
            SELECT date, member, debate_title, frame, quote, extraction_quality
            FROM speeches
            ORDER BY extraction_quality DESC
        ''').fetchall()
    
    st.write(f"Found {len(speeches)} speeches")
    
    # Display speeches
    for i, (date, member, title, frame, quote, quality) in enumerate(speeches):
        with st.expander(f"{member} - {title} (Quality: {quality})"):
            st.write(f"**Frame:** {frame or 'Not classified'}")
            st.write(f"**Date:** {date}")
            st.write("**Quote:**")
            st.write(quote)
    
    # System info
    st.markdown("---")
    st.markdown("**System Performance Demo:**")
    st.write("✅ Hybrid JSON+HTML collection")
    st.write("✅ SQLite FTS5 full-text search")  
    st.write("✅ Two-stage retrieval system")
    st.write("✅ Frame classification")
    st.write("✅ Quality scoring")
    
    st.markdown("**Ready to scale:**")
    st.write("🚀 1905-1906: ~2 hours, ~10,000 speeches")
    st.write("🚀 1900-1930: ~20 hours, ~100,000 speeches")

if __name__ == "__main__":
    main()
"""
    
    # Write demo explorer
    with open("demo_explorer.py", "w", encoding="utf-8") as f:
        f.write(explorer_content)
    
    print("✅ Demo explorer created")
    print("🚀 Starting Streamlit...")
    
    # Launch streamlit
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "demo_explorer.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Explorer closed")
    except Exception as e:
        print(f"Error launching explorer: {e}")

if __name__ == "__main__":
    launch_explorer()