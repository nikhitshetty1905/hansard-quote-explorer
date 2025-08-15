# enhanced_explorer.py
# High-performance Streamlit explorer with SQLite backend

import streamlit as st
import sqlite3
import pandas as pd
import json
from pathlib import Path

st.set_page_config(
    page_title="Enhanced Hansard Quote Bank", 
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def get_database_connection(db_path="hansard_hybrid.db"):
    """Get cached database connection"""
    if not Path(db_path).exists():
        st.error(f"Database not found: {db_path}")
        st.stop()
    return sqlite3.connect(db_path, check_same_thread=False)

@st.cache_data
def get_database_stats(_conn):
    """Get cached database statistics"""
    cursor = _conn.execute("""
        SELECT 
            COUNT(*) as total_speeches,
            COUNT(DISTINCT date) as total_days,
            COUNT(DISTINCT debate_title) as total_debates,
            COUNT(DISTINCT member) as total_members,
            MIN(date) as earliest_date,
            MAX(date) as latest_date,
            COUNT(CASE WHEN frame IS NOT NULL THEN 1 END) as classified_speeches
        FROM speeches
    """)
    
    stats = cursor.fetchone()
    
    # Frame distribution
    cursor = _conn.execute("""
        SELECT frame, COUNT(*) as count
        FROM speeches 
        WHERE frame IS NOT NULL
        GROUP BY frame
        ORDER BY count DESC
    """)
    
    frame_stats = dict(cursor.fetchall())
    
    # House distribution
    cursor = _conn.execute("""
        SELECT house, COUNT(*) as count
        FROM speeches 
        GROUP BY house
        ORDER BY count DESC
    """)
    
    house_stats = dict(cursor.fetchall())
    
    return {
        'total_speeches': stats[0],
        'total_days': stats[1], 
        'total_debates': stats[2],
        'total_members': stats[3],
        'earliest_date': stats[4],
        'latest_date': stats[5],
        'classified_speeches': stats[6],
        'frame_distribution': frame_stats,
        'house_distribution': house_stats
    }

@st.cache_data
def search_speeches(_conn, search_query=None, frames=None, houses=None, 
                   date_range=None, members=None, min_quality=None, limit=500):
    """Search speeches with caching"""
    
    # Build SQL query
    where_conditions = []
    params = []
    
    # Text search using FTS5
    if search_query and search_query.strip():
        where_conditions.append("""
            s.id IN (
                SELECT rowid FROM speeches_fts 
                WHERE speeches_fts MATCH ?
            )
        """)
        params.append(search_query.strip())
    
    # Frame filter
    if frames:
        where_conditions.append(f"s.frame IN ({','.join(['?' for _ in frames])})")
        params.extend(frames)
    
    # House filter
    if houses:
        where_conditions.append(f"s.house IN ({','.join(['?' for _ in houses])})")
        params.extend(houses)
    
    # Date range filter
    if date_range and len(date_range) == 2:
        where_conditions.append("s.date BETWEEN ? AND ?")
        params.extend(date_range)
    
    # Member filter
    if members:
        where_conditions.append(f"s.member IN ({','.join(['?' for _ in members])})")
        params.extend(members)
    
    # Quality filter
    if min_quality is not None:
        where_conditions.append("s.extraction_quality >= ?")
        params.append(min_quality)
    
    # Build final query
    base_query = """
        SELECT s.date, s.house, s.debate_title, s.member, s.party, 
               s.quote, s.frame, s.url, s.extraction_quality,
               LENGTH(s.quote) as quote_length
        FROM speeches s
    """
    
    if where_conditions:
        query = base_query + " WHERE " + " AND ".join(where_conditions)
    else:
        query = base_query
    
    query += " ORDER BY s.extraction_quality DESC, s.date DESC LIMIT ?"
    params.append(limit)
    
    # Execute query
    cursor = _conn.execute(query, params)
    columns = [desc[0] for desc in cursor.description]
    results = cursor.fetchall()
    
    return pd.DataFrame(results, columns=columns)

def main():
    # Get database connection
    conn = get_database_connection()
    
    # Get database stats
    stats = get_database_stats(conn)
    
    # Header
    st.title("🏛️ Enhanced Hansard Quote Bank")
    st.markdown("*High-performance exploration of UK Parliamentary debates (1900-1930)*")
    
    # Sidebar with database stats
    with st.sidebar:
        st.header("📊 Database Overview")
        st.metric("Total Speeches", f"{stats['total_speeches']:,}")
        st.metric("Classified Speeches", f"{stats['classified_speeches']:,}")
        st.metric("Date Range", f"{stats['earliest_date']} to {stats['latest_date']}")
        st.metric("Total Debates", f"{stats['total_debates']:,}")
        st.metric("Unique Members", f"{stats['total_members']:,}")
        
        st.subheader("Frame Distribution")
        for frame, count in stats['frame_distribution'].items():
            st.write(f"**{frame}**: {count}")
        
        st.subheader("House Distribution")
        for house, count in stats['house_distribution'].items():
            st.write(f"**{house.title()}**: {count}")
    
    # Main search interface
    st.header("🔍 Search & Filter")
    
    # Search controls in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_query = st.text_input(
            "Full-text search",
            help="Search within speech content using FTS5. Use terms like: alien AND wage, unemployment OR competition"
        )
        
        frames = st.multiselect(
            "Frames",
            options=list(stats['frame_distribution'].keys()),
            default=list(stats['frame_distribution'].keys()) if stats['frame_distribution'] else []
        )
    
    with col2:
        houses = st.multiselect(
            "Houses",
            options=list(stats['house_distribution'].keys()),
            default=list(stats['house_distribution'].keys())
        )
        
        min_quality = st.slider(
            "Minimum Quality Score",
            min_value=0.0,
            max_value=10.0,
            value=0.0,
            step=0.5,
            help="Filter by extraction quality score"
        )
    
    with col3:
        # Date range selector
        if stats['earliest_date'] and stats['latest_date']:
            from datetime import datetime
            
            earliest = datetime.strptime(stats['earliest_date'], '%Y-%m-%d').date()
            latest = datetime.strptime(stats['latest_date'], '%Y-%m-%d').date()
            
            date_range = st.date_input(
                "Date Range",
                value=(earliest, latest),
                min_value=earliest,
                max_value=latest
            )
            
            if len(date_range) == 2:
                date_range = [date_range[0].strftime('%Y-%m-%d'), date_range[1].strftime('%Y-%m-%d')]
            else:
                date_range = None
        else:
            date_range = None
        
        # Member filter
        all_members_query = """
            SELECT DISTINCT member 
            FROM speeches 
            WHERE member != 'Unknown Speaker' 
            ORDER BY member
        """
        all_members = [row[0] for row in conn.execute(all_members_query)]
        
        selected_members = st.multiselect(
            "Members",
            options=all_members,
            help="Filter by specific MPs (leave empty for all)"
        )
    
    # Advanced options
    with st.expander("🔧 Advanced Options"):
        col_a, col_b = st.columns(2)
        
        with col_a:
            result_limit = st.selectbox(
                "Result Limit",
                options=[100, 500, 1000, 2000, 5000],
                index=1,
                help="Maximum number of results to display"
            )
        
        with col_b:
            export_format = st.selectbox(
                "Export Format",
                options=["CSV", "JSON", "JSONL"],
                help="Format for downloading results"
            )
    
    # Perform search
    if st.button("🔍 Search", type="primary"):
        with st.spinner("Searching speeches..."):
            results_df = search_speeches(
                conn,
                search_query=search_query if search_query.strip() else None,
                frames=frames if frames else None,
                houses=houses if houses else None,
                date_range=date_range,
                members=selected_members if selected_members else None,
                min_quality=min_quality if min_quality > 0 else None,
                limit=result_limit
            )
        
        # Display results
        st.header(f"📋 Results ({len(results_df)} speeches)")
        
        if len(results_df) > 0:
            # Summary metrics
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            
            with col_m1:
                st.metric("Speeches Found", len(results_df))
            
            with col_m2:
                avg_quality = results_df['extraction_quality'].mean()
                st.metric("Avg Quality", f"{avg_quality:.1f}")
            
            with col_m3:
                unique_debates = results_df['debate_title'].nunique()
                st.metric("Unique Debates", unique_debates)
            
            with col_m4:
                unique_members = results_df['member'].nunique()
                st.metric("Unique Members", unique_members)
            
            # Frame distribution of results
            if 'frame' in results_df.columns:
                frame_counts = results_df['frame'].value_counts()
                st.subheader("Frame Distribution in Results")
                st.bar_chart(frame_counts)
            
            # Results table
            st.subheader("Speech Details")
            
            # Display options
            display_cols = st.multiselect(
                "Columns to display",
                options=['date', 'house', 'debate_title', 'member', 'party', 'frame', 'extraction_quality', 'quote_length', 'url'],
                default=['date', 'house', 'debate_title', 'member', 'frame', 'extraction_quality']
            )
            
            if display_cols:
                display_df = results_df[display_cols + ['quote']].copy()
                
                # Truncate quote for display
                display_df['quote_preview'] = display_df['quote'].apply(lambda x: x[:200] + "..." if len(x) > 200 else x)
                display_df = display_df.drop('quote', axis=1)
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    height=600
                )
            
            # Individual speech viewer
            st.subheader("📄 Individual Speech Viewer")
            
            speech_index = st.selectbox(
                "Select speech to view in full",
                options=range(len(results_df)),
                format_func=lambda x: f"{results_df.iloc[x]['member']} - {results_df.iloc[x]['debate_title'][:50]}..."
            )
            
            if speech_index is not None:
                selected_speech = results_df.iloc[speech_index]
                
                col_s1, col_s2 = st.columns([2, 1])
                
                with col_s1:
                    st.markdown(f"**{selected_speech['member']}** ({selected_speech['date']})")
                    st.markdown(f"*{selected_speech['debate_title']}*")
                    st.markdown(f"**Frame:** {selected_speech.get('frame', 'Not classified')}")
                    
                    # Full quote
                    st.markdown("---")
                    st.markdown(selected_speech['quote'])
                    st.markdown("---")
                    
                    if selected_speech['url']:
                        st.markdown(f"[📄 View in Hansard]({selected_speech['url']})")
                
                with col_s2:
                    st.json({
                        "House": selected_speech['house'],
                        "Date": selected_speech['date'],
                        "Member": selected_speech['member'],
                        "Party": selected_speech.get('party', ''),
                        "Frame": selected_speech.get('frame', 'Not classified'),
                        "Quality": selected_speech['extraction_quality'],
                        "Length": selected_speech['quote_length']
                    })
            
            # Export functionality
            st.subheader("📥 Export Results")
            
            if export_format == "CSV":
                csv_data = results_df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    data=csv_data,
                    file_name="hansard_speeches.csv",
                    mime="text/csv"
                )
            
            elif export_format == "JSON":
                json_data = results_df.to_json(orient='records', indent=2)
                st.download_button(
                    "Download JSON",
                    data=json_data,
                    file_name="hansard_speeches.json",
                    mime="application/json"
                )
            
            elif export_format == "JSONL":
                jsonl_data = "\n".join([
                    json.dumps(row.to_dict(), ensure_ascii=False) 
                    for _, row in results_df.iterrows()
                ])
                st.download_button(
                    "Download JSONL",
                    data=jsonl_data,
                    file_name="hansard_speeches.jsonl",
                    mime="application/x-ndjson"
                )
        
        else:
            st.warning("No speeches found matching your criteria. Try adjusting your filters.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "*Enhanced Hansard Quote Bank powered by hybrid JSON+HTML collection, "
        "SQLite FTS5 search, and intelligent frame classification.*"
    )

if __name__ == "__main__":
    main()