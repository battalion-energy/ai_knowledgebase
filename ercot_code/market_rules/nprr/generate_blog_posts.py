#!/usr/bin/env python3
"""
Blog Post Generator for NPRR Analysis
Generates various content formats from analyzed NPRRs
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List

class BlogGenerator:
    def __init__(self, analysis_dir: str = None):
        if analysis_dir is None:
            analysis_dir = "/pool/ssd8tb/data/iso/ERCOT/market_rules/nprr/nprr_analysis"
        self.analysis_dir = Path(analysis_dir)
        self.blog_dir = self.analysis_dir / "blog_posts"
        self.blog_dir.mkdir(exist_ok=True)
        
    def load_analysis(self, filename: str) -> Dict:
        """Load analysis JSON file"""
        filepath = self.analysis_dir / filename
        if filepath.exists():
            with open(filepath, 'r') as f:
                return json.load(f)
        return None
    
    def generate_pending_nprr_blog(self):
        """Generate blog post about pending NPRRs and approval likelihood"""
        data = self.load_analysis("nprr_pending_analysis_simple.json")
        if not data:
            print("No pending NPRR analysis found")
            return
        
        analyses = data.get('analyses', {})
        
        # Sort by likelihood
        sorted_nprrs = []
        for nprr_id, analysis in analyses.items():
            if 'approval_likelihood' in analysis:
                sorted_nprrs.append((
                    nprr_id,
                    analysis['title'],
                    analysis['approval_likelihood']['likelihood_percentage'],
                    analysis['approval_likelihood']['assessment'],
                    analysis['approval_likelihood']['positive_factors'],
                    analysis['approval_likelihood']['negative_factors']
                ))
        
        sorted_nprrs.sort(key=lambda x: x[2], reverse=True)
        
        # Generate blog content
        blog_content = f"""# ERCOT Pending NPRRs: What's Coming Down the Pipeline?

*Generated: {datetime.now().strftime('%B %d, %Y')}*

## Executive Summary

The ERCOT market continues to evolve with {len(sorted_nprrs)} pending Nodal Protocol Revision Requests (NPRRs) currently under review. These proposed changes could significantly impact various market participants, from renewable developers to traditional generators. Let's dive into what's likely to be approved and what might face challenges.

## High Likelihood of Approval (>60%)

"""
        
        high_likelihood = [n for n in sorted_nprrs if n[2] > 60]
        if high_likelihood:
            for nprr in high_likelihood[:5]:
                blog_content += f"### {nprr[0]}: {nprr[1][:80]}\n"
                blog_content += f"**Approval Likelihood: {nprr[2]}%** - {nprr[3]}\n\n"
                if nprr[4]:  # positive factors
                    blog_content += f"**Why it's likely to pass:**\n"
                    for factor in nprr[4]:
                        blog_content += f"- {factor}\n"
                blog_content += "\n"
        else:
            blog_content += "*No NPRRs currently show high likelihood of approval*\n\n"
        
        blog_content += """## Moderate Chances (40-60%)

These NPRRs could go either way and will likely depend on stakeholder feedback and political considerations:

"""
        
        moderate = [n for n in sorted_nprrs if 40 <= n[2] <= 60]
        for nprr in moderate[:5]:
            blog_content += f"**{nprr[0]}**: {nprr[1][:80]} ({nprr[2]}%)\n"
        
        blog_content += """\n## Facing Headwinds (<40%)

These proposals face significant challenges:

"""
        
        low_likelihood = [n for n in sorted_nprrs if n[2] < 40]
        if low_likelihood:
            for nprr in low_likelihood[:3]:
                blog_content += f"**{nprr[0]}**: {nprr[1][:80]}\n"
                if nprr[5]:  # negative factors
                    blog_content += f"*Challenges: {', '.join(nprr[5])}*\n\n"
        else:
            blog_content += "*All pending NPRRs show moderate to high approval likelihood*\n"
        
        blog_content += """
## Market Impact Preview

Based on our analysis of pending NPRRs, here are the key trends we're seeing:

1. **Continued Focus on Grid Reliability** - Multiple NPRRs address winterization and extreme weather preparedness
2. **Market Efficiency Improvements** - Several proposals aim to optimize dispatch and settlement processes
3. **Renewable Integration** - Ongoing efforts to better integrate battery storage and renewable resources
4. **Cost Allocation Debates** - Several NPRRs propose changes to how costs are allocated among market participants

## What This Means for Market Participants

- **Renewable Developers**: Stay tuned for potential improvements in storage integration rules
- **Traditional Generators**: Watch for changes in capacity obligations and performance requirements
- **Load Serving Entities**: Prepare for potential cost allocation shifts
- **Traders**: Monitor for market rule changes that could affect pricing dynamics

## Next Steps

These NPRRs will proceed through the ERCOT stakeholder process, including:
1. Technical Advisory Committee (TAC) review
2. Board consideration
3. Potential PUCT approval (for some items)

We'll continue monitoring these proposals and provide updates as they progress through the approval process.

---

*This analysis is based on publicly available NPRR documentation and historical approval patterns. Actual outcomes may vary based on stakeholder input and regulatory considerations.*
"""
        
        # Save blog post
        output_file = self.blog_dir / "pending_nprrs_approval_analysis.md"
        with open(output_file, 'w') as f:
            f.write(blog_content)
        
        print(f"Blog post generated: {output_file}")
        return output_file
    
    def generate_technology_impact_blog(self):
        """Generate blog about technology impacts from approved NPRRs"""
        data = self.load_analysis("nprr_approved_analysis_simple.json")
        if not data:
            print("No approved NPRR analysis found")
            return
        
        analyses = data.get('analyses', {})
        
        # Aggregate technology impacts
        tech_impacts = {}
        for nprr_id, analysis in analyses.items():
            for tech, score in analysis.get('impact_scores', {}).items():
                if score != 0:
                    if tech not in tech_impacts:
                        tech_impacts[tech] = {"positive": [], "negative": []}
                    
                    if score > 0:
                        tech_impacts[tech]["positive"].append((nprr_id, analysis['title'][:60], score))
                    else:
                        tech_impacts[tech]["negative"].append((nprr_id, analysis['title'][:60], score))
        
        # Generate blog content
        blog_content = f"""# Technology Impact Report: How Recent ERCOT NPRRs Affect Your Assets

