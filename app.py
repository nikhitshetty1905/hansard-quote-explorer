# app.py - Streamlit Cloud deployment version
# Hansard Quote Explorer (1900-1930) - Immigration × Labour Market Debates

import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path
import os

# Import our modules
from enhanced_historian import EvidenceBasedHistorian
from enhanced_speaker_parser import EnhancedSpeakerParser

st.set_page_config(
    page_title="Hansard Quote Explorer (1900-1930)", 
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Clean white background with SF Pro fonts
st.markdown("""
<style>
    /* Global styling - white background, SF Pro fonts */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #ffffff !important;
        font-family: 'SF Pro Display', 'SF Pro Text', -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
    }
    
    .main {
        background-color: #ffffff !important;
        font-family: 'SF Pro Display', 'SF Pro Text', -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
    }
    
    .main * {
        font-family: 'SF Pro Display', 'SF Pro Text', -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
        color: #000000 !important;
    }
    
    /* Main title styling */
    h1 {
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
        font-weight: 600 !important;
        font-size: 2.5rem !important;
        color: #000000 !important;
        letter-spacing: -0.02em !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Expander styling - clean white with black text */
    .streamlit-expanderHeader {
        font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
        font-weight: 500 !important;
        font-size: 1rem !important;
        color: #000000 !important;
        background-color: #ffffff !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 6px !important;
        padding: 14px 18px !important;
    }
    
    .streamlit-expanderHeader:hover {
        background-color: #f8f8f8 !important;
        border-color: #cccccc !important;
    }
    
    /* Expander content */
    .streamlit-expanderContent {
        background-color: #ffffff !important;
        border: 1px solid #e0e0e0 !important;
        border-top: none !important;
        border-radius: 0 0 6px 6px !important;
        padding: 28px !important;
        line-height: 1.8 !important;
    }
    
    /* Analysis text styling */
    .main em {
        font-style: italic !important;
        color: #000000 !important;
        font-weight: 400 !important;
        line-height: 1.6 !important;
    }
    
    /* Quote text - readable */
    .main p {
        font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
        line-height: 1.7 !important;
        color: #000000 !important;
        font-weight: 400 !important;
        font-size: 16px !important;
    }
    
    /* Force all text to be black */
    .main div, .main span, .main label, .stMarkdown, .stText {
        color: #000000 !important;
    }
    
    /* Download button - black background, white text */
    .stDownloadButton > button {
        background-color: #000000 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
    }
    
    .stDownloadButton > button:hover {
        background-color: #333333 !important;
    }
    
    /* Links styling */
    .main a {
        color: #000000 !important;
        text-decoration: underline !important;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_database():
    """Get database connection"""
    db_path = "hansard_simple.db"
    if not Path(db_path).exists():
        st.error("Database not found. Please contact the administrator.")
        st.stop()
    return sqlite3.connect(db_path, check_same_thread=False)

def main():
    st.title("Hansard Quote Explorer (1900-1930)")
    st.markdown("*Immigration × Labour Market Debates in UK Parliament*")
    
    # Info box
    st.info("🏛️ **Academic Research Tool** | Explore 430+ parliamentary quotes on immigration and labour with enhanced framing analysis | Only high-quality quotes (confidence ≥ 5) are displayed")
    
    db = get_database()
    
    # Get available years
    years_data = db.execute("SELECT DISTINCT year FROM quotes ORDER BY year").fetchall()
    if not years_data:
        st.warning("No data found in database.")
        return
    
    available_years = [row[0] for row in years_data]
    
    # Controls
    col1, col2 = st.columns(2)
    
    with col1:
        if len(available_years) > 1:
            year_range = st.select_slider(
                "Select Year(s)",
                options=available_years,
                value=(min(available_years), max(available_years)),
                format_func=lambda x: str(x)
            )
            if isinstance(year_range, tuple):
                selected_years = list(range(year_range[0], year_range[1] + 1))
            else:
                selected_years = [year_range]
        else:
            selected_years = available_years
            st.write(f"Year: {selected_years[0]}")
    
    with col2:
        # Frame filter
        frames = db.execute("SELECT DISTINCT frame FROM quotes ORDER BY frame").fetchall()
        frame_options = [row[0] for row in frames]
        
        selected_frames = st.multiselect(
            "Filter by Frame",
            options=frame_options,
            default=frame_options,
            help="LABOUR_NEED: Arguments for immigration | LABOUR_THREAT: Arguments against | RACIALISED: Character-based arguments | MIXED: Balanced views"
        )
    
    # Initialize historian
    historian = EvidenceBasedHistorian()
    
    # Build query with confidence filter
    where_conditions = []
    params = []
    
    # Year filter
    if len(selected_years) == 1:
        where_conditions.append("year = ?")
        params.append(selected_years[0])
    else:
        year_placeholders = ",".join(["?"] * len(selected_years))
        where_conditions.append(f"year IN ({year_placeholders})")
        params.extend(selected_years)
    
    # Frame filter
    if selected_frames:
        frame_placeholders = ",".join(["?"] * len(selected_frames))
        where_conditions.append(f"frame IN ({frame_placeholders})")
        params.extend(selected_frames)
    
    # Quality filter - only show high confidence quotes
    min_confidence = 5
    where_conditions.append("confidence >= ?")
    params.append(min_confidence)
    
    # Execute query
    query = """
        SELECT id, year, date, speaker, party, frame, quote, hansard_url, historian_analysis, confidence
        FROM quotes
    """
    
    if where_conditions:
        query += " WHERE " + " AND ".join(where_conditions)
    
    query += " ORDER BY confidence DESC, year, date"
    
    results = db.execute(query, params).fetchall()
    
    # Results info
    total_in_db = db.execute("SELECT COUNT(*) FROM quotes").fetchone()[0]
    st.write(f"**{len(results)} high-quality quotes found** (from {total_in_db} total in database)")
    
    if results:
        # Display results
        for i, (quote_id, year, date, speaker, party, frame, quote, url, analysis, confidence) in enumerate(results):
            with st.expander(f"{speaker} ({date}) - {frame}", expanded=False):
                
                # Historian Analysis
                if not analysis:
                    analysis = historian.analyze_quote(quote_id)
                
                if analysis:
                    st.markdown(f"**Historical Analysis:** *{analysis}*")
                else:
                    st.markdown("**Historical Analysis:** *Analysis pending...*")
                
                # Full quote
                st.markdown("**Full Quote:**")
                st.write(quote)
                
                # Metadata
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.write(f"**Date:** {date}")
                    st.write(f"**Year:** {year}")
                
                with col_b:
                    st.write(f"**Speaker:** {speaker}")
                    if party:
                        st.write(f"**Party:** {party}")
                
                with col_c:
                    st.write(f"**Frame:** {frame}")
                    st.markdown(f"**[View in Hansard]({url})**")
        
        # Summary statistics
        st.markdown("---")
        st.subheader("Summary")
        
        # Frame breakdown
        frame_counts = {}
        for _, _, _, _, _, frame, _, _, _, _ in results:
            frame_counts[frame] = frame_counts.get(frame, 0) + 1
        
        col_x, col_y = st.columns(2)
        
        with col_x:
            st.write("**Frame Distribution:**")
            for frame, count in sorted(frame_counts.items()):
                percentage = (count / len(results)) * 100
                st.write(f"• {frame}: {count} ({percentage:.1f}%)")
        
        with col_y:
            if len(selected_years) > 1:
                year_counts = {}
                for _, year, _, _, _, _, _, _, _, _ in results:
                    year_counts[year] = year_counts.get(year, 0) + 1
                
                st.write("**Year Distribution:**")
                for year, count in sorted(year_counts.items()):
                    st.write(f"• {year}: {count}")
        
        # Download option
        st.markdown("---")
        
        # Prepare data for download
        df = pd.DataFrame(results, columns=['ID', 'Year', 'Date', 'Speaker', 'Party', 'Frame', 'Quote', 'Hansard_URL', 'Analysis', 'Confidence'])
        df = df.drop(['ID', 'Confidence'], axis=1)  # Remove technical fields from export
        csv = df.to_csv(index=False)
        
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"hansard_quotes_{min(selected_years)}_{max(selected_years)}.csv",
            mime="text/csv"
        )
    
    else:
        st.info("No high-quality quotes found matching your criteria. Try adjusting the filters.")
    
    # Footer
    st.markdown("---")
    st.markdown("*Academic Research Tool | UK Parliamentary Debates on Immigration & Labour (1900-1930) | Enhanced with linkage patterns and confidence scoring*")

if __name__ == "__main__":
    main()