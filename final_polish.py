# final_polish.py
# Final pass to ensure all analyses are concise and clean

import sqlite3
import re

def make_concise(analysis):
    """Make analysis more concise while preserving meaning"""
    
    if not analysis or len(analysis) < 100:
        return analysis
    
    # Remove remaining meta language
    text = analysis.strip()
    text = re.sub(r'This analysis reflects my expertise.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'while avoiding presentist interpretations.*', '', text, flags=re.IGNORECASE)
    text = text.strip()
    
    # If still over 150 chars, try to shorten while keeping meaning
    if len(text) > 150:
        # Look for main clause before first comma or "while/particularly" 
        parts = re.split(r',\s*(?:while|particularly|specifically)', text)
        if len(parts) > 1 and len(parts[0]) > 50:
            main_insight = parts[0].strip()
            if not main_insight.endswith('.'):
                main_insight += '.'
            return main_insight
        
        # Try splitting at "revealing" or similar
        parts = re.split(r',\s*(?:revealing|demonstrating|highlighting)', text)
        if len(parts) > 1 and len(parts[0]) > 50:
            main_insight = parts[0].strip()
            if not main_insight.endswith('.'):
                main_insight += '.'
            return main_insight
    
    return text

# Apply final polish
db = sqlite3.connect('database_fixed.db')

try:
    cursor = db.execute("SELECT id, historian_analysis FROM quotes WHERE LENGTH(historian_analysis) > 150")
    long_analyses = cursor.fetchall()
    
    print(f"Polishing {len(long_analyses)} lengthy analyses...")
    
    polished = 0
    for quote_id, analysis in long_analyses:
        concise_version = make_concise(analysis)
        
        if concise_version != analysis and len(concise_version) < len(analysis):
            db.execute("UPDATE quotes SET historian_analysis = ? WHERE id = ?", 
                      (concise_version, quote_id))
            polished += 1
            
            if polished <= 3:  # Show examples
                print(f"\\nQuote {quote_id}:")
                print(f"LONG:    {analysis}")
                print(f"CONCISE: {concise_version}")
                print("-" * 60)
    
    db.commit()
    print(f"\\nPolished {polished} analyses to be more concise")
    
    # Final quality check
    avg_length = db.execute("SELECT AVG(LENGTH(historian_analysis)) FROM quotes WHERE historian_analysis IS NOT NULL").fetchone()[0]
    print(f"Average analysis length now: {avg_length:.1f} characters")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()