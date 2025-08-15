# simple_cleanup.py  
# Manual cleanup of analyses to pithy 1-2 line descriptions

import sqlite3

# Create new clean database
import shutil
shutil.copy('database_updated.db', 'database_clean.db')

db = sqlite3.connect('database_clean.db')

# Manual cleanup patterns for common verbose phrases
cleanup_rules = [
    # Rule 1: Extract core insight from "This parliamentary intervention reveals..."
    ("This parliamentary intervention reveals the complex intersection between immigration control and labor market regulation in Edwardian Britain",
     "Frames immigration restriction as alternative to domestic labor regulation in the East End."),
    
    # Rule 2: Sophisticated critique patterns
    ("This parliamentary intervention represents a sophisticated critique of class-based immigration restrictions, deploying personal narrative to challenge the prevailing assumption that wealth should serve as a proxy for desirability in immigration policy",
     "Critiques class-based immigration restrictions, arguing productive labor matters more than wealth."),
    
    # Rule 3: Tension/conflict patterns  
    ("This parliamentary exchange illuminates a fundamental tension in early 20th-century British immigration policy between free-trade liberals and emerging protectionist interests",
     "Reveals Conservative Party split between free-trade and protectionist wings during Aliens Act debates."),
    
    # Rule 4: Constitutional/procedural arguments
    ("sophisticated critique of the Aliens Bill's practical enforceability regarding labor market protections",
     "Questions Aliens Bill enforceability regarding labor market protections."),
    
    # Rule 5: Historical comparison patterns
    ("Digby's intervention exemplifies the sophisticated fusion of economic protectionism and selective immigration rhetoric that characterized the 1905 Aliens Act debates, specifically by contrasting the \"desirable\" historical Huguenot immigration with contemporary Jewish immigration from Eastern Europe",
     "Contrasts desirable Huguenot immigration with contemporary Eastern European immigration through skilled vs unskilled labor lens.")
]

# Apply cleanup rules
updated = 0
cursor = db.execute("SELECT id, historian_analysis FROM quotes WHERE historian_analysis IS NOT NULL")
all_analyses = cursor.fetchall()

print(f"Processing {len(all_analyses)} analyses...")

for quote_id, analysis in all_analyses:
    if not analysis or len(analysis) < 100:
        continue
        
    # Remove preambles first
    clean_text = analysis
    clean_text = clean_text.replace("Here's my historical analysis as a specialist in early 20th-century British immigration policy:", "")
    clean_text = clean_text.replace("Here's my historical analysis:", "")
    clean_text = clean_text.replace("As a historian of early 20th-century British immigration policy, I would analyze this 1905 parliamentary intervention as", "")
    clean_text = clean_text.replace("As a historian of early 20th-century British labor policy, I would analyze this quote as follows:", "")
    clean_text = clean_text.strip()
    
    # Apply specific cleanup rules
    new_analysis = None
    for pattern, replacement in cleanup_rules:
        if pattern.lower() in clean_text.lower():
            new_analysis = replacement
            break
    
    # If no specific rule matched, extract first substantial sentence
    if not new_analysis:
        sentences = clean_text.split('. ')
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 40 and len(sentence) < 120:  # Good length
                new_analysis = sentence + '.'
                break
    
    # Final fallback - truncate to reasonable length
    if not new_analysis:
        new_analysis = clean_text[:100].strip()
        if not new_analysis.endswith('.'):
            new_analysis += '.'
    
    # Update if changed
    if new_analysis and new_analysis != analysis:
        db.execute("UPDATE quotes SET historian_analysis = ? WHERE id = ?", (new_analysis, quote_id))
        updated += 1

db.commit()
db.close()

print(f"Updated {updated} analyses to be pithy descriptions")
print("New clean database saved as database_clean.db")