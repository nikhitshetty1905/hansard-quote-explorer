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
    """Get database connection with pithy Claude AI analysis"""
    # Use neutral-tone database without pretentious academic language
    db_path = "database_neutral.db"
    
    if Path(db_path).exists():
        return sqlite3.connect(db_path, check_same_thread=False)
    
    # Fallback to verbose version
    fallback_path = "database_updated.db"
    if Path(fallback_path).exists():
        st.warning("Using verbose analysis database - may contain lengthy descriptions")
        return sqlite3.connect(fallback_path, check_same_thread=False)
    
    # Final fallback
    original_path = "hansard_simple.db"
    if Path(original_path).exists():
        st.warning("Using original database - Claude AI analysis may not be available")
        return sqlite3.connect(original_path, check_same_thread=False)
    
    st.error("Database not found. Please contact the administrator.")
    st.stop()

def main():
    st.title("Hansard Quote Explorer (1900-1930)")
    st.markdown("*Immigration × Labour Market Debates in UK Parliament*")
    
    # Info box
    st.info("🏛️ **Academic Research Tool** | Explore 530+ parliamentary quotes on immigration and labour (1900-1930) with Claude AI historical analysis, verified speaker attributions, and enhanced framing analysis | Only high-quality quotes (confidence ≥ 5) are displayed")
    
    db = get_database()
    
    # Get available years
    years_data = db.execute("SELECT DISTINCT year FROM quotes ORDER BY year").fetchall()
    if not years_data:
        st.warning("No data found in database.")
        return
    
    available_years = [row[0] for row in years_data]
    
    # Controls
    col1, col2, col3 = st.columns(3)
    
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
        # Add sorting control
        sort_options = {
            "Chronological (Oldest First)": "year, date, confidence DESC",
            "Highest Quality First": "confidence DESC, year, date"
        }
        
        selected_sort = st.selectbox(
            "Sort Order",
            options=list(sort_options.keys()),
            index=0,
            help="Choose how to organize the quotes"
        )
        
    with col3:
        # Frame filter
        frames = db.execute("SELECT DISTINCT frame FROM quotes ORDER BY frame").fetchall()
        frame_options = [row[0] for row in frames]
        
        # Make frame options readable
        readable_frame_options = [frame.replace('_', ' ').title() for frame in frame_options]
        frame_mapping = dict(zip(readable_frame_options, frame_options))
        
        selected_readable_frames = st.multiselect(
            "Filter by Frame",
            options=readable_frame_options,
            default=readable_frame_options,
            help="Labour Need: Arguments for immigration | Labour Threat: Arguments against | Racialised: Character-based arguments | Mixed: Balanced views"
        )
        
        # Convert back to database format
        selected_frames = [frame_mapping[rf] for rf in selected_readable_frames]
    
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
    
    # Execute query - check if verified_speaker column exists
    try:
        # Try to get column info to see what columns exist
        db_columns = db.execute("PRAGMA table_info(quotes)").fetchall()
        column_names = [col[1] for col in db_columns]
        
        # Build query based on available columns
        base_columns = "id, year, date, speaker, party, frame, quote, hansard_url, historian_analysis, confidence"
        optional_columns = []
        
        if 'corrected_speaker' in column_names:
            optional_columns.append('corrected_speaker')
        if 'enhanced_speaker' in column_names:
            optional_columns.append('enhanced_speaker')
        if 'debate_title' in column_names:
            optional_columns.append('debate_title')
        if 'verified_speaker' in column_names:
            optional_columns.append('verified_speaker')
        
        if optional_columns:
            query = f"SELECT {base_columns}, {', '.join(optional_columns)} FROM quotes"
        else:
            query = f"SELECT {base_columns} FROM quotes"
            
    except Exception as e:
        # Fallback to basic query if column check fails
        query = "SELECT id, year, date, speaker, party, frame, quote, hansard_url, historian_analysis, confidence FROM quotes"
    
    if where_conditions:
        query += " WHERE " + " AND ".join(where_conditions)
    
    query += f" ORDER BY {sort_options[selected_sort]}"
    
    results = db.execute(query, params).fetchall()
    
    # Results info
    total_in_db = db.execute("SELECT COUNT(*) FROM quotes").fetchone()[0]
    st.write(f"**{len(results)} high-quality quotes found** (from {total_in_db} total in database)")
    
    if results:
        # Display results
        for i, row in enumerate(results):
            # Handle variable number of columns based on what's available
            quote_id, year, date, original_speaker, party, frame, quote, url, analysis, confidence = row[:10]
            
            # Extract optional columns if they exist
            corrected_speaker = row[10] if len(row) > 10 else None
            enhanced_speaker = row[11] if len(row) > 11 else None
            debate_title = row[12] if len(row) > 12 else None
            verified_speaker = row[13] if len(row) > 13 else None
            
            # Use best available speaker name - verified speaker has highest priority
            speaker = verified_speaker or corrected_speaker or enhanced_speaker or original_speaker
            # Make frame readable
            readable_frame = frame.replace('_', ' ').title()
            
            # Use extracted debate title if available, otherwise URL-based context
            if debate_title:
                debate_context = f"{debate_title} - "
            else:
                # Fallback to URL-based extraction
                debate_context = ""
                if 'aliens' in url.lower():
                    debate_context = "Aliens Act Debate - "
                elif 'unemployment' in url.lower():
                    debate_context = "Unemployment Debate - "
                elif 'labour' in url.lower():
                    debate_context = "Labour Debate - "
            
            # Convert date to British format (DD/MM/YYYY)
            try:
                # Assuming date is in YYYY-MM-DD or DD/MM/YYYY format from database
                if '-' in date and len(date.split('-')[0]) == 4:
                    # Convert from YYYY-MM-DD to DD/MM/YYYY
                    year, month, day = date.split('-')
                    british_date = f"{day}/{month}/{year}"
                else:
                    british_date = date  # Already in correct format or different format
            except:
                british_date = date  # Fallback to original if parsing fails
            
            # Clean up debate title for header
            def clean_debate_title(title):
                if not title:
                    return ""
                # Remove trailing periods and extra spaces
                title = title.strip().rstrip('.')
                # Take first part before em dash or regular dash
                if '—' in title:
                    title = title.split('—')[0].strip()
                elif ' - ' in title and len(title) > 40:
                    title = title.split(' - ')[0].strip()
                # Limit length and clean up
                if len(title) > 35:
                    title = title[:32] + "..."
                return title
            
            # Use cleaned debate title
            clean_title = clean_debate_title(debate_title) if debate_title else ""
            if clean_title:
                debate_context = f"{clean_title} - "
            elif 'aliens' in url.lower():
                debate_context = "Aliens Act Debate - "
            elif 'unemployment' in url.lower():
                debate_context = "Unemployment Debate - "
            elif 'labour' in url.lower():
                debate_context = "Labour Debate - "
            else:
                debate_context = ""
            
            # Create clean readable header (no frame)
            party_info = f" ({party})" if party else ""
            header = f"{british_date}: {debate_context}{speaker}{party_info}"
            
            with st.expander(header, expanded=False):
                
                # Historian Analysis
                if not analysis:
                    analysis = historian.analyze_quote(quote_id)
                
                if analysis:
                    st.markdown(f"**Analysis:** *{analysis}*")
                else:
                    st.markdown("**Analysis:** *Analysis pending...*")
                
                # Full quote
                st.markdown("**Full Quote:**")
                st.write(quote)
                
                # Metadata
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.write(f"**📅 Date:** {british_date}")
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
        for row in results:
            frame = row[5]  # frame is the 6th column (0-indexed)
            frame_counts[frame] = frame_counts.get(frame, 0) + 1
        
        col_x, col_y = st.columns(2)
        
        with col_x:
            st.write("**Frame Distribution:**")
            for frame, count in sorted(frame_counts.items()):
                percentage = (count / len(results)) * 100
                readable_frame = frame.replace('_', ' ').title()
                st.write(f"• {readable_frame}: {count} ({percentage:.1f}%)")
        
        with col_y:
            if len(selected_years) > 1:
                year_counts = {}
                for row in results:
                    year = row[1]  # year is the 2nd column (0-indexed)
                    year_counts[year] = year_counts.get(year, 0) + 1
                
                st.write("**Year Distribution:**")
                for year, count in sorted(year_counts.items()):
                    st.write(f"• {year}: {count}")
        
        # Download option
        st.markdown("---")
        
        # Prepare data for download - handle variable column counts
        if results:
            # Create base columns that always exist
            base_data = []
            for row in results:
                # Extract the data we processed above
                quote_id, year, date, original_speaker, party, frame, quote, url, analysis, confidence = row[:10]
                
                # Extract optional columns if they exist
                corrected_speaker = row[10] if len(row) > 10 else None
                enhanced_speaker = row[11] if len(row) > 11 else None
                debate_title = row[12] if len(row) > 12 else None
                verified_speaker = row[13] if len(row) > 13 else None
                
                # Use best available speaker
                final_speaker = verified_speaker or corrected_speaker or enhanced_speaker or original_speaker
                
                base_data.append([year, date, final_speaker, party, frame, quote, url, analysis, debate_title or ""])
            
            df = pd.DataFrame(base_data, columns=['Year', 'Date', 'Speaker', 'Party', 'Frame', 'Quote', 'Hansard_URL', 'Analysis', 'Debate_Title'])
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
    st.markdown("*Academic Research Tool | UK Parliamentary Debates on Immigration & Labour (1900-1930) | Enhanced with Claude AI historical analysis, verified speaker attributions, chronological organization, debate context, and confidence scoring*")

if __name__ == "__main__":
    main()