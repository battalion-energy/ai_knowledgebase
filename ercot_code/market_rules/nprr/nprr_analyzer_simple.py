#!/usr/bin/env python3
"""
Simplified NPRR Analyzer - Analyzes ERCOT NPRRs without external Claude CLI
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimplifiedNPRRAnalyzer:
    def __init__(self, catalog_path: str = "nprr_data/nprr_catalog.json", 
                 output_dir: str = "nprr_analysis", status: str = "approved"):
        self.catalog_path = Path(catalog_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.status = status
        self.analysis_file = self.output_dir / f"nprr_{status}_analysis_simple.json"
        
        # Technology keywords for impact analysis
        self.tech_keywords = {
            "BESS": ["battery", "energy storage", "bess", "storage resource"],
            "Solar": ["solar", "photovoltaic", "pv", "solar generation"],
            "Wind": ["wind", "wind generation", "wind resource"],
            "DataCenters": ["data center", "large load", "cryptocurrency", "mining"],
            "Microgrids": ["microgrid", "distributed", "islanding"],
            "Nuclear": ["nuclear", "atomic"],
            "Gas": ["natural gas", "gas turbine", "combined cycle", "combustion"],
            "Coal": ["coal", "lignite"],
            "Hydro": ["hydro", "water", "dam"],
            "Hydrogen": ["hydrogen", "fuel cell", "electrolyzer"],
            "VPP": ["virtual power plant", "aggregation", "distributed energy"],
            "DemandResponse": ["demand response", "load resource", "controllable load"],
            "Emerging": ["emerging", "new technology", "innovative"]
        }
        
    def load_catalog(self) -> Dict:
        """Load NPRR catalog"""
        if not self.catalog_path.exists():
            raise FileNotFoundError(f"Catalog not found: {self.catalog_path}")
        
        with open(self.catalog_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def analyze_text_for_technology_impact(self, text: str) -> Dict[str, int]:
        """Analyze text to determine technology impact scores"""
        text_lower = text.lower()
        impact_scores = {}
        
        for tech, keywords in self.tech_keywords.items():
            score = 0
            mentions = 0
            
            for keyword in keywords:
                if keyword in text_lower:
                    mentions += text_lower.count(keyword)
            
            if mentions > 0:
                # Simple scoring based on mentions and context
                if "improve" in text_lower or "enhance" in text_lower or "benefit" in text_lower:
                    score = min(mentions * 2, 8)
                elif "restrict" in text_lower or "limit" in text_lower or "reduce" in text_lower:
                    score = max(-mentions * 2, -8)
                else:
                    score = min(mentions, 3)
                    
            impact_scores[tech] = score
            
        return impact_scores
    
    def analyze_pending_approval_likelihood(self, nprr_data: Dict) -> Dict:
        """Analyze likelihood of approval for pending NPRRs"""
        title = nprr_data.get('title', '').lower()
        
        # Factors that increase approval likelihood
        positive_factors = []
        negative_factors = []
        
        # Check for reliability improvements
        if any(word in title for word in ["reliability", "resilience", "winter", "weatherization"]):
            positive_factors.append("Addresses reliability concerns")
        
        # Check for market efficiency improvements
        if any(word in title for word in ["efficiency", "optimization", "improvement"]):
            positive_factors.append("Improves market efficiency")
            
        # Check for renewable integration
        if any(word in title for word in ["renewable", "solar", "wind", "battery", "storage"]):
            positive_factors.append("Supports renewable integration")
            
        # Check for controversial elements
        if any(word in title for word in ["cost", "charge", "fee", "penalty"]):
            negative_factors.append("May increase costs")
            
        if any(word in title for word in ["restrict", "limit", "prohibit"]):
            negative_factors.append("Imposes restrictions")
        
        # Calculate likelihood score
        likelihood_score = 50  # Base score
        likelihood_score += len(positive_factors) * 15
        likelihood_score -= len(negative_factors) * 10
        likelihood_score = max(0, min(100, likelihood_score))
        
        return {
            "likelihood_percentage": likelihood_score,
            "positive_factors": positive_factors,
            "negative_factors": negative_factors,
            "assessment": self.get_likelihood_assessment(likelihood_score)
        }
    
    def get_likelihood_assessment(self, score: int) -> str:
        """Get textual assessment based on likelihood score"""
        if score >= 80:
            return "Very likely to be approved"
        elif score >= 60:
            return "Likely to be approved"
        elif score >= 40:
            return "Moderate chance of approval"
        elif score >= 20:
            return "Unlikely to be approved"
        else:
            return "Very unlikely to be approved"
    
    def generate_summary(self, nprr_data: Dict, impact_scores: Dict) -> str:
        """Generate a summary of the NPRR"""
        title = nprr_data.get('title', 'Unknown')
        nprr_id = nprr_data.get('nprr_id', 'Unknown')
        
        # Find most impacted technologies
        positive_impacts = [(tech, score) for tech, score in impact_scores.items() if score > 0]
        negative_impacts = [(tech, score) for tech, score in impact_scores.items() if score < 0]
        
        positive_impacts.sort(key=lambda x: x[1], reverse=True)
        negative_impacts.sort(key=lambda x: x[1])
        
        summary = f"NPRR {nprr_id}: {title}\n\n"
        
        if positive_impacts:
            summary += "Positive impacts on: " + ", ".join([f"{tech} (+{score})" for tech, score in positive_impacts[:3]]) + "\n"
        
        if negative_impacts:
            summary += "Negative impacts on: " + ", ".join([f"{tech} ({score})" for tech, score in negative_impacts[:3]]) + "\n"
        
        if not positive_impacts and not negative_impacts:
            summary += "No significant technology impacts identified.\n"
            
        return summary
    
    def analyze_nprr(self, nprr_data: Dict) -> Dict:
        """Analyze a single NPRR"""
        nprr_id = nprr_data.get('nprr_id', 'Unknown')
        logger.info(f"Analyzing {nprr_id}")
        
        # Combine title and available document names for analysis
        text_to_analyze = nprr_data.get('title', '')
        
        # Add document titles if available
        if 'documents' in nprr_data:
            for doc in nprr_data['documents']:
                if 'title' in doc:
                    text_to_analyze += " " + doc['title']
        
        # Analyze technology impacts
        impact_scores = self.analyze_text_for_technology_impact(text_to_analyze)
        
        # Generate summary
        summary = self.generate_summary(nprr_data, impact_scores)
        
        analysis = {
            "nprr_id": nprr_id,
            "title": nprr_data.get('title', 'Unknown'),
            "status": self.status,
            "approval_date": nprr_data.get('approval_date', None),
            "impact_scores": impact_scores,
            "summary": summary,
            "analyzed_at": datetime.now().isoformat()
        }
        
        # Add approval likelihood for pending NPRRs
        if self.status == "pending":
            approval_analysis = self.analyze_pending_approval_likelihood(nprr_data)
            analysis["approval_likelihood"] = approval_analysis
        
        return analysis
    
    def run_analysis(self, limit: Optional[int] = None, years: Optional[int] = None):
        """Run analysis on NPRRs from catalog"""
        catalog = self.load_catalog()
        nprrs = catalog.get('nprrs', {})
        
        # Convert to list if it's a dict
        if isinstance(nprrs, dict):
            nprr_list = [{"nprr_id": k, **v} for k, v in nprrs.items()]
        else:
            nprr_list = nprrs
        
        # Filter by years if specified
        if years:
            cutoff_date = datetime.now() - timedelta(days=years * 365)
            filtered_list = []
            for nprr in nprr_list:
                date_str = nprr.get('approval_date') or nprr.get('submitted_date', '')
                if date_str:
                    try:
                        nprr_date = datetime.strptime(date_str[:10], '%Y-%m-%d')
                        if nprr_date >= cutoff_date:
                            filtered_list.append(nprr)
                    except:
                        pass
            nprr_list = filtered_list
        
        # Apply limit if specified
        if limit:
            nprr_list = nprr_list[:limit]
        
        # Analyze each NPRR
        analyses = {}
        for i, nprr_data in enumerate(nprr_list):
            nprr_id = nprr_data.get('nprr_id', f'unknown_{i}')
            logger.info(f"Processing {i+1}/{len(nprr_list)}: {nprr_id}")
            
            try:
                analysis = self.analyze_nprr(nprr_data)
                analyses[nprr_id] = analysis
            except Exception as e:
                logger.error(f"Error analyzing {nprr_id}: {e}")
        
        # Save results
        results = {
            "analyses": analyses,
            "total_analyzed": len(analyses),
            "status_type": self.status,
            "analysis_date": datetime.now().isoformat()
        }
        
        with open(self.analysis_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Analysis complete. Results saved to {self.analysis_file}")
        return results

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze ERCOT NPRRs")
    parser.add_argument("--catalog", default="nprr_data/nprr_approved_catalog.json",
                       help="Path to catalog JSON file")
    parser.add_argument("--status", default="approved", 
                       choices=["approved", "pending", "rejected"],
                       help="NPRR status type")
    parser.add_argument("--output-dir", default="nprr_analysis",
                       help="Output directory for analysis results")
    parser.add_argument("--limit", type=int, help="Limit number of NPRRs to analyze")
    parser.add_argument("--years", type=int, help="Analyze NPRRs from last N years")
    
    args = parser.parse_args()
    
    analyzer = SimplifiedNPRRAnalyzer(
        catalog_path=args.catalog,
        output_dir=args.output_dir,
        status=args.status
    )
    
    results = analyzer.run_analysis(limit=args.limit, years=args.years)
    
    print(f"\nAnalysis Summary:")
    print(f"Total NPRRs analyzed: {results['total_analyzed']}")
    print(f"Status type: {results['status_type']}")
    print(f"Results saved to: {analyzer.analysis_file}")

if __name__ == "__main__":
    main()