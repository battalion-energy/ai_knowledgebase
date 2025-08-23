#!/usr/bin/env python3
"""
Filter NOGRRs by date range for analysis
"""

import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_date(date_str: str) -> datetime:
    """Parse various date formats from NOGRR data"""
    formats = [
        '%m/%d/%Y',
        '%Y-%m-%d',
        '%B %d, %Y',
        '%b %d, %Y',
        '%d-%b-%Y'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    
    # If all formats fail, try to extract just the date part
    # Sometimes dates have extra text
    parts = date_str.strip().split()
    if len(parts) >= 3:
        date_part = ' '.join(parts[:3])
        for fmt in formats:
            try:
                return datetime.strptime(date_part, fmt)
            except ValueError:
                continue
    
    logger.warning(f"Could not parse date: {date_str}")
    return None

def filter_nogrrs_by_years(data_dir: str, years_back: int) -> list:
    """Filter NOGRRs from the past N years"""
    data_path = Path(data_dir)
    catalog_path = data_path / "nogrr_catalog.json"
    
    if not catalog_path.exists():
        logger.error(f"Catalog not found: {catalog_path}")
        return []
    
    with open(catalog_path, 'r') as f:
        catalog = json.load(f)
    
    cutoff_date = datetime.now() - timedelta(days=years_back * 365)
    logger.info(f"Filtering NOGRRs from {cutoff_date.strftime('%Y-%m-%d')} to present")
    
    filtered_nogrrs = []
    
    for nogrr in catalog.get('nogrrs', []):
        date_str = nogrr.get('date_posted', '')
        if not date_str:
            continue
            
        nogrr_date = parse_date(date_str)
        if nogrr_date and nogrr_date >= cutoff_date:
            filtered_nogrrs.append(nogrr['id'])
    
    logger.info(f"Found {len(filtered_nogrrs)} NOGRRs from the past {years_back} years")
    return filtered_nogrrs

def create_filtered_list_file(nogrr_ids: list, output_file: str):
    """Create a file with filtered NOGRR IDs for batch processing"""
    with open(output_file, 'w') as f:
        for nogrr_id in nogrr_ids:
            f.write(f"{nogrr_id}\n")
    logger.info(f"Saved {len(nogrr_ids)} NOGRR IDs to {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Filter NOGRRs by date range')
    base_dir = "/pool/ssd8tb/data/iso/ERCOT/market_rules/nogrr/"
    parser.add_argument('--data-dir', default=f'{base_dir}/nogrr_data', help='Directory with NOGRR data')
    parser.add_argument('--years', type=int, required=True, help='Number of years back to filter')
    parser.add_argument('--output', help='Output file for filtered NOGRR IDs')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    filtered_ids = filter_nogrrs_by_years(args.data_dir, args.years)
    
    if args.output:
        if args.json:
            with open(args.output, 'w') as f:
                json.dump({'nogrr_ids': filtered_ids, 'years_back': args.years}, f, indent=2)
        else:
            create_filtered_list_file(filtered_ids, args.output)
    else:
        # Print to stdout for use in pipelines
        for nogrr_id in filtered_ids:
            print(nogrr_id)
    
    return 0 if filtered_ids else 1

if __name__ == "__main__":
    exit(main())