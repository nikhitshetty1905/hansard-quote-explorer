# updated_hybrid_collector.py
# Integrate enhanced quote logic into the hybrid collector

import requests
import sqlite3
import re
import json
import hashlib
import time
from datetime import date, datetime, timedelta
from bs4 import BeautifulSoup
from pathlib import Path
from enhanced_quote_logic import EnhancedQuoteExtractor

class UpdatedHybridCollector:
    def __init__(self, db_path="hansard_enhanced.db", cache_dir="hansard_cache"):
        self.db_path = db_path
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "HansardResearch/1.0"})
        
        self.db = self.init_database()
        
        # Use enhanced quote extractor
        self.quote_extractor = EnhancedQuoteExtractor()
        
        # Immigration/labor relevant debate title patterns
        self.relevant_patterns = [
            r'alien[s]?\b', r'immigration?\b', r'immigrant[s]?\b',
            r'unemployment\b', r'labour\b', r'labor\b', r'employment\b',
            r'wage[s]?\b', r'worker[s]?\b', r'trade.*union[s]?\b',
            r'foreign.*worker[s]?\b', r'man.*power\b', r'sweating\b',
            r'competition\b', r'industry\b', r'economic\b'
        ]
        
        self.title_filter = re.compile('|'.join(self.relevant_patterns), re.IGNORECASE)
        
        # Speaker identification patterns
        self.speaker_patterns = [
            re.compile(r'(Mr\.|Mrs\.|Sir|Lord|Dr\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*:', re.MULTILINE),
            re.compile(r'(Mr\.|Mrs\.|Sir|Lord|Dr\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:said|asked|replied|continued)', re.MULTILINE),
            re.compile(r'^([A-Z][A-Z\s]{3,}):\s*', re.MULTILINE),
            re.compile(r'The\s+(Secretary|Minister|President|Chairman)\s+of\s+State', re.MULTILINE),
        ]

    def init_database(self):
        """Initialize SQLite database with enhanced schema"""
        conn = sqlite3.connect(self.db_path)
        
        # Enhanced speeches table with word-based metrics
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
                word_count INTEGER,
                mig_term_count INTEGER,
                lab_term_count INTEGER,
                extraction_method TEXT,
                url TEXT,
                sitting_url TEXT,
                extraction_quality REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Sitting cache table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sitting_cache (
                sitting_url TEXT PRIMARY KEY,
                date TEXT,
                house TEXT,
                json_data TEXT,
                debate_count INTEGER,
                relevant_debates INTEGER,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Enhanced FTS5 virtual table
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS speeches_fts USING fts5(
                quote, member, debate_title,
                content='speeches',
                content_rowid='id',
                tokenize='porter'
            )
        """)
        
        # FTS5 triggers
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

    def fetch_sitting_json(self, year, month, day, use_cache=True):
        """Fetch sitting-day JSON with caching (unchanged)"""
        try:
            date_obj = datetime(year, month, day)
            month_abbrev = date_obj.strftime("%b").lower()
            sitting_url = f"https://api.parliament.uk/historic-hansard/sittings/{year}/{month_abbrev}/{day:02d}.js"
            
            # Check cache first
            if use_cache:
                cached = self.db.execute(
                    "SELECT json_data FROM sitting_cache WHERE sitting_url = ?",
                    (sitting_url,)
                ).fetchone()
                
                if cached:
                    return json.loads(cached[0]), sitting_url
            
            # Fetch from API
            response = self.session.get(sitting_url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Cache the result
                debate_count = self.count_debates_in_sitting(data)
                relevant_count = self.count_relevant_debates(data)
                
                self.db.execute("""
                    INSERT OR REPLACE INTO sitting_cache 
                    (sitting_url, date, house, json_data, debate_count, relevant_debates)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    sitting_url, 
                    f"{year}-{month:02d}-{day:02d}",
                    self.extract_houses_from_sitting(data),
                    json.dumps(data),
                    debate_count,
                    relevant_count
                ))
                self.db.commit()
                
                return data, sitting_url
            else:
                return None, sitting_url
                
        except Exception as e:
            print(f"Error fetching sitting {year}-{month:02d}-{day:02d}: {e}")
            return None, None

    def count_debates_in_sitting(self, sitting_data):
        """Count total debates in sitting JSON (unchanged)"""
        count = 0
        if isinstance(sitting_data, list):
            for item in sitting_data:
                if isinstance(item, dict):
                    for house_key in ["house_of_commons_sitting", "house_of_lords_sitting"]:
                        if house_key in item:
                            sitting = item[house_key]
                            if "top_level_sections" in sitting:
                                count += len(sitting["top_level_sections"])
        return count

    def count_relevant_debates(self, sitting_data):
        """Count immigration/labor relevant debates (unchanged)"""
        count = 0
        if isinstance(sitting_data, list):
            for item in sitting_data:
                if isinstance(item, dict):
                    for house_key in ["house_of_commons_sitting", "house_of_lords_sitting"]:
                        if house_key in item:
                            sitting = item[house_key]
                            if "top_level_sections" in sitting:
                                for section in sitting["top_level_sections"]:
                                    title = self.extract_section_title(section)
                                    if title and self.title_filter.search(title):
                                        count += 1
        return count

    def extract_section_title(self, section):
        """Extract title from section data (unchanged)"""
        if isinstance(section, dict):
            if "section" in section and "title" in section["section"]:
                return section["section"]["title"]
            elif "oral_questions" in section and "title" in section["oral_questions"]:
                return section["oral_questions"]["title"]
        return None

    def extract_houses_from_sitting(self, sitting_data):
        """Extract house names from sitting data (unchanged)"""
        houses = []
        if isinstance(sitting_data, list):
            for item in sitting_data:
                if isinstance(item, dict):
                    if "house_of_commons_sitting" in item:
                        houses.append("commons")
                    if "house_of_lords_sitting" in item:
                        houses.append("lords")
        return ",".join(houses)

    def extract_debates_from_sitting(self, sitting_data, filter_relevant=True):
        """Extract debate metadata from sitting JSON (unchanged)"""
        debates = []
        
        if not isinstance(sitting_data, list):
            return debates
            
        for item in sitting_data:
            if not isinstance(item, dict):
                continue
                
            for house_key in ["house_of_commons_sitting", "house_of_lords_sitting"]:
                if house_key not in item:
                    continue
                    
                sitting = item[house_key]
                house = "commons" if house_key == "house_of_commons_sitting" else "lords"
                
                if "top_level_sections" not in sitting:
                    continue
                    
                for section in sitting["top_level_sections"]:
                    title = self.extract_section_title(section)
                    if not title:
                        continue
                    
                    # Filter by relevance if requested
                    if filter_relevant and not self.title_filter.search(title):
                        continue
                    
                    # Extract section info
                    section_info = section.get("section") or section.get("oral_questions")
                    if not section_info:
                        continue
                    
                    slug = section_info.get("slug", "")
                    date_str = section_info.get("date", "")
                    
                    if date_str and slug:
                        # Construct HTML URL
                        date_parts = date_str.split("-")
                        if len(date_parts) == 3:
                            year, month, day = date_parts
                            month_names = {
                                "01": "jan", "02": "feb", "03": "mar", "04": "apr",
                                "05": "may", "06": "jun", "07": "jul", "08": "aug",
                                "09": "sep", "10": "oct", "11": "nov", "12": "dec"
                            }
                            month_name = month_names.get(month, month)
                            
                            html_url = f"https://api.parliament.uk/historic-hansard/{house}/{year}/{month_name}/{int(day):02d}/{slug}"
                            
                            debates.append({
                                "title": title,
                                "house": house,
                                "date": date_str,
                                "url": html_url,
                                "slug": slug,
                                "section_id": section_info.get("id"),
                                "start_column": section_info.get("start_column"),
                                "end_column": section_info.get("end_column")
                            })
        
        return debates

    def find_speaker_boundaries(self, text):
        """Find speaker boundaries with precompiled patterns (unchanged)"""
        speaker_positions = []
        
        for pattern in self.speaker_patterns:
            for match in pattern.finditer(text):
                speaker_name = match.group(0).rstrip(':').rstrip()
                speaker_name = re.sub(r'\s+(?:said|asked|replied|continued)$', '', speaker_name)
                
                speaker_positions.append({
                    'position': match.start(),
                    'speaker': speaker_name
                })
        
        speaker_positions.sort(key=lambda x: x['position'])
        return speaker_positions

    def process_debate_html(self, debate_info, sitting_url):
        """Process individual debate HTML using enhanced quote extraction"""
        url = debate_info["url"]
        
        try:
            response = self.session.get(url, timeout=45)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            full_text = soup.get_text()
            
            # Quick proximity check using enhanced logic
            passes, _, _ = self.quote_extractor.precise_proximity_test(full_text)
            if not passes:
                return []
            
            print(f"    Processing: {debate_info['title']} ({len(full_text)} chars)")
            
            # Find speakers and extract quotes using enhanced method
            speaker_positions = self.find_speaker_boundaries(full_text)
            quotes = self.quote_extractor.extract_word_based_quotes(full_text)
            
            speeches = []
            for quote_data in quotes:
                # Find speaker for this quote
                quote_text = quote_data['text']
                quote_pos = full_text.find(quote_text[:50])
                speaker = "Unknown Speaker"
                
                for speaker_info in reversed(speaker_positions):
                    if speaker_info['position'] < quote_pos:
                        speaker = speaker_info['speaker']
                        break
                
                # Generate dedup key
                dedup_key = self.generate_dedup_key(url, speaker, quote_text)
                
                # Calculate basic quality score (will be enhanced in Phase 2)
                quality = self.calculate_basic_quality(quote_data)
                
                speeches.append({
                    'dedup_key': dedup_key,
                    'date': debate_info['date'],
                    'house': debate_info['house'],
                    'debate_title': debate_info['title'],
                    'member': speaker,
                    'party': '',  # To be filled later
                    'quote': quote_text,
                    'word_count': quote_data['word_count'],
                    'mig_term_count': quote_data['mig_term_count'],
                    'lab_term_count': quote_data['lab_term_count'],
                    'extraction_method': quote_data['extraction_method'],
                    'url': url,
                    'sitting_url': sitting_url,
                    'extraction_quality': quality
                })
            
            return speeches
            
        except Exception as e:
            print(f"    Error processing {url}: {e}")
            return []

    def calculate_basic_quality(self, quote_data):
        """Calculate basic quality score for Phase 1"""
        score = 0
        
        word_count = quote_data['word_count']
        mig_count = quote_data['mig_term_count']
        lab_count = quote_data['lab_term_count']
        
        # Word count scoring (150-300 = +3, 301-450 = +2)
        if 150 <= word_count <= 300:
            score += 3
        elif 301 <= word_count <= 450:
            score += 2
        
        # Term density scoring
        if mig_count >= 2 and lab_count >= 2:
            score += 3
        elif mig_count >= 1 and lab_count >= 1:
            score += 2
        
        # Basic argument detection
        quote_text = quote_data['text'].lower()
        if re.search(r'\b(argue|maintain|contend|assert|claim|believe)\b', quote_text):
            score += 1
        
        # Policy context
        if re.search(r'\b(bill|act|legislation|measure|policy)\b', quote_text):
            score += 1
        
        return score

    def generate_dedup_key(self, url, member, quote):
        """Generate deduplication key (unchanged)"""
        content = f"{url}|{member}|{quote[:120]}"
        return hashlib.sha1(content.encode('utf-8')).hexdigest()[:16]

    def store_speeches(self, speeches):
        """Store speeches in enhanced database schema"""
        stored = 0
        
        for speech in speeches:
            try:
                self.db.execute("""
                    INSERT OR IGNORE INTO speeches 
                    (dedup_key, date, house, debate_title, member, party, quote, 
                     word_count, mig_term_count, lab_term_count, extraction_method,
                     url, sitting_url, extraction_quality)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    speech['dedup_key'], speech['date'], speech['house'],
                    speech['debate_title'], speech['member'], speech['party'],
                    speech['quote'], speech['word_count'], speech['mig_term_count'],
                    speech['lab_term_count'], speech['extraction_method'],
                    speech['url'], speech['sitting_url'], speech['extraction_quality']
                ))
                stored += 1
            except sqlite3.IntegrityError:
                pass  # Duplicate, skip
        
        self.db.commit()
        return stored

    def collect_date_range(self, start_year, end_year, start_month=1, end_month=12):
        """Collect data for a date range using enhanced extraction"""
        print(f"=== ENHANCED HYBRID COLLECTION: {start_year}-{end_year} ===")
        print("Using word-based filtering (150-450 words) and precise proximity testing")
        
        total_sittings = 0
        successful_sittings = 0
        total_debates = 0
        relevant_debates = 0
        total_speeches = 0
        
        current_date = datetime(start_year, start_month, 1)
        end_date = datetime(end_year, end_month, 28)
        
        while current_date <= end_date:
            year, month, day = current_date.year, current_date.month, current_date.day
            
            # Skip weekends
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue
            
            print(f"\n--- {year}-{month:02d}-{day:02d} ---")
            total_sittings += 1
            
            # Fetch sitting JSON
            sitting_data, sitting_url = self.fetch_sitting_json(year, month, day)
            
            if sitting_data:
                successful_sittings += 1
                
                # Extract relevant debates
                debates = self.extract_debates_from_sitting(sitting_data, filter_relevant=True)
                total_debates += self.count_debates_in_sitting(sitting_data)
                relevant_debates += len(debates)
                
                print(f"  Found {len(debates)} relevant debates (of {self.count_debates_in_sitting(sitting_data)} total)")
                
                # Process each relevant debate
                day_speeches = 0
                for debate in debates:
                    speeches = self.process_debate_html(debate, sitting_url)
                    stored = self.store_speeches(speeches)
                    day_speeches += stored
                    
                    if stored > 0:
                        # Show enhanced metrics
                        avg_words = sum(s['word_count'] for s in speeches) / len(speeches) if speeches else 0
                        print(f"      {debate['title']}: {stored} speeches (avg {avg_words:.0f} words)")
                    
                    # Rate limiting
                    time.sleep(1)
                
                total_speeches += day_speeches
                if day_speeches > 0:
                    print(f"  Day total: {day_speeches} speeches stored")
            
            else:
                print(f"  No sitting data available")
            
            current_date += timedelta(days=1)
        
        # Enhanced summary
        print(f"\n=== ENHANCED COLLECTION SUMMARY ===")
        print(f"Sitting success rate: {successful_sittings}/{total_sittings} ({successful_sittings/total_sittings*100:.1f}%)")
        print(f"Total debates found: {total_debates}")
        print(f"Relevant debates: {relevant_debates} ({relevant_debates/total_debates*100:.1f}%)")
        print(f"Total speeches extracted: {total_speeches}")
        
        if total_speeches > 0:
            # Show word count statistics
            stats = self.db.execute("""
                SELECT 
                    AVG(word_count) as avg_words,
                    MIN(word_count) as min_words,
                    MAX(word_count) as max_words,
                    AVG(mig_term_count) as avg_mig,
                    AVG(lab_term_count) as avg_lab,
                    AVG(extraction_quality) as avg_quality
                FROM speeches
            """).fetchone()
            
            print(f"Word count: avg {stats[0]:.0f}, range {stats[1]}-{stats[2]}")
            print(f"Term density: avg {stats[3]:.1f} MIG, {stats[4]:.1f} LAB terms")
            print(f"Avg quality score: {stats[5]:.1f}")
        
        print(f"Database: {self.db_path}")

    def close(self):
        """Close database connection"""
        self.db.close()

# Test the enhanced collector
if __name__ == "__main__":
    collector = UpdatedHybridCollector()
    
    # Test with May 1905 to compare with previous results
    print("Testing enhanced collector with 1905 May")
    collector.collect_date_range(1905, 1905, start_month=5, end_month=5)
    
    collector.close()
    print("\nEnhanced collection test complete!")