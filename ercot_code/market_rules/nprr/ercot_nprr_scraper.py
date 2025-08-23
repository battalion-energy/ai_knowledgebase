#!/usr/bin/env python3
"""
ERCOT NPRR Scraper and Downloader
Downloads and catalogs all approved NPRRs from ERCOT website
"""

import os
import json
import time
import logging
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ERCOTNPRRScraper:
    def __init__(self, base_dir: str = "nprr_data", status: str = "approved"):
        self.status = status
        if status == "approved":
            self.base_url = "https://www.ercot.com/mktrules/issues/reports/nprr/approved"
        elif status == "pending":
            self.base_url = "https://www.ercot.com/mktrules/issues/reports/nprr/pending"
        elif status == "rejected":
            self.base_url = "https://www.ercot.com/mktrules/issues/reports/nprr/rejected"
        else:
            raise ValueError("Status must be 'approved', 'pending', or 'rejected'")
        
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.catalog_file = self.base_dir / f"nprr_{status}_catalog.json"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def load_existing_catalog(self) -> Dict:
        """Load existing catalog if it exists"""
        if self.catalog_file.exists():
            with open(self.catalog_file, 'r') as f:
                return json.load(f)
        return {"nprrs": {}, "last_updated": None}
    
    def save_catalog(self, catalog: Dict):
        """Save catalog to JSON file"""
        catalog["last_updated"] = datetime.now().isoformat()
        with open(self.catalog_file, 'w') as f:
            json.dump(catalog, f, indent=2)
        logger.info(f"Catalog saved to {self.catalog_file}")
    
    def get_nprr_list(self) -> List[Dict]:
        """Get list of all NPRRs from the main page"""
        logger.info(f"Fetching NPRR list from {self.base_url}")
        
        try:
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch NPRR list: {e}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        nprrs = []
        
        # Find the table with NPRRs
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')[1:]  # Skip header
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 4:
                    nprr_link = cells[0].find('a')
                    if nprr_link:
                        nprr_id = nprr_link.text.strip()
                        nprr_url = urljoin(self.base_url, nprr_link.get('href', ''))
                        title = cells[1].text.strip()
                        status = cells[2].text.strip()
                        date = cells[3].text.strip()
                        
                        nprrs.append({
                            'id': nprr_id,
                            'url': nprr_url,
                            'title': title,
                            'status': status,
                            'approval_date': date
                        })
        
        # Sort by NPRR number (most recent first)
        nprrs.sort(key=lambda x: int(re.sub(r'\D', '', x['id'])), reverse=True)
        logger.info(f"Found {len(nprrs)} NPRRs")
        return nprrs
    
    def scrape_nprr_details(self, nprr: Dict) -> Dict:
        """Scrape detailed information for a specific NPRR"""
        logger.info(f"Scraping details for {nprr['id']}")
        
        try:
            response = self.session.get(nprr['url'], timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {nprr['id']}: {e}")
            return nprr
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract key sections
        details = {
            **nprr,
            'summary': '',
            'action': '',
            'background': '',
            'documents': []
        }
        
        # Look for standard sections
        content = soup.get_text()
        
        # Extract Summary
        summary_match = re.search(r'Summary[:\s]+(.*?)(?=Action|Background|$)', content, re.DOTALL | re.IGNORECASE)
        if summary_match:
            details['summary'] = summary_match.group(1).strip()[:2000]  # Limit length
        
        # Extract Action
        action_match = re.search(r'Action[:\s]+(.*?)(?=Background|Summary|$)', content, re.DOTALL | re.IGNORECASE)
        if action_match:
            details['action'] = action_match.group(1).strip()[:2000]
        
        # Extract Background
        background_match = re.search(r'Background[:\s]+(.*?)(?=Action|Summary|Documents|$)', content, re.DOTALL | re.IGNORECASE)
        if background_match:
            details['background'] = background_match.group(1).strip()[:3000]
        
        # Find document links
        for link in soup.find_all('a'):
            href = link.get('href', '')
            text = link.text.strip()
            
            # Look for document links (PDFs, DOCs, etc.)
            if any(ext in href.lower() for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip']):
                doc_url = urljoin(nprr['url'], href)
                details['documents'].append({
                    'name': text or os.path.basename(urlparse(doc_url).path),
                    'url': doc_url,
                    'type': os.path.splitext(urlparse(doc_url).path)[1].lower()
                })
        
        return details
    
    def download_documents(self, nprr: Dict) -> List[str]:
        """Download all documents for an NPRR"""
        nprr_dir = self.base_dir / nprr['id'].replace('/', '_')
        nprr_dir.mkdir(exist_ok=True)
        
        downloaded = []
        for doc in nprr.get('documents', []):
            filename = f"{nprr['id']}_{doc['name']}".replace('/', '_').replace(' ', '_')
            filepath = nprr_dir / filename
            
            if filepath.exists():
                logger.info(f"Document already exists: {filename}")
                downloaded.append(str(filepath))
                continue
            
            try:
                logger.info(f"Downloading: {doc['name']}")
                response = self.session.get(doc['url'], timeout=60)
                response.raise_for_status()
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                downloaded.append(str(filepath))
                logger.info(f"Downloaded: {filename}")
                time.sleep(1)  # Be polite to the server
                
            except Exception as e:
                logger.error(f"Failed to download {doc['name']}: {e}")
        
        return downloaded
    
    def filter_by_years(self, nprr_list: List[Dict], years: int) -> List[Dict]:
        """Filter NPRRs by years from today"""
        if not years:
            return nprr_list
            
        cutoff_date = datetime.now() - timedelta(days=years * 365)
        filtered = []
        
        for nprr in nprr_list:
            # Try to parse the approval/submission date
            date_str = nprr.get('approval_date', '')
            if not date_str:
                continue
                
            try:
                # Try different date formats
                for fmt in ['%m/%d/%Y', '%m/%d/%y', '%Y-%m-%d']:
                    try:
                        nprr_date = datetime.strptime(date_str, fmt)
                        if nprr_date >= cutoff_date:
                            filtered.append(nprr)
                        break
                    except ValueError:
                        continue
            except Exception as e:
                logger.warning(f"Could not parse date for {nprr['id']}: {date_str}")
                
        logger.info(f"Filtered to {len(filtered)} NPRRs from last {years} years")
        return filtered
    
    def run(self, limit: Optional[int] = None, skip_existing: bool = True, years: Optional[int] = None):
        """Main scraping function"""
        catalog = self.load_existing_catalog()
        
        # Get list of NPRRs
        nprr_list = self.get_nprr_list()
        
        # Filter by years if specified
        if years:
            nprr_list = self.filter_by_years(nprr_list, years)
        
        if limit:
            nprr_list = nprr_list[:limit]
            logger.info(f"Processing {limit} most recent NPRRs")
        
        for i, nprr in enumerate(nprr_list, 1):
            logger.info(f"Processing {i}/{len(nprr_list)}: {nprr['id']}")
            
            # Skip if already processed
            if skip_existing and nprr['id'] in catalog.get('nprrs', {}):
                logger.info(f"Skipping {nprr['id']} (already in catalog)")
                continue
            
            # Scrape details
            details = self.scrape_nprr_details(nprr)
            
            # Download documents
            downloaded_files = self.download_documents(details)
            details['downloaded_files'] = downloaded_files
            
            # Add to catalog
            catalog['nprrs'][nprr['id']] = details
            
            # Save catalog after each NPRR (in case of interruption)
            self.save_catalog(catalog)
            
            # Be polite
            time.sleep(2)
        
        logger.info("Scraping completed!")
        return catalog

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape ERCOT NPRRs')
    parser.add_argument('--limit', type=int, help='Limit number of NPRRs to process')
    parser.add_argument('--output-dir', default='nprr_data', help='Output directory')
    parser.add_argument('--force', action='store_true', help='Re-download existing NPRRs')
    parser.add_argument('--status', choices=['approved', 'pending', 'rejected'], default='approved',
                       help='Download approved, pending, or rejected NPRRs')
    parser.add_argument('--years', type=int, help='Filter NPRRs from last N years')
    
    args = parser.parse_args()
    
    scraper = ERCOTNPRRScraper(base_dir=args.output_dir, status=args.status)
    catalog = scraper.run(limit=args.limit, skip_existing=not args.force, years=args.years)
    
    print(f"\nProcessed {len(catalog['nprrs'])} {args.status} NPRRs")
    print(f"Catalog saved to: {scraper.catalog_file}")

if __name__ == "__main__":
    main()