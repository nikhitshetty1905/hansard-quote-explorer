# batch_cleanup.py
# Clean analyses in small batches to avoid lock issues

import sqlite3
import re
import time

def clean_analysis(text):
    if not text or len(text) < 50:
        return text
    
    # Remove preambles  
    text = re.sub(r'Here.*?s my.*?analysis.*?:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'As a historian.*?follows:', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'As a historian.*?:', '', text, flags=re.IGNORECASE)
    
    # Get first meaningful sentence
    text = text.strip()
    if '. ' in text:
        sentences = text.split('. ')
        for sentence in sentences:
            if len(sentence) > 30:  # Substantial sentence
                return sentence + '.'
    
    # Fallback
    return text[:150] + '...' if len(text) > 150 else text

# Process in small batches
batch_size = 50
processed = 0

while processed < 532:
    try:
        db = sqlite3.connect('database_updated.db')
        
        # Get batch
        cursor = db.execute(
            'SELECT id, historian_analysis FROM quotes WHERE id > ? AND historian_analysis IS NOT NULL LIMIT ?',
            (processed, batch_size)
        )
        batch = cursor.fetchall()
        
        if not batch:
            break
            
        # Update batch
        updated_in_batch = 0
        for quote_id, analysis in batch:
            if analysis and len(analysis) > 80:
                cleaned = clean_analysis(analysis)
                if cleaned != analysis:
                    db.execute('UPDATE quotes SET historian_analysis = ? WHERE id = ?', (cleaned, quote_id))
                    updated_in_batch += 1
        
        db.commit()
        processed += len(batch)
        
        print(f'Processed batch: {processed} total, {updated_in_batch} updated in this batch')
        
        db.close()
        time.sleep(0.1)  # Brief pause
        
    except Exception as e:
        print(f'Error in batch starting at {processed}: {e}')
        if 'db' in locals():
            db.close()
        break

print(f'✅ Completed processing {processed} analyses')