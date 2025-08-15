# run_cleanup.py
# Clean all analyses to be pithy descriptions

import sqlite3
import re

def clean_analysis(analysis_text):
    """Convert verbose Claude analysis to pithy description"""
    
    if not analysis_text:
        return ""
    
    # Remove historian preambles and meta language
    text = analysis_text
    text = re.sub(r"Here's my.*?analysis.*?:", "", text, flags=re.IGNORECASE)
    text = re.sub(r"As a historian.*?follows:", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"As a historian.*?:", "", text, flags=re.IGNORECASE | re.DOTALL)
    
    # Clean up start
    text = text.strip()
    
    # Get first substantial sentence (30+ chars)
    sentences = text.split('. ')
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 30 and len(sentence) < 200:  # Not too short, not too long
            if not sentence.endswith('.'):
                sentence += '.'
            return sentence
    
    # Fallback: first 150 characters
    if len(text) > 150:
        text = text[:147] + '...'
    return text

# Process all analyses
db = sqlite3.connect('database_updated.db')

try:
    cursor = db.execute("SELECT id, historian_analysis FROM quotes WHERE historian_analysis IS NOT NULL")
    rows = cursor.fetchall()
    
    print(f"Processing {len(rows)} analyses...")
    
    updated = 0
    for quote_id, analysis in rows:
        if analysis and len(analysis) > 80:  # Only clean long ones
            cleaned = clean_analysis(analysis)
            
            if cleaned and cleaned != analysis:
                db.execute("UPDATE quotes SET historian_analysis = ? WHERE id = ?", (cleaned, quote_id))
                updated += 1
    
    db.commit()
    print(f"✅ Updated {updated} analyses to be pithy descriptions")
    
except Exception as e:
    print(f"Error: {e}")
    
finally:
    db.close()