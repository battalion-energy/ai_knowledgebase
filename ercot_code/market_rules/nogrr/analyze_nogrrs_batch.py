#!/usr/bin/env python3
"""
Batch analyzer for specific NOGRRs
"""

import argparse
import sys
from pathlib import Path
import logging
from analyze_nogrrs import NOGRRAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Batch analyze specific NOGRRs')
    base_dir = "/pool/ssd8tb/data/iso/ERCOT/market_rules/nogrr/"
    parser.add_argument('--data-dir', default=f'{base_dir}/nogrr_data', help='Directory with NOGRR data')
    parser.add_argument('--output-dir', default=f'{base_dir}/nogrr_analysis', help='Output directory')
    parser.add_argument('--ids-file', help='File containing NOGRR IDs to analyze (one per line)')
    parser.add_argument('--ids', nargs='+', help='NOGRR IDs to analyze')
    
    args = parser.parse_args()
    
    # Get list of IDs to process
    nogrr_ids = []
    
    if args.ids_file:
        ids_path = Path(args.ids_file)
        if ids_path.exists():
            with open(ids_path, 'r') as f:
                nogrr_ids.extend([line.strip() for line in f if line.strip()])
    
    if args.ids:
        nogrr_ids.extend(args.ids)
    
    if not nogrr_ids:
        # Read from stdin if no arguments provided
        for line in sys.stdin:
            line = line.strip()
            if line:
                nogrr_ids.append(line)
    
    if not nogrr_ids:
        logger.error("No NOGRR IDs provided")
        return 1
    
    logger.info(f"Analyzing {len(nogrr_ids)} NOGRRs")
    
    # Initialize analyzer
    analyzer = NOGRRAnalyzer(data_dir=args.data_dir, output_dir=args.output_dir)
    
    # Analyze each NOGRR
    success_count = 0
    failed = []
    
    for i, nogrr_id in enumerate(nogrr_ids, 1):
        logger.info(f"Processing {i}/{len(nogrr_ids)}: {nogrr_id}")
        try:
            analyzer.analyze_nogrr(nogrr_id)
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to analyze {nogrr_id}: {e}")
            failed.append(nogrr_id)
    
    logger.info(f"Successfully analyzed {success_count}/{len(nogrr_ids)} NOGRRs")
    
    if failed:
        logger.warning(f"Failed NOGRRs: {', '.join(failed)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())