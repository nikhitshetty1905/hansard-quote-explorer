# intelligent_cleanup.py
# Properly extract meaningful insights from verbose Claude analyses

import sqlite3
import re

def extract_meaningful_insight(verbose_analysis):
    """Intelligently extract the core insight from verbose Claude analysis"""
    
    if not verbose_analysis or len(verbose_analysis) < 20:
        return verbose_analysis
    
    text = verbose_analysis.strip()
    
    # Step 1: Remove all preambles completely
    preambles_to_remove = [
        r"Here's my historical analysis as a specialist in.*?:",
        r"As a historian of.*?:",
        r"Here's my analysis.*?:",
        r"My analysis.*?:",
        r"I would analyze this.*?as follows:",
        r"As a historian.*?I would analyze this.*?as",
        r"Here's my historical analysis:",
        r"As a historian.*?follows:"
    ]
    
    for pattern in preambles_to_remove:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)
    
    text = text.strip()
    
    # Step 2: Find the actual analytical content
    # Look for sentences that contain substantive analysis
    sentences = text.split('. ')
    
    good_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        
        # Skip meta sentences
        if any(skip in sentence.lower() for skip in [
            'this parliamentary intervention', 'this exchange', 'this debate',
            'this analysis captures', 'this is historically significant',
            'the significance lies', 'historically significant'
        ]):
            continue
            
        # Look for sentences with real content
        if (len(sentence) > 30 and 
            any(content_word in sentence.lower() for content_word in [
                'argues', 'reveals', 'demonstrates', 'reflects', 'advocates',
                'critiques', 'challenges', 'frames', 'positions', 'emphasizes',
                'highlights', 'questions', 'contrasts', 'represents'
            ])):
            good_sentences.append(sentence)
    
    # Step 3: Build concise insight
    if len(good_sentences) >= 1:
        # Take first substantial analytical sentence
        result = good_sentences[0]
        if not result.endswith('.'):
            result += '.'
        return result
    
    # Step 4: Fallback - extract from original structure
    # Look for key analytical phrases in the original text
    key_phrases = [
        r"(Digby's.*?competition)",
        r"(reveals.*?interests)",  
        r"(demonstrates.*?policy)",
        r"(reflects.*?concerns)",
        r"(frames.*?regulation)",
        r"(critiques.*?restrictions)",
        r"(questions.*?protections)",
        r"(contrasts.*?immigration)"
    ]
    
    for pattern in key_phrases:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            result = match.group(1).strip()
            if not result.endswith('.'):
                result += '.'
            return result
    
    # Step 5: Final fallback - take first complete sentence that makes sense
    first_sentences = text.split('. ')[:3]  # First 3 sentences only
    for sentence in first_sentences:
        sentence = sentence.strip()
        if (len(sentence) > 40 and 
            sentence.count(' ') > 5 and  # At least 6 words
            not sentence.lower().startswith(('this', 'the analysis', 'my analysis')) and
            '.' not in sentence[:-10]):  # Not truncated mid-sentence
            
            if not sentence.endswith('.'):
                sentence += '.'
            return sentence
    
    # Last resort - return first 100 chars if they form complete words
    if len(text) > 100:
        truncated = text[:100]
        last_space = truncated.rfind(' ')
        if last_space > 50:  # Reasonable cutoff point
            return truncated[:last_space] + '.'
    
    return text

def fix_all_analyses():
    """Fix all broken analyses with intelligent extraction"""
    
    # Start fresh from the verbose but complete database
    import shutil
    shutil.copy('database_updated.db', 'database_fixed.db')
    
    db = sqlite3.connect('database_fixed.db')
    
    try:
        # Get all analyses
        cursor = db.execute("SELECT id, historian_analysis FROM quotes WHERE historian_analysis IS NOT NULL")
        all_analyses = cursor.fetchall()
        
        print(f"Processing {len(all_analyses)} analyses with intelligent extraction...")
        
        fixed = 0
        for quote_id, analysis in all_analyses:
            if analysis and len(analysis) > 50:
                
                # Extract meaningful insight
                clean_insight = extract_meaningful_insight(analysis)
                
                if clean_insight and clean_insight != analysis and len(clean_insight) < len(analysis):
                    db.execute("UPDATE quotes SET historian_analysis = ? WHERE id = ?", 
                              (clean_insight, quote_id))
                    fixed += 1
                    
                    # Show first 5 examples
                    if fixed <= 5:
                        print(f"\\nQuote {quote_id}:")
                        print(f"BEFORE: {analysis[:120]}...")
                        print(f"AFTER:  {clean_insight}")
                        print("-" * 60)
        
        db.commit()
        print(f"\\n✅ Successfully fixed {fixed} analyses")
        print("Created database_fixed.db with proper content extraction")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_all_analyses()