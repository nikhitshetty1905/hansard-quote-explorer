# neutralize_tone.py
# Remove pretentious academic words to create neutral tone

import sqlite3
import re

def neutralize_academic_tone(analysis):
    """Remove pretentious academic words and phrases for neutral tone"""
    
    if not analysis:
        return analysis
    
    text = analysis
    
    # Step 1: Remove evaluative adjectives entirely
    evaluative_removals = [
        (r'\b(sophisticated|astute|shrewd|clever|nuanced|deft|strategic|strategically)\s+', ''),
        (r'\b(particularly|specifically|notably|significantly)\s+', ''),
        (r'\bthe\s+(sophisticated|astute|shrewd|clever|nuanced|strategic)\s+', 'the '),
    ]
    
    for pattern, replacement in evaluative_removals:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Step 2: Replace academic verbs with neutral ones
    verb_replacements = [
        (r'\bexemplifies\b', 'shows'),
        (r'\billuminates\b', 'shows'),
        (r'\bencapsulates\b', 'shows'),
        (r'\breveals\b', 'shows'),
        (r'\bdemonstrates\b', 'shows'),
        (r'\bhighlights\b', 'shows'),
        (r'\bunderscores\b', 'shows'),
        (r'\bmanifests\b', 'shows'),
        (r'\breflects\b', 'shows'),
    ]
    
    for pattern, replacement in verb_replacements:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Step 3: Simplify pretentious phrases
    phrase_simplifications = [
        (r'\bcomplex intersection of\b', 'intersection of'),
        (r'\bfundamental tension between\b', 'tension between'),
        (r'\bcrucial intersection of\b', 'intersection of'),
        (r'\bbroad(er)?\s+tensions\b', 'tensions'),
        (r'\bkey tensions\b', 'tensions'),
        (r'\bcrucial tensions\b', 'tensions'),
        (r'\bcomplex tensions\b', 'tensions'),
    ]
    
    for pattern, replacement in phrase_simplifications:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Step 4: Clean up any double spaces or awkward phrasing
    text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single
    text = re.sub(r'\s+,', ',', text)  # Space before comma
    text = re.sub(r'\.\s*\.', '.', text)  # Double periods
    
    # Step 5: Fix common awkward phrasings after removals
    awkward_fixes = [
        (r'\bargument\s+frames\b', 'argument frames'),
        (r'\bcritique\s+of\b', 'critique of'),
        (r'\bintervention\s+shows\b', 'intervention shows'),
        (r'\bthe\s+the\b', 'the'),  # Double "the"
    ]
    
    for pattern, replacement in awkward_fixes:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    return text.strip()

def neutralize_all_analyses():
    """Apply neutral tone to all analyses in database"""
    
    import shutil
    shutil.copy('database_fixed.db', 'database_neutral.db')
    
    db = sqlite3.connect('database_neutral.db')
    
    try:
        cursor = db.execute("SELECT id, historian_analysis FROM quotes WHERE historian_analysis IS NOT NULL")
        all_analyses = cursor.fetchall()
        
        print(f"Neutralizing tone for {len(all_analyses)} analyses...")
        
        changed = 0
        for quote_id, analysis in all_analyses:
            if analysis:
                neutral_analysis = neutralize_academic_tone(analysis)
                
                if neutral_analysis != analysis:
                    db.execute("UPDATE quotes SET historian_analysis = ? WHERE id = ?", 
                              (neutral_analysis, quote_id))
                    changed += 1
                    
                    # Show first 5 examples
                    if changed <= 5:
                        print(f"\\nQuote {quote_id}:")
                        print(f"BEFORE: {analysis}")
                        print(f"AFTER:  {neutral_analysis}")
                        print("-" * 70)
        
        db.commit()
        print(f"\\nChanged {changed} analyses to neutral tone")
        print("Created database_neutral.db with neutral tone")
        
        # Check for remaining academic words
        remaining = db.execute('''
            SELECT COUNT(*) FROM quotes 
            WHERE historian_analysis LIKE '%sophisticated%' 
               OR historian_analysis LIKE '%astute%'
               OR historian_analysis LIKE '%strategic%'
               OR historian_analysis LIKE '%exemplifies%'
        ''').fetchone()[0]
        
        print(f"Remaining academic words: {remaining} (should be 0)")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    neutralize_all_analyses()