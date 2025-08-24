#!/usr/bin/env python3
"""
Extract policy information from DSIRE PDF maps and save to JSON files.
"""

import pdfplumber
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any

# State abbreviations to full names mapping
STATE_ABBR = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
    'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
    'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
    'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
    'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
    'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
    'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
    'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
    'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
    'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
    'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia',
    'PR': 'Puerto Rico', 'VI': 'Virgin Islands', 'GU': 'Guam'
}

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from a PDF file."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
    return text

def parse_state_policies(text: str, policy_type: str) -> Dict[str, Any]:
    """Parse state-specific policy information from extracted text."""
    state_data = {}
    
    # Try to identify states and their associated policies
    lines = text.split('\n')
    current_state = None
    current_policy = []
    
    for line in lines:
        # Check if line contains a state name or abbreviation
        for abbr, full_name in STATE_ABBR.items():
            if abbr in line or full_name in line:
                # Save previous state data if exists
                if current_state and current_policy:
                    policy_text = ' '.join(current_policy).strip()
                    if policy_text:
                        state_data[current_state] = {
                            'policy_type': policy_type,
                            'policy_details': policy_text[:500]  # Limit to 500 chars
                        }
                
                current_state = full_name
                current_policy = [line]
                break
        else:
            # Add to current state policy if we have an active state
            if current_state and line.strip():
                current_policy.append(line.strip())
    
    # Save last state data
    if current_state and current_policy:
        policy_text = ' '.join(current_policy).strip()
        if policy_text:
            state_data[current_state] = {
                'policy_type': policy_type,
                'policy_details': policy_text[:500]
            }
    
    return state_data

def get_policy_type_from_filename(filename: str) -> str:
    """Extract policy type from filename."""
    policy_map = {
        'Solar_Decommissioning': 'Solar Decommissioning Policies',
        'Energy_Storage_Targets': 'Energy Storage Targets',
        'Solar_Access_Laws': 'Solar Access and Easement Laws',
        'Energy_Storage_Incentives': 'Energy Storage Financial Incentives',
        'Offshore_Wind_Targets': 'Offshore Wind Energy Targets',
        'RPS_CES': 'Renewable Portfolio Standards and Clean Energy Standards',
        'Third_Party_PPA': 'Third-Party Solar Power Purchase Agreement Policies',
        'Net_Metering': 'Net Metering Policies',
        'DG_Credit_Rates': 'Distributed Generation Customer Credit Rates',
        'Energy_Efficiency_Standards': 'Energy Efficiency Resource Standards',
        'EV_Incentives': 'Passenger Electric Vehicle Incentives',
        'EVSE_Incentives': 'Electric Vehicle Charging Equipment Incentives',
        'Community_Solar_Rules': 'Community Solar Rules'
    }
    
    for key, value in policy_map.items():
        if key in filename:
            return value
    return 'Unknown Policy'

def process_all_pdfs(pdf_dir: str) -> Dict[str, Dict[str, Any]]:
    """Process all PDF files in the directory."""
    all_policies = {}
    pdf_files = list(Path(pdf_dir).glob('*.pdf'))
    
    print(f"Found {len(pdf_files)} PDF files to process")
    
    for pdf_file in pdf_files:
        print(f"Processing {pdf_file.name}...")
        
        # Extract text from PDF
        text = extract_text_from_pdf(str(pdf_file))
        
        if text:
            # Get policy type from filename
            policy_type = get_policy_type_from_filename(pdf_file.name)
            
            # Parse state policies
            state_policies = parse_state_policies(text, policy_type)
            
            # Merge with existing data
            for state, policy_data in state_policies.items():
                if state not in all_policies:
                    all_policies[state] = {}
                
                # Use policy type as key to allow multiple policies per state
                all_policies[state][policy_type] = policy_data
            
            print(f"  Extracted data for {len(state_policies)} states")
    
    return all_policies

def main():
    """Main function to extract PDF data and save to JSON."""
    pdf_dir = 'dsire_maps'
    output_file = 'dsire_policies.json'
    
    # Process all PDFs
    all_policies = process_all_pdfs(pdf_dir)
    
    # Save to JSON file
    with open(output_file, 'w') as f:
        json.dump(all_policies, f, indent=2)
    
    print(f"\nExtracted policy data for {len(all_policies)} states/territories")
    print(f"Saved to {output_file}")
    
    # Print summary
    print("\nSummary of extracted policies:")
    for state in sorted(all_policies.keys())[:5]:  # Show first 5 states
        print(f"\n{state}:")
        for policy_type in all_policies[state]:
            print(f"  - {policy_type}")

if __name__ == "__main__":
    main()