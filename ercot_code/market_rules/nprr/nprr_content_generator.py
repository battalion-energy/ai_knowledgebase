#!/usr/bin/env python3
"""
NPRR Content Generator and Article Ideas
Generates various content types and article ideas from ERCOT NPRRs
"""

import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import pandas as pd

class NPRRContentGenerator:
    def __init__(self, analysis_dir: str = "nprr_analysis"):
        self.analysis_dir = Path(analysis_dir)
        self.analysis_dir.mkdir(exist_ok=True)
        
    def generate_article_ideas(self) -> List[Dict]:
        """Generate comprehensive article ideas for NPRR content"""
        
        article_ideas = [
            {
                "title": "Weekly NPRR Impact Dashboard",
                "description": "Interactive dashboard showing technology impact scores across all recent NPRRs",
                "format": "Interactive Web Dashboard",
                "audience": "Energy professionals, traders, developers",
                "key_features": [
                    "Heat map of technology impacts",
                    "Timeline of rule changes",
                    "Winners and losers analysis",
                    "Predictive impact modeling"
                ]
            },
            {
                "title": "The Great Texas Grid Wars: BESS vs Traditional Generators",
                "description": "Deep dive into the ongoing battle between battery storage and traditional generation in ERCOT market rules",
                "format": "Long-form investigative piece",
                "audience": "Industry executives, investors",
                "key_features": [
                    "Historical analysis of rule changes favoring/hurting BESS",
                    "Economic impact quantification",
                    "Key player interviews simulation",
                    "Future outlook and predictions"
                ]
            },
            {
                "title": "NPRR Decoder Ring: What Energy Developers Need to Know",
                "description": "Monthly guide translating complex NPRRs into actionable insights for developers",
                "format": "Monthly newsletter/guide",
                "audience": "Project developers, engineers",
                "key_features": [
                    "Plain English explanations",
                    "Implementation timelines",
                    "Compliance checklists",
                    "Cost impact calculators"
                ]
            },
            {
                "title": "Follow the Money: Economic Impact Analysis of ERCOT Rule Changes",
                "description": "Quantitative analysis of how NPRRs affect project economics",
                "format": "Research report with models",
                "audience": "Financial analysts, investors",
                "key_features": [
                    "NPV impact calculations",
                    "IRR sensitivity analysis",
                    "Market price projections",
                    "Investment recommendation changes"
                ]
            },
            {
                "title": "The Interconnection Queue Saga: How NPRRs Shape Grid Access",
                "description": "Analysis of how rule changes affect interconnection timelines and costs",
                "format": "Technical white paper",
                "audience": "Developers, grid planners",
                "key_features": [
                    "Queue position impacts",
                    "Study requirement changes",
                    "Cost allocation shifts",
                    "Strategic positioning advice"
                ]
            },
            {
                "title": "Ancillary Services Gold Rush: New Revenue Streams from NPRRs",
                "description": "Guide to emerging ancillary service opportunities created by recent NPRRs",
                "format": "Opportunity guide",
                "audience": "Asset owners, traders",
                "key_features": [
                    "New service definitions",
                    "Revenue potential analysis",
                    "Technical requirements",
                    "Market entry strategies"
                ]
            },
            {
                "title": "Data Center Power Play: How Tech Giants Are Reshaping Texas Grid Rules",
                "description": "Investigation into data center influence on ERCOT market design",
                "format": "Investigative series",
                "audience": "General business audience",
                "key_features": [
                    "Lobbying analysis",
                    "Load growth projections",
                    "Reliability impacts",
                    "Cost socialization debates"
                ]
            },
            {
                "title": "Virtual Power Plant Revolution: NPRRs Enabling Distributed Energy",
                "description": "How rule changes are enabling aggregation and VPP business models",
                "format": "Business strategy guide",
                "audience": "VPP operators, aggregators",
                "key_features": [
                    "Aggregation rule evolution",
                    "Telemetry requirements",
                    "Settlement calculations",
                    "Growth opportunity mapping"
                ]
            },
            {
                "title": "Nuclear Renaissance in Texas? NPRRs Paving the Way",
                "description": "Analysis of how market rules are evolving to accommodate nuclear",
                "format": "Policy analysis",
                "audience": "Policy makers, nuclear developers",
                "key_features": [
                    "Capacity payment structures",
                    "Long-term contract provisions",
                    "Reliability credit mechanisms",
                    "Federal-state coordination"
                ]
            },
            {
                "title": "The Dispatchability Debate: Real-Time Co-Optimization Impacts",
                "description": "Technical deep-dive into RTC implementation and market impacts",
                "format": "Technical analysis",
                "audience": "Market operators, traders",
                "key_features": [
                    "Algorithm changes",
                    "Price formation impacts",
                    "Dispatch efficiency gains",
                    "Gaming opportunities/risks"
                ]
            },
            {
                "title": "Green Hydrogen's Grid Challenge: NPRR Adaptations for Electrolyzers",
                "description": "How ERCOT is adapting rules for large flexible loads",
                "format": "Technology focus piece",
                "audience": "Hydrogen developers, industrials",
                "key_features": [
                    "Controllable load resource provisions",
                    "Interruptibility credits",
                    "Transmission cost allocation",
                    "Green attribute tracking"
                ]
            },
            {
                "title": "ERCOT Market Manipulation: Loopholes and Fixes in Recent NPRRs",
                "description": "Analysis of market gaming strategies and regulatory responses",
                "format": "Regulatory analysis",
                "audience": "Compliance officers, regulators",
                "key_features": [
                    "Historical manipulation cases",
                    "Rule tightening measures",
                    "Monitoring enhancements",
                    "Penalty structure changes"
                ]
            },
            {
                "title": "Weather Wars: Extreme Event NPRRs After Uri and Beryl",
                "description": "How winter storm Uri and hurricane Beryl shaped new market rules",
                "format": "Historical analysis",
                "audience": "Risk managers, regulators",
                "key_features": [
                    "Weatherization requirements",
                    "Reserve margin changes",
                    "Price cap adjustments",
                    "Black start evolution"
                ]
            },
            {
                "title": "The Locational Marginal Price Revolution: Nodal Pricing Updates",
                "description": "Impact of LMP calculation changes on congestion and basis risk",
                "format": "Market structure analysis",
                "audience": "Traders, transmission developers",
                "key_features": [
                    "Congestion pattern shifts",
                    "Hub price impacts",
                    "FTR valuation changes",
                    "Transmission investment signals"
                ]
            },
            {
                "title": "Demand Response 2.0: NPRRs Transforming Load Participation",
                "description": "Evolution of demand response programs and performance requirements",
                "format": "Program guide",
                "audience": "C&I customers, aggregators",
                "key_features": [
                    "Baseline methodology changes",
                    "Performance measurement updates",
                    "Settlement improvements",
                    "Technology requirements"
                ]
            }
        ]
        
        return article_ideas
    
    def generate_comparison_matrix(self, catalog_path: str) -> pd.DataFrame:
        """Generate a comparison matrix of NPRRs and their impacts"""
        with open(catalog_path, 'r') as f:
            catalog = json.load(f)
        
        data = []
        for nprr_id, nprr_data in catalog['nprrs'].items():
            data.append({
                'NPRR': nprr_id,
                'Title': nprr_data.get('title', ''),
                'Approval Date': nprr_data.get('approval_date', ''),
                'Document Count': len(nprr_data.get('documents', [])),
                'Has Comments': any('comment' in doc['name'].lower() for doc in nprr_data.get('documents', [])),
                'Status': nprr_data.get('status', '')
            })
        
        df = pd.DataFrame(data)
        return df
    
    def generate_trend_analysis(self, catalog_path: str) -> Dict:
        """Analyze trends in NPRR submissions and topics"""
        with open(catalog_path, 'r') as f:
            catalog = json.load(f)
        
        trends = {
            'technology_mentions': {
                'battery': 0,
                'solar': 0,
                'wind': 0,
                'gas': 0,
                'nuclear': 0,
                'hydrogen': 0,
                'data_center': 0,
                'demand_response': 0,
                'virtual_power_plant': 0
            },
            'topic_categories': {
                'ancillary_services': 0,
                'real_time_operations': 0,
                'settlements': 0,
                'interconnection': 0,
                'reliability': 0,
                'market_power': 0,
                'transmission': 0
            },
            'stakeholder_activity': {},
            'monthly_submissions': {}
        }
        
        for nprr_id, nprr_data in catalog['nprrs'].items():
            # Analyze title and summary for technology mentions
            text = (nprr_data.get('title', '') + ' ' + 
                   nprr_data.get('summary', '')).lower()
            
            for tech in trends['technology_mentions']:
                if tech.replace('_', ' ') in text:
                    trends['technology_mentions'][tech] += 1
            
            # Count stakeholder participation
            for doc in nprr_data.get('documents', []):
                if 'comment' in doc['name'].lower():
                    commenter = doc['name'].split(' ')[0]
                    trends['stakeholder_activity'][commenter] = \
                        trends['stakeholder_activity'].get(commenter, 0) + 1
        
        return trends
    
    def save_all_ideas(self):
        """Save all generated ideas and analyses"""
        # Save article ideas
        ideas = self.generate_article_ideas()
        ideas_file = self.analysis_dir / "article_ideas.json"
        with open(ideas_file, 'w') as f:
            json.dump(ideas, f, indent=2)
        
        # Create markdown summary
        summary_file = self.analysis_dir / "content_ideas_summary.md"
        with open(summary_file, 'w') as f:
            f.write("# ERCOT NPRR Content Strategy for Energence.ai\n\n")
            f.write("## Executive Summary\n\n")
            f.write("This document outlines comprehensive content opportunities based on ERCOT NPRR analysis.\n\n")
            
            f.write("## Article Ideas\n\n")
            for i, idea in enumerate(ideas, 1):
                f.write(f"### {i}. {idea['title']}\n")
                f.write(f"**Format:** {idea['format']}\n")
                f.write(f"**Audience:** {idea['audience']}\n")
                f.write(f"**Description:** {idea['description']}\n")
                f.write("**Key Features:**\n")
                for feature in idea['key_features']:
                    f.write(f"- {feature}\n")
                f.write("\n")
            
            f.write("## Implementation Recommendations\n\n")
            f.write("1. **Priority Content:**\n")
            f.write("   - Start with Weekly Impact Dashboard for immediate value\n")
            f.write("   - Launch monthly NPRR Decoder Ring newsletter\n")
            f.write("   - Develop investigative pieces on BESS vs Traditional Gen\n\n")
            
            f.write("2. **Content Calendar:**\n")
            f.write("   - Weekly: Dashboard updates\n")
            f.write("   - Bi-weekly: Short analysis pieces\n")
            f.write("   - Monthly: Deep dives and decoder guides\n")
            f.write("   - Quarterly: Major investigative reports\n\n")
            
            f.write("3. **Monetization Opportunities:**\n")
            f.write("   - Premium subscriptions for detailed analysis\n")
            f.write("   - Custom reports for specific technologies\n")
            f.write("   - API access to impact scores\n")
            f.write("   - Consulting services based on insights\n\n")
            
            f.write("4. **Platform Integration:**\n")
            f.write("   - Embed dashboard in energence.ai\n")
            f.write("   - RSS feed for updates\n")
            f.write("   - Email newsletter automation\n")
            f.write("   - Social media snippets\n\n")
        
        print(f"Content ideas saved to {self.analysis_dir}")
        return ideas

def main():
    generator = NPRRContentGenerator()
    ideas = generator.save_all_ideas()
    
    # If catalog exists, generate comparison matrix
    catalog_path = Path("nprr_data/nprr_catalog.json")
    if catalog_path.exists():
        df = generator.generate_comparison_matrix(str(catalog_path))
        df.to_csv(generator.analysis_dir / "nprr_comparison.csv", index=False)
        
        trends = generator.generate_trend_analysis(str(catalog_path))
        with open(generator.analysis_dir / "nprr_trends.json", 'w') as f:
            json.dump(trends, f, indent=2)
    
    print(f"\nGenerated {len(ideas)} article ideas")
    print(f"Results saved to {generator.analysis_dir}")

if __name__ == "__main__":
    main()