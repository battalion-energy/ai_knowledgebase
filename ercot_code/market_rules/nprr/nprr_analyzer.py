#!/usr/bin/env python3
"""
NPRR Analyzer using Claude Code CLI
Analyzes ERCOT NPRRs for impact on various energy technologies
"""

import os
import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NPRRAnalyzer:
    def __init__(self, catalog_path: str = "nprr_data/nprr_catalog.json", output_dir: str = "nprr_analysis", status: str = "approved"):
        self.catalog_path = Path(catalog_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.status = status
        self.analysis_file = self.output_dir / f"nprr_{status}_analysis.json"
        self.blog_dir = self.output_dir / "blog_posts"
        self.blog_dir.mkdir(exist_ok=True)
        
    def load_catalog(self) -> Dict:
        """Load NPRR catalog"""
        if not self.catalog_path.exists():
            raise FileNotFoundError(f"Catalog not found: {self.catalog_path}")
        
        with open(self.catalog_path, 'r') as f:
            return json.load(f)
    
    def load_existing_analysis(self) -> Dict:
        """Load existing analysis if it exists"""
        if self.analysis_file.exists():
            with open(self.analysis_file, 'r') as f:
                return json.load(f)
        return {"analyses": {}, "last_updated": None}
    
    def save_analysis(self, analysis: Dict):
        """Save analysis to JSON file"""
        analysis["last_updated"] = datetime.now().isoformat()
        with open(self.analysis_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        logger.info(f"Analysis saved to {self.analysis_file}")
    
    def create_claude_prompt(self, nprr: Dict, documents_content: str, status: str = "approved") -> str:
        """Create a comprehensive prompt for Claude analysis"""
        
        status_context = ""
        if status == "pending":
            status_context = """
NOTE: This is a PENDING NPRR that has not been approved yet. Your analysis should:
- Compare proposed changes to current rules
- Discuss how this might change the market dynamics
- Analyze who benefits and who loses from these changes
- Consider likelihood of approval based on stakeholder positions
"""
        elif status == "rejected":
            status_context = """
NOTE: This is a REJECTED NPRR that was NOT approved. Your analysis should focus on:
- What the proposers were trying to accomplish
- Why it likely failed (based on comments and voting patterns)
- What types of projects and businesses would have been impacted
- What were the key arguments for and against
- Lessons learned for future similar proposals
"""
        
        prompt = f"""Analyze NPRR {nprr['id']}: {nprr.get('title', '')}
{status_context}
Summary: {nprr.get('summary', 'Not available')}
Action: {nprr.get('action', 'Not available')}
Background: {nprr.get('background', 'Not available')}

Documents Content:
{documents_content[:50000]}  # Limit to avoid token limits

Please provide a comprehensive analysis with the following sections:

1. EXPERT EXPLANATION
Provide a detailed technical explanation of this NPRR including:
- What specific market rule changes {'were proposed' if status == 'rejected' else 'are being proposed' if status == 'pending' else 'are being implemented'}
- How this {'would have differed' if status == 'rejected' else 'differs'} from current rules
- Technical details and mechanisms
{'- Why the proposal was rejected' if status == 'rejected' else '- Timeline and implementation phases'}
- Key stakeholders affected
{'- Lessons for future proposals' if status == 'rejected' else '- Likelihood of approval and potential modifications' if status == 'pending' else ''}

2. TECHNOLOGY IMPACT SCORES (-10 to +10)
Rate the impact on each technology (negative = harmful, positive = beneficial):
- BESS (Battery Energy Storage Systems): [score] - [brief explanation]
- PV (Solar Photovoltaic): [score] - [brief explanation]
- Wind Generation: [score] - [brief explanation]
- Data Centers: [score] - [brief explanation]
- Microgrids: [score] - [brief explanation]
- Nuclear Generation: [score] - [brief explanation]
- Natural Gas Generation: [score] - [brief explanation]
- Coal Generation: [score] - [brief explanation]
- Hydro Generation: [score] - [brief explanation]
- Hydrogen/Fuel Cells: [score] - [brief explanation]
- Virtual Power Plants: [score] - [brief explanation]
- Demand Response: [score] - [brief explanation]
- Other Emerging Technologies: [score] - [brief explanation]

3. SHORT TEASER (2-3 sentences)
Write an engaging teaser that would make energy professionals want to read more about this {'rejected' if status == 'rejected' else 'proposed' if status == 'pending' else ''} NPRR.

4. LONG FORM BLOG POST (500-800 words)
Write a comprehensive blog post that:
- Opens with why this {'failed proposal mattered' if status == 'rejected' else 'proposal' if status == 'pending' else 'change'} matters to the Texas energy market
- Explains {'what would have changed' if status == 'rejected' else 'what would change from current rules' if status == 'pending' else 'the technical changes'} in accessible language
- Discusses winners and losers {'from the rejection' if status == 'rejected' else 'if approved' if status == 'pending' else ''}
- Provides market outlook and implications
- Ends with actionable insights for energy professionals

5. DRAMA & POLITICS PIECE
Write a more colorful analysis of the stakeholder dynamics:
- Who's fighting whom and why?
- What are the real economic interests at stake?
- Are traditional utilities resisting new technologies?
- What compromises {'could have saved this proposal' if status == 'rejected' else 'might be needed' if status == 'pending' else 'were made'}?
- Include specific quotes or positions from comments if available

6. KEY TAKEAWAYS
List 3-5 bullet points of the most important implications

Format your response as a valid JSON object with these keys:
expert_explanation, impact_scores, short_teaser, long_blog, drama_piece, key_takeaways"""
        
        return prompt
    
    def read_documents(self, nprr: Dict) -> str:
        """Read and combine document contents"""
        content = ""
        for doc_path in nprr.get('downloaded_files', []):
            if Path(doc_path).exists():
                # For PDFs and other binary files, we'll need to extract text
                # For now, we'll just note the file exists
                content += f"\n\n--- Document: {Path(doc_path).name} ---\n"
                if doc_path.endswith('.txt'):
                    try:
                        with open(doc_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content += f.read()[:10000]  # Limit per file
                    except Exception as e:
                        logger.error(f"Error reading {doc_path}: {e}")
        
        return content if content else "No document content available"
    
    def call_claude(self, prompt: str) -> Optional[Dict]:
        """Call Claude Code CLI to analyze the NPRR"""
        try:
            # Use claude CLI with JSON output format
            result = subprocess.run(
                ['claude', '-p', '--output-format', 'json'],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                # Parse the Claude CLI JSON wrapper
                response_text = result.stdout
                try:
                    # First parse the outer Claude response wrapper
                    wrapper = json.loads(response_text)
                    if 'result' in wrapper:
                        # Extract the actual analysis from the result field
                        result_text = wrapper['result']
                        # Look for JSON within the result text
                        import re
                        # Find JSON between ```json and ``` or just raw JSON
                        json_match = re.search(r'```json\s*(.*?)\s*```', result_text, re.DOTALL)
                        if json_match:
                            return json.loads(json_match.group(1))
                        else:
                            # Try to find raw JSON
                            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                            if json_match:
                                return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
                
                # Fallback: try to extract JSON from raw response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group())
                    except:
                        pass
                    
                # If no JSON found, structure the response
                    # If not JSON, structure the response
                    return {
                        "expert_explanation": response_text,
                        "impact_scores": {},
                        "short_teaser": "",
                        "long_blog": "",
                        "drama_piece": "",
                        "key_takeaways": []
                    }
            else:
                logger.error(f"Claude CLI error: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("Claude CLI timeout")
            return None
        except Exception as e:
            logger.error(f"Error calling Claude: {e}")
            return None
    
    def analyze_nprr(self, nprr_id: str, nprr_data: Dict) -> Optional[Dict]:
        """Analyze a single NPRR"""
        logger.info(f"Analyzing {nprr_id}")
        
        # Read document contents
        documents_content = self.read_documents(nprr_data)
        
        # Create prompt with correct status
        prompt = self.create_claude_prompt(nprr_data, documents_content, status=self.status)
        
        # Call Claude for analysis
        analysis = self.call_claude(prompt)
        
        if analysis:
            analysis['nprr_id'] = nprr_id
            analysis['title'] = nprr_data.get('title', '')
            analysis['approval_date'] = nprr_data.get('approval_date', '')
            analysis['analyzed_at'] = datetime.now().isoformat()
            
            # Save blog posts to separate files
            self.save_blog_posts(nprr_id, analysis)
            
            return analysis
        
        return None
    
    def save_blog_posts(self, nprr_id: str, analysis: Dict):
        """Save blog posts to separate markdown files"""
        # Short teaser
        if analysis.get('short_teaser'):
            teaser_file = self.blog_dir / f"{nprr_id}_teaser.md"
            with open(teaser_file, 'w') as f:
                f.write(f"# {nprr_id}: {analysis.get('title', '')}\n\n")
                f.write(analysis['short_teaser'])
        
        # Long blog
        if analysis.get('long_blog'):
            blog_file = self.blog_dir / f"{nprr_id}_blog.md"
            with open(blog_file, 'w') as f:
                f.write(f"# {nprr_id}: {analysis.get('title', '')}\n\n")
                f.write(analysis['long_blog'])
        
        # Drama piece
        if analysis.get('drama_piece'):
            drama_file = self.blog_dir / f"{nprr_id}_drama.md"
            with open(drama_file, 'w') as f:
                f.write(f"# Behind the Scenes: {nprr_id}\n\n")
                f.write(analysis['drama_piece'])
    
    def generate_summary_report(self, analyses: Dict):
        """Generate a summary report of all analyses"""
        report_file = self.output_dir / "summary_report.md"
        
        with open(report_file, 'w') as f:
            f.write("# ERCOT NPRR Analysis Summary\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            
            # Technology impact summary
            f.write("## Technology Impact Summary\n\n")
            tech_impacts = {}
            
            for nprr_id, analysis in analyses.get('analyses', {}).items():
                scores = analysis.get('impact_scores', {})
                for tech, score in scores.items():
                    if tech not in tech_impacts:
                        tech_impacts[tech] = []
                    tech_impacts[tech].append((nprr_id, score))
            
            for tech, impacts in tech_impacts.items():
                avg_score = sum(s for _, s in impacts) / len(impacts) if impacts else 0
                f.write(f"### {tech}\n")
                f.write(f"Average Impact: {avg_score:.1f}\n")
                f.write("Top Impacts:\n")
                for nprr_id, score in sorted(impacts, key=lambda x: abs(x[1]), reverse=True)[:3]:
                    f.write(f"- {nprr_id}: {score}\n")
                f.write("\n")
            
            # Recent NPRRs
            f.write("## Recent NPRRs Analyzed\n\n")
            recent = sorted(
                analyses.get('analyses', {}).items(),
                key=lambda x: x[1].get('analyzed_at', ''),
                reverse=True
            )[:10]
            
            for nprr_id, analysis in recent:
                f.write(f"### {nprr_id}: {analysis.get('title', '')}\n")
                f.write(f"{analysis.get('short_teaser', '')}\n\n")
        
        logger.info(f"Summary report saved to {report_file}")
    
    def filter_by_years(self, nprr_items: List[tuple], years: int) -> List[tuple]:
        """Filter NPRRs by years from today"""
        if not years:
            return nprr_items
            
        cutoff_date = datetime.now() - timedelta(days=years * 365)
        filtered = []
        
        for nprr_id, nprr_data in nprr_items:
            date_str = nprr_data.get('approval_date', '')
            if not date_str:
                continue
                
            try:
                # Try different date formats
                for fmt in ['%m/%d/%Y', '%m/%d/%y', '%Y-%m-%d']:
                    try:
                        nprr_date = datetime.strptime(date_str, fmt)
                        if nprr_date >= cutoff_date:
                            filtered.append((nprr_id, nprr_data))
                        break
                    except ValueError:
                        continue
            except Exception as e:
                logger.warning(f"Could not parse date for {nprr_id}: {date_str}")
                
        logger.info(f"Filtered to {len(filtered)} NPRRs from last {years} years")
        return filtered
    
    def run(self, limit: Optional[int] = None, skip_existing: bool = True, years: Optional[int] = None):
        """Run analysis on NPRRs"""
        catalog = self.load_catalog()
        analyses = self.load_existing_analysis()
        
        nprr_items = list(catalog['nprrs'].items())
        
        # Filter by years if specified
        if years:
            nprr_items = self.filter_by_years(nprr_items, years)
        
        if limit:
            nprr_items = nprr_items[:limit]
        
        for i, (nprr_id, nprr_data) in enumerate(nprr_items, 1):
            logger.info(f"Processing {i}/{len(nprr_items)}: {nprr_id}")
            
            if skip_existing and nprr_id in analyses.get('analyses', {}):
                logger.info(f"Skipping {nprr_id} (already analyzed)")
                continue
            
            analysis = self.analyze_nprr(nprr_id, nprr_data)
            
            if analysis:
                analyses['analyses'][nprr_id] = analysis
                self.save_analysis(analyses)
            
            # Rate limiting
            time.sleep(5)
        
        # Generate summary report
        self.generate_summary_report(analyses)
        
        logger.info("Analysis completed!")
        return analyses

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze ERCOT NPRRs')
    parser.add_argument('--catalog', default='nprr_data/nprr_catalog.json', help='Path to NPRR catalog')
    parser.add_argument('--output-dir', default='nprr_analysis', help='Output directory')
    parser.add_argument('--limit', type=int, help='Limit number of NPRRs to analyze')
    parser.add_argument('--force', action='store_true', help='Re-analyze existing NPRRs')
    parser.add_argument('--status', choices=['approved', 'pending', 'rejected'], default='approved',
                       help='NPRR status for context-aware analysis')
    parser.add_argument('--years', type=int, help='Analyze NPRRs from last N years')
    
    args = parser.parse_args()
    
    analyzer = NPRRAnalyzer(catalog_path=args.catalog, output_dir=args.output_dir, status=args.status)
    analyses = analyzer.run(limit=args.limit, skip_existing=not args.force, years=args.years)
    
    print(f"\nAnalyzed {len(analyses['analyses'])} NPRRs")
    print(f"Results saved to: {analyzer.output_dir}")

if __name__ == "__main__":
    main()