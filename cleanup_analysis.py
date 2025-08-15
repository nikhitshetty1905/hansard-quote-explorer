# cleanup_analysis.py
# Clean up Claude analyses to be pithy 2-line descriptions

import sqlite3
import re

def clean_analysis(analysis_text):
    """Convert verbose Claude analysis to pithy 2-line description"""
    
    if not analysis_text:
        return ""
    
    # Remove historian preambles
    text = analysis_text
    text = re.sub(r"Here's my historical analysis.*?follows:", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"As a historian.*?follows:", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"Here's my analysis.*?:", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"My analysis.*?:", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"This.*?analysis.*?:", "", text, flags=re.IGNORECASE)
    
    # Clean up start of text
    text = text.strip()
    
    # Split into sentences and take first two meaningful ones
    sentences = text.split('. ')
    
    # Filter out very short or meta sentences
    good_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 20 and not sentence.lower().startswith(('this', 'the analysis', 'my analysis')):
            good_sentences.append(sentence)
        if len(good_sentences) >= 2:
            break
    
    if len(good_sentences) >= 2:
        result = good_sentences[0] + '. ' + good_sentences[1]
        if not result.endswith('.'):
            result += '.'
    elif len(good_sentences) == 1:
        result = good_sentences[0]
        if not result.endswith('.'):
            result += '.'
    else:
        # Fallback: take first substantial chunk
        words = text.split()[:30]  # First 30 words max
        result = ' '.join(words)
        if not result.endswith('.'):
            result += '.'
    
    # Remove any remaining meta language
    result = re.sub(r"This parliamentary.*?reveals", "Reveals", result)
    result = re.sub(r"This intervention.*?demonstrates", "Demonstrates", result)
    result = re.sub(r"The speaker's.*?reflects", "Reflects", result)
    
    return result.strip()

def cleanup_all_analyses():
    """Clean up all analyses in the database"""
    
    db = sqlite3.connect('database_updated.db')
    
    try:
        # Get all analyses
        cursor = db.execute("SELECT id, historian_analysis FROM quotes WHERE historian_analysis IS NOT NULL")
        rows = cursor.fetchall()
        
        print(f"Cleaning up {len(rows)} analyses...")
        
        cleaned = 0
        for quote_id, analysis in rows:
            if analysis and len(analysis) > 100:  # Only clean verbose ones
                clean_analysis_text = clean_analysis(analysis)
                
                if clean_analysis_text and clean_analysis_text != analysis:
                    db.execute("UPDATE quotes SET historian_analysis = ? WHERE id = ?", 
                              (clean_analysis_text, quote_id))
                    cleaned += 1
                    
                    if cleaned <= 5:  # Show first 5 examples
                        print(f"\nQuote {quote_id}:")
                        print(f"BEFORE: {analysis[:100]}...")
                        print(f"AFTER:  {clean_analysis_text}")
                        print("-" * 50)
        
        db.commit()
        print(f"\n✅ Cleaned up {cleaned} verbose analyses")
        print("Analyses are now pithy 2-line descriptions without historian language")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_all_analyses()