# simple_explorer.py
# Clean, focused interface for exploring Hansard quotes

import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path
from enhanced_historian import EvidenceBasedHistorian
from enhanced_speaker_parser import EnhancedSpeakerParser

st.set_page_config(
    page_title="Hansard Quote Explorer", 
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
    
    /* Subtitle styling */
    .main > div:first-child > div > div > div > div:nth-child(2) > div > p {
        font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
        font-size: 1.1rem !important;
        color: #000000 !important;
        font-weight: 400 !important;
        margin-top: 0 !important;
    }
    
    /* Sidebar and main background */
    .css-1d391kg, .css-18e3th9, .css-1kyxreq {
        background-color: #ffffff !important;
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
    
    /* Expander content - better spacing for quotes */
    .streamlit-expanderContent {
        background-color: #ffffff !important;
        border: 1px solid #e0e0e0 !important;
        border-top: none !important;
        border-radius: 0 0 6px 6px !important;
        padding: 28px !important;
        line-height: 1.8 !important;
    }
    
    /* Analysis text styling - clean black italic */
    .main em {
        font-style: italic !important;
        color: #000000 !important;
        font-weight: 400 !important;
        line-height: 1.6 !important;
    }
    
    /* Metadata styling */
    .main strong {
        font-weight: 600 !important;
        color: #000000 !important;
    }
    
    /* Quote text - simple and readable */
    .main p {
        font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
        line-height: 1.7 !important;
        color: #000000 !important;
        font-weight: 400 !important;
        font-size: 16px !important;
    }
    
    /* All text elements - force black */
    .main div, .main span, .main label, .main p, .stMarkdown, .stText {
        color: #000000 !important;
        font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
    }
    
    /* Force all Streamlit text to be black */
    .stMarkdown > div, .element-container div, .stExpander div {
        color: #000000 !important;
    }
    
    /* Button styling - white with black text */
    .stButton > button {
        font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
        font-weight: 500 !important;
        border-radius: 6px !important;
        border: 1px solid #cccccc !important;
        background-color: #ffffff !important;
        color: #000000 !important;
        transition: all 0.15s ease !important;
    }
    
    .stButton > button:hover {
        background-color: #f8f8f8 !important;
        border-color: #999999 !important;
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div, .stMultiSelect > div > div {
        font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
        border-radius: 6px !important;
        border-color: #cccccc !important;
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Slider styling */
    .stSlider > div > div {
        background-color: #ffffff !important;
    }
    
    /* Summary section */
    .main hr {
        border-color: #e0e0e0 !important;
        margin: 2rem 0 !important;
    }
    
    /* Clean spacing */
    .main .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        background-color: #ffffff !important;
    }
    
    /* Download button - black background, white text */
    .stDownloadButton > button {
        font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
        font-weight: 500 !important;
        background-color: #000000 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 8px 16px !important;
    }
    
    .stDownloadButton > button:hover {
        background-color: #333333 !important;
    }
    
    /* Links styling */
    .main a {
        color: #000000 !important;
        text-decoration: underline !important;
    }
    
    .main a:hover {
        color: #333333 !important;
    }
    
    /* Remove any background colors from containers */
    .stApp, .main .element-container {
        background-color: #ffffff !important;
    }
    
    /* Metrics and other components */
    .metric-container, .stMetric {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_database():
    db_path = "hansard_simple.db"
    if not Path(db_path).exists():
        st.error("Database not found. Run the collector first.")
        st.stop()
    return sqlite3.connect(db_path, check_same_thread=False)


def main():
    st.title("Hansard Quote Explorer (1900-1930)")
    st.markdown("*Immigration × Labour Market Debates*")
    
    db = get_database()
    
    # Get available years
    years_data = db.execute("SELECT DISTINCT year FROM quotes ORDER BY year").fetchall()
    if not years_data:
        st.warning("No data found. Run the collector first.")
        return
    
    available_years = [row[0] for row in years_data]
    
    # Year selection
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
            default=frame_options
        )
    
    # Initialize enhanced evidence-based historian
    historian = EvidenceBasedHistorian()
    
    # Build query
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
    
    # No search filter - removed for cleaner interface
    
    # Add confidence filter for quality quotes (don't show in UI)
    min_confidence = 5  # Show medium to high quality quotes only
    where_conditions.append("confidence >= ?")
    params.append(min_confidence)
    
    # Execute query with historian analysis and confidence filtering
    query = """
        SELECT id, year, date, speaker, party, frame, quote, hansard_url, historian_analysis, confidence
        FROM quotes
    """
    
    if where_conditions:
        query += " WHERE " + " AND ".join(where_conditions)
    
    query += " ORDER BY confidence DESC, year, date"
    
    results = db.execute(query, params).fetchall()
    
    st.write(f"**{len(results)} quotes found**")
    
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
                
                # Full quote - simple and readable
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
            # Year breakdown if multiple years selected
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
        df = df.drop(['ID', 'Confidence'], axis=1)  # Remove ID and Confidence from export
        csv = df.to_csv(index=False)
        
        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name=f"hansard_quotes_{min(selected_years)}_{max(selected_years)}.csv",
            mime="text/csv"
        )
    
    else:
        st.info("No quotes found matching your criteria.")
    
    # Footer
    st.markdown("---")
    st.markdown("*Simple Hansard Quote Explorer - Immigration × Labour Debates 1900-1930*")

if __name__ == "__main__":
    main()