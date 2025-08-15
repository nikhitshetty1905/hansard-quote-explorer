# app.py - Enhanced Hansard Quote Explorer with Deep Linking
# Immigration × Labour Market Debates (1900-1930)

import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path
import os
from urllib.parse import quote
import re
from datetime import datetime

# Import our modules
from enhanced_historian import EvidenceBasedHistorian
from enhanced_speaker_parser import EnhancedSpeakerParser

st.set_page_config(
    page_title="Hansard Quotes — Clean",
    page_icon="🗂️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Clean styling - minimal approach for Streamlit Cloud
st.markdown("""
<style>
.btn-link { 
    display: inline-block; 
    padding: 8px 12px; 
    border: 1px solid #ddd; 
    border-radius: 6px; 
    background: white; 
    text-decoration: none; 
    color: #111827; 
    margin: 4px 0;
}
.btn-link:hover { background: #f5f5f5; }
.header-wrap { 
    padding: 8px 0 16px; 
    border-bottom: 1px solid #eee; 
    margin-bottom: 16px; 
}
.badge { 
    display: inline-block; 
    padding: 4px 8px; 
    background: #f3f4f6; 
    border-radius: 12px; 
    font-size: 12px; 
    color: #6b7280; 
}
</style>
""", unsafe_allow_html=True)

# Text Fragment Deep Linking Helpers
SMARTS = {"'":"'", "'":"'", """:'"', """:'"', "—":"-", "–":"-", "\u00A0":" "}

def normalize_text(s: str) -> str:
    """Normalize text for better URL fragment matching"""
    if not s: return s
    for k, v in SMARTS.items():
        s = s.replace(k, v)
    return re.sub(r"\s+", " ", s).strip()

def text_fragment_url(base_url: str, exact: str, prefix: str = "", suffix: str = "") -> str:
    """
    Build Scroll-To-Text Fragment:  {url}#:~:text=prefix-,exact,-suffix
    Use small prefix/suffix (2–4 words) if needed to disambiguate.
    """
    base_url = (base_url or "").strip()
    exact_n = normalize_text(exact or "")
    prefix_n = normalize_text(prefix or "")
    suffix_n = normalize_text(suffix or "")
    
    if not base_url or not exact_n:
        return base_url or ""
    
    if prefix_n or suffix_n:
        frag = f"text={quote(prefix_n)}-,{quote(exact_n)},-{quote(suffix_n)}"
    else:
        frag = f"text={quote(exact_n)}"
    
    return f"{base_url}#:~:{frag}"

def make_hansard_link(url: str, quote: str, prefix: str = "", suffix: str = "") -> str:
    """Public helper to create deep-linked Hansard URLs with full quote highlighting"""
    if not quote:
        return url
    
    # Clean and normalize the quote for URL usage
    clean_quote = normalize_text(quote.strip())
    
    # For very long quotes (>800 chars), use a smart excerpt strategy
    if len(clean_quote) > 800:
        # Use first 300 chars + last 100 chars to capture beginning and end
        first_part = clean_quote[:300].strip()
        last_part = clean_quote[-100:].strip()
        
        # Find a good break point (end of sentence or clause)
        for punct in ['. ', '! ', '; ', ', ']:
            if punct in first_part[-50:]:
                break_point = first_part.rfind(punct) + len(punct)
                if break_point > 250:  # Don't make it too short
                    first_part = first_part[:break_point].strip()
                    break
        
        # Create multiple text fragments
        fragments = [first_part]
        if last_part and not last_part in first_part:
            fragments.append(last_part)
        
        # Build URL with multiple text fragments
        frag_parts = [f"text={quote(normalize_text(frag))}" for frag in fragments if frag]
        fragment_url = f"{url}#:~:{'&'.join(frag_parts)}"
        
        return fragment_url
    
    # For shorter quotes, use the full quote
    return text_fragment_url(url, clean_quote, prefix, suffix)

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

def fix_speaker_name(speaker_name):
    """Fix capitalization and formatting issues in speaker names"""
    if not speaker_name:
        return speaker_name
    
    # Remove trailing commas and periods
    name = speaker_name.strip().rstrip(',.')
    
    # Fix all caps names like "SECRETARY of STATE" -> "Secretary of State"
    if name.isupper():
        name = name.title()
    
    # Fix mixed case issues
    # Common titles that should be capitalized properly
    title_fixes = {
        'secretary of state': 'Secretary of State',
        'home department': 'Home Department',
        'foreign office': 'Foreign Office',
        'prime minister': 'Prime Minister',
        'chancellor': 'Chancellor',
        'attorney general': 'Attorney General',
        'regulation of native': 'Regulation of Native',
        'regulation of native and immigra': 'Regulation of Native and Immigration'
    }
    
    name_lower = name.lower()
    for wrong, correct in title_fixes.items():
        if wrong in name_lower:
            name = name_lower.replace(wrong, correct)
    
    # Fix "the SECRETARY" -> "the Secretary"
    words = name.split()
    fixed_words = []
    for word in words:
        if word.isupper() and len(word) > 1:
            fixed_words.append(word.title())
        elif '-' in word:
            # Fix hyphenated names like "Evans-gordon" -> "Evans-Gordon"
            parts = word.split('-')
            fixed_parts = [part.title() if part.islower() or part.isupper() else part for part in parts]
            fixed_words.append('-'.join(fixed_parts))
        else:
            fixed_words.append(word)
    
    return ' '.join(fixed_words)

def main():
    # Clean Header with black background
    st.markdown(
        """
        <div style="text-align: center; padding: 2rem 0; background: #000000; color: white; margin: -1rem -1rem 2rem -1rem;">
            <h1 style="margin: 0; font-size: 3rem; font-weight: bold;">Hansard Quotes</h1>
            <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;">Debates at the intersection of Labour and Migration</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Info box with enhanced features
    st.info("🗂️ **Academic Research Tool** | Explore 530+ parliamentary quotes on immigration and labour (1900-1930) with Claude AI analysis, verified speaker attributions, and **direct deep-links to exact quotes** in original Hansard pages | Only high-quality quotes (confidence ≥ 5) are displayed")
    
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
        # Display results with enhanced cards
        for i, row in enumerate(results):
            # Handle variable number of columns based on what's available
            quote_id, year, date, original_speaker, party, frame, quote, url, analysis, confidence = row[:10]
            
            # Extract optional columns if they exist
            corrected_speaker = row[10] if len(row) > 10 else None
            enhanced_speaker = row[11] if len(row) > 11 else None
            debate_title = row[12] if len(row) > 12 else None
            verified_speaker = row[13] if len(row) > 13 else None
            
            # Use best available speaker name - verified speaker has highest priority
            raw_speaker = verified_speaker or corrected_speaker or enhanced_speaker or original_speaker
            speaker = fix_speaker_name(raw_speaker)
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
                    year_part, month, day = date.split('-')
                    british_date = f"{day}/{month}/{year_part}"
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
                
                # Fix all caps titles
                if title.isupper():
                    title = title.title()
                
                # Fix specific capitalization issues
                title = title.replace('REGULATION OF NATIVE AND IMMIGRA', 'Regulation of Native and Immigration')
                title = title.replace('REGULATION OF NATIVE', 'Regulation of Native')
                
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
                
                # Analysis
                if not analysis:
                    analysis = historian.analyze_quote(quote_id)
                
                if analysis:
                    st.markdown(f"**Analysis:** *{analysis}*")
                else:
                    st.markdown("**Analysis:** *Analysis pending...*")
                
                # Full quote
                st.markdown("**Full Quote:**")
                st.write(quote)
                
                # Enhanced metadata with deep link
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
                    # Enhanced deep link
                    deep_link = make_hansard_link(url, quote)
                    st.markdown(
                        f'<a class="btn-link" href="{deep_link}" target="_blank" rel="noopener">View on Hansard ↗</a>', 
                        unsafe_allow_html=True
                    )
        
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
                raw_final_speaker = verified_speaker or corrected_speaker or enhanced_speaker or original_speaker
                final_speaker = fix_speaker_name(raw_final_speaker)
                
                # Add deep link for download
                deep_link = make_hansard_link(url, quote)
                
                base_data.append([year, date, final_speaker, party, frame, quote, url, deep_link, analysis, debate_title or ""])
            
            df = pd.DataFrame(base_data, columns=['Year', 'Date', 'Speaker', 'Party', 'Frame', 'Quote', 'Hansard_URL', 'Deep_Link_URL', 'Analysis', 'Debate_Title'])
        csv = df.to_csv(index=False)
        
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"hansard_quotes_{min(selected_years)}_{max(selected_years)}.csv",
            mime="text/csv"
        )
    
    else:
        st.info("No high-quality quotes found matching your criteria. Try adjusting the filters.")
    
    # Browser compatibility hint
    st.markdown(
        """
        <script>
        // If not supported, show a tiny hint as a tooltip on buttons (no UI flash if supported)
        try {
          if (!('fragmentDirective' in document)) {
            for (const el of document.querySelectorAll('.btn-link')) {
              if (!el.dataset.hinted) {
                el.title = "If the page doesn't jump to the quote, press Ctrl/Cmd+F and paste the excerpt.";
                el.dataset.hinted = "1";
              }
            }
          }
        } catch(e) {}
        </script>
        """,
        unsafe_allow_html=True
    )
    
    # Footer
    st.markdown("---")
    st.markdown("*Academic Research Tool | UK Parliamentary Debates on Immigration & Labour (1900-1930) | Enhanced with Claude AI analysis, verified speaker attributions, deep-linking to exact quotes, and modern interface*")

if __name__ == "__main__":
    main()