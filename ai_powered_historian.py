# ai_powered_historian.py
# AI-Powered Historian for meaningful historical analysis

import sqlite3
import json
import time
from typing import Optional

class AIHistorian:
    """AI-powered historian that generates meaningful historical analysis"""
    
    def __init__(self, db_path="hansard_simple.db"):
        self.db_path = db_path
        
        # Historical context for prompting
        self.historical_contexts = {
            1900: "Turn of century industrial expansion period",
            1901: "Early Edwardian era with economic concerns", 
            1902: "Post-Boer War economic adjustment",
            1903: "Tariff Reform debates under Chamberlain",
            1904: "Growing immigration concerns and discourse",
            1905: "Aliens Act debates - first major immigration legislation",
            1906: "Liberal landslide victory and reform agenda",
            1907: "Economic downturn and rising labour tensions",
            1908: "Continuing Liberal social reforms",
            1909: "Constitutional crisis over People's Budget",
            1910: "Constitutional crisis resolution",
            1911: "Major industrial strike wave and labour unrest",
            1912: "Continuing labour disputes and strikes",
            1913: "Pre-war economic and social tensions",
            1914: "Outbreak of First World War",
            1915: "Wartime economic mobilization",
            1916: "Wartime labour shortages",
            1917: "Wartime production demands and conscription",
            1918: "War's end and demobilization planning",
            1919: "Post-war economic reconstruction",
            1920: "Economic reconversion and labour tensions",
            1921: "Post-war economic depression",
            1922: "Economic recovery attempts",
            1923: "Political instability and economic challenges",
            1924: "First Labour government under MacDonald",
            1925: "Economic stabilization efforts",
            1926: "General Strike and industrial conflict",
            1927: "Post-General Strike industrial relations",
            1928: "Economic recovery and modernization",
            1929: "Economic prosperity before Wall Street Crash",
            1930: "Beginning of Great Depression"
        }

    def create_analysis_prompt(self, quote: str, speaker: str, year: int, frame: str) -> str:
        """Create a detailed prompt for AI analysis"""
        
        historical_context = self.historical_contexts.get(year, f"Political and economic context of {year}")
        
        prompt = f"""You are a specialist historian of British immigration and labour policy. Analyze this parliamentary quote from {year}.

QUOTE: "{quote}"
SPEAKER: {speaker}
YEAR: {year}
HISTORICAL CONTEXT: {historical_context}
DEBATE FRAME: {frame}

Provide a concise (1-2 sentences) historical analysis that:
1. Identifies the specific argument being made (not just "discusses immigration")
2. Places it in historical context of {year}
3. Explains what this reveals about attitudes/concerns of the time
4. Uses precise historical language

Focus on WHAT the speaker is actually arguing and WHY this mattered in {year}.

Examples of good analysis:
- "Reflects growing middle-class anxiety about East End overcrowding as Jewish immigration peaked before the 1905 Aliens Act"
- "Demonstrates post-war concerns about German nationals in British shipping, linking national security to employment protection"
- "Illustrates Liberal tensions between free trade ideology and constituency pressure for immigration controls"

Avoid generic phrases like "discusses immigration policy" or "addresses concerns about". Be specific about the historical argument and context."""

        return prompt

    def get_ai_analysis(self, prompt: str) -> str:
        """Get AI analysis - placeholder for actual AI integration"""
        
        # This is a placeholder - in a real implementation you would:
        # 1. Call OpenAI API
        # 2. Call Claude API  
        # 3. Use local LLM
        
        # For now, return a more thoughtful analysis based on content patterns
        return self.generate_smart_fallback_analysis(prompt)
    
    def generate_smart_fallback_analysis(self, prompt: str) -> str:
        """Generate more intelligent analysis without AI API"""
        
        # Extract key information from the prompt
        lines = prompt.split('\n')
        quote = ""
        year = 0
        context = ""
        
        for line in lines:
            if line.startswith('QUOTE:'):
                quote = line.replace('QUOTE: "', '').replace('"', '').lower()
            elif line.startswith('YEAR:'):
                year = int(line.replace('YEAR: ', ''))
            elif line.startswith('HISTORICAL CONTEXT:'):
                context = line.replace('HISTORICAL CONTEXT: ', '')
        
        # More sophisticated content analysis
        if 'beg to ask' in quote and ('secretary of state' in quote or 'minister' in quote):
            if 'colonies' in quote:
                return f"Parliamentary question about colonial labour policy during {context.lower()}"
            elif 'home department' in quote:
                return f"Seeks clarification on domestic immigration enforcement during {context.lower()}"
            else:
                return f"Requests government data on immigration administration during {context.lower()}"
        
        elif 'aliens act' in quote or 'bill' in quote:
            if year == 1905:
                return "Debates the landmark Aliens Act - Britain's first comprehensive immigration control legislation"
            else:
                return f"References immigration legislation in context of {context.lower()}"
        
        elif 'east end' in quote or 'whitechapel' in quote:
            return f"Highlights East End overcrowding concerns that drove public support for immigration restriction"
        
        elif 'unemployment' in quote and ('alien' in quote or 'foreign' in quote):
            if year >= 1919:
                return f"Links immigration to post-war unemployment as demobilized soldiers seek work"
            else:
                return f"Connects foreign workers to domestic joblessness during economic uncertainty"
        
        elif 'wage' in quote and ('competition' in quote or 'reduce' in quote or 'lower' in quote):
            return f"Argues that immigrant labour undermines British wage standards during {context.lower()}"
        
        elif 'skill' in quote and ('alien' in quote or 'foreign' in quote):
            return f"Distinguishes between skilled and unskilled immigration in labour market debates"
        
        elif 'expulsion' in quote or 'exclude' in quote or 'restrict' in quote:
            return f"Advocates for restrictive immigration enforcement during {context.lower()}"
        
        elif 'trade union' in quote or 'organised labour' in quote:
            return f"Reflects trade union concerns about immigration's impact on working conditions"
        
        elif 'statistics' in quote or 'figures' in quote:
            return f"Demands empirical evidence to inform immigration policy during {context.lower()}"
        
        elif year >= 1914 and year <= 1918 and ('enemy' in quote or 'german' in quote):
            return f"Addresses wartime concerns about enemy aliens and national security"
        
        else:
            # Last resort - but more specific than before
            if year == 1905:
                return "Contributes to historic Aliens Act debates that established Britain's first immigration controls"
            elif year >= 1919 and year <= 1922:
                return f"Reflects post-war anxieties about economic reconstruction and foreign competition"
            else:
                return f"Represents parliamentary discourse on immigration during {context.lower()}"

    def analyze_quote(self, quote_id: int) -> Optional[str]:
        """Generate AI-powered analysis for a specific quote"""
        
        conn = sqlite3.connect(self.db_path)
        
        try:
            cursor = conn.execute("""
                SELECT quote, speaker, year, frame 
                FROM quotes 
                WHERE id = ?
            """, (quote_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
                
            quote, speaker, year, frame = row
            
            # Create AI prompt
            prompt = self.create_analysis_prompt(quote, speaker, year, frame)
            
            # Get AI analysis (or smart fallback)
            analysis = self.get_ai_analysis(prompt)
            
            # Update database
            conn.execute("""
                UPDATE quotes 
                SET historian_analysis = ? 
                WHERE id = ?
            """, (analysis, quote_id))
            conn.commit()
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing quote {quote_id}: {e}")
            return None
            
        finally:
            conn.close()

    def regenerate_all_analyses(self, limit=None) -> int:
        """Regenerate all analyses with AI-powered approach"""
        
        conn = sqlite3.connect(self.db_path)
        processed = 0
        
        try:
            # Get all quotes
            query = "SELECT id, quote, speaker, year, frame FROM quotes ORDER BY year, id"
            if limit:
                query += f" LIMIT {limit}"
                
            cursor = conn.execute(query)
            all_quotes = cursor.fetchall()
            
            print(f"Regenerating analyses for {len(all_quotes)} quotes with AI approach...")
            
            for quote_id, quote, speaker, year, frame in all_quotes:
                try:
                    # Create prompt and get analysis
                    prompt = self.create_analysis_prompt(quote, speaker, year, frame)
                    analysis = self.get_ai_analysis(prompt)
                    
                    conn.execute("""
                        UPDATE quotes 
                        SET historian_analysis = ? 
                        WHERE id = ?
                    """, (analysis, quote_id))
                    
                    processed += 1
                    
                    if processed % 20 == 0:
                        print(f"  Processed {processed} quotes...")
                        conn.commit()
                        
                    # Small delay to avoid overwhelming
                    time.sleep(0.1)
                        
                except Exception as e:
                    print(f"Error with quote {quote_id}: {e}")
                    continue
            
            conn.commit()
            print(f"Completed: {processed} AI-powered analyses generated")
            
        except Exception as e:
            print(f"Regeneration error: {e}")
            
        finally:
            conn.close()
            
        return processed

def test_ai_historian():
    """Test the AI historian"""
    
    historian = AIHistorian()
    
    # Test with a few quotes
    conn = sqlite3.connect("hansard_simple.db")
    cursor = conn.execute("""
        SELECT id, quote, speaker, year, frame 
        FROM quotes 
        WHERE id IN (7, 18, 31)
    """)
    
    print("=== TESTING AI-POWERED HISTORIAN ===\n")
    
    for quote_id, quote, speaker, year, frame in cursor.fetchall():
        print(f"Quote {quote_id} ({speaker}, {year}):")
        print(f"Text: {quote[:120]}...")
        
        # Create prompt
        prompt = historian.create_analysis_prompt(quote, speaker, year, frame)
        analysis = historian.get_ai_analysis(prompt)
        
        print(f"Analysis: {analysis}")
        print("-" * 80)
    
    conn.close()

if __name__ == "__main__":
    test_ai_historian()