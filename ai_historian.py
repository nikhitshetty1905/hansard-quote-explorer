# ai_historian.py
# AI Labour Historian Analysis System

import sqlite3
import re
from typing import Optional

class LabourHistorian:
    """World-class labour historian AI analyst"""
    
    def __init__(self, db_path="hansard_simple.db"):
        self.db_path = db_path
        
        # Historical context knowledge
        self.period_contexts = {
            (1900, 1905): "early Edwardian concerns about alien immigration",
            (1906, 1910): "Liberal government reforms and Aliens Act implementation", 
            (1911, 1914): "pre-war labour unrest and industrial strikes",
            (1915, 1918): "wartime labour shortages and essential workers",
            (1919, 1925): "post-war reconstruction and unemployment",
            (1926, 1930): "economic downturn and mass unemployment"
        }
        
        # Frame-specific analysis patterns
        self.frame_patterns = {
            'LABOUR_THREAT': [
                "Warns that {context} threatens British workers through {mechanism}",
                "Argues that foreign labour creates {effect} for domestic workers", 
                "Contends that {immigration_type} undermines {worker_category} employment"
            ],
            'LABOUR_NEED': [
                "Advocates for {immigration_type} to address {labour_shortage}",
                "Argues that foreign workers provide essential {skills/industry} during {context}",
                "Defends immigration as necessary for {economic_need}"
            ],
            'RACIALISED': [
                "Frames aliens as {character_flaw} threatening {national_values}",
                "Argues for exclusion based on {racial/character} grounds rather than economic",
                "Contends that {alien_type} are inherently {undesirable_trait}"
            ],
            'MIXED': [
                "Acknowledges {benefit} while warning of {threat} from foreign labour",
                "Balances {positive_aspect} against {negative_consequence} of immigration"
            ],
            'OTHER': [
                "Discusses {topic} in relation to {context}",
                "Addresses {issue} within {framework}"
            ]
        }

    def get_historical_context(self, year: int) -> str:
        """Get historical context for a specific year"""
        for (start, end), context in self.period_contexts.items():
            if start <= year <= end:
                return context
        return f"{year}s political climate"

    def extract_key_elements(self, quote: str, frame: str) -> dict:
        """Extract key argumentative elements from quote"""
        
        # Immigration-related terms
        immigration_terms = re.findall(
            r'\b(aliens?|immigrants?|foreigners?|foreign\s+workers?|alien\s+immigration)\b', 
            quote, re.IGNORECASE
        )
        
        # Labour-related terms  
        labour_terms = re.findall(
            r'\b(labou?r|workers?|employment|unemployment|wages?|competition|unskilled\s+labou?r|dock\s+workers?)\b',
            quote, re.IGNORECASE
        )
        
        # Economic indicators
        economic_terms = re.findall(
            r'\b(depression?|prosperity|shortage|surplus|competition|wages?|employment)\b',
            quote, re.IGNORECASE
        )
        
        # Extract main verb/action
        action_verbs = re.findall(
            r'\b(argues?|contends?|warns?|advocates?|defends?|opposes?|supports?|threatens?|benefits?)\b',
            quote, re.IGNORECASE
        )
        
        return {
            'immigration_terms': immigration_terms[:2],  # Top 2
            'labour_terms': labour_terms[:2],
            'economic_terms': economic_terms[:2], 
            'action_verbs': action_verbs[:1],
            'quote_length': len(quote.split())
        }

    def generate_analysis(self, quote: str, speaker: str, year: int, frame: str) -> str:
        """Generate expert labour historian analysis"""
        
        context = self.get_historical_context(year)
        elements = self.extract_key_elements(quote, frame)
        
        # Core argument extraction
        if 'competition' in quote.lower() and any('alien' in term.lower() for term in elements['immigration_terms']):
            argument_type = "wage competition"
        elif 'shortage' in quote.lower() or 'need' in quote.lower():
            argument_type = "labour shortage"
        elif 'undesirable' in quote.lower() or 'character' in quote.lower():
            argument_type = "character exclusion"
        elif 'unemployment' in quote.lower():
            argument_type = "unemployment causation"
        else:
            argument_type = "labour market regulation"
        
        # Generate frame-specific analysis
        if frame == 'LABOUR_THREAT':
            if 'dock' in quote.lower() or 'unskilled' in quote.lower():
                worker_type = "unskilled workers"
            elif 'trade' in quote.lower():
                worker_type = "skilled tradesmen"
            else:
                worker_type = "British workers"
                
            analysis = f"Argues that foreign immigration threatens {worker_type} through wage competition during {context}"
            
        elif frame == 'LABOUR_NEED':
            if 'skill' in quote.lower() or 'trade' in quote.lower():
                analysis = f"Advocates for skilled foreign workers to fill labour shortages despite {context}"
            else:
                analysis = f"Defends immigration as economically necessary during {context}"
                
        elif frame == 'RACIALISED':
            if 'pauper' in quote.lower():
                analysis = f"Frames aliens as economic burdens threatening national resources during {context}"
            elif 'criminal' in quote.lower():
                analysis = f"Argues for exclusion based on alleged criminal character rather than economic grounds"
            else:
                analysis = f"Contends that aliens are inherently undesirable threats to British national character"
                
        elif frame == 'MIXED':
            analysis = f"Acknowledges economic benefits while warning of social threats from immigration during {context}"
            
        else:  # OTHER
            if argument_type == "unemployment causation":
                analysis = f"Links alien immigration to unemployment patterns during {context}"
            else:
                analysis = f"Addresses immigration policy within broader labour market concerns of {context}"
        
        # Add speaker credibility if notable
        if 'secretary' in speaker.lower() or 'minister' in speaker.lower():
            analysis = analysis.replace("Argues", "Officially argues")
        elif 'sir' in speaker.lower():
            analysis = analysis.replace("Argues", "Authoritatively argues")
            
        return analysis

    def analyze_quote(self, quote_id: int) -> Optional[str]:
        """Analyze a specific quote by ID"""
        
        conn = sqlite3.connect(self.db_path)
        
        try:
            cursor = conn.execute("""
                SELECT quote, speaker, year, frame, historian_analysis 
                FROM quotes 
                WHERE id = ?
            """, (quote_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
                
            quote, speaker, year, frame, existing_analysis = row
            
            # Return existing analysis if available
            if existing_analysis:
                return existing_analysis
            
            # Generate new analysis
            analysis = self.generate_analysis(quote, speaker, year, frame)
            
            # Cache in database
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

    def bulk_analyze(self, limit: int = None) -> int:
        """Analyze all quotes without existing analysis"""
        
        conn = sqlite3.connect(self.db_path)
        processed = 0
        
        try:
            # Get quotes needing analysis
            query = """
                SELECT id, quote, speaker, year, frame 
                FROM quotes 
                WHERE historian_analysis IS NULL 
                ORDER BY year, id
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor = conn.execute(query)
            quotes_to_analyze = cursor.fetchall()
            
            print(f"Analyzing {len(quotes_to_analyze)} quotes...")
            
            for quote_id, quote, speaker, year, frame in quotes_to_analyze:
                try:
                    analysis = self.generate_analysis(quote, speaker, year, frame)
                    
                    conn.execute("""
                        UPDATE quotes 
                        SET historian_analysis = ? 
                        WHERE id = ?
                    """, (analysis, quote_id))
                    
                    processed += 1
                    
                    if processed % 10 == 0:
                        print(f"  Processed {processed} quotes...")
                        conn.commit()
                        
                except Exception as e:
                    print(f"Error with quote {quote_id}: {e}")
                    continue
            
            conn.commit()
            print(f"Completed: {processed} analyses generated")
            
        except Exception as e:
            print(f"Bulk analysis error: {e}")
            
        finally:
            conn.close()
            
        return processed

def test_historian():
    """Test the historian on a few sample quotes"""
    
    historian = LabourHistorian()
    
    # Test with first few quotes
    conn = sqlite3.connect("hansard_simple.db")
    cursor = conn.execute("""
        SELECT id, quote, speaker, year, frame 
        FROM quotes 
        LIMIT 3
    """)
    
    print("=== TESTING LABOUR HISTORIAN ===\n")
    
    for quote_id, quote, speaker, year, frame in cursor.fetchall():
        print(f"Quote {quote_id} ({speaker}, {year}, {frame}):")
        print(f"Original: {quote[:100]}...")
        
        analysis = historian.analyze_quote(quote_id)
        print(f"Analysis: {analysis}")
        print("-" * 60)
    
    conn.close()

if __name__ == "__main__":
    test_historian()