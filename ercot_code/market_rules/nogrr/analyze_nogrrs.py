#!/usr/bin/env python3
"""
ERCOT NOGRR Analyzer using Claude API
Analyzes NOGRRs and their documents to generate insights for energy intelligence
"""

import os
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NOGRRAnalyzer:
    def __init__(self, data_dir: str = None, output_dir: str = None):
        base_dir = "/pool/ssd8tb/data/iso/ERCOT/market_rules/nogrr/"
        self.data_dir = Path(data_dir) if data_dir else Path(base_dir) / "nogrr_data"
        self.output_dir = Path(output_dir) if output_dir else Path(base_dir) / "nogrr_analysis"
        self.output_dir.mkdir(exist_ok=True)
        
        # Technology categories for impact scoring
        self.tech_categories = [
            "BESS (Battery Energy Storage Systems)",
            "PV (Solar Photovoltaic)",
            "Wind Generation",
            "Datacenters",
            "Microgrids",
            "Nuclear Generation",
            "Natural Gas Generation",
            "Coal Generation",
            "Hydro Generation",
            "Distributed Energy Resources (DER)",
            "Virtual Power Plants (VPP)",
            "Electric Vehicles (EV) Infrastructure",
            "Demand Response",
            "Transmission Infrastructure",
            "Grid Modernization/Smart Grid"
        ]
    
    def load_nogrr_data(self, nogrr_id: str) -> Dict:
        """Load NOGRR data from JSON file"""
        json_path = self.data_dir / f"{nogrr_id}.json"
        if not json_path.exists():
            logger.error(f"NOGRR data file not found: {json_path}")
            return {}
            
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_document_paths(self, nogrr_data: Dict) -> List[str]:
        """Get list of local document paths for a NOGRR"""
        doc_paths = []
        for doc in nogrr_data.get('documents', []):
            if 'local_path' in doc:
                path = Path(doc['local_path'])
                if path.exists():
                    doc_paths.append(str(path))
        return doc_paths
    
    def call_claude_cli(self, prompt: str, files: Optional[List[str]] = None) -> str:
        """Call Claude CLI with a prompt and optional files"""
        cmd = ["claude", "code"]
        
        # Add file reading commands if files provided
        if files:
            file_reads = " && ".join([f"cat '{f}'" for f in files[:5]])  # Limit to 5 files
            full_prompt = f"First read these files: {file_reads}\n\nThen analyze: {prompt}"
        else:
            full_prompt = prompt
        
        # Use echo to pass the prompt to claude
        full_cmd = f"echo {json.dumps(full_prompt)} | claude code"
        
        try:
            result = subprocess.run(
                full_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.error(f"Claude CLI error: {result.stderr}")
                return f"Error: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            logger.error("Claude CLI timeout")
            return "Error: Analysis timeout"
        except Exception as e:
            logger.error(f"Claude CLI exception: {e}")
            return f"Error: {str(e)}"
    
    def analyze_nogrr_expert(self, nogrr_data: Dict) -> Dict:
        """Generate expert analysis with technology impact scores"""
        logger.info(f"Generating expert analysis for {nogrr_data['id']}...")
        
        # Prepare context
        context = f"""
NOGRR ID: {nogrr_data['id']}
Title: {nogrr_data.get('title', '')}
Description: {nogrr_data.get('description', '')}
Sponsor: {nogrr_data.get('sponsor', '')}
Protocol Sections: {nogrr_data.get('protocol_sections', '')}
Summary: {nogrr_data.get('summary', '')[:1000]}
Background: {nogrr_data.get('background', '')[:1000]}
Action: {nogrr_data.get('action', '')[:500]}
"""
        
        # Get document paths
        doc_paths = self.get_document_paths(nogrr_data)
        
        # Create impact scoring prompt
        tech_list = '\n'.join([f"- {tech}" for tech in self.tech_categories])
        
        prompt = f"""You are an expert energy market analyst. Analyze this ERCOT NOGRR and provide:

{context}

Documents available: {len(doc_paths)} files

Please provide:

1. EXPERT EXPLANATION (300-500 words):
   - What this NOGRR does technically
   - Key operational changes it introduces
   - Market implications
   - Timeline and implementation requirements

2. TECHNOLOGY IMPACT SCORES (-10 to +10):
   Rate the impact on each technology where:
   -10 = Severely negative impact
   0 = No impact
   +10 = Highly beneficial
   
   Technologies to score:
{tech_list}

3. KEY STAKEHOLDER IMPACTS:
   - Who benefits most
   - Who faces challenges
   - Compliance requirements

Format your response as JSON with these keys:
- expert_explanation: string
- impact_scores: object with technology names as keys and scores as values
- stakeholder_impacts: object with benefits, challenges, and compliance keys
"""
        
        response = self.call_claude_cli(prompt, doc_paths[:3] if doc_paths else None)
        
        # Try to parse JSON from response
        try:
            # Find JSON in response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Fallback structure if parsing fails
        return {
            "expert_explanation": response[:2000] if len(response) > 2000 else response,
            "impact_scores": {tech: 0 for tech in self.tech_categories},
            "stakeholder_impacts": {
                "benefits": "Analysis pending",
                "challenges": "Analysis pending",
                "compliance": "Analysis pending"
            }
        }
    
    def generate_blog_posts(self, nogrr_data: Dict, expert_analysis: Dict) -> Dict:
        """Generate blog posts about the NOGRR"""
        logger.info(f"Generating blog posts for {nogrr_data['id']}...")
        
        context = f"""
NOGRR: {nogrr_data['id']} - {nogrr_data.get('title', '')}
Expert Analysis: {expert_analysis.get('expert_explanation', '')[:500]}
"""
        
        # Teaser blog post
        teaser_prompt = f"""{context}

Write a compelling 150-word teaser blog post for energence.ai that:
- Hooks readers with why this NOGRR matters
- Highlights the most impactful change
- Creates urgency for energy market participants
- Ends with a call-to-action

Make it engaging and accessible to both technical and business audiences."""
        
        teaser = self.call_claude_cli(teaser_prompt)
        
        # Long-form blog post
        longform_prompt = f"""{context}

Write a comprehensive 800-word blog post for energence.ai that:

1. Opens with market context and why this matters now
2. Explains the technical changes in accessible language
3. Analyzes winners and losers in the market
4. Provides strategic recommendations for different stakeholders
5. Discusses implementation timeline and challenges
6. Concludes with forward-looking insights

Include section headers and make it informative yet engaging."""
        
        longform = self.call_claude_cli(longform_prompt)
        
        return {
            "teaser": teaser,
            "longform": longform
        }
    
    def generate_opinion_piece(self, nogrr_data: Dict, expert_analysis: Dict) -> str:
        """Generate an opinion piece about stakeholder conflicts"""
        logger.info(f"Generating opinion piece for {nogrr_data['id']}...")
        
        # Get document paths for deeper analysis
        doc_paths = self.get_document_paths(nogrr_data)
        
        context = f"""
NOGRR: {nogrr_data['id']} - {nogrr_data.get('title', '')}
Sponsor: {nogrr_data.get('sponsor', '')}
Voting Record: {nogrr_data.get('voting_record', '')[:500]}
Documents: {len(doc_paths)} submissions from various stakeholders
"""
        
        prompt = f"""{context}

Write a provocative 600-word opinion piece about the drama and conflicts in this NOGRR:

1. Identify the competing interests and hidden agendas
2. Expose tensions between traditional utilities and new energy players
3. Highlight any David vs Goliath dynamics
4. Discuss lobbying efforts and political maneuvering
5. Reveal what stakeholders aren't saying publicly
6. Predict future battles this might trigger

Make it spicy but factual! Focus on:
- Are utilities fighting BESS and solar developers?
- Is this protecting incumbents or enabling innovation?
- Who's really pulling the strings?
- What compromises were made behind closed doors?

Title it something attention-grabbing."""
        
        opinion = self.call_claude_cli(prompt, doc_paths[:2] if doc_paths else None)
        
        return opinion
    
    def generate_additional_content(self, nogrr_data: Dict, expert_analysis: Dict) -> Dict:
        """Generate additional interesting content"""
        logger.info(f"Generating additional content for {nogrr_data['id']}...")
        
        content = {}
        
        # Market intelligence brief
        intel_prompt = f"""Based on NOGRR {nogrr_data['id']}:

Create a 300-word MARKET INTELLIGENCE BRIEF for energy traders and investors:
- Trading opportunities this creates
- Asset valuation impacts
- Risk factors to monitor
- Investment thesis changes
- Arbitrage possibilities"""
        
        content['market_intelligence'] = self.call_claude_cli(intel_prompt)
        
        # Technical deep dive
        tech_prompt = f"""Based on NOGRR {nogrr_data['id']}:

Write a 400-word TECHNICAL DEEP DIVE for engineers and operators:
- Specific technical requirements
- System integration challenges
- Testing and compliance procedures
- Operational workflow changes
- Technology stack implications"""
        
        content['technical_deepdive'] = self.call_claude_cli(tech_prompt)
        
        # Policy implications
        policy_prompt = f"""Based on NOGRR {nogrr_data['id']}:

Write a 350-word POLICY IMPLICATIONS analysis:
- Regulatory precedents being set
- Alignment with state/federal energy policy
- Environmental and reliability impacts
- Consumer cost implications
- Future regulatory direction signals"""
        
        content['policy_implications'] = self.call_claude_cli(policy_prompt)
        
        return content
    
    def save_analysis(self, nogrr_id: str, analysis: Dict) -> None:
        """Save analysis results to JSON"""
        output_path = self.output_dir / f"{nogrr_id}_analysis.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Analysis saved to {output_path}")
    
    def generate_html_report(self, nogrr_id: str, nogrr_data: Dict, analysis: Dict) -> None:
        """Generate an HTML report for easy viewing"""
        html_path = self.output_dir / f"{nogrr_id}_report.html"
        
        # Create impact scores table
        scores_html = ""
        for tech, score in analysis['expert_analysis'].get('impact_scores', {}).items():
            color = "green" if score > 0 else "red" if score < 0 else "gray"
            scores_html += f"""
            <tr>
                <td>{tech}</td>
                <td style="color: {color}; font-weight: bold;">{score:+d}</td>
            </tr>"""
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>NOGRR {nogrr_id} Analysis - Energence.ai</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        h3 {{ color: #7f8c8d; }}
        .metadata {{ background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .section {{ background: #f8f9fa; padding: 20px; margin: 20px 0; border-left: 4px solid #3498db; }}
        .scores-table {{ border-collapse: collapse; width: 100%; }}
        .scores-table th, .scores-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        .scores-table th {{ background: #3498db; color: white; }}
        .opinion {{ background: #fff3cd; padding: 20px; border-left: 4px solid #ffc107; }}
        pre {{ white-space: pre-wrap; word-wrap: break-word; }}
    </style>
</head>
<body>
    <h1>NOGRR {nogrr_id}: {nogrr_data.get('title', '')}</h1>
    
    <div class="metadata">
        <strong>Sponsor:</strong> {nogrr_data.get('sponsor', '')}<br>
        <strong>Date Posted:</strong> {nogrr_data.get('date_posted', '')}<br>
        <strong>Status:</strong> {nogrr_data.get('status', '')}<br>
        <strong>Effective Date:</strong> {nogrr_data.get('effective_date', '')}<br>
        <strong>Protocol Sections:</strong> {nogrr_data.get('protocol_sections', '')}
    </div>
    
    <div class="section">
        <h2>Original Description</h2>
        <p>{nogrr_data.get('description', '')}</p>
    </div>
    
    <div class="section">
        <h2>Expert Analysis</h2>
        <pre>{analysis['expert_analysis'].get('expert_explanation', '')}</pre>
    </div>
    
    <div class="section">
        <h2>Technology Impact Scores</h2>
        <table class="scores-table">
            <tr><th>Technology</th><th>Impact Score (-10 to +10)</th></tr>
            {scores_html}
        </table>
    </div>
    
    <div class="section">
        <h2>Teaser Blog Post</h2>
        <pre>{analysis['blog_posts'].get('teaser', '')}</pre>
    </div>
    
    <div class="section">
        <h2>Long-form Blog Post</h2>
        <pre>{analysis['blog_posts'].get('longform', '')}</pre>
    </div>
    
    <div class="opinion">
        <h2>Opinion: The Drama Behind the Scenes</h2>
        <pre>{analysis.get('opinion_piece', '')}</pre>
    </div>
    
    <div class="section">
        <h2>Market Intelligence Brief</h2>
        <pre>{analysis['additional_content'].get('market_intelligence', '')}</pre>
    </div>
    
    <div class="section">
        <h2>Technical Deep Dive</h2>
        <pre>{analysis['additional_content'].get('technical_deepdive', '')}</pre>
    </div>
    
    <div class="section">
        <h2>Policy Implications</h2>
        <pre>{analysis['additional_content'].get('policy_implications', '')}</pre>
    </div>
    
    <footer style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #ddd; color: #7f8c8d;">
        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} for Energence.ai</p>
    </footer>
</body>
</html>"""
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        logger.info(f"HTML report saved to {html_path}")
    
    def analyze_nogrr(self, nogrr_id: str) -> Dict:
        """Complete analysis pipeline for a single NOGRR"""
        logger.info(f"Starting analysis of {nogrr_id}")
        
        # Load NOGRR data
        nogrr_data = self.load_nogrr_data(nogrr_id)
        if not nogrr_data:
            return {}
        
        # Perform analyses
        analysis = {
            'nogrr_id': nogrr_id,
            'timestamp': datetime.now().isoformat(),
            'expert_analysis': self.analyze_nogrr_expert(nogrr_data),
            'blog_posts': self.generate_blog_posts(nogrr_data, {}),
            'opinion_piece': self.generate_opinion_piece(nogrr_data, {}),
            'additional_content': self.generate_additional_content(nogrr_data, {})
        }
        
        # Save results
        self.save_analysis(nogrr_id, analysis)
        self.generate_html_report(nogrr_id, nogrr_data, analysis)
        
        return analysis
    
    def analyze_all_nogrrs(self) -> None:
        """Analyze all downloaded NOGRRs"""
        catalog_path = self.data_dir / "nogrr_catalog.json"
        
        if not catalog_path.exists():
            logger.error("NOGRR catalog not found. Run download_nogrrs.py first.")
            return
            
        with open(catalog_path, 'r') as f:
            catalog = json.load(f)
            
        nogrrs = catalog.get('nogrrs', [])
        logger.info(f"Found {len(nogrrs)} NOGRRs to analyze")
        
        results = []
        for i, nogrr_info in enumerate(nogrrs, 1):
            logger.info(f"Analyzing {i}/{len(nogrrs)}: {nogrr_info['id']}")
            
            try:
                analysis = self.analyze_nogrr(nogrr_info['id'])
                results.append({
                    'nogrr_id': nogrr_info['id'],
                    'title': nogrr_info.get('title', ''),
                    'analysis_path': f"{nogrr_info['id']}_analysis.json",
                    'report_path': f"{nogrr_info['id']}_report.html"
                })
            except Exception as e:
                logger.error(f"Failed to analyze {nogrr_info['id']}: {e}")
                
            # Rate limiting
            time.sleep(2)
        
        # Save analysis catalog
        catalog_path = self.output_dir / "analysis_catalog.json"
        with open(catalog_path, 'w') as f:
            json.dump({
                'generated': datetime.now().isoformat(),
                'total_analyzed': len(results),
                'analyses': results
            }, f, indent=2)
            
        logger.info(f"Analysis complete. Results in {self.output_dir}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze ERCOT NOGRRs')
    parser.add_argument('--nogrr-id', help='Analyze specific NOGRR ID')
    base_dir = "/pool/ssd8tb/data/iso/ERCOT/market_rules/nogrr/"
    parser.add_argument('--data-dir', default=None, help='Directory with NOGRR data (default: base_dir/nogrr_data)')
    parser.add_argument('--output-dir', default=None, help='Output directory (default: base_dir/nogrr_analysis)')
    parser.add_argument('--all', action='store_true', help='Analyze all NOGRRs')
    
    args = parser.parse_args()
    
    analyzer = NOGRRAnalyzer(data_dir=args.data_dir, output_dir=args.output_dir)
    
    if args.nogrr_id:
        analyzer.analyze_nogrr(args.nogrr_id)
    elif args.all:
        analyzer.analyze_all_nogrrs()
    else:
        print("Please specify --nogrr-id or --all")

if __name__ == "__main__":
    main()