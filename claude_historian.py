# claude_historian.py
# Claude AI-powered historian for superior historical analysis

import sqlite3
from anthropic import Anthropic
import time
from typing import Optional
import os

class ClaudeHistorian:
    """Claude AI-powered historian - optimized for historical analysis"""
    
    def __init__(self, db_path="database_updated.db", api_key=None):
        self.db_path = db_path
        
        # Set up Claude client
        if api_key:
            self.client = Anthropic(api_key=api_key)
        elif os.getenv('ANTHROPIC_API_KEY'):
            self.client = Anthropic()  # Uses ANTHROPIC_API_KEY env var
        else:
            print("Warning: No Claude API key provided. Set ANTHROPIC_API_KEY environment variable or pass api_key parameter.")
            self.client = None
        
        # Historical contexts optimized for Claude
        self.historical_contexts = {
            1900: "era of New Imperialism and growing concerns about mass immigration from Eastern Europe",
            1901: "early Edwardian period with post-Boer War economic anxieties and rising immigration tensions", 
            1902: "post-Boer War reconstruction period with imperial consolidation and domestic economic adjustment",
            1903: "height of Tariff Reform controversy under Joseph Chamberlain, dividing Conservative Party",
            1904: "pre-Aliens Act period of intensifying immigration discourse and East End social tensions",
            1905: "historic Aliens Act debates establishing Britain's first comprehensive immigration controls",
            1906: "Liberal landslide election victory launching major social reform agenda",
            1907: "economic recession with rising unemployment and growing labour movement strength",
            1908: "peak Liberal reform period with Old Age Pensions and social welfare expansion",
            1909: "People's Budget constitutional crisis challenging House of Lords authority",
            1910: "constitutional crisis resolution through two general elections and Parliament Act preparations",
            1911: "Great Labour Unrest with major strikes across transport, mining, and dock industries",
            1912: "continuing industrial militancy and suffrage campaign intensification",
            1913: "pre-war social tensions with Irish Home Rule crisis and labour disputes",
            1914: "outbreak of Great War transforming British politics and society",
            1915: "wartime economic mobilization with unprecedented state intervention in industry",
            1916: "total war economy with conscription, rationing, and industrial dilution of skilled labour",
            1917: "war's climax with Russian Revolution inspiring British labour militancy",
            1918: "armistice and demobilization planning amid fears of revolutionary upheaval",
            1919: "post-war reconstruction struggles with returning veterans and labour shortages",
            1920: "post-war boom and inflation with intense labour-capital conflicts",
            1921: "severe economic depression with mass unemployment and deflation",
            1922: "economic crisis deepening with political instability and Conservative return",
            1923: "failed Conservative attempt at protectionist revival under Stanley Baldwin",
            1924: "first Labour government under Ramsay MacDonald challenging establishment",
            1925: "return to Gold Standard and economic stabilization efforts",
            1926: "General Strike representing climax of industrial class conflict",
            1927: "post-General Strike settlement with Trade Union Act restrictions",
            1928: "economic recovery and industrial modernization with franchise extension to women",
            1929: "economic optimism before Wall Street Crash and global depression onset",
            1930: "Great Depression's arrival bringing mass unemployment and political upheaval"
        }

    def create_claude_prompt(self, quote: str, speaker: str, year: int, frame: str) -> str:
        """Create optimized prompt for Claude's historical analysis strengths"""
        
        historical_context = self.historical_contexts.get(year, f"complex political and economic conditions of {year}")
        
        # Claude works better with structured, detailed prompts
        prompt = f"""You are a distinguished historian specializing in British immigration and labour policy (1900-1930). Provide a sophisticated historical analysis of this parliamentary quote.

**QUOTE TO ANALYZE:**
"{quote}"

**CONTEXT:**
• Speaker: {speaker}
• Year: {year} 
• Historical Period: {historical_context}
• Debate Classification: {frame}

**ANALYSIS REQUEST:**
Write a concise but insightful historical analysis (2-3 sentences, max 200 words) that demonstrates:

1. **Specific Argument Identification**: What precise political or economic argument is being made?
2. **Historical Contextualization**: How does this reflect broader {year} political/social tensions?  
3. **Parliamentary Strategy**: What does this reveal about political tactics or coalition-building?
4. **Significance**: Why does this matter for understanding British immigration/labour policy development?

**ANALYTICAL FRAMEWORK:**
Consider these historical dimensions:
• Economic conditions and labour market pressures
• Political party positioning and electoral considerations  
• Social tensions around immigration and national identity
• Imperial context and international comparisons
• Class dynamics and trade union concerns

**STYLE REQUIREMENTS:**
• Academic precision with scholarly vocabulary
• Avoid presentist interpretations or modern terminology
• Connect to broader historical patterns and significance
• Be specific about causal relationships and implications

**AVOID:**
• Generic phrases like "discusses immigration policy"
• Mere description without analytical insight
• Anachronistic language or concepts
• Overly technical jargon without explanation

Provide nuanced historical interpretation that illuminates the political and social dynamics of the period."""

        return prompt

    def get_claude_analysis(self, prompt: str) -> str:
        """Get analysis from Claude API"""
        
        if not self.client:
            return self.generate_fallback_analysis(prompt)
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",  # Latest Claude model, excellent for analysis
                max_tokens=300,  # Enough for detailed analysis
                temperature=0.3,  # Lower temperature for more consistent analysis
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            analysis = response.content[0].text.strip()
            return analysis
            
        except Exception as e:
            print(f"Claude API error: {e}")
            # Fallback to enhanced rule-based analysis
            return self.generate_fallback_analysis(prompt)

    def generate_fallback_analysis(self, prompt: str) -> str:
        """Enhanced fallback analysis if API fails"""
        
        # Extract key info from prompt
        lines = prompt.split('\n')
        quote_line = next((line for line in lines if line.startswith('QUOTE:') or '"' in line), "")
        year_line = next((line for line in lines if line.startswith('• Year:')), "")
        
        if quote_line and year_line:
            quote = quote_line.replace('QUOTE TO ANALYZE:', '').replace('"', '').lower().strip()
            year = int(year_line.replace('• Year: ', '').strip())
            
            # Enhanced content-based analysis
            if 'beg to ask' in quote and 'secretary of state' in quote:
                if 'colonies' in quote:
                    return f"Parliamentary inquiry into colonial labour policies reflecting {year} concerns about imperial economic development and settler-indigenous labour competition."
                elif 'home department' in quote:
                    return f"Seeks government data on immigration enforcement, illustrating parliamentary oversight of administrative implementation during {year} policy development."
                else:
                    return f"Parliamentary question demanding ministerial accountability on immigration policy during {year} administrative challenges."
            
            elif 'aliens act' in quote and year == 1905:
                return "Addresses Britain's landmark 1905 Aliens Act, the nation's first comprehensive immigration legislation targeting Eastern European Jewish refugees."
            
            elif 'exclusion' in quote or 'expulsion' in quote:
                if year >= 1914 and year <= 1918:
                    return f"Wartime advocacy for restrictive enforcement reflecting {year} national security concerns and anti-alien sentiment."
                else:
                    return f"Supports immigration restriction reflecting {year} economic anxieties and rising nativist political pressure."
            
            elif 'east end' in quote or 'whitechapel' in quote:
                return f"References East London overcrowding and social tensions that galvanized middle-class support for immigration controls during {year} urban crisis."
            
            elif 'unemployment' in quote and ('alien' in quote or 'foreign' in quote):
                if year >= 1919:
                    return f"Links immigration to post-war unemployment crisis as demobilized veterans competed for scarce employment opportunities."
                else:
                    return f"Connects foreign labour to domestic joblessness during {year} economic uncertainty and labour market pressures."
            
            elif 'wage' in quote and ('competition' in quote or 'reduce' in quote):
                return f"Economic argument about immigrant wage competition reflecting {year} labour movement concerns and trade union political influence."
            
            else:
                # Context-specific fallbacks
                if year == 1905:
                    return "Contributes to historic 1905 Aliens Act parliamentary debates establishing Britain's first systematic immigration controls."
                elif year >= 1919 and year <= 1922:
                    return f"Reflects post-war reconstruction debates balancing economic recovery needs with veterans' employment concerns."
                elif year >= 1926 and year <= 1930:
                    return f"Part of later 1920s immigration discourse amid economic depression and rising unemployment pressures."
                else:
                    return f"Represents parliamentary engagement with immigration policy during {year} broader political and economic transformations."
        
        return "Parliamentary contribution to British immigration policy debates."

    def analyze_quote(self, quote_id: int) -> Optional[str]:
        """Generate Claude analysis for a specific quote"""
        
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
            
            # Create Claude-optimized prompt
            prompt = self.create_claude_prompt(quote, speaker, year, frame)
            
            # Get Claude analysis
            analysis = self.get_claude_analysis(prompt)
            
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
        """Regenerate all analyses using Claude API"""
        
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
            
            print(f"Generating Claude analyses for {len(all_quotes)} quotes...")
            print(f"Using Claude-3.5-Sonnet for superior historical analysis")
            print(f"Estimated cost: ${len(all_quotes) * 0.003:.2f} (much cheaper than OpenAI!)")
            
            for quote_id, quote, speaker, year, frame in all_quotes:
                try:
                    # Create prompt and get Claude analysis
                    prompt = self.create_claude_prompt(quote, speaker, year, frame)
                    analysis = self.get_claude_analysis(prompt)
                    
                    conn.execute("""
                        UPDATE quotes 
                        SET historian_analysis = ? 
                        WHERE id = ?
                    """, (analysis, quote_id))
                    
                    processed += 1
                    
                    if processed % 10 == 0:
                        print(f"  Processed {processed} quotes...")
                        conn.commit()
                        
                    # Rate limiting - Claude allows more requests than OpenAI
                    time.sleep(0.5)  # Faster than OpenAI
                        
                except Exception as e:
                    print(f"Error with quote {quote_id}: {e}")
                    continue
            
            conn.commit()
            print(f"Completed: {processed} Claude analyses generated")
            
        except Exception as e:
            print(f"Regeneration error: {e}")
            
        finally:
            conn.close()
            
        return processed

def test_claude_historian():
    """Test Claude historian with sample quotes"""
    
    print("=== TESTING CLAUDE HISTORIAN ===")
    print("This will test Claude's historical analysis capabilities")
    
    # This would need API key to actually call Claude
    historian = ClaudeHistorian()
    
    # Test prompt generation
    test_quote = "The right policy with regard to undesirable aliens is the policy of expulsion. We cannot blame the Australasians for the attitude they have adopted."
    test_prompt = historian.create_claude_prompt(test_quote, "Sir Kenelm Digby", 1905, "LABOUR_THREAT")
    
    print("Sample prompt being sent to Claude:")
    print(test_prompt[:500] + "...")
    
    return historian

if __name__ == "__main__":
    test_claude_historian()