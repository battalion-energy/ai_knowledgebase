#!/usr/bin/env python3
"""
ERCOT NOGRR Downloader
Downloads and catalogs all ERCOT NOGRRs with their documents
"""

import os
import json
import time
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NOGRRDownloader:
    def __init__(self, base_dir: str = None):
        self.base_url = "https://www.ercot.com"
        self.list_url = "https://www.ercot.com/mktrules/issues/reports/nogrr/approved"
        if base_dir is None:
            base_dir = "/pool/ssd8tb/data/iso/ERCOT/market_rules/nogrr/nogrr_data"
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def get_nogrr_list(self) -> List[Dict]:
        """Fetch the list of all approved NOGRRs"""
        logger.info("Fetching NOGRR list...")
        response = self.session.get(self.list_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        nogrrs = []
        
        # Find the main table
        table = soup.find('table')
        if not table:
            logger.error("Could not find NOGRR table")
            return nogrrs
            
        rows = table.find_all('tr')[1:]  # Skip header
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 9:
                continue
                
            # Extract NOGRR link and ID
            link_cell = cells[0]
            link = link_cell.find('a')
            if not link:
                continue
                
            nogrr_id = link.text.strip()
            detail_url = urljoin(self.base_url, link.get('href', ''))
            
            nogrr_info = {
                'id': nogrr_id,
                'detail_url': detail_url,
                'title': cells[1].text.strip() if len(cells) > 1 else '',
                'description': cells[2].text.strip() if len(cells) > 2 else '',
                'date_posted': cells[3].text.strip() if len(cells) > 3 else '',
                'sponsor': cells[4].text.strip() if len(cells) > 4 else '',
                'urgent': cells[5].text.strip() if len(cells) > 5 else '',
                'protocol_sections': cells[6].text.strip() if len(cells) > 6 else '',
                'status': cells[7].text.strip() if len(cells) > 7 else '',
                'effective_date': cells[8].text.strip() if len(cells) > 8 else ''
            }
            
            nogrrs.append(nogrr_info)
            
        logger.info(f"Found {len(nogrrs)} NOGRRs")
        return nogrrs
    
    def get_nogrr_details(self, nogrr: Dict) -> Dict:
        """Fetch detailed information for a specific NOGRR"""
        logger.info(f"Fetching details for {nogrr['id']}...")
        
        try:
            response = self.session.get(nogrr['detail_url'])
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to fetch {nogrr['id']}: {e}")
            return nogrr
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract sections
        nogrr['summary'] = self._extract_section(soup, ['summary', 'Summary'])
        nogrr['action'] = self._extract_section(soup, ['action', 'Action', 'Timeline'])
        nogrr['background'] = self._extract_section(soup, ['background', 'Background'])
        nogrr['voting_record'] = self._extract_section(soup, ['voting', 'Voting Record'])
        
        # Extract document links
        nogrr['documents'] = self._extract_documents(soup)
        
        return nogrr
    
    def _extract_section(self, soup: BeautifulSoup, keywords: List[str]) -> str:
        """Extract a specific section from the NOGRR page"""
        text_content = []
        
        # Try finding by headers
        for keyword in keywords:
            # Look for headers containing the keyword
            headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            for header in headers:
                if keyword.lower() in header.text.lower():
                    # Get the next sibling content
                    next_elem = header.find_next_sibling()
                    while next_elem and next_elem.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        if next_elem.name in ['p', 'div', 'ul', 'ol', 'table']:
                            text_content.append(next_elem.get_text(strip=True))
                        next_elem = next_elem.find_next_sibling()
                    
            # Also try finding by class or id
            for attr in ['class', 'id']:
                element = soup.find(attrs={attr: re.compile(keyword, re.I)})
                if element:
                    text_content.append(element.get_text(strip=True))
                    
        return '\n'.join(text_content)
    
    def _extract_documents(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract all document links from the NOGRR page"""
        documents = []
        
        # Find all links to documents
        doc_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.txt']
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href', '')
            link_text = link.get_text(strip=True)
            
            # Check if it's a document link
            if any(ext in href.lower() for ext in doc_extensions):
                doc_url = urljoin(self.base_url, href)
                doc_name = link_text or os.path.basename(urlparse(doc_url).path)
                
                documents.append({
                    'name': doc_name,
                    'url': doc_url,
                    'type': self._get_doc_type(doc_url)
                })
                
        return documents
    
    def _get_doc_type(self, url: str) -> str:
        """Determine document type from URL"""
        url_lower = url.lower()
        if '.pdf' in url_lower:
            return 'pdf'
        elif '.doc' in url_lower or '.docx' in url_lower:
            return 'word'
        elif '.xls' in url_lower or '.xlsx' in url_lower:
            return 'excel'
        elif '.zip' in url_lower:
            return 'zip'
        elif '.txt' in url_lower:
            return 'text'
        else:
            return 'other'
    
    def download_documents(self, nogrr: Dict) -> None:
        """Download all documents for a NOGRR"""
        if not nogrr.get('documents'):
            return
            
        # Create directory for this NOGRR
        nogrr_dir = self.base_dir / f"{nogrr['id']}_documents"
        nogrr_dir.mkdir(exist_ok=True)
        
        for doc in nogrr['documents']:
            try:
                logger.info(f"Downloading {doc['name']} for {nogrr['id']}...")
                response = self.session.get(doc['url'], stream=True)
                response.raise_for_status()
                
                # Generate safe filename
                filename = re.sub(r'[^\w\s.-]', '', doc['name'])
                if not filename:
                    filename = f"document_{doc['type']}"
                    
                # Add extension if missing
                if not any(filename.endswith(ext) for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.txt']):
                    ext_map = {
                        'pdf': '.pdf',
                        'word': '.docx',
                        'excel': '.xlsx',
                        'zip': '.zip',
                        'text': '.txt'
                    }
                    filename += ext_map.get(doc['type'], '')
                
                filepath = nogrr_dir / filename
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        
                doc['local_path'] = str(filepath)
                logger.info(f"Saved to {filepath}")
                
            except Exception as e:
                logger.error(f"Failed to download {doc['name']}: {e}")
                doc['download_error'] = str(e)
            
            time.sleep(0.5)  # Be polite to the server
    
    def save_nogrr_data(self, nogrr: Dict) -> None:
        """Save NOGRR data to JSON file"""
        json_path = self.base_dir / f"{nogrr['id']}.json"
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(nogrr, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Saved {nogrr['id']} data to {json_path}")
    
    def process_all_nogrrs(self, limit: Optional[int] = None) -> None:
        """Process all NOGRRs"""
        nogrrs = self.get_nogrr_list()
        
        # Sort by date (most recent first)
        nogrrs.sort(key=lambda x: x.get('date_posted', ''), reverse=True)
        
        if limit:
            nogrrs = nogrrs[:limit]
            
        catalog = []
        
        for i, nogrr in enumerate(nogrrs, 1):
            logger.info(f"Processing {i}/{len(nogrrs)}: {nogrr['id']}")
            
            # Get detailed information
            nogrr = self.get_nogrr_details(nogrr)
            
            # Download documents
            self.download_documents(nogrr)
            
            # Save individual NOGRR data
            self.save_nogrr_data(nogrr)
            
            # Add to catalog
            catalog.append({
                'id': nogrr['id'],
                'title': nogrr.get('title', ''),
                'description': nogrr.get('description', ''),
                'date_posted': nogrr.get('date_posted', ''),
                'sponsor': nogrr.get('sponsor', ''),
                'status': nogrr.get('status', ''),
                'effective_date': nogrr.get('effective_date', ''),
                'json_file': f"{nogrr['id']}.json",
                'documents_folder': f"{nogrr['id']}_documents"
            })
            
            # Rate limiting
            time.sleep(1)
        
        # Save master catalog
        catalog_path = self.base_dir / "nogrr_catalog.json"
        with open(catalog_path, 'w', encoding='utf-8') as f:
            json.dump({
                'generated': datetime.now().isoformat(),
                'total_nogrrs': len(catalog),
                'nogrrs': catalog
            }, f, indent=2)
            
        logger.info(f"Catalog saved to {catalog_path}")
        logger.info(f"Completed processing {len(catalog)} NOGRRs")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Download ERCOT NOGRRs')
    parser.add_argument('--limit', type=int, help='Limit number of NOGRRs to process')
    parser.add_argument('--output-dir', default=None, help='Output directory (default: /pool/ssd8tb/data/iso/ERCOT/market_rules/nogrr/nogrr_data)')
    
    args = parser.parse_args()
    
    downloader = NOGRRDownloader(base_dir=args.output_dir)
    downloader.process_all_nogrrs(limit=args.limit)

if __name__ == "__main__":
    main()