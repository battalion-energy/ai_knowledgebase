#!/usr/bin/env python3
import re
import os
import time
import requests
from pathlib import Path
from urllib.parse import urlparse

def extract_urls_from_markdown(file_path):
    """Extract all file URLs from the markdown file"""
    urls_by_ktc = {}
    current_ktc = None
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to find KTC sections
    ktc_pattern = r'### KTC (\d+):'
    # Pattern to find URLs
    url_pattern = r'URL: (https://[^\s]+)'
    
    lines = content.split('\n')
    for line in lines:
        # Check for KTC section
        ktc_match = re.search(ktc_pattern, line)
        if ktc_match:
            current_ktc = f"ktc{ktc_match.group(1)}"
            if current_ktc not in urls_by_ktc:
                urls_by_ktc[current_ktc] = []
        
        # Check for URL
        url_match = re.search(url_pattern, line)
        if url_match and current_ktc:
            urls_by_ktc[current_ktc].append(url_match.group(1))
    
    return urls_by_ktc

def download_file(url, output_path, retry=3):
    """Download a file with retry logic"""
    for attempt in range(retry):
        try:
            print(f"  Downloading: {os.path.basename(output_path)}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            print(f"  ✓ Downloaded: {os.path.basename(output_path)}")
            return True
            
        except Exception as e:
            print(f"  ✗ Attempt {attempt+1} failed: {e}")
            if attempt < retry - 1:
                time.sleep(2)
    
    return False

def main():
    # Read the markdown file
    base_dir = "/pool/ssd8tb/data/iso/ERCOT/market_info/energy_storage_resources/"
    md_file = f'{base_dir}ERCOT_BES_KTC_Downloadable_Resources.md'
    urls_by_ktc = extract_urls_from_markdown(md_file)
    
    # Statistics
    total_files = sum(len(urls) for urls in urls_by_ktc.values())
    downloaded = 0
    failed = []
    
    print(f"Found {total_files} files to download across {len(urls_by_ktc)} KTC sections")
    print("="*60)
    
    # Download files for each KTC
    for ktc, urls in sorted(urls_by_ktc.items()):
        if not urls:
            continue
            
        print(f"\nProcessing {ktc.upper()} ({len(urls)} files)")
        print("-"*40)
        
        download_dir = Path(f"{base_dir}downloads/{ktc}")
        download_dir.mkdir(parents=True, exist_ok=True)
        
        for url in urls:
            # Extract filename from URL
            parsed = urlparse(url)
            filename = os.path.basename(parsed.path)
            
            # Clean filename
            if not filename or filename == '':
                filename = f"document_{len(os.listdir(download_dir))+1}.file"
            
            output_path = download_dir / filename
            
            # Skip if already downloaded
            if output_path.exists():
                print(f"  ⊙ Skipping (already exists): {filename}")
                downloaded += 1
                continue
            
            # Download the file
            if download_file(url, output_path):
                downloaded += 1
            else:
                failed.append((ktc, url))
            
            # Small delay between downloads
            time.sleep(0.5)
    
    # Summary
    print("\n" + "="*60)
    print("DOWNLOAD SUMMARY")
    print("="*60)
    print(f"Total files: {total_files}")
    print(f"Successfully downloaded: {downloaded}")
    print(f"Failed: {len(failed)}")
    
    if failed:
        print("\nFailed downloads:")
        for ktc, url in failed:
            print(f"  - {ktc}: {url}")
    
    # Create a summary file
    with open(f'{base_dir}download_summary.txt', 'w') as f:
        f.write(f"ERCOT ESR Files Download Summary\n")
        f.write(f"{'='*40}\n")
        f.write(f"Total files: {total_files}\n")
        f.write(f"Downloaded: {downloaded}\n")
        f.write(f"Failed: {len(failed)}\n\n")
        
        for ktc in sorted(urls_by_ktc.keys()):
            download_dir = Path(f"{base_dir}downloads/{ktc}")
            if download_dir.exists():
                files = list(download_dir.glob('*'))
                f.write(f"\n{ktc.upper()}: {len(files)} files\n")
                for file in sorted(files):
                    f.write(f"  - {file.name}\n")

if __name__ == "__main__":
    main()