# verification_and_formatting.py
# Verify speaker attributions and standardize name formatting

import sqlite3
import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urlparse

class SpeakerVerificationAndFormatting:
    def __init__(self, db_path="hansard_simple.db"):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "HansardResearch/1.0"})
        self.PEOPLE_RE = re.compile(r"^/historic-hansard/people/")
        
    def standardize_name_format(self, name):
        """Standardize name formatting consistently"""
        if not name or name.strip() == "":
            return None
            
        name = name.strip()
        
        # Handle common patterns
        # Remove extra spaces
        name = re.sub(r'\s+', ' ', name)
        
        # Standardize titles and capitalize properly
        # Handle ALL CAPS names
        if name.isupper():
            # Split into parts and capitalize each properly
            parts = name.split()
            formatted_parts = []
            
            for part in parts:
                # Handle titles
                if part.lower() in ['mr', 'mr.', 'mrs', 'mrs.', 'sir', 'lord', 'dr', 'dr.', 'hon', 'hon.']:
                    if part.lower() in ['mr', 'mrs', 'dr']:
                        formatted_parts.append(part.capitalize() + '.')
                    elif part.lower() in ['mr.', 'mrs.', 'dr.']:
                        formatted_parts.append(part.capitalize())
                    else:
                        formatted_parts.append(part.capitalize())
                # Handle "THE SECRETARY OF STATE" etc.
                elif part.lower() in ['the', 'of', 'for', 'and', 'to']:
                    formatted_parts.append(part.lower())
                elif part.lower() in ['secretary', 'minister', 'president', 'state', 'home', 'colonies', 'department']:
                    formatted_parts.append(part.capitalize())
                # Regular names
                else:
                    formatted_parts.append(part.capitalize())
            
            name = ' '.join(formatted_parts)
        
        # Fix common formatting issues
        name = re.sub(r'\bMr\b', 'Mr.', name)
        name = re.sub(r'\bMrs\b', 'Mrs.', name)
        name = re.sub(r'\bDr\b', 'Dr.', name)
        
        # Fix double periods
        name = re.sub(r'\.\.+', '.', name)
        
        # Ensure proper spacing after periods
        name = re.sub(r'\.(\w)', r'. \1', name)
        
        # Handle "THE SECRETARY OF STATE" formatting
        name = re.sub(r'\bThe Secretary Of State\b', 'The Secretary of State', name)
        name = re.sub(r'\bThe President Of\b', 'The President of', name)
        name = re.sub(r'\bThe Minister Of\b', 'The Minister of', name)
        
        return name

    def parse_debate_and_verify(self, url, target_quote_words):
        """Parse debate and find the correct speaker for target quote"""
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
                    # Apply consistent formatting
                    formatted_name = self.standardize_name_format(name)
                    if formatted_name:
                        current = {"member": formatted_name, "member_href": href, "paras": []}
                        speeches.append(current)

                        # Collect subsequent sibling text until the next people-link or section break
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

            # Find the speaker who actually said the target quote
            for speech in speeches:
                if not speech["paras"]:
                    continue
                
                full_speech = " ".join(speech["paras"]).lower()
                
                # Check if this speech contains the target quote words
                matches = 0
                for word in target_quote_words:
                    if word in full_speech:
                        matches += 1
                
                # If we find a good match (most target words present)
                if matches >= len(target_quote_words) * 0.7:  # 70% of words must match
                    return speech["member"], f"https://api.parliament.uk{speech['member_href']}", matches
            
            return None, None, 0
            
        except Exception as e:
            print(f"Error parsing {url}: {e}")
            return None, None, 0

    def verify_and_fix_attributions(self, limit=None):
        """Verify all speaker attributions and fix formatting"""
        conn = sqlite3.connect(self.db_path)
        
        # Add verification columns
        try:
            conn.execute("ALTER TABLE quotes ADD COLUMN verified_speaker TEXT")
            conn.execute("ALTER TABLE quotes ADD COLUMN verification_confidence INTEGER")
            conn.execute("ALTER TABLE quotes ADD COLUMN verification_status TEXT")
            conn.commit()
            print("Added verification columns to database")
        except sqlite3.OperationalError:
            print("Verification columns already exist")
        
        # Get quotes that need verification - focus on corrected ones first
        query = """
            SELECT id, hansard_url, quote, speaker, corrected_speaker, enhanced_speaker
            FROM quotes 
            WHERE corrected_speaker IS NOT NULL 
            OR enhanced_speaker IS NOT NULL
            OR speaker = 'Unknown Speaker'
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        quotes = conn.execute(query).fetchall()
        print(f"\nVerifying {len(quotes)} quotes...")
        
        verified_count = 0
        misattribution_count = 0
        
        for quote_id, hansard_url, quote, original_speaker, corrected_speaker, enhanced_speaker in quotes:
            current_best = corrected_speaker or enhanced_speaker or original_speaker
            
            print(f"\nQuote {quote_id}: Currently attributed to '{current_best}'")
            print(f"  Quote: {quote[:100]}...")
            
            # Extract key words from quote for matching
            quote_words = []
            # Clean and extract meaningful words from quote
            clean_quote = re.sub(r'[^\w\s]', ' ', quote.lower())
            words = clean_quote.split()
            # Take significant words (length > 3, not common words)
            stop_words = {'that', 'this', 'with', 'from', 'they', 'were', 'been', 'have', 'will', 'would', 'could', 'should', 'there', 'their', 'them', 'then', 'than', 'when', 'what', 'which', 'where', 'while'}
            quote_words = [w for w in words if len(w) > 3 and w not in stop_words][:15]  # Take first 15 significant words
            
            # Verify against actual Hansard page
            verified_speaker, speaker_url, confidence = self.parse_debate_and_verify(hansard_url, quote_words)
            
            if verified_speaker:
                # Apply consistent formatting
                verified_speaker = self.standardize_name_format(verified_speaker)
                
                print(f"  Verified: {verified_speaker} (confidence: {confidence})")
                
                # Check if this is different from current attribution
                if verified_speaker != current_best:
                    print(f"  MISATTRIBUTION DETECTED!")
                    print(f"     Current: {current_best}")
                    print(f"     Correct: {verified_speaker}")
                    misattribution_count += 1
                    status = "CORRECTED"
                else:
                    print(f"  Attribution confirmed")
                    status = "VERIFIED"
                
                # Update database with verified information
                conn.execute("""
                    UPDATE quotes 
                    SET verified_speaker = ?, verification_confidence = ?, verification_status = ?
                    WHERE id = ?
                """, (verified_speaker, confidence, status, quote_id))
                conn.commit()
                
                verified_count += 1
            else:
                print(f"  Could not verify speaker")
                conn.execute("""
                    UPDATE quotes 
                    SET verification_status = 'UNVERIFIABLE'
                    WHERE id = ?
                """, (quote_id,))
                conn.commit()
            
            # Rate limiting
            time.sleep(0.5)
        
        conn.close()
        
        print(f"\nVERIFICATION COMPLETE!")
        print(f"Verified: {verified_count} quotes")
        print(f"Misattributions found: {misattribution_count}")
        print(f"All speaker names now consistently formatted")
        
        return verified_count, misattribution_count

    def format_all_existing_speakers(self):
        """Apply consistent formatting to all existing speaker names"""
        conn = sqlite3.connect(self.db_path)
        
        # Get all unique speaker names
        speakers = conn.execute("""
            SELECT DISTINCT speaker FROM quotes WHERE speaker IS NOT NULL
            UNION
            SELECT DISTINCT enhanced_speaker FROM quotes WHERE enhanced_speaker IS NOT NULL
            UNION  
            SELECT DISTINCT corrected_speaker FROM quotes WHERE corrected_speaker IS NOT NULL
        """).fetchall()
        
        print(f"Formatting {len(speakers)} unique speaker names...")
        
        for (speaker,) in speakers:
            if speaker and speaker.strip():
                formatted = self.standardize_name_format(speaker)
                if formatted != speaker:
                    print(f"  {speaker} -> {formatted}")
                    
                    # Update all instances in database
                    conn.execute("UPDATE quotes SET speaker = ? WHERE speaker = ?", (formatted, speaker))
                    conn.execute("UPDATE quotes SET enhanced_speaker = ? WHERE enhanced_speaker = ?", (formatted, speaker))
                    conn.execute("UPDATE quotes SET corrected_speaker = ? WHERE corrected_speaker = ?", (formatted, speaker))
        
        conn.commit()
        conn.close()
        print("All speaker names formatted consistently")

def main():
    print("=== SPEAKER VERIFICATION & FORMATTING ===")
    print("This will verify attributions and standardize name formatting")
    
    verifier = SpeakerVerificationAndFormatting()
    
    # First, format existing names consistently
    print("\n1. Formatting existing speaker names...")
    verifier.format_all_existing_speakers()
    
    # Then verify and fix attributions
    print("\n2. Starting verification process...")
    print("Testing on first 10 quotes...")
    
    verified, misattributions = verifier.verify_and_fix_attributions(limit=10)
    
    if verified > 0:
        print(f"\nTest complete! Found {misattributions} misattributions out of {verified} verified")
        
        if misattributions > 0:
            proceed = input(f"\nFound {misattributions} misattributions in test. Continue with full verification? (y/N): ").strip().lower()
            
            if proceed == 'y':
                print("\nRunning full verification...")
                total_verified, total_misattributions = verifier.verify_and_fix_attributions()
                print(f"\nComplete! {total_verified} verified, {total_misattributions} corrected")
            else:
                print("Verification stopped.")
        else:
            print("No misattributions found in test sample!")
    else:
        print("Verification test failed - check your internet connection")

if __name__ == "__main__":
    main()