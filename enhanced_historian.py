# enhanced_historian.py
# Evidence-based Labour Historian Analysis (No Hallucination)

import sqlite3
import re
from typing import Optional, Dict, List
from enhanced_speaker_parser import EnhancedSpeakerParser

class EvidenceBasedHistorian:
    """Academic-grade labour historian - evidence-based analysis only"""
    
    def __init__(self, db_path="hansard_simple.db"):
        self.db_path = db_path
        
        # Conservative historical contexts (well-established facts only)
        self.year_contexts = {
            1900: "turn-of-century industrial expansion",
            1901: "early Edwardian economic concerns", 
            1902: "post-Boer War economic adjustment",
            1903: "Tariff Reform debates",
            1904: "growing immigration discourse",
            1905: "Aliens Act parliamentary debates",
            1906: "Liberal electoral victory and reform agenda",
            1907: "economic downturn and labour tensions",
            1908: "continuing Liberal reforms",
            1909: "constitutional crisis period",
            1910: "constitutional crisis resolution",
            1911: "major industrial strike wave",
            1912: "continuing labour unrest",
            1913: "pre-war economic tensions",
            1914: "outbreak of European war",
            1915: "wartime economic mobilization",
            1916: "wartime labour shortages",
            1917: "wartime production demands",
            1918: "war's end and demobilization planning",
            1919: "post-war reconstruction debates",
            1920: "economic reconversion challenges"
        }

    def extract_textual_evidence(self, quote: str) -> Dict[str, List[str]]:
        """Extract only what's explicitly stated in the quote"""
        
        evidence = {
            'worker_types': [],
            'immigrant_terms': [],
            'economic_concepts': [],
            'geographic_references': [],
            'policy_mechanisms': [],
            'causal_claims': [],
            'economic_effects': []
        }
        
        quote_lower = quote.lower()
        
        # Worker types (only if explicitly mentioned)
        worker_patterns = [
            r'\b(unskilled\s+(?:labour|labor|workers?))\b',
            r'\b(skilled\s+(?:labour|labor|workers?))\b', 
            r'\b(dock\s+workers?)\b',
            r'\b(casual\s+(?:labour|labor))\b',
            r'\b(trade\s+union\s+members?)\b',
            r'\b(british\s+(?:labour|workers?))\b',
            r'\b(factory\s+workers?)\b',
            r'\b(industrial\s+workers?)\b'
        ]
        
        for pattern in worker_patterns:
            matches = re.findall(pattern, quote_lower)
            evidence['worker_types'].extend([m if isinstance(m, str) else m[0] for m in matches])
        
        # Immigration terms (only what's stated)
        immigrant_patterns = [
            r'\b(aliens?)\b',
            r'\b(immigrants?)\b', 
            r'\b(foreigners?)\b',
            r'\b(foreign\s+(?:labour|workers?))\b',
            r'\b(alien\s+immigration)\b'
        ]
        
        for pattern in immigrant_patterns:
            matches = re.findall(pattern, quote_lower)
            evidence['immigrant_terms'].extend(matches)
        
        # Economic concepts (explicit mentions only)
        economic_patterns = [
            r'\b(wages?)\b',
            r'\b(unemployment)\b',
            r'\b(competition)\b',
            r'\b(employment)\b',
            r'\b(labour\s+market)\b',
            r'\b(trade)\b',
            r'\b(industry)\b',
            r'\b(economic)\b'
        ]
        
        for pattern in economic_patterns:
            matches = re.findall(pattern, quote_lower)
            evidence['economic_concepts'].extend(matches)
        
        # Geographic references (only if mentioned)
        geo_patterns = [
            r'\b(east\s+end)\b',
            r'\b(london)\b',
            r'\b(england)\b',
            r'\b(britain)\b',
            r'\b(country)\b'
        ]
        
        for pattern in geo_patterns:
            matches = re.findall(pattern, quote_lower)
            evidence['geographic_references'].extend(matches)
        
        # Policy mechanisms (actual terms used)
        policy_patterns = [
            r'\b(exclusion?)\b',
            r'\b(restrict(?:ion|ed)?)\b',
            r'\b(admission)\b',
            r'\b(control)\b',
            r'\b(regulation?)\b',
            r'\b(bill)\b',
            r'\b(act)\b'
        ]
        
        for pattern in policy_patterns:
            matches = re.findall(pattern, quote_lower)
            evidence['policy_mechanisms'].extend(matches)
        
        # Causal language (how arguments are structured)
        causal_patterns = [
            r'\b(causes?)\b',
            r'\b(leads?\s+to)\b',
            r'\b(results?\s+in)\b',
            r'\b(produces?)\b',
            r'\b(creates?)\b',
            r'\b(threatens?)\b',
            r'\b(benefits?)\b'
        ]
        
        for pattern in causal_patterns:
            matches = re.findall(pattern, quote_lower)
            evidence['causal_claims'].extend(matches)
        
        # Economic effects (what outcomes are claimed)
        effect_patterns = [
            r'\b(mischief)\b',
            r'\b(suffering?)\b',
            r'\b(benefit)\b',
            r'\b(advantage)\b',
            r'\b(harm)\b',
            r'\b(damage)\b',
            r'\b(improvement)\b'
        ]
        
        for pattern in effect_patterns:
            matches = re.findall(pattern, quote_lower)
            evidence['economic_effects'].extend(matches)
        
        # Remove duplicates and empty values
        for key in evidence:
            evidence[key] = list(set([item for item in evidence[key] if item]))
        
        return evidence

    def analyze_argument_structure(self, quote: str) -> Dict[str, str]:
        """Analyze the actual argumentative moves made"""
        
        structure = {
            'stance': 'neutral',
            'argument_type': 'descriptive',
            'evidence_type': 'none',
            'target': 'general'
        }
        
        quote_lower = quote.lower()
        
        # Determine stance based on language used
        if any(word in quote_lower for word in ['threaten', 'danger', 'mischief', 'suffer', 'harm', 'against']):
            structure['stance'] = 'critical'
        elif any(word in quote_lower for word in ['benefit', 'advantage', 'welcome', 'necessary', 'support']):
            structure['stance'] = 'supportive'
        elif any(word in quote_lower for word in ['however', 'but', 'although', 'while']):
            structure['stance'] = 'balanced'
        
        # Argument type
        if any(phrase in quote_lower for phrase in ['we know that', 'statistics', 'evidence', 'fact']):
            structure['argument_type'] = 'empirical'
        elif any(phrase in quote_lower for phrase in ['ought', 'should', 'must', 'policy']):
            structure['argument_type'] = 'normative'
        elif any(phrase in quote_lower for phrase in ['if', 'would', 'could', 'might']):
            structure['argument_type'] = 'hypothetical'
        
        # Evidence type
        if 'gazette' in quote_lower or 'board of trade' in quote_lower or '%' in quote:
            structure['evidence_type'] = 'official_statistics'
        elif any(word in quote_lower for word in ['example', 'instance', 'case']):
            structure['evidence_type'] = 'examples'
        elif any(word in quote_lower for word in ['principle', 'general', 'always']):
            structure['evidence_type'] = 'principles'
        
        # Target of argument
        if 'unskilled' in quote_lower:
            structure['target'] = 'unskilled_workers'
        elif 'skilled' in quote_lower or 'trade' in quote_lower:
            structure['target'] = 'skilled_workers'
        elif 'country' in quote_lower or 'nation' in quote_lower:
            structure['target'] = 'national_interest'
        
        return structure

    def generate_evidence_based_analysis(self, quote: str, speaker: str, year: int, frame: str) -> str:
        """Generate analysis based strictly on textual evidence"""
        
        evidence = self.extract_textual_evidence(quote)
        structure = self.analyze_argument_structure(quote)
        context = self.year_contexts.get(year, f"{year} political context")
        
        # Analyze the specific argument being made
        quote_lower = quote.lower()
        
        # More sophisticated argument detection
        if 'competition' in quote_lower and evidence['worker_types'] and evidence['immigrant_terms']:
            worker_type = evidence['worker_types'][0]
            immigrant_term = evidence['immigrant_terms'][0]
            if 'wages' in evidence['economic_concepts']:
                return f"Warns that {immigrant_term} create wage competition for {worker_type} during {context}"
            else:
                return f"Argues that {immigrant_term} compete with {worker_type} during {context}"
        
        elif 'unemployment' in quote_lower:
            if evidence['immigrant_terms']:
                immigrant_term = evidence['immigrant_terms'][0]
                return f"Links {immigrant_term} to unemployment concerns during {context}"
            else:
                return f"Addresses unemployment issues in the context of {context}"
        
        elif 'exclusion' in quote_lower or 'exclude' in quote_lower:
            if evidence['immigrant_terms']:
                immigrant_term = evidence['immigrant_terms'][0]
                return f"Advocates for excluding {immigrant_term} during {context}"
            else:
                return f"Supports exclusionary immigration policy during {context}"
        
        elif 'benefit' in quote_lower or 'advantage' in quote_lower:
            if evidence['immigrant_terms']:
                immigrant_term = evidence['immigrant_terms'][0] 
                return f"Defends economic benefits of {immigrant_term} during {context}"
            else:
                return f"Argues for immigration benefits during {context}"
        
        elif 'skill' in quote_lower and evidence['immigrant_terms']:
            immigrant_term = evidence['immigrant_terms'][0]
            return f"Discusses skilled {immigrant_term} in the context of {context}"
        
        elif 'mischief' in quote_lower or 'harm' in quote_lower:
            if evidence['immigrant_terms'] and evidence['worker_types']:
                immigrant_term = evidence['immigrant_terms'][0]
                worker_type = evidence['worker_types'][0]
                return f"Warns of harm to {worker_type} from {immigrant_term} during {context}"
            elif evidence['immigrant_terms']:
                immigrant_term = evidence['immigrant_terms'][0]
                return f"Warns of economic harm from {immigrant_term} during {context}"
        
        elif 'trade' in evidence['economic_concepts'] and evidence['immigrant_terms']:
            immigrant_term = evidence['immigrant_terms'][0]
            return f"Examines trade implications of {immigrant_term} during {context}"
        
        elif evidence['policy_mechanisms'] and 'bill' in evidence['policy_mechanisms']:
            return f"Addresses immigration legislation during {context}"
        
        elif evidence['immigrant_terms'] and evidence['economic_concepts']:
            immigrant_term = evidence['immigrant_terms'][0]
            econ_concept = evidence['economic_concepts'][0]
            return f"Connects {immigrant_term} to {econ_concept} concerns during {context}"
        
        # Frame-based fallback with context
        elif frame == 'LABOUR_THREAT':
            return f"Expresses concerns about labour market threats during {context}"
        elif frame == 'LABOUR_NEED':
            return f"Argues for labour market needs during {context}"
        elif frame == 'RACIALISED':
            return f"Frames immigration in terms of national character during {context}"
        elif frame == 'MIXED':
            return f"Presents balanced view of immigration during {context}"
        else:
            return f"Discusses immigration policy during {context}"

    def analyze_quote(self, quote_id: int) -> Optional[str]:
        """Analyze a specific quote with evidence-based approach"""
        
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
            
            # Generate evidence-based analysis
            analysis = self.generate_evidence_based_analysis(quote, speaker, year, frame)
            
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

    def regenerate_all_analyses(self) -> int:
        """Regenerate all analyses with improved evidence-based approach"""
        
        conn = sqlite3.connect(self.db_path)
        processed = 0
        
        try:
            # Get all quotes
            cursor = conn.execute("""
                SELECT id, quote, speaker, year, frame 
                FROM quotes 
                ORDER BY year, id
            """)
            
            all_quotes = cursor.fetchall()
            print(f"Regenerating analyses for {len(all_quotes)} quotes...")
            
            for quote_id, quote, speaker, year, frame in all_quotes:
                try:
                    analysis = self.generate_evidence_based_analysis(quote, speaker, year, frame)
                    
                    conn.execute("""
                        UPDATE quotes 
                        SET historian_analysis = ? 
                        WHERE id = ?
                    """, (analysis, quote_id))
                    
                    processed += 1
                    
                    if processed % 20 == 0:
                        print(f"  Processed {processed} quotes...")
                        conn.commit()
                        
                except Exception as e:
                    print(f"Error with quote {quote_id}: {e}")
                    continue
            
            conn.commit()
            print(f"Completed: {processed} analyses regenerated")
            
        except Exception as e:
            print(f"Regeneration error: {e}")
            
        finally:
            conn.close()
            
        return processed

def test_enhanced_historian():
    """Test the enhanced evidence-based historian"""
    
    historian = EvidenceBasedHistorian()
    
    # Test with first few quotes
    conn = sqlite3.connect("hansard_simple.db")
    cursor = conn.execute("""
        SELECT id, quote, speaker, year, frame 
        FROM quotes 
        LIMIT 5
    """)
    
    print("=== TESTING ENHANCED EVIDENCE-BASED HISTORIAN ===\n")
    
    for quote_id, quote, speaker, year, frame in cursor.fetchall():
        print(f"Quote {quote_id} ({speaker}, {year}, {frame}):")
        print(f"Text: {quote[:150]}...")
        
        # Show evidence extraction
        evidence = historian.extract_textual_evidence(quote)
        print(f"Evidence: {evidence}")
        
        # Show new analysis
        analysis = historian.generate_evidence_based_analysis(quote, speaker, year, frame)
        print(f"Analysis: {analysis}")
        print("-" * 80)
    
    conn.close()

if __name__ == "__main__":
    test_enhanced_historian()