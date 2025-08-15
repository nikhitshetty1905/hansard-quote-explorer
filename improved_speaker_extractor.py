# improved_speaker_extractor.py
# Fix speaker extraction using proper Hansard HTML parsing

import sqlite3
import requests
import re
from bs4 import BeautifulSoup
import time

class ImprovedSpeakerExtractor:
    def __init__(self, db_path="hansard_simple.db"):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "HansardResearch/1.0"})
        self.PEOPLE_RE = re.compile(r"^/historic-hansard/people/")
    
    def parse_debate(self, url):
        """Parse debate using proper Hansard HTML structure"""
        try:
            html = self.session.get(url, timeout=60).text
            soup = BeautifulSoup(html, "html.parser")

            # The main content area on Historic Hansard
            main = soup.find(id="content") or soup.find("div", attrs={"class": re.compile("content|main", re.I)}) or soup

            speeches = []
            current = None

            # Walk all elements in order; a people-link starts a new speech block
            for el in main.descendants:
                if getattr(el, "name", None) != "a":
                    continue
                href = el.get("href") or ""
                if self.PEOPLE_RE.match(href):
                    # Start a new speech headed by this speaker
                    name = el.get_text(strip=True)
                    # Defensive normalisation (Hansard often uses ALL CAPS)
                    norm = " ".join(w.capitalize() if w.isupper() else w for w in name.split())
                    current = {"member": norm, "member_href": href, "paras": []}
                    speeches.append(current)

                    # Collect subsequent sibling text until the next people-link or section break
                    # We walk forward through next elements, appending <p> text
                    node = el.parent
                    while node and node.name not in ("h1","h2","hr"):
                        node = node.find_next_sibling()
                        if not node:
                            break
                        # Stop if we hit another speaker link
                        a = node.find("a", href=self.PEOPLE_RE)
                        if a:
                            break
                        if node.name in ("p","blockquote","div"):
                            txt = node.get_text(" ", strip=True)
                            if txt and current is not None:
                                current["paras"].append(txt)

            # Flatten and return results
            results = []
            for sp in speeches:
                if not sp["paras"]:
                    continue
                results.append({
                    "member": sp["member"],
                    "member_url": "https://api.parliament.uk" + sp["member_href"],
                    "quote": "\n\n".join(sp["paras"])
                })
            return results
            
        except Exception as e:
            print(f"Error parsing {url}: {e}")
            return []

    def find_speaker_for_quote(self, hansard_url, quote_text):
        """Find the correct speaker for a specific quote using improved parsing"""
        print(f"  Processing: {hansard_url[:60]}...")
        
        speeches = self.parse_debate(hansard_url)
        if not speeches:
            print(f"    No speeches found")
            return None, None
        
        # Clean the quote text for matching
        quote_words = quote_text.lower().split()[:20]  # First 20 words
        
        # Find best matching speech
        best_match = None
        best_score = 0
        
        for speech in speeches:
            speech_words = speech["quote"].lower().split()
            
            # Count matching words in first part of speech
            matches = 0
            for word in quote_words:
                if len(word) > 3 and word in speech_words[:50]:  # Check first 50 words
                    matches += 1
            
            # Calculate match score
            if matches > best_score:
                best_score = matches
                best_match = speech
        
        if best_match and best_score >= 3:  # Require at least 3 matching words
            print(f"    Found speaker: {best_match['member']} (score: {best_score})")
            return best_match["member"], best_match.get("member_url")
        else:
            print(f"    No matching speaker found (best score: {best_score})")
            return None, None

    def extract_debate_title(self, hansard_url):
        """Extract debate title from Hansard page"""
        try:
            html = self.session.get(hansard_url, timeout=30).text
            soup = BeautifulSoup(html, "html.parser")
            
            # Try to find debate title in various locations
            title_selectors = [
                'h1',  # Main heading
                '.debate-title',
                '#content h1',
                'title'
            ]
            
            for selector in title_selectors:
                elements = soup.select(selector)
                if elements:
                    title = elements[0].get_text().strip()
                    if title and len(title) > 3:
                        # Clean up title
                        title = re.sub(r'^(HC Deb|HL Deb)\s*', '', title)
                        title = re.sub(r'\s*-\s*Hansard.*$', '', title, re.IGNORECASE)
                        title = title.strip()
                        
                        # Handle common debate types
                        if 'aliens' in title.lower():
                            return "Aliens Bill"
                        elif 'industrial' in title.lower() and 'unrest' in title.lower():
                            return "Industrial Unrest Debate"
                        
                        return title
            
            # Fallback: extract from URL
            path_parts = hansard_url.split('/')
            if len(path_parts) >= 2:
                debate_part = path_parts[-1]
                if debate_part:
                    return debate_part.replace('-', ' ').title()
            
            return None
            
        except Exception as e:
            print(f"    Error extracting title: {e}")
            return None

    def fix_problematic_quotes(self, limit=None):
        """Fix quotes with 'Unknown Speaker' or incorrect attributions"""
        conn = sqlite3.connect(self.db_path)
        
        # Add corrected_speaker column if it doesn't exist
        try:
            conn.execute("ALTER TABLE quotes ADD COLUMN corrected_speaker TEXT")
            conn.commit()
            print("Added corrected_speaker column to database")
        except sqlite3.OperationalError:
            print("corrected_speaker column already exists")
        
        # Get problematic quotes (Unknown Speaker or known misattributions)
        query = """
            SELECT id, hansard_url, quote, speaker, enhanced_speaker, debate_title
            FROM quotes 
            WHERE speaker = 'Unknown Speaker' 
            OR enhanced_speaker = 'Mr. RAMSAY'  -- Known misattribution
            OR corrected_speaker IS NULL
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        quotes = conn.execute(query).fetchall()
        print(f"\nFixing {len(quotes)} problematic quotes...")
        
        fixed_count = 0
        
        for quote_id, hansard_url, quote, original_speaker, enhanced_speaker, debate_title in quotes:
            print(f"\nQuote {quote_id}: {original_speaker}")
            print(f"  Quote start: {quote[:100]}...")
            
            # Find correct speaker
            correct_speaker, speaker_url = self.find_speaker_for_quote(hansard_url, quote)
            
            # Extract debate title if not available
            if not debate_title:
                debate_title = self.extract_debate_title(hansard_url)
            
            # Update database with corrections
            updates = []
            params = []
            
            if correct_speaker:
                updates.append("corrected_speaker = ?")
                params.append(correct_speaker)
                fixed_count += 1
            
            if debate_title and not conn.execute("SELECT debate_title FROM quotes WHERE id = ?", (quote_id,)).fetchone()[0]:
                updates.append("debate_title = ?")
                params.append(debate_title)
            
            if updates:
                params.append(quote_id)
                update_query = f"UPDATE quotes SET {', '.join(updates)} WHERE id = ?"
                conn.execute(update_query, params)
                conn.commit()
                
                if correct_speaker:
                    print(f"    Fixed: {original_speaker} -> {correct_speaker}")
                if debate_title:
                    print(f"    Debate: {debate_title}")
            
            # Rate limiting
            time.sleep(0.5)
        
        conn.close()
        
        print(f"\nFixed {fixed_count} speaker attributions!")
        return fixed_count

def main():
    print("=== IMPROVED SPEAKER EXTRACTOR ===")
    print("Using proper Hansard HTML parsing with People links")
    print("This will fix 'Unknown Speaker' and misattributed quotes")
    
    extractor = ImprovedSpeakerExtractor()
    
    # Test on a small sample first
    print("\nTesting on 5 problematic quotes...")
    test_count = extractor.fix_problematic_quotes(limit=5)
    
    if test_count > 0:
        print(f"\nTest successful! Fixed {test_count} quotes")
        
        proceed = input("\nContinue with all problematic quotes? (y/N): ").strip().lower()
        
        if proceed == 'y':
            print("\nRunning full correction...")
            total_fixed = extractor.fix_problematic_quotes()
            print(f"\nComplete! Fixed {total_fixed} quotes total")
        else:
            print("Correction stopped. Test data remains in database.")
    else:
        print("Test found no quotes to fix - either all quotes are already correct or there's an issue.")

if __name__ == "__main__":
    main()