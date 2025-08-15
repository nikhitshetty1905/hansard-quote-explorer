# app.py - Enhanced Hansard Quote Explorer with Deep Linking
# Immigration × Labour Market Debates (1900-1930)

import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path
import os
from urllib.parse import quote as url_quote
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

# Exact Cloudflare Agents UI Match
st.markdown("""
<style>
/* Import Inter font exactly as Cloudflare uses */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@300;400;500;600&display=swap');

/* Reset and global styling */
.main .block-container {
    padding: 0;
    max-width: none;
}

/* Exact Cloudflare color variables */
:root {
    --cf-orange: #FF6B00;
    --cf-orange-hover: #e66000;
    --cf-orange-light: #fff5ef;
}

/* Exact Cloudflare font stack */
.cf-font {
    font-family: "Inter", sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial;
}

/* Typography hierarchy matching Cloudflare */
h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, 
.stSelectbox, .stMultiselect, .stSlider, .stButton, .stDownloadButton {
    font-family: "Inter", sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial;
    font-weight: 700;
    line-height: 1.2;
    letter-spacing: -0.02em;
}

/* Body text with Inter */
body, .stMarkdown, .stText, p, div, span {
    font-family: "Inter", sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial;
    font-weight: 400;
    line-height: 1.5;
}

/* Analysis text with serif complement */
.analysis-text {
    font-family: 'Source Serif 4', 'Georgia', 'Times New Roman', serif;
    font-weight: 400;
    font-style: normal;
    line-height: 1.6;
    color: #374151;
    background: #f8fafc;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    border-left: 4px solid var(--cf-orange);
    margin: 1rem 0;
}

/* Hero section */
.hero-section {
    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
    color: white;
    text-align: center;
    padding: 4rem 2rem;
    margin: -1rem -1rem 3rem -1rem;
}

.hero-title {
    font-size: 3.5rem;
    font-weight: 700;
    margin: 0 0 1rem 0;
    letter-spacing: -0.03em;
    color: var(--cf-orange);
    font-family: "Inter", sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial;
}

.hero-subtitle {
    font-family: "Inter", sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial;
    font-size: 1.25rem;
    font-weight: 400;
    opacity: 0.9;
    margin: 0;
    max-width: 600px;
    margin: 0 auto;
    line-height: 1.5;
    color: white;
}

/* Content container */
.content-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 2rem;
}

/* Professional orange color scheme */
:root {
    --cf-orange: #ff6600;
    --cf-orange-hover: #e55a00;
    --cf-orange-light: #fff4f0;
}


/* Controls section */
.controls-section {
    background: #f8fafc;
    border-radius: 16px;
    padding: 2rem;
    margin: 2rem 0;
    border: 1px solid #e2e8f0;
}

/* Exact Cloudflare primary button styling */
.btn-primary { 
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 0.5rem;
    background: var(--cf-orange);
    text-decoration: none;
    color: #FFFFFF !important;
    font-family: "Inter", sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial;
    font-weight: 600;
    font-size: 14px;
    line-height: 1.2;
    transition: background-color 0.2s ease;
    cursor: pointer;
}

.btn-primary:hover { 
    background: var(--cf-orange-hover);
    color: #FFFFFF !important;
}

/* Exact Cloudflare secondary button styling */
.btn-secondary {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0.75rem 1.5rem;
    border: 1px solid var(--cf-orange);
    border-radius: 0.5rem;
    background: #FFFFFF;
    text-decoration: none;
    color: var(--cf-orange) !important;
    font-family: "Inter", sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial;
    font-weight: 600;
    font-size: 14px;
    line-height: 1.2;
    transition: background-color 0.2s ease;
    cursor: pointer;
}

.btn-secondary:hover {
    background: var(--cf-orange-light);
    color: var(--cf-orange) !important;
}

/* Legacy button class for compatibility */
.btn-link { 
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 0.5rem;
    background: var(--cf-orange);
    text-decoration: none;
    color: #FFFFFF !important;
    font-family: "Inter", sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial;
    font-weight: 600;
    font-size: 14px;
    line-height: 1.2;
    transition: background-color 0.2s ease;
    cursor: pointer;
}

.btn-link:hover { 
    background: var(--cf-orange-hover);
    color: #FFFFFF !important;
}

/* Quote cards with professional styling */
.quote-expander {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    margin: 1.5rem 0;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    transition: all 0.3s ease;
    overflow: hidden;
}

.quote-expander:hover {
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
    border-color: var(--cf-orange);
}

/* Cloudflare-style section headers */
.section-header {
    font-family: "Inter", sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial;
    font-size: 2.25rem;
    font-weight: 700;
    color: var(--cf-orange);
    text-align: center;
    margin: 3rem 0 2rem 0;
    letter-spacing: -0.02em;
    line-height: 1.1;
}

.section-subheader {
    font-family: "Inter", sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial;
    font-size: 1.5rem;
    font-weight: 600;
    color: #1a1a1a;
    margin: 2rem 0 1rem 0;
    line-height: 1.2;
}

/* Summary grid */
.summary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    margin: 2rem 0;
}

.summary-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 2rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    transition: all 0.3s ease;
}

.summary-card:hover {
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
}

.summary-card h4 {
    font-size: 1.25rem;
    font-weight: 600;
    color: #1a1a1a;
    margin: 0 0 1rem 0;
}

/* Results counter */
.results-counter {
    text-align: center;
    font-size: 1.1rem;
    font-weight: 500;
    color: #374151;
    margin: 2rem 0;
    padding: 1rem;
    background: #f8fafc;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
}

/* Download section */
.download-section {
    text-align: center;
    margin: 3rem 0;
    padding: 2rem;
    background: #f8fafc;
    border-radius: 16px;
    border: 1px solid #e2e8f0;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .hero-title {
        font-size: 2.5rem;
    }
    
    .content-container {
        padding: 0 1rem;
    }
    
    .controls-section {
        padding: 1.5rem;
    }
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
        frag = f"text={url_quote(prefix_n)}-,{url_quote(exact_n)},-{url_quote(suffix_n)}"
    else:
        frag = f"text={url_quote(exact_n)}"
    
    return f"{base_url}#:~:{frag}"

def clean_quote_for_matching(quote: str) -> str:
    """Clean quote text for better matching with Hansard pages"""
    if not quote:
        return quote
    
    # Basic normalization
    text = normalize_text(quote.strip())
    
    # Remove common parliamentary formatting that might not match
    text = re.sub(r'\bhon\.\s+Member\b', 'hon. Member', text, flags=re.IGNORECASE)
    text = re.sub(r'\bMr\.\s+Speaker\b', 'Mr. Speaker', text, flags=re.IGNORECASE)
    
    # Remove extra quotes and formatting
    text = re.sub(r'[""''`]', '"', text)
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def make_hansard_link(url: str, quote: str, prefix: str = "", suffix: str = "") -> str:
    """Public helper to create deep-linked Hansard URLs with multiple fallback strategies"""
    if not quote:
        return url
    
    clean_quote = clean_quote_for_matching(quote)
    
    # Strategy 1: Try distinctive middle portion (often works better than start/end)
    if len(clean_quote) > 200:
        # Find a good middle excerpt (avoid "I beg to ask" beginnings)
        start_pos = max(50, len(clean_quote) // 4)
        middle_length = min(200, len(clean_quote) - start_pos)
        middle_part = clean_quote[start_pos:start_pos + middle_length]
        
        # Find sentence boundaries
        for punct in ['. ', '! ', '; ']:
            if punct in middle_part[:50]:
                sentence_start = middle_part.find(punct) + len(punct)
                middle_part = middle_part[sentence_start:].strip()
                break
        
        if len(middle_part) > 30:  # Only use if substantial
            fragments = [middle_part[:150]]  # Limit to 150 chars for reliability
        else:
            fragments = [clean_quote[:150]]  # Fallback to beginning
    else:
        fragments = [clean_quote]
    
    # Strategy 2: Add first sentence as backup
    first_sentence_match = re.match(r'^[^.!?]+[.!?]', clean_quote)
    if first_sentence_match and len(first_sentence_match.group()) > 20:
        first_sentence = first_sentence_match.group().strip()
        if first_sentence not in ' '.join(fragments):
            fragments.append(first_sentence)
    
    # Strategy 3: Add most distinctive phrase (words not common in all quotes)
    distinctive_words = []
    for word in clean_quote.split():
        if len(word) > 6 and word.lower() not in ['secretary', 'whether', 'colonies', 'question', 'member']:
            distinctive_words.append(word)
    
    if len(distinctive_words) >= 3:
        distinctive_phrase = ' '.join(distinctive_words[:5])
        if len(distinctive_phrase) > 20 and distinctive_phrase not in ' '.join(fragments):
            fragments.append(distinctive_phrase)
    
    # Build URL with multiple fallback fragments
    frag_parts = [f"text={url_quote(frag)}" for frag in fragments[:3] if frag and len(frag) > 15]
    if frag_parts:
        return f"{url}#:~:{'&'.join(frag_parts)}"
    
    # Final fallback
    return text_fragment_url(url, clean_quote[:100], prefix, suffix)

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
    # Professional Hero Section
    st.markdown(
        """
        <div class="hero-section">
            <div class="hero-title">Hansard Quotes</div>
            <div class="hero-subtitle">Debates at the intersection of Labour and Migration</div>
            <div style="font-family: 'Inter', sans-serif; font-size: 0.875rem; font-weight: 400; opacity: 0.7; margin-top: 1rem; max-width: 700px; margin-left: auto; margin-right: auto; line-height: 1.4;">
                Academic Research Tool | Explore 530+ parliamentary quotes on immigration and labour (1900-1930), verified speaker attributions, and direct deep-links to exact quotes in original Hansard pages.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Content container
    st.markdown('<div class="content-container">', unsafe_allow_html=True)
    
    db = get_database()
    
    # Get available years
    years_data = db.execute("SELECT DISTINCT year FROM quotes ORDER BY year").fetchall()
    if not years_data:
        st.warning("No data found in database.")
        return
    
    available_years = [row[0] for row in years_data]
    
    # Professional Controls Section
    st.markdown('<div class="controls-section">', unsafe_allow_html=True)
    st.markdown('<h3 class="section-subheader">Filter & Search Options</h3>', unsafe_allow_html=True)
    
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
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close controls section
    
    
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
    
    # Results info with professional styling
    total_in_db = db.execute("SELECT COUNT(*) FROM quotes").fetchone()[0]
    st.markdown(
        f"""
        <div class="results-counter">
            <strong>{len(results)} high-quality quotes found</strong> (from {total_in_db} total in database)
        </div>
        """,
        unsafe_allow_html=True
    )
    
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
                    st.markdown(f'<div class="analysis-text"><strong>Analysis:</strong> {analysis}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="analysis-text"><strong>Analysis:</strong> Analysis pending...</div>', unsafe_allow_html=True)
                
                # Full quote
                st.markdown("**Full Quote:**")
                st.write(quote)
                
                # Enhanced metadata with deep link
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.write(f"**📅 Date:** {british_date}")
                
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
        
        # Professional Summary Section
        st.markdown('<div class="section-header">Summary</div>', unsafe_allow_html=True)
        
        # Frame breakdown
        frame_counts = {}
        for row in results:
            frame = row[5]  # frame is the 6th column (0-indexed)
            frame_counts[frame] = frame_counts.get(frame, 0) + 1
        
        st.markdown('<div class="summary-grid">', unsafe_allow_html=True)
        
        col_x, col_y = st.columns(2)
        
        with col_x:
            st.markdown('<div class="summary-card">', unsafe_allow_html=True)
            st.markdown('<h4>Frame Distribution</h4>', unsafe_allow_html=True)
            for frame, count in sorted(frame_counts.items()):
                percentage = (count / len(results)) * 100
                readable_frame = frame.replace('_', ' ').title()
                st.write(f"• {readable_frame}: {count} ({percentage:.1f}%)")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col_y:
            if len(selected_years) > 1:
                year_counts = {}
                for row in results:
                    year = row[1]  # year is the 2nd column (0-indexed)
                    year_counts[year] = year_counts.get(year, 0) + 1
                
                st.markdown('<div class="summary-card">', unsafe_allow_html=True)
                st.markdown('<h4>Year Distribution</h4>', unsafe_allow_html=True)
                for year, count in sorted(year_counts.items()):
                    st.write(f"• {year}: {count}")
                st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close summary grid
        
        # Professional Download Section
        st.markdown('<div class="download-section">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-subheader">Export Data</h3>', unsafe_allow_html=True)
        
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
        st.markdown('</div>', unsafe_allow_html=True)  # Close download section
    
    else:
        st.info("No high-quality quotes found matching your criteria. Try adjusting the filters.")
    
    # Close content container
    st.markdown('</div>', unsafe_allow_html=True)
    
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

if __name__ == "__main__":
    main()