# enhanced_speaker_parser.py
# Improved speaker identification for Hansard quotes

import re
import sqlite3
from typing import Optional, List, Tuple

class EnhancedSpeakerParser:
    """Enhanced speaker identification for parliamentary debates"""
    
    def __init__(self):
        # Comprehensive speaker patterns
        self.speaker_patterns = [
            # Basic patterns with proper cleanup
            r'(Mr\.|Mrs\.|Sir|Lord|Dr\.)\s+([A-Z][A-Za-z\s\-\']+?)(?=\s*[:.\n]|\s+(?:asked|said|replied|stated|declared|moved|rose))',
            
            # Government positions
            r'(The\s+(?:Secretary|Minister|President|Chairman|Speaker|Attorney-General))\s*(?:of\s+State)?\s*(?:for\s+[A-Za-z\s]+)?',
            
            # Full titles with constituencies
            r'(Mr\.|Mrs\.|Sir|Lord|Dr\.)\s+([A-Z][A-Za-z\s\-\']+?)\s*\([^)]+\)',
            
            # Simple name extraction
            r'^(Mr\.|Mrs\.|Sir|Lord|Dr\.)\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)',
            
            # Names in capitals
            r'(Mr\.|Mrs\.|Sir|Lord|Dr\.)\s+([A-Z]+(?:\s+[A-Z]+)*)',
        ]
        
        # Compile patterns
        self.compiled_patterns = [re.compile(pattern, re.MULTILINE) for pattern in self.speaker_patterns]
        
        # Known parliamentary roles
        self.parliamentary_roles = [
            'Secretary of State', 'Minister', 'President', 'Chairman', 'Speaker',
            'Attorney-General', 'Chancellor', 'Prime Minister'
        ]

    def clean_speaker_name(self, raw_speaker: str) -> str:
        """Clean and standardize speaker names"""
        
        if not raw_speaker or raw_speaker.strip() == "":
            return "Unknown Speaker"
        
        # Remove extra whitespace and newlines
        cleaned = re.sub(r'\s+', ' ', raw_speaker.strip())
        
        # Fix double periods (Mr.. -> Mr.)
        cleaned = re.sub(r'\.\.+', '.', cleaned)
        
        # Remove trailing punctuation
        cleaned = re.sub(r'[.:,;]+$', '', cleaned)
        
        # Remove common trailing phrases
        trailing_patterns = [
            r'\s+asked\b.*',
            r'\s+said\b.*', 
            r'\s+replied\b.*',
            r'\s+stated\b.*',
            r'\s+declared\b.*',
            r'\s+moved\b.*',
            r'\s+rose\b.*',
            r'\s+\([^)]*\)$',  # Remove constituency in brackets at end
        ]
        
        for pattern in trailing_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Standardize titles
        cleaned = re.sub(r'\bMr\.?\b', 'Mr.', cleaned)
        cleaned = re.sub(r'\bMrs\.?\b', 'Mrs.', cleaned)
        cleaned = re.sub(r'\bDr\.?\b', 'Dr.', cleaned)
        
        # Handle incomplete names (single letters after titles) - only if originally incomplete
        if re.match(r'^(Mr\.|Mrs\.|Dr\.|Sir|Lord)\s+[A-Z]$', cleaned) and re.match(r'^(Mr\.|Mrs\.|Dr\.|Sir|Lord)\s+[A-Z]$', raw_speaker.strip()):
            return "Unknown Speaker"
        
        # Handle very short names that are likely incomplete - only if originally very short
        if len(cleaned) <= 4 and len(raw_speaker.strip()) <= 4 and not any(title in cleaned for title in ['Sir', 'Lord']):
            return "Unknown Speaker"
        
        # Final cleanup
        cleaned = cleaned.strip()
        
        return cleaned if cleaned else "Unknown Speaker"

    def extract_speakers_from_text(self, text: str) -> List[str]:
        """Extract all potential speakers from text"""
        
        speakers = []
        
        for pattern in self.compiled_patterns:
            matches = pattern.findall(text)
            
            for match in matches:
                if isinstance(match, tuple):
                    # Handle tuple matches (title, name)
                    if len(match) >= 2:
                        speaker = f"{match[0]} {match[1]}".strip()
                    else:
                        speaker = match[0].strip()
                else:
                    speaker = match.strip()
                
                cleaned_speaker = self.clean_speaker_name(speaker)
                if cleaned_speaker != "Unknown Speaker" and len(cleaned_speaker) > 3:
                    speakers.append(cleaned_speaker)
        
        return speakers

    def extract_speaker_from_html(self, html_content: str) -> str:
        """Extract speaker from HTML content using multiple methods"""
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Method 1: Look for speaker in specific HTML elements
            for tag in ['h3', 'h4', 'strong', 'b']:
                elements = soup.find_all(tag)
                for element in elements:
                    text = element.get_text().strip()
                    speakers = self.extract_speakers_from_text(text)
                    if speakers:
                        return speakers[0]
            
            # Method 2: Look in the beginning of paragraphs
            paragraphs = soup.find_all('p')
            for p in paragraphs[:5]:  # Check first 5 paragraphs
                text = p.get_text().strip()
                if len(text) > 20:  # Skip very short paragraphs
                    speakers = self.extract_speakers_from_text(text[:200])  # First 200 chars
                    if speakers:
                        return speakers[0]
            
            # Method 3: Full text search (fallback)
            full_text = soup.get_text()
            speakers = self.extract_speakers_from_text(full_text[:1000])  # First 1000 chars
            if speakers:
                return speakers[0]
                
        except Exception:
            pass
        
        return "Unknown Speaker"

    def extract_speaker_from_quote(self, quote_text: str) -> str:
        """Extract speaker from quote text itself"""
        
        # Try to find speaker at beginning of quote
        speakers = self.extract_speakers_from_text(quote_text[:300])  # First 300 chars
        
        if speakers:
            return speakers[0]
        
        # Look for common parliamentary phrases that might indicate speaker
        lines = quote_text.split('\n')
        for line in lines[:3]:  # Check first 3 lines
            if any(phrase in line.lower() for phrase in ['asked', 'said', 'replied', 'stated']):
                speakers = self.extract_speakers_from_text(line)
                if speakers:
                    return speakers[0]
        
        return "Unknown Speaker"

    def fix_database_speakers(self) -> int:
        """Fix all speaker names in the database"""
        
        conn = sqlite3.connect("hansard_simple.db")
        fixed_count = 0
        
        try:
            # Get all quotes with their current speakers
            cursor = conn.execute("SELECT id, speaker, quote, hansard_url FROM quotes")
            all_quotes = cursor.fetchall()
            
            print(f"Processing {len(all_quotes)} quotes for speaker identification...")
            
            for quote_id, current_speaker, quote_text, url in all_quotes:
                new_speaker = current_speaker
                
                # If current speaker is problematic, try to fix it
                if (current_speaker == "Unknown Speaker" or 
                    len(current_speaker) > 100 or  # Overly long speaker names
                    '\n' in current_speaker or     # Multi-line speaker names
                    'asked' in current_speaker.lower() or
                    'said' in current_speaker.lower() or
                    '..' in current_speaker or     # Double periods
                    re.match(r'^(Mr\.|Mrs\.|Dr\.)\s+[A-Z]$', current_speaker) or  # Single letter names
                    len(current_speaker.strip()) <= 4):  # Very short names
                    
                    # Try to extract from quote text
                    extracted_speaker = self.extract_speaker_from_quote(quote_text)
                    
                    if extracted_speaker != "Unknown Speaker":
                        new_speaker = extracted_speaker
                    else:
                        # Clean the existing speaker name if possible
                        new_speaker = self.clean_speaker_name(current_speaker)
                
                # Update if we have a better speaker name
                if new_speaker != current_speaker:
                    conn.execute("UPDATE quotes SET speaker = ? WHERE id = ?", (new_speaker, quote_id))
                    fixed_count += 1
                    
                    if fixed_count % 10 == 0:
                        print(f"  Fixed {fixed_count} speakers...")
                        conn.commit()
            
            conn.commit()
            print(f"Speaker fixing complete: {fixed_count} speakers improved")
            
        except Exception as e:
            print(f"Error fixing speakers: {e}")
        
        finally:
            conn.close()
        
        return fixed_count

    def analyze_speaker_quality(self) -> dict:
        """Analyze current speaker data quality"""
        
        conn = sqlite3.connect("hansard_simple.db")
        
        try:
            # Get speaker statistics
            total = conn.execute("SELECT COUNT(*) FROM quotes").fetchone()[0]
            unknown = conn.execute("SELECT COUNT(*) FROM quotes WHERE speaker = 'Unknown Speaker'").fetchone()[0]
            
            # Get problematic speakers
            problematic = conn.execute("""
                SELECT COUNT(*) FROM quotes 
                WHERE LENGTH(speaker) > 50 OR speaker LIKE '%\n%' OR speaker LIKE '%asked%' OR speaker LIKE '%said%'
            """).fetchone()[0]
            
            # Get unique speakers
            unique_speakers = conn.execute("SELECT COUNT(DISTINCT speaker) FROM quotes").fetchone()[0]
            
            # Sample of current speakers
            sample_speakers = conn.execute("SELECT DISTINCT speaker FROM quotes LIMIT 10").fetchall()
            
            return {
                'total_quotes': total,
                'unknown_speakers': unknown,
                'unknown_percentage': (unknown / total * 100) if total > 0 else 0,
                'problematic_speakers': problematic,
                'unique_speakers': unique_speakers,
                'sample_speakers': [s[0] for s in sample_speakers]
            }
            
        finally:
            conn.close()

def test_speaker_parser():
    """Test the enhanced speaker parser"""
    
    parser = EnhancedSpeakerParser()
    
    # Test cases
    test_texts = [
        "Mr. POINTER asked the terms of reference...",
        "Sir Kenelm Digby said that in his opinion...",
        "The Secretary of State for the Colonies replied...",
        "Lord Robert Cecil declared that the government...",
        "Dr. Wilson (Holmfirth) asked whether..."
    ]
    
    print("=== TESTING SPEAKER PARSER ===")
    
    for text in test_texts:
        speaker = parser.extract_speaker_from_quote(text)
        print(f"Text: {text[:50]}...")
        print(f"Speaker: {speaker}")
        print()

if __name__ == "__main__":
    test_speaker_parser()