*Generated: {datetime.now().strftime('%B %d, %Y')}*

## Overview

Our analysis of recent ERCOT NPRRs reveals significant impacts across various technology types. Here's what asset owners and developers need to know about how recent rule changes affect their investments.

## Winners and Losers by Technology

"""
        
        # Sort technologies by total impact
        tech_scores = {}
        for tech, impacts in tech_impacts.items():
            total_positive = sum(s[2] for s in impacts["positive"])
            total_negative = sum(s[2] for s in impacts["negative"])
            tech_scores[tech] = total_positive + total_negative
        
        sorted_techs = sorted(tech_scores.items(), key=lambda x: x[1], reverse=True)
        
        for tech, total_score in sorted_techs[:5]:
            if tech in tech_impacts:
                impacts = tech_impacts[tech]
                blog_content += f"### {tech.replace('_', ' ').title()}\n"
                
                if total_score > 0:
                    blog_content += f"**Overall Impact: POSITIVE (+{total_score})**\n\n"
                elif total_score < 0:
                    blog_content += f"**Overall Impact: NEGATIVE ({total_score})**\n\n"
                else:
                    blog_content += f"**Overall Impact: MIXED**\n\n"
                
                if impacts["positive"]:
                    blog_content += "**Beneficial NPRRs:**\n"
                    for nprr_id, title, score in impacts["positive"][:3]:
                        blog_content += f"- {nprr_id}: {title} (+{score})\n"
                    blog_content += "\n"
                
                if impacts["negative"]:
                    blog_content += "**Challenging NPRRs:**\n"
                    for nprr_id, title, score in impacts["negative"][:3]:
                        blog_content += f"- {nprr_id}: {title} ({score})\n"
                    blog_content += "\n"
        
        blog_content += """## Key Takeaways

1. **Battery Storage Continues to Win** - Multiple NPRRs continue to improve market access and compensation for energy storage
2. **Traditional Generation Faces Headwinds** - Increased performance requirements and penalties affect profitability
3. **Renewable Integration Accelerates** - Market rules increasingly accommodate variable renewable resources
4. **Grid Flexibility Rewarded** - Resources that can respond quickly to grid needs see improved opportunities

## Action Items for Asset Owners

- **Review your compliance obligations** under new weatherization and performance standards
- **Evaluate new revenue opportunities** in ancillary services markets
- **Update your bidding strategies** to account for rule changes
- **Consider technology upgrades** to meet new technical requirements

---

*This analysis is based on simplified keyword analysis. For detailed impacts on specific assets, consult with your market analyst or legal team.*
"""
        
        # Save blog post
        output_file = self.blog_dir / "technology_impact_analysis.md"
        with open(output_file, 'w') as f:
            f.write(blog_content)
        
        print(f"Blog post generated: {output_file}")
        return output_file
    
    def generate_weekly_summary(self):
        """Generate weekly summary of all NPRRs"""
        blog_content = f"""# ERCOT NPRR Weekly Digest

*Week of {datetime.now().strftime('%B %d, %Y')}*

## This Week's NPRR Activity

### New Pending NPRRs
Check our pending NPRR analysis for approval likelihood assessments.

### Recently Approved NPRRs
See our technology impact analysis for detailed breakdowns.

### Market Trends
- Continued focus on grid reliability post-Winter Storm Uri
- Increasing accommodation for renewable and storage resources
- Ongoing debates about cost allocation and market efficiency

## Looking Ahead

Key items to watch:
1. TAC meetings for pending NPRR discussions
2. Board decisions on controversial proposals
3. PUCT reviews of market structure changes

## Resources

- [ERCOT NPRR Page](https://www.ercot.com/mktrules/issues/nprr)
- [TAC Meeting Schedule](https://www.ercot.com/calendar)
- [Market Notices](https://www.ercot.com/services/comm/mkt_notices)

---

*Subscribe to energence.ai for detailed NPRR analysis and market insights.*
"""
        
        # Save blog post
        output_file = self.blog_dir / "weekly_summary.md"
        with open(output_file, 'w') as f:
            f.write(blog_content)
        
        print(f"Blog post generated: {output_file}")
        return output_file
    
    def generate_all_blogs(self):
        """Generate all blog posts"""
        print("Generating blog posts...")
        
        # Generate pending NPRR blog
        self.generate_pending_nprr_blog()
        
        # Generate technology impact blog if approved analysis exists
        if (self.analysis_dir / "nprr_approved_analysis_simple.json").exists():
            self.generate_technology_impact_blog()
        
        # Generate weekly summary
        self.generate_weekly_summary()
        
        print(f"\nAll blog posts generated in: {self.blog_dir}")
        
        # List generated files
        blog_files = list(self.blog_dir.glob("*.md"))
        if blog_files:
            print("\nGenerated blog posts:")
            for bf in blog_files:
                print(f"  - {bf.name}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate blog posts from NPRR analysis")
    parser.add_argument("--analysis-dir", default="nprr_analysis",
                       help="Directory containing analysis JSON files")
    
    args = parser.parse_args()
    
    generator = BlogGenerator(analysis_dir=args.analysis_dir)
    generator.generate_all_blogs()

if __name__ == "__main__":
    main()