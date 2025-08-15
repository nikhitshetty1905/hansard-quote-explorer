# efficient_collector.py
# High-performance Hansard collector with SQLite FTS5 and optimized parsing

import requests
import sqlite3
import re
import json
import hashlib
from datetime import date, datetime
from bs4 import BeautifulSoup
from pathlib import Path

# ===== DATABASE SETUP =====

def init_database(db_path="hansard_speeches.db"):
    """Initialize SQLite database with FTS5 for fast text search"""
    conn = sqlite3.connect(db_path)
    
    # Create main speeches table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS speeches (
            id INTEGER PRIMARY KEY,
            dedup_key TEXT UNIQUE,
            date TEXT,
            house TEXT,
            debate_title TEXT,
            member TEXT,
            party TEXT,
            quote TEXT,
            url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create FTS5 virtual table for fast text search
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS speeches_fts USING fts5(
            quote, member, debate_title, 
            content='speeches',
            content_rowid='id',
            tokenize='porter'
        )
    """)
    
    # Create triggers to keep FTS5 in sync
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS speeches_ai AFTER INSERT ON speeches BEGIN
            INSERT INTO speeches_fts(rowid, quote, member, debate_title) 
            VALUES (new.id, new.quote, new.member, new.debate_title);
        END
    """)
    
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS speeches_ad AFTER DELETE ON speeches BEGIN
            INSERT INTO speeches_fts(speeches_fts, rowid, quote, member, debate_title) 
            VALUES('delete', old.id, old.quote, old.member, old.debate_title);
        END
    """)
    
    conn.commit()
    return conn

# ===== OPTIMIZED PARSING =====

class OptimizedParser:
    def __init__(self):
        # Precompile regex patterns
        self.speaker_patterns = [
            re.compile(r'(Mr\.|Mrs\.|Sir|Lord|Dr\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*:', re.MULTILINE),
            re.compile(r'(Mr\.|Mrs\.|Sir|Lord|Dr\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:said|asked|replied|continued)', re.MULTILINE),
            re.compile(r'^([A-Z][A-Z\s]{3,}):\s*', re.MULTILINE),
            re.compile(r'The\s+(Secretary|Minister|President|Chairman)\s+of\s+State', re.MULTILINE),
        ]
        
        # Immigration and labor terms for proximity matching
        self.immigration_terms = re.compile(r'\b(?:immigration|immigrant[s]?|alien[s]?|foreign(?:er|ers)?)\b', re.IGNORECASE)
        self.labor_terms = re.compile(r'\b(?:labour|labor|worker[s]?|employment|job[s]?|wage[s]?|unemploy)\b', re.IGNORECASE)
        
        # Text cleaning patterns
        self.space_cleaner = re.compile(r'\s+')
        self.sentence_splitter = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')
    
    def clean_text(self, text):
        """Clean and normalize text"""
        return self.space_cleaner.sub(' ', text).strip()
    
    def find_speaker_boundaries(self, html_text):
        """Find speaker boundaries with precompiled patterns"""
        speaker_positions = []
        
        for pattern in self.speaker_patterns:
            for match in pattern.finditer(html_text):
                speaker_name = match.group(0).rstrip(':').rstrip()
                speaker_name = re.sub(r'\s+(?:said|asked|replied|continued)$', '', speaker_name)
                
                speaker_positions.append({
                    'position': match.start(),
                    'speaker': speaker_name
                })
        
        speaker_positions.sort(key=lambda x: x['position'])
        return speaker_positions
    
    def proximity_check_fast(self, text, window_words=40):
        """Fast proximity check using precompiled patterns"""
        imm_matches = [(m.start(), m.end()) for m in self.immigration_terms.finditer(text)]
        lab_matches = [(m.start(), m.end()) for m in self.labor_terms.finditer(text)]
        
        if not imm_matches or not lab_matches:
            return False
        
        # Convert character positions to approximate word positions
        words = text.split()
        word_positions = []
        char_pos = 0
        
        for i, word in enumerate(words):
            word_positions.append((char_pos, char_pos + len(word), i))
            char_pos += len(word) + 1  # +1 for space
        
        def char_to_word_pos(char_pos):
            for start, end, word_idx in word_positions:
                if start <= char_pos <= end:
                    return word_idx
            return 0
        
        imm_word_positions = [char_to_word_pos(start) for start, end in imm_matches]
        lab_word_positions = [char_to_word_pos(start) for start, end in lab_matches]
        
        # Check if any pairs are within window
        for imm_pos in imm_word_positions:
            for lab_pos in lab_word_positions:
                if abs(imm_pos - lab_pos) <= window_words:
                    return True
        
        return False
    
    def expand_to_paragraph(self, text, start_char, end_char):
        """Expand quote to paragraph boundaries for better context"""
        # Find nearest paragraph breaks (double newlines)
        left_break = text.rfind('\n\n', 0, start_char)
        right_break = text.find('\n\n', end_char)
        
        start = 0 if left_break == -1 else left_break + 2
        end = len(text) if right_break == -1 else right_break
        
        return text[start:end].strip()
    
    def extract_contextual_quotes(self, text, min_length=400, max_length=800):
        """Extract quotes with paragraph-aware windowing"""
        sentences = self.sentence_splitter.split(text)
        quotes = []
        
        for i in range(len(sentences)):
            for window_size in [4, 6, 8, 10, 12]:  # Different window sizes
                if i + window_size > len(sentences):
                    continue
                
                passage = '. '.join(sentences[i:i+window_size]).strip()
                
                if min_length <= len(passage) <= max_length:
                    if self.proximity_check_fast(passage):
                        quotes.append({
                            'text': passage,
                            'start_sentence': i,
                            'window_size': window_size,
                            'length': len(passage)
                        })
        
        # Deduplicate and sort by length/quality
        seen_starts = set()
        unique_quotes = []
        
        for quote in sorted(quotes, key=lambda x: -x['length']):
            if quote['start_sentence'] not in seen_starts:
                unique_quotes.append(quote)
                # Mark nearby sentences as seen to avoid overlap
                for j in range(max(0, quote['start_sentence']-2), 
                              min(len(sentences), quote['start_sentence'] + quote['window_size'] + 2)):
                    seen_starts.add(j)
        
        return unique_quotes[:5]  # Top 5 quotes per section

# ===== EFFICIENT COLLECTOR =====

class EfficientCollector:
    def __init__(self, db_path="hansard_speeches.db"):
        self.db = init_database(db_path)
        self.parser = OptimizedParser()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "HansardResearch/1.0"})
    
    def dedup_key(self, url, member, quote):
        """Generate deduplication key"""
        head = self.parser.clean_text(quote)[:120].encode("utf-8")
        return f"{url}|{member}|{hashlib.sha1(head).hexdigest()[:10]}"
    
    def fetch_html(self, url):
        """Fetch HTML with retry logic"""
        try:
            r = self.session.get(url, timeout=30)
            r.raise_for_status()
            return r.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def process_section(self, section_url, section_title, sitting_date, house):
        """Process a single debate section"""
        html = self.fetch_html(section_url)
        if not html:
            return []
        
        # Parse with BeautifulSoup to get clean text
        soup = BeautifulSoup(html, 'html.parser')
        full_text = soup.get_text()
        
        # Quick proximity check before expensive processing
        if not self.parser.proximity_check_fast(full_text):
            return []
        
        print(f"  Processing {section_title} ({len(full_text)} chars)")
        
        # Find speakers and extract quotes
        speaker_positions = self.parser.find_speaker_boundaries(full_text)
        quotes = self.parser.extract_contextual_quotes(full_text)
        
        results = []
        for quote in quotes:
            # Find speaker for this quote
            quote_pos = full_text.find(quote['text'][:50])
            speaker = "Unknown Speaker"
            
            for speaker_info in reversed(speaker_positions):
                if speaker_info['position'] < quote_pos:
                    speaker = speaker_info['speaker']
                    break
            
            dedup = self.dedup_key(section_url, speaker, quote['text'])
            
            results.append({
                'dedup_key': dedup,
                'date': sitting_date,
                'house': house,
                'debate_title': section_title,
                'member': speaker,
                'party': '',  # To be filled later
                'quote': quote['text'],
                'url': section_url
            })
        
        return results
    
    def store_speeches(self, speeches):
        """Store speeches in database with deduplication"""
        stored = 0
        
        for speech in speeches:
            try:
                self.db.execute("""
                    INSERT OR IGNORE INTO speeches 
                    (dedup_key, date, house, debate_title, member, party, quote, url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    speech['dedup_key'], speech['date'], speech['house'],
                    speech['debate_title'], speech['member'], speech['party'],
                    speech['quote'], speech['url']
                ))
                stored += 1
            except sqlite3.IntegrityError:
                pass  # Duplicate, skip
        
        self.db.commit()
        return stored
    
    def coarse_filter_candidates(self, limit=1000):
        """Use FTS5 to quickly find candidates"""
        cursor = self.db.execute("""
            SELECT s.id, s.quote, s.date, s.url, s.member, s.debate_title
            FROM speeches_fts fts
            JOIN speeches s ON fts.rowid = s.id
            WHERE speeches_fts MATCH '(immig* OR alien* OR migrant* OR foreigner*) AND (wage* OR employ* OR job* OR labour*)'
            LIMIT ?
        """, (limit,))
        
        return cursor.fetchall()

# ===== TEST THE SYSTEM =====

if __name__ == "__main__":
    print("=== TESTING EFFICIENT COLLECTOR ===")
    
    collector = EfficientCollector()
    
    # Test sections from our known working debates
    test_sections = [
        ("https://api.parliament.uk/historic-hansard/commons/1905/may/02/aliens-bill", "ALIENS BILL", "1905-05-02", "commons"),
        ("https://api.parliament.uk/historic-hansard/commons/1905/may/02/aliens-bill-1", "ALIENS BILL (continued)", "1905-05-02", "commons"),
    ]
    
    all_speeches = []
    for url, title, date, house in test_sections:
        speeches = collector.process_section(url, title, date, house)
        all_speeches.extend(speeches)
        print(f"  Found {len(speeches)} speeches in {title}")
    
    # Store in database
    stored_count = collector.store_speeches(all_speeches)
    print(f"\nStored {stored_count} unique speeches in database")
    
    # Test FTS5 search
    print(f"\n=== TESTING FTS5 SEARCH ===")
    candidates = collector.coarse_filter_candidates(10)
    print(f"Found {len(candidates)} candidates with coarse filter")
    
    for i, (rowid, quote, date, url, member, title) in enumerate(candidates[:3]):
        print(f"\nCandidate {i+1}:")
        print(f"  {member} ({date}): {title}")
        print(f"  {quote[:200]}...")
    
    collector.db.close()
    print(f"\nDatabase saved as hansard_speeches.db")