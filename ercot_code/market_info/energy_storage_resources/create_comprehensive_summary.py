#!/usr/bin/env python3
"""
ERCOT ESR/BESS Comprehensive Analysis and Summary Generator
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict

class ERCOTComprehensiveSummary:
    def __init__(self, analysis_file: str):
        with open(analysis_file, 'r') as f:
            self.analysis_data = json.load(f)
        
        self.summary = {
            'executive_summary': {},
            'ktc_summaries': {},
            'implementation_timeline': {},
            'technical_requirements': {},
            'business_implications': {},
            'system_impacts': {}
        }
    
    def extract_numeric_values(self, text: str) -> List[str]:
        """Extract numeric values with units (MW, kW, %, etc.)"""
        patterns = [
            r'\b\d+(?:\.\d+)?\s*(?:MW|kW|kVA|%|Hz|V|A|seconds?|minutes?|hours?)\b',
            r'\b\d+(?:\.\d+)?\s*(?:percent|percentage)\b',
            r'\$\d+(?:,\d{3})*(?:\.\d{2})?',
        ]
        
        values = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            values.extend(matches)
        
        return list(set(values))  # Remove duplicates
    
    def extract_dates_and_timelines(self, text: str) -> List[str]:
        """Extract dates and timeline information"""
        patterns = [
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
            r'\b\d{4}-\d{2}-\d{2}\b',
            r'(?i)\b(?:effective|implementation|deadline|by)\s+[^.]{1,50}(?:date|time|period)\b',
            r'(?i)\bwithin\s+\d+\s+(?:days?|months?|years?)\b'
        ]
        
        dates = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        
        return dates
    
    def extract_key_concepts(self, text: str) -> Dict[str, List[str]]:
        """Extract key concepts by category"""
        concepts = {
            'registration': [],
            'performance_metrics': [],
            'technical_specs': [],
            'market_participation': [],
            'settlement': [],
            'testing': [],
            'compliance': []
        }
        
        concept_patterns = {
            'registration': [r'(?i)\b(?:registration|register|QSE|qualified|application)\b'],
            'performance_metrics': [r'(?i)\b(?:ESREDP|GREDP|performance|scoring|threshold)\b'],
            'technical_specs': [r'(?i)\b(?:ramp\s+rate|SOC|state\s+of\s+charge|telemetry|SCADA)\b'],
            'market_participation': [r'(?i)\b(?:ORDC|PRC|reserves?|dispatch|pricing|offer|bid)\b'],
            'settlement': [r'(?i)\b(?:settlement|billing|payment|charge|invoice)\b'],
            'testing': [r'(?i)\b(?:test|validation|verification|commissioning)\b'],
            'compliance': [r'(?i)\b(?:compliance|requirement|shall|must|mandatory)\b']
        }
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) < 15:  # Skip very short lines
                continue
                
            for category, patterns in concept_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, line):
                        concepts[category].append(line)
                        break  # Only add to first matching category
        
        return concepts
    
    def analyze_ktc(self, ktc_number: str, ktc_data: Dict) -> Dict:
        """Analyze a specific KTC in detail"""
        analysis = ktc_data['analysis']
        
        # Combine all text from documents
        all_text = ""
        document_summaries = {}
        
        for doc_name, doc_data in analysis['documents'].items():
            all_text += doc_data['text'] + "\n"
            
            # Analyze individual document
            doc_summary = {
                'filename': doc_name,
                'type': 'TAC_Approved' if 'TAC_Approved' in doc_name else 
                       'Consensus' if 'Consensus' in doc_name else 'Proposal',
                'key_info': doc_data['key_info'],
                'numeric_values': self.extract_numeric_values(doc_data['text']),
                'dates': self.extract_dates_and_timelines(doc_data['text']),
                'concepts': self.extract_key_concepts(doc_data['text'])
            }
            document_summaries[doc_name] = doc_summary
        
        # Overall KTC analysis
        ktc_summary = {
            'ktc_number': ktc_number,
            'description': ktc_data['description'],
            'document_count': len(analysis['documents']),
            'documents': document_summaries,
            'combined_analysis': {
                'all_numeric_values': self.extract_numeric_values(all_text),
                'all_dates': self.extract_dates_and_timelines(all_text),
                'combined_concepts': self.extract_key_concepts(all_text)
            },
            'status': self.determine_implementation_status(all_text),
            'key_requirements': self.extract_requirements(all_text),
            'technical_parameters': self.extract_technical_parameters(all_text)
        }
        
        return ktc_summary
    
    def determine_implementation_status(self, text: str) -> str:
        """Determine the implementation status of a KTC"""
        if re.search(r'(?i)TAC\s+approved', text):
            return 'TAC_APPROVED'
        elif re.search(r'(?i)consensus', text):
            return 'CONSENSUS'
        elif re.search(r'(?i)discussion', text):
            return 'IN_DISCUSSION'
        else:
            return 'PROPOSAL'
    
    def extract_requirements(self, text: str) -> List[str]:
        """Extract key requirements from text"""
        requirements = []
        
        # Look for sentences with requirement keywords
        requirement_patterns = [
            r'(?i)[^.]*(?:shall|must|required|mandatory)[^.]*\.',
            r'(?i)[^.]*ESR[^.]*(?:requirement|standard|specification)[^.]*\.',
            r'(?i)[^.]*(?:compliance|conform)[^.]*\.'
        ]
        
        for pattern in requirement_patterns:
            matches = re.findall(pattern, text)
            requirements.extend([match.strip() for match in matches if len(match.strip()) > 20])
        
        return list(set(requirements))[:10]  # Limit to top 10 unique requirements
    
    def extract_technical_parameters(self, text: str) -> Dict[str, List[str]]:
        """Extract technical parameters by category"""
        params = {
            'power_ratings': [],
            'performance_thresholds': [],
            'timing_requirements': [],
            'frequency_response': [],
            'state_of_charge': []
        }
        
        # Power ratings
        power_matches = re.findall(r'\b\d+(?:\.\d+)?\s*(?:MW|kW|kVA)\b', text, re.IGNORECASE)
        params['power_ratings'] = list(set(power_matches))
        
        # Performance thresholds
        threshold_matches = re.findall(r'\b\d+(?:\.\d+)?\s*%\b', text)
        params['performance_thresholds'] = list(set(threshold_matches))
        
        # Timing requirements
        timing_matches = re.findall(r'\b\d+(?:\.\d+)?\s*(?:seconds?|minutes?|hours?)\b', text, re.IGNORECASE)
        params['timing_requirements'] = list(set(timing_matches))
        
        # SOC related
        soc_matches = re.findall(r'(?i)[^.]*(?:SOC|state\s+of\s+charge)[^.]*\.', text)
        params['state_of_charge'] = [match.strip() for match in soc_matches if len(match.strip()) > 10][:5]
        
        return params
    
    def generate_executive_summary(self) -> Dict:
        """Generate executive summary of all KTCs"""
        total_docs = 0
        approved_ktcs = 0
        consensus_ktcs = 0
        
        key_topics = {
            'registration': [],
            'market_participation': [],
            'technical_requirements': [],
            'hybrid_resources': [],
            'performance_management': []
        }
        
        for ktc_number, ktc_data in self.analysis_data.items():
            if ktc_number.startswith('KTC'):
                total_docs += len(ktc_data['analysis']['documents'])
                
                # Count status
                all_text = ""
                for doc_data in ktc_data['analysis']['documents'].values():
                    all_text += doc_data['text'] + "\n"
                
                status = self.determine_implementation_status(all_text)
                if status == 'TAC_APPROVED':
                    approved_ktcs += 1
                elif status == 'CONSENSUS':
                    consensus_ktcs += 1
                
                # Categorize KTCs
                desc = ktc_data['description'].lower()
                if 'registration' in desc:
                    key_topics['registration'].append(ktc_number)
                elif any(word in desc for word in ['reserve', 'ordc', 'prc', 'pricing', 'dispatch']):
                    key_topics['market_participation'].append(ktc_number)
                elif any(word in desc for word in ['technical', 'interconnection', 'soc', 'wsL']):
                    key_topics['technical_requirements'].append(ktc_number)
                elif any(word in desc for word in ['hybrid', 'dc-coupled', 'ac-connected']):
                    key_topics['hybrid_resources'].append(ktc_number)
                elif any(word in desc for word in ['performance', 'esredp', 'bpd', 'proxy']):
                    key_topics['performance_management'].append(ktc_number)
        
        return {
            'total_ktcs_analyzed': len([k for k in self.analysis_data.keys() if k.startswith('KTC')]),
            'total_documents_processed': total_docs,
            'approved_ktcs': approved_ktcs,
            'consensus_ktcs': consensus_ktcs,
            'key_topic_categories': key_topics,
            'analysis_date': '2023-08-23',
            'scope': 'ERCOT Battery Energy Storage Task Force (BESTF) Key Topic Concepts (KTC) 1-15'
        }
    
    def generate_comprehensive_summary(self) -> Dict:
        """Generate the complete comprehensive summary"""
        
        # Executive Summary
        self.summary['executive_summary'] = self.generate_executive_summary()
        
        # Analyze each KTC
        for ktc_number, ktc_data in self.analysis_data.items():
            if ktc_number.startswith('KTC'):
                self.summary['ktc_summaries'][ktc_number] = self.analyze_ktc(ktc_number, ktc_data)
        
        # Generate timeline
        self.generate_implementation_timeline()
        
        # Generate technical requirements summary
        self.generate_technical_requirements_summary()
        
        # Generate business implications
        self.generate_business_implications()
        
        return self.summary
    
    def generate_implementation_timeline(self):
        """Generate implementation timeline from all KTCs"""
        timeline_events = []
        
        for ktc_number, ktc_summary in self.summary['ktc_summaries'].items():
            for doc_name, doc_data in ktc_summary['documents'].items():
                for date in doc_data['dates']:
                    timeline_events.append({
                        'date': date,
                        'ktc': ktc_number,
                        'document': doc_name,
                        'type': doc_data['type']
                    })
        
        self.summary['implementation_timeline'] = sorted(timeline_events, 
                                                        key=lambda x: x['date'] if isinstance(x['date'], str) else str(x['date']))
    
    def generate_technical_requirements_summary(self):
        """Summarize technical requirements across all KTCs"""
        tech_summary = {
            'power_requirements': set(),
            'performance_thresholds': set(),
            'timing_requirements': set(),
            'communication_requirements': [],
            'testing_requirements': []
        }
        
        for ktc_summary in self.summary['ktc_summaries'].values():
            params = ktc_summary['technical_parameters']
            tech_summary['power_requirements'].update(params['power_ratings'])
            tech_summary['performance_thresholds'].update(params['performance_thresholds'])
            tech_summary['timing_requirements'].update(params['timing_requirements'])
        
        # Convert sets to lists for JSON serialization
        tech_summary['power_requirements'] = list(tech_summary['power_requirements'])
        tech_summary['performance_thresholds'] = list(tech_summary['performance_thresholds'])
        tech_summary['timing_requirements'] = list(tech_summary['timing_requirements'])
        
        self.summary['technical_requirements'] = tech_summary
    
    def generate_business_implications(self):
        """Generate business and operational implications"""
        implications = {
            'for_developers': [],
            'for_operators': [],
            'for_financiers': [],
            'for_ems_implementers': []
        }
        
        # Extract implications based on KTC content
        key_ktcs = {
            'KTC1': 'Registration processes and timelines critical for project development',
            'KTC2': 'Reserve market participation provides additional revenue opportunities',
            'KTC5': 'Performance monitoring requires sophisticated control systems',
            'KTC6': 'SOC management is crucial for optimal market participation',
            'KTC11': 'DC-coupled hybrid resources offer operational flexibility',
            'KTC12': 'AC-connected resources have different interconnection requirements'
        }
        
        for ktc, implication in key_ktcs.items():
            if ktc in self.summary['ktc_summaries']:
                status = self.summary['ktc_summaries'][ktc]['status']
                implications['for_developers'].append(f"{ktc}: {implication} (Status: {status})")
        
        self.summary['business_implications'] = implications

def main():
    analysis_file = "/pool/ssd8tb/data/iso/ERCOT/market_info/energy_storage_resources/ercot_esr_analysis.json"
    
    # Generate comprehensive summary
    summary_generator = ERCOTComprehensiveSummary(analysis_file)
    comprehensive_summary = summary_generator.generate_comprehensive_summary()
    
    # Save comprehensive summary
    output_file = "/pool/ssd8tb/data/iso/ERCOT/market_info/energy_storage_resources/ercot_esr_comprehensive_summary.json"
    with open(output_file, 'w') as f:
        json.dump(comprehensive_summary, f, indent=2, default=str)
    
    print("="*80)
    print("ERCOT ESR/BESS COMPREHENSIVE ANALYSIS SUMMARY")
    print("="*80)
    
    # Print Executive Summary
    exec_summary = comprehensive_summary['executive_summary']
    print(f"\nEXECUTIVE SUMMARY:")
    print(f"- Total KTCs Analyzed: {exec_summary['total_ktcs_analyzed']}")
    print(f"- Total Documents Processed: {exec_summary['total_documents_processed']}")
    print(f"- TAC Approved KTCs: {exec_summary['approved_ktcs']}")
    print(f"- Consensus KTCs: {exec_summary['consensus_ktcs']}")
    
    print(f"\nKEY TOPIC CATEGORIES:")
    for category, ktcs in exec_summary['key_topic_categories'].items():
        if ktcs:
            print(f"- {category.title().replace('_', ' ')}: {', '.join(ktcs)}")
    
    # Print KTC Summaries
    print(f"\n" + "="*80)
    print("DETAILED KTC ANALYSIS")
    print("="*80)
    
    for ktc_number, ktc_summary in comprehensive_summary['ktc_summaries'].items():
        print(f"\n{ktc_number}: {ktc_summary['description']}")
        print(f"Status: {ktc_summary['status']}")
        print(f"Documents: {ktc_summary['document_count']}")
        
        if ktc_summary['technical_parameters']['power_ratings']:
            print(f"Power Ratings Found: {', '.join(ktc_summary['technical_parameters']['power_ratings'][:5])}")
        
        if ktc_summary['technical_parameters']['performance_thresholds']:
            print(f"Performance Thresholds: {', '.join(ktc_summary['technical_parameters']['performance_thresholds'][:3])}")
        
        if ktc_summary['key_requirements']:
            print(f"Key Requirements: {len(ktc_summary['key_requirements'])} found")
    
    # Print Technical Requirements Summary
    print(f"\n" + "="*80)
    print("TECHNICAL REQUIREMENTS SUMMARY")
    print("="*80)
    
    tech_reqs = comprehensive_summary['technical_requirements']
    if tech_reqs['power_requirements']:
        print(f"Power Requirements: {', '.join(tech_reqs['power_requirements'][:10])}")
    if tech_reqs['performance_thresholds']:
        print(f"Performance Thresholds: {', '.join(tech_reqs['performance_thresholds'][:10])}")
    if tech_reqs['timing_requirements']:
        print(f"Timing Requirements: {', '.join(tech_reqs['timing_requirements'][:10])}")
    
    print(f"\nComprehensive summary saved to: {output_file}")
    return comprehensive_summary

if __name__ == "__main__":
    main()