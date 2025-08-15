# enhanced_tagger.py
# Two-stage retrieval and frame classification system

import sqlite3
import re
import json
from pathlib import Path

class EnhancedTagger:
    def __init__(self, db_path="hansard_hybrid.db"):
        self.db = sqlite3.connect(db_path)
        
        # Frame classification rules - enhanced for better accuracy
        self.frame_rules = {
            "LABOUR_NEED": [
                r"(labour|labor)\s+shortage", 
                r"manpower\s+(?:shortage|need|required|want)",
                r"(fill|filled|filling)\s+(?:vacanc|shortage|gaps?|positions?)",
                r"essential\s+(?:workers|workforce|labou?r)",
                r"(?:skilled|trained)\s+(?:workers?|labour|labor).*(?:needed|required|wanted)",
                r"(?:benefit|beneficial|advantage).*(?:employment|labour|labor|work)",
                r"(?:new\s+trades?|skills?).*(?:brought|introduced|taught)",
                r"(?:increase|expand).*(?:employment|work|industry)",
                r"economic.*(?:benefit|advantage|development|growth)"
            ],
            
            "LABOUR_THREAT": [
                r"(depress(?:ing)?|lower(?:ing)?|reduce|reducing)\s+wage[s]?",
                r"(job[s]?\s+competition|taking\s+our\s+jobs?|steal.*jobs?)",
                r"surplus\s+labou?r", 
                r"unemployment\s+(?:rise|increase|pressure|among)",
                r"(?:competition|compete|competing).*(?:with|against).*(?:british|english|our).*(?:workers?|labour|labor)",
                r"(?:under-sell|undersell|undercutting?).*(?:workers?|labour|labor)",
                r"(?:displac|displacing|turn.*out|drive.*out).*(?:workers?|labour|labor)",
                r"(?:damage|harm|evil|injur).*(?:done|caused).*(?:by|from).*(?:alien|foreign|immigrant)",
                r"over.*(?:crowded|supplied|stocked).*(?:labour|labor|market)"
            ],
            
            "RACIALISED": [
                r"(?:undesirable|inferior|degraded?|criminal|pauper).*aliens?",
                r"(?:racial|race)\s+(?:problem|question|issue|conflict)",
                r"(?:character|quality|type|class|sort|kind)\s+(?:of|these)\s+(?:people|aliens?|immigrants?)",
                r"aliens?\s+(?:pour|flood|swarm|invasion|influx)",
                r"(?:exclude|expel|deport|send\s+back).*aliens?",
                r"(?:moral|social|cultural)\s+(?:standard|level|condition|threat)",
                r"(?:civilization|civilized|barbarous|savage)",
                r"(?:habits|customs|way\s+of\s+life).*(?:alien|foreign|different|inferior)"
            ],
            
            "MIXED": [
                r"on\s+the\s+(?:one\s+)?hand.*on\s+the\s+(?:other\s+)?hand",
                r"(?:while|whereas|although).*(?:however|but|nevertheless|yet)",
                r"(?:benefits?|advantages?).*(?:but|however|yet).*(?:harm|damage|problems?)",
                r"(?:some|certain).*(?:good|benefit).*(?:other|some).*(?:harm|damage)",
                r"balanced?\s+(?:view|approach|consideration)",
                r"(?:both|two)\s+sides?\s+(?:of\s+)?(?:question|argument|issue)"
            ]
        }
        
        # Compile patterns for speed
        self.compiled_rules = {}
        for frame, patterns in self.frame_rules.items():
            self.compiled_rules[frame] = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
        
        # Immigration and labor terms for proximity checking
        self.immigration_terms = re.compile(
            r'\b(?:immigration|immigrant[s]?|alien[s]?|foreign(?:er|ers)?|migrant[s]?)\b', 
            re.IGNORECASE
        )
        self.labor_terms = re.compile(
            r'\b(?:labour|labor|worker[s]?|employment|job[s]?|wage[s]?|unemploy|work(?:ing|ers?)?)\b', 
            re.IGNORECASE
        )

    def coarse_filter_candidates(self, limit=1000):
        """Stage 1: Use FTS5 to quickly find candidates"""
        fts_query = '(immig* OR alien* OR migrant* OR foreigner*) AND (wage* OR employ* OR job* OR labour* OR labor* OR work*)'
        
        cursor = self.db.execute("""
            SELECT s.id, s.quote, s.date, s.url, s.member, s.debate_title, s.house, s.extraction_quality
            FROM speeches_fts fts
            JOIN speeches s ON fts.rowid = s.id
            WHERE speeches_fts MATCH ?
            ORDER BY rank, s.extraction_quality DESC
            LIMIT ?
        """, (fts_query, limit))
        
        return cursor.fetchall()

    def fine_proximity_check(self, text, window_words=40):
        """Stage 2: Precise proximity checking on candidates"""
        # Find all immigration and labor term positions
        imm_positions = [m.start() for m in self.immigration_terms.finditer(text)]
        lab_positions = [m.start() for m in self.labor_terms.finditer(text)]
        
        if not imm_positions or not lab_positions:
            return False
        
        # Convert to word positions (approximate)
        words = text.split()
        char_to_word = {}
        char_pos = 0
        
        for word_idx, word in enumerate(words):
            for i in range(len(word)):
                char_to_word[char_pos + i] = word_idx
            char_pos += len(word) + 1  # +1 for space
        
        imm_word_positions = [char_to_word.get(pos, 0) for pos in imm_positions]
        lab_word_positions = [char_to_word.get(pos, 0) for pos in lab_positions]
        
        # Check if any pairs are within window
        for imm_pos in imm_word_positions:
            for lab_pos in lab_word_positions:
                if abs(imm_pos - lab_pos) <= window_words:
                    return True
        
        return False

    def classify_frame(self, text):
        """Classify text into frames using enhanced rules"""
        text_lower = text.lower()
        frame_scores = {}
        
        # Score each frame
        for frame, patterns in self.compiled_rules.items():
            score = 0
            matches = []
            
            for pattern in patterns:
                if pattern.search(text_lower):
                    score += 1
                    matches.append(pattern.pattern)
            
            if score > 0:
                frame_scores[frame] = {
                    'score': score,
                    'matches': matches
                }
        
        # Classification logic
        if not frame_scores:
            return "OTHER"
        
        # Multiple frames detected
        if len(frame_scores) > 1:
            # Prioritize RACIALISED if present (as in original system)
            if "RACIALISED" in frame_scores:
                return "RACIALISED"
            else:
                return "MIXED"
        
        # Single frame
        frame = list(frame_scores.keys())[0]
        
        # Require minimum confidence for single frames
        if frame_scores[frame]['score'] >= 1:
            return frame
        else:
            return "OTHER"

    def enhance_speeches_with_frames(self):
        """Add frame classifications to all speeches"""
        print("=== ENHANCING SPEECHES WITH FRAME CLASSIFICATION ===")
        
        # Add frame column if it doesn't exist
        try:
            self.db.execute("ALTER TABLE speeches ADD COLUMN frame TEXT")
            self.db.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Get candidates using two-stage retrieval
        print("Stage 1: FTS5 coarse filtering...")
        candidates = self.coarse_filter_candidates(limit=10000)
        print(f"Found {len(candidates)} initial candidates")
        
        # Stage 2: Fine proximity filtering and frame classification
        print("Stage 2: Proximity filtering and frame classification...")
        
        classified = 0
        frame_counts = {}
        
        for row in candidates:
            speech_id, quote, date, url, member, debate_title, house, quality = row
            
            # Fine proximity check
            if self.fine_proximity_check(quote):
                # Classify frame
                frame = self.classify_frame(quote)
                
                # Update database
                self.db.execute(
                    "UPDATE speeches SET frame = ? WHERE id = ?",
                    (frame, speech_id)
                )
                
                classified += 1
                frame_counts[frame] = frame_counts.get(frame, 0) + 1
                
                if classified <= 5:  # Show first 5
                    print(f"  Example {classified}: {frame} - {member} ({date})")
                    print(f"    {quote[:100]}...")
        
        self.db.commit()
        
        print(f"\nClassified {classified} speeches:")
        for frame, count in sorted(frame_counts.items()):
            print(f"  {frame}: {count}")
        
        return classified

    def export_classified_speeches(self, output_file="enhanced_speeches.jsonl"):
        """Export classified speeches to JSONL"""
        print(f"\n=== EXPORTING TO {output_file} ===")
        
        cursor = self.db.execute("""
            SELECT date, house, debate_title, member, party, quote, frame, url, extraction_quality
            FROM speeches 
            WHERE frame IS NOT NULL
            ORDER BY date, extraction_quality DESC
        """)
        
        exported = 0
        with open(output_file, 'w', encoding='utf-8') as f:
            for row in cursor:
                date, house, debate_title, member, party, quote, frame, url, quality = row
                
                record = {
                    "date": date,
                    "house": house,
                    "debate_title": debate_title,
                    "member": member,
                    "party": party or "",
                    "quote": quote,
                    "frame": frame,
                    "hansard_url": url,
                    "extraction_quality": quality
                }
                
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
                exported += 1
        
        print(f"Exported {exported} classified speeches")
        return exported

    def get_frame_statistics(self):
        """Get detailed frame statistics"""
        print("\n=== FRAME STATISTICS ===")
        
        # Overall counts
        cursor = self.db.execute("""
            SELECT frame, COUNT(*) as count, AVG(extraction_quality) as avg_quality
            FROM speeches 
            WHERE frame IS NOT NULL
            GROUP BY frame
            ORDER BY count DESC
        """)
        
        print("Frame distribution:")
        total = 0
        for frame, count, avg_quality in cursor:
            print(f"  {frame}: {count} speeches (avg quality: {avg_quality:.2f})")
            total += count
        
        print(f"Total classified: {total}")
        
        # Best examples per frame
        print("\nBest examples per frame:")
        for frame in ["LABOUR_NEED", "LABOUR_THREAT", "RACIALISED", "MIXED", "OTHER"]:
            cursor = self.db.execute("""
                SELECT member, date, debate_title, quote, extraction_quality
                FROM speeches 
                WHERE frame = ?
                ORDER BY extraction_quality DESC
                LIMIT 1
            """, (frame,))
            
            result = cursor.fetchone()
            if result:
                member, date, title, quote, quality = result
                print(f"\n{frame} (quality: {quality:.1f}):")
                print(f"  {member} ({date}): {title}")
                print(f"  {quote[:200]}...")

    def close(self):
        """Close database connection"""
        self.db.close()

if __name__ == "__main__":
    tagger = EnhancedTagger()
    
    # Run enhanced classification
    classified_count = tagger.enhance_speeches_with_frames()
    
    if classified_count > 0:
        # Export results
        tagger.export_classified_speeches()
        
        # Show statistics
        tagger.get_frame_statistics()
    else:
        print("No speeches found for classification")
    
    tagger.close()
    print("\nEnhanced tagging complete!")