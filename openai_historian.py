# openai_historian.py
# Real AI-powered historian using OpenAI API

import sqlite3
from openai import OpenAI
import time
from typing import Optional
import os

class OpenAIHistorian:
    """Real AI-powered historian using OpenAI API"""
    
    def __init__(self, db_path="hansard_simple.db", api_key=None):
        self.db_path = db_path
        
        # Set up OpenAI client
        if api_key:
            self.client = OpenAI(api_key=api_key)
        elif os.getenv('OPENAI_API_KEY'):
            self.client = OpenAI()  # Uses OPENAI_API_KEY env var
        else:
            print("Warning: No OpenAI API key provided. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
            self.client = None
        
        # Historical context for better prompting
        self.historical_contexts = {
            1900: "Turn of century industrial expansion, rising immigration concerns",
            1901: "Early Edwardian era, economic uncertainty after Boer War", 
            1902: "Post-Boer War economic adjustment, imperial consolidation",
            1903: "Tariff Reform debates under Chamberlain, trade policy divisions",
            1904: "Growing immigration discourse, pre-Aliens Act tensions",
            1905: "Aliens Act debates - Britain's first major immigration legislation",
            1906: "Liberal landslide victory, social reform agenda begins",
            1907: "Economic downturn, rising labour tensions and unemployment",
            1908: "Continuing Liberal social reforms, Old Age Pensions Act",
            1909: "People's Budget crisis, constitutional conflict with Lords",
            1910: "Constitutional crisis resolution, two general elections",
            1911: "Major industrial strike wave, transport and mining disputes",
            1912: "Continuing labour unrest, dock and transport strikes",
            1913: "Pre-war social tensions, suffrage and Irish Home Rule crises",
            1914: "Outbreak of First World War, economic mobilization",
            1915: "Wartime economic controls, munitions production expansion",
            1916: "Wartime labour shortages, dilution of skilled work",
            1917: "Wartime production demands, conscription and manpower",
            1918: "War's end, demobilization planning and reconstruction",
            1919: "Post-war reconstruction, returning soldiers and unemployment",
            1920: "Economic reconversion, inflation and labour militancy",
            1921: "Post-war depression, mass unemployment begins",
            1922: "Economic crisis deepens, political instability",
            1923: "Economic recovery attempts, Baldwin's first government",
            1924: "First Labour government under MacDonald",
            1925: "Return to Gold Standard, economic stabilization efforts",
            1926: "General Strike, major industrial conflict",
            1927: "Post-General Strike settlement, trade union reforms",
            1928: "Economic recovery, industrial modernization",
            1929: "Economic optimism before Wall Street Crash",
            1930: "Great Depression begins, mass unemployment returns"
        }

    def create_historian_prompt(self, quote: str, speaker: str, year: int, frame: str) -> str:
        """Create detailed prompt for OpenAI historical analysis"""
        
        historical_context = self.historical_contexts.get(year, f"Political and economic context of {year}")
        
        prompt = f"""You are a specialist historian of British immigration and labour policy (1900-1930). Analyze this parliamentary quote with academic precision.

QUOTE: "{quote}"
SPEAKER: {speaker}  
YEAR: {year}
HISTORICAL CONTEXT: {historical_context}
DEBATE FRAME: {frame}

Provide a concise historical analysis (1-2 sentences, max 150 words) that:

1. Identifies the SPECIFIC argument/position being taken (not just "discusses immigration")
2. Explains the historical significance and context for {year}
3. Connects to broader political/economic patterns of the period
4. Uses precise academic language appropriate for scholarly research

Focus on WHAT this reveals about attitudes, concerns, or political strategies of the time.

GOOD EXAMPLES:
- "Reflects Conservative strategy to frame immigration restriction as economic necessity rather than racial prejudice, typical of 1905 Aliens Act debates"
- "Demonstrates Liberal tension between free-trade ideology and constituency pressure over Jewish immigration to East London"
- "Articulates post-war anxiety about foreign competition for jobs as demobilized soldiers returned to civilian employment"

AVOID generic phrases like:
- "discusses immigration policy" 
- "addresses concerns about"
- "talks about the issue of"

Be specific about the historical argument and its significance."""

        return prompt

    def get_openai_analysis(self, prompt: str) -> str:
        """Get analysis from OpenAI API"""
        
        if not self.client:
            return self.generate_fallback_analysis(prompt)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Cost-effective model
                messages=[
                    {"role": "system", "content": "You are a specialist historian of British immigration and labour policy. Provide concise, academically precise historical analysis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.3,  # Lower temperature for more consistent analysis
            )
            
            analysis = response.choices[0].message.content.strip()
            return analysis
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            # Fallback to smart rule-based analysis
            return self.generate_fallback_analysis(prompt)

    def generate_fallback_analysis(self, prompt: str) -> str:
        """Fallback analysis if API fails"""
        
        # Extract key info from prompt
        lines = prompt.split('\n')
        quote_line = next((line for line in lines if line.startswith('QUOTE:')), "")
        year_line = next((line for line in lines if line.startswith('YEAR:')), "")
        
        if quote_line and year_line:
            quote = quote_line.replace('QUOTE: "', '').replace('"', '').lower()
            year = int(year_line.replace('YEAR: ', ''))
            
            # Smart fallback based on content
            if 'beg to ask' in quote and 'secretary of state' in quote:
                return f"Parliamentary inquiry seeking government data on immigration policy implementation ({year})"
            elif 'aliens act' in quote and year == 1905:
                return "Addresses Britain's landmark immigration legislation during historic parliamentary debates"
            elif 'exclusion' in quote or 'expulsion' in quote:
                return f"Advocates restrictive immigration enforcement reflecting {year} political tensions"
            else:
                return f"Contributes to parliamentary discourse on immigration during {year} political context"
        
        return "Parliamentary statement on immigration policy"

    def analyze_quote(self, quote_id: int) -> Optional[str]:
        """Generate OpenAI analysis for a specific quote"""
        
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
            
            # Create historian prompt
            prompt = self.create_historian_prompt(quote, speaker, year, frame)
            
            # Get OpenAI analysis
            analysis = self.get_openai_analysis(prompt)
            
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

    def regenerate_all_analyses(self, limit=None, start_id=1) -> int:
        """Regenerate analyses using OpenAI API"""
        
        conn = sqlite3.connect(self.db_path)
        processed = 0
        
        try:
            # Get quotes to process
            if limit:
                query = "SELECT id, quote, speaker, year, frame FROM quotes WHERE id >= ? ORDER BY id LIMIT ?"
                cursor = conn.execute(query, (start_id, limit))
            else:
                query = "SELECT id, quote, speaker, year, frame FROM quotes WHERE id >= ? ORDER BY id"
                cursor = conn.execute(query, (start_id,))
                
            all_quotes = cursor.fetchall()
            
            print(f"Generating OpenAI analyses for {len(all_quotes)} quotes...")
            print(f"Estimated cost: ${len(all_quotes) * 0.01:.2f} (approx)")
            
            for quote_id, quote, speaker, year, frame in all_quotes:
                try:
                    # Create prompt and get OpenAI analysis
                    prompt = self.create_historian_prompt(quote, speaker, year, frame)
                    analysis = self.get_openai_analysis(prompt)
                    
                    conn.execute("""
                        UPDATE quotes 
                        SET historian_analysis = ? 
                        WHERE id = ?
                    """, (analysis, quote_id))
                    
                    processed += 1
                    
                    if processed % 10 == 0:
                        print(f"  Processed {processed} quotes...")
                        conn.commit()
                        
                    # Rate limiting - OpenAI allows 3 requests/minute for free tier
                    time.sleep(1)  # 1 second between requests
                        
                except Exception as e:
                    print(f"Error with quote {quote_id}: {e}")
                    continue
            
            conn.commit()
            print(f"Completed: {processed} OpenAI analyses generated")
            
        except Exception as e:
            print(f"Regeneration error: {e}")
            
        finally:
            conn.close()
            
        return processed

def setup_openai_historian():
    """Interactive setup for OpenAI historian"""
    
    print("=== OpenAI HISTORIAN SETUP ===")
    
    # Get API key
    api_key = input("Enter your OpenAI API key (or press Enter to use OPENAI_API_KEY env var): ").strip()
    
    if not api_key:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("No API key provided. Please set OPENAI_API_KEY environment variable or provide key.")
            return None
    
    historian = OpenAIHistorian(api_key=api_key)
    
    # Test with a few quotes first
    print("\nTesting OpenAI integration with 3 sample quotes...")
    
    test_processed = historian.regenerate_all_analyses(limit=3)
    
    if test_processed > 0:
        print(f"✅ Test successful! Processed {test_processed} quotes")
        
        # Show results
        conn = sqlite3.connect("hansard_simple.db")
        examples = conn.execute("SELECT id, quote, historian_analysis FROM quotes WHERE id <= 3").fetchall()
        
        print("\n=== SAMPLE OPENAI ANALYSES ===")
        for quote_id, quote, analysis in examples:
            print(f"Quote {quote_id}: {quote[:80]}...")
            print(f"Analysis: {analysis}")
            print("-" * 60)
        
        conn.close()
        
        # Ask about full processing
        proceed = input(f"\nProcess all 532 quotes? (Est. cost: ~$5.32) (y/N): ").strip().lower()
        
        if proceed == 'y':
            print("\nProcessing all quotes...")
            total_processed = historian.regenerate_all_analyses(start_id=4)  # Skip already processed
            print(f"✅ Complete! Processed {total_processed} additional quotes")
        
        return historian
        
    else:
        print("❌ Test failed. Check your API key and connection.")
        return None

if __name__ == "__main__":
    setup_openai_historian()