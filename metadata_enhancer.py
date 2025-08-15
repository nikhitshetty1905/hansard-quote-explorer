# metadata_enhancer.py
# Enhance existing quotes with better speaker names and debate titles

import sqlite3
import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urlparse

class HansardMetadataEnhancer:
    def __init__(self, db_path="hansard_simple.db"):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "HansardResearch/1.0"})
        
    def extract_speaker_from_html(self, html_content, quote_text):
        """Extract speaker name from HTML, looking for blue links near the quote"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for speaker links (typically in <a> tags with member hrefs)
        speaker_links = soup.find_all('a', href=re.compile(r'/members/|/people/'))
        
        # Try to find speaker near the quote text
        quote_words = quote_text.split()[:10]  # First 10 words of quote
        
        for link in speaker_links:
            speaker_name = link.get_text().strip()
            if not speaker_name:
                continue
                
            # Look for this speaker near quote text in the page
            link_parent = link.parent
            if link_parent:
                parent_text = link_parent.get_text()
                
                # Check if quote words appear near this speaker
                for word in quote_words:
                    if len(word) > 3 and word.lower() in parent_text.lower():
                        return self.clean_speaker_name(speaker_name)
        
        # Fallback: look for common speaker patterns
        speaker_patterns = [
            r'(Mr\.?\s+[A-Z][a-zA-Z\s]+?)(?:\s|:|\()',
            r'(Sir\s+[A-Z][a-zA-Z\s]+?)(?:\s|:|\()',
            r'(Lord\s+[A-Z][a-zA-Z\s]+?)(?:\s|:|\()',
            r'(The\s+(?:Secretary|Minister|President)\s+[a-zA-Z\s]+?)(?:\s|:|\()',
        ]
        
        full_text = soup.get_text()
        for pattern in speaker_patterns:
            matches = re.findall(pattern, full_text)
            if matches:
                return self.clean_speaker_name(matches[0])
        
        return None
    
    def clean_speaker_name(self, name):
        """Clean and standardize speaker name"""
        name = name.strip()
        # Remove extra whitespace
        name = re.sub(r'\s+', ' ', name)
        # Ensure proper title formatting
        if name.startswith('mr '):
            name = 'Mr. ' + name[3:]
        elif name.startswith('sir '):
            name = 'Sir ' + name[4:]
        elif name.startswith('lord '):
            name = 'Lord ' + name[5:]
        
        return name
    
    def extract_debate_title(self, html_content, url):
        """Extract debate title from HTML page"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Try multiple selectors for debate title
        title_selectors = [
            'h1',  # Main heading
            '.debate-title',
            '.content-header h1',
            '.page-header h1',
            'title'
        ]
        
        for selector in title_selectors:
            elements = soup.select(selector)
            if elements:
                title = elements[0].get_text().strip()
                if title and len(title) > 5:  # Avoid empty or too short titles
                    return self.clean_debate_title(title)
        
        # Fallback: extract from URL
        path_parts = urlparse(url).path.split('/')
        if len(path_parts) > 3:
            # Look for debate identifier in URL
            debate_part = path_parts[-1] or path_parts[-2]
            if debate_part:
                return debate_part.replace('-', ' ').title()
        
        return None
    
    def clean_debate_title(self, title):
        """Clean and standardize debate title"""
        # Remove common prefixes/suffixes
        title = re.sub(r'^(HC Deb|HL Deb)\s*', '', title)
        title = re.sub(r'\s*-\s*Hansard.*$', '', title, re.IGNORECASE)
        
        # Clean up formatting
        title = title.strip()
        title = re.sub(r'\s+', ' ', title)
        
        # Handle common debate types
        if 'aliens' in title.lower():
            if 'bill' in title.lower():
                return "Aliens Bill"
            else:
                return "Aliens Act Debate"
        elif 'unemployed' in title.lower() or 'unemployment' in title.lower():
            return "Unemployment Debate"
        elif 'industrial' in title.lower() and 'unrest' in title.lower():
            return "Industrial Unrest Debate"
        elif 'trade' in title.lower() and ('dispute' in title.lower() or 'union' in title.lower()):
            return "Trade Disputes Debate"
        elif 'labour' in title.lower() and 'exchange' in title.lower():
            return "Labour Exchange Debate"
        
        return title
    
    def extract_party_info(self, html_content, speaker_name):
        """Try to extract party information for speaker"""
        if not speaker_name:
            return None
            
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for party info near speaker name
        party_patterns = [
            r'(Conservative|Liberal|Labour|Unionist|Irish\s+Nationalist)',
        ]
        
        full_text = soup.get_text()
        speaker_index = full_text.find(speaker_name)
        if speaker_index >= 0:
            # Look for party info within 200 characters of speaker name
            context = full_text[max(0, speaker_index-100):speaker_index+100]
            
            for pattern in party_patterns:
                match = re.search(pattern, context, re.IGNORECASE)
                if match:
                    return match.group(1)
        
        return None
    
    def enhance_quote_metadata(self, quote_id, hansard_url, quote_text, current_speaker):
        """Enhance metadata for a single quote"""
        try:
            print(f"  Enhancing quote {quote_id}: {hansard_url[:60]}...")
            
            # Fetch the Hansard page
            response = self.session.get(hansard_url, timeout=15)
            if response.status_code != 200:
                print(f"    Failed to fetch (status {response.status_code})")
                return None, None, None
            
            html_content = response.text
            
            # Extract enhanced metadata
            speaker = None
            if current_speaker == "Unknown Speaker" or not current_speaker:
                speaker = self.extract_speaker_from_html(html_content, quote_text)
            
            debate_title = self.extract_debate_title(html_content, hansard_url)
            party = self.extract_party_info(html_content, speaker or current_speaker)
            
            print(f"    Speaker: {speaker or 'Not found'}")
            print(f"    Debate: {debate_title or 'Not found'}")
            print(f"    Party: {party or 'Not found'}")
            
            # Rate limiting
            time.sleep(0.5)
            
            return speaker, debate_title, party
            
        except Exception as e:
            print(f"    Error enhancing quote {quote_id}: {e}")
            return None, None, None
    
    def enhance_all_quotes(self, limit=None):
        """Enhance metadata for all quotes in database"""
        conn = sqlite3.connect(self.db_path)
        
        # Add new columns if they don't exist
        try:
            conn.execute("ALTER TABLE quotes ADD COLUMN debate_title TEXT")
            conn.execute("ALTER TABLE quotes ADD COLUMN enhanced_speaker TEXT")
            conn.execute("ALTER TABLE quotes ADD COLUMN enhanced_party TEXT")
            conn.commit()
            print("Added new metadata columns to database")
        except sqlite3.OperationalError:
            print("Metadata columns already exist")
        
        # Get quotes to enhance
        query = "SELECT id, hansard_url, quote, speaker, party FROM quotes"
        if limit:
            query += f" LIMIT {limit}"
        
        quotes = conn.execute(query).fetchall()
        print(f"\nEnhancing metadata for {len(quotes)} quotes...")
        
        enhanced_count = 0
        
        for quote_id, hansard_url, quote, current_speaker, current_party in quotes:
            speaker, debate_title, party = self.enhance_quote_metadata(
                quote_id, hansard_url, quote, current_speaker
            )
            
            # Update database with enhanced metadata
            updates = []
            params = []
            
            if debate_title:
                updates.append("debate_title = ?")
                params.append(debate_title)
            
            if speaker and speaker != current_speaker:
                updates.append("enhanced_speaker = ?")
                params.append(speaker)
            
            if party and party != current_party:
                updates.append("enhanced_party = ?")
                params.append(party)
            
            if updates:
                params.append(quote_id)
                update_query = f"UPDATE quotes SET {', '.join(updates)} WHERE id = ?"
                conn.execute(update_query, params)
                conn.commit()
                enhanced_count += 1
        
        conn.close()
        
        print(f"\nEnhancement complete!")
        print(f"Enhanced metadata for {enhanced_count} quotes")
        
        return enhanced_count

def main():
    print("=== HANSARD METADATA ENHANCER ===")
    print("This will enhance existing quotes with better speaker names and debate titles")
    print("Your quote text will NOT be changed - only metadata improvements")
    
    enhancer = HansardMetadataEnhancer()
    
    # Start with a small test
    print("\nTesting on first 5 quotes...")
    test_count = enhancer.enhance_all_quotes(limit=5)
    
    if test_count > 0:
        print(f"\nTest successful! Enhanced {test_count} quotes")
        
        proceed = input("\nContinue with full enhancement of all quotes? (y/N): ").strip().lower()
        
        if proceed == 'y':
            print("\nRunning full enhancement...")
            total_enhanced = enhancer.enhance_all_quotes()
            print(f"\nComplete! Enhanced {total_enhanced} quotes total")
        else:
            print("Enhancement stopped. Test data remains in database.")
    else:
        print("Test failed - no quotes were enhanced. Check your database and network connection.")

if __name__ == "__main__":
    main()