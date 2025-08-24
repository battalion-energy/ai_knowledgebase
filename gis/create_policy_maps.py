#!/usr/bin/env python3
"""
Create GeoJSON maps with policy information embedded in state polygons.
"""

import json
import geopandas as gpd
from pathlib import Path
from typing import Dict, Any, List

def load_policy_data(json_file: str) -> Dict[str, Any]:
    """Load policy data from JSON file."""
    with open(json_file, 'r') as f:
        return json.load(f)

def load_states_geojson(geojson_file: str) -> gpd.GeoDataFrame:
    """Load US states GeoJSON as GeoDataFrame."""
    gdf = gpd.read_file(geojson_file)
    return gdf

def merge_policy_with_states(states_gdf: gpd.GeoDataFrame, policy_data: Dict[str, Any]) -> gpd.GeoDataFrame:
    """Merge policy data with state geometries."""
    # Create a copy of the GeoDataFrame
    result_gdf = states_gdf.copy()
    
    # Initialize policy columns
    policy_types = set()
    for state_policies in policy_data.values():
        policy_types.update(state_policies.keys())
    
    # Add policy information to each state
    for idx, row in result_gdf.iterrows():
        state_name = row.get('name', row.get('NAME', ''))
        
        if state_name in policy_data:
            state_policies = policy_data[state_name]
            
            # Add each policy type as a property
            for policy_type, policy_info in state_policies.items():
                # Create column names based on policy type
                col_name = policy_type.replace(' ', '_').replace('-', '_')
                result_gdf.at[idx, f'has_{col_name}'] = True
                result_gdf.at[idx, f'{col_name}_details'] = policy_info.get('policy_details', '')
        else:
            # Mark as no policy data available
            for policy_type in policy_types:
                col_name = policy_type.replace(' ', '_').replace('-', '_')
                result_gdf.at[idx, f'has_{col_name}'] = False
                result_gdf.at[idx, f'{col_name}_details'] = ''
    
    return result_gdf

def create_policy_specific_maps(states_gdf: gpd.GeoDataFrame, policy_data: Dict[str, Any]) -> Dict[str, gpd.GeoDataFrame]:
    """Create separate GeoJSON for each policy type, including only states with that policy."""
    policy_maps = {}
    
    # Get all unique policy types
    policy_types = set()
    for state_policies in policy_data.values():
        policy_types.update(state_policies.keys())
    
    # Create a map for each policy type
    for policy_type in policy_types:
        # Start with empty list to collect states with this policy
        states_with_policy = []
        
        # Check each state
        for idx, row in states_gdf.iterrows():
            state_name = row.get('name', row.get('NAME', ''))
            
            if state_name in policy_data and policy_type in policy_data[state_name]:
                # State has this policy - add it to the list
                policy_info = policy_data[state_name][policy_type]
                row_copy = row.copy()
                row_copy['has_policy'] = True
                row_copy['policy_details'] = policy_info.get('policy_details', '')
                row_copy['policy_type'] = policy_type
                states_with_policy.append(row_copy)
        
        # Create GeoDataFrame only with states that have this policy
        if states_with_policy:
            policy_gdf = gpd.GeoDataFrame(states_with_policy, crs=states_gdf.crs)
            policy_maps[policy_type] = policy_gdf
            print(f"  {policy_type}: {len(policy_gdf)} states with policy")
    
    return policy_maps

def save_geojson_maps(policy_maps: Dict[str, gpd.GeoDataFrame], output_dir: str = 'geojson_maps'):
    """Save GeoJSON maps to files."""
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    for policy_type, gdf in policy_maps.items():
        # Create filename from policy type
        filename = policy_type.lower().replace(' ', '_').replace('-', '_') + '.geojson'
        filepath = Path(output_dir) / filename
        
        # Save to GeoJSON
        gdf.to_file(filepath, driver='GeoJSON')
        print(f"Saved {policy_type} map to {filepath}")

def create_combined_map(states_gdf: gpd.GeoDataFrame, policy_data: Dict[str, Any]) -> gpd.GeoDataFrame:
    """Create a combined map with all policies, including only states that have at least one policy."""
    states_with_policies = []
    
    # Check each state
    for idx, row in states_gdf.iterrows():
        state_name = row.get('name', row.get('NAME', ''))
        
        if state_name in policy_data:
            state_policies = policy_data[state_name]
            
            # State has policies - add it to the list
            row_copy = row.copy()
            
            # Create a summary of all policies
            policy_list = list(state_policies.keys())
            row_copy['num_policies'] = len(policy_list)
            row_copy['policy_types'] = ', '.join(policy_list)
            
            # Add individual policy details as nested JSON
            row_copy['all_policies'] = json.dumps(state_policies)
            
            states_with_policies.append(row_copy)
    
    # Create GeoDataFrame only with states that have policies
    if states_with_policies:
        combined_gdf = gpd.GeoDataFrame(states_with_policies, crs=states_gdf.crs)
        print(f"  Combined map: {len(combined_gdf)} states with at least one policy")
        return combined_gdf
    else:
        return gpd.GeoDataFrame()

def main():
    """Main function to create policy maps."""
    # File paths
    policy_json = 'dsire_policies.json'
    states_geojson = 'us_states.geojson'
    output_dir = 'geojson_maps'
    
    print("Loading data...")
    # Load policy data
    policy_data = load_policy_data(policy_json)
    
    # Load states GeoJSON
    states_gdf = load_states_geojson(states_geojson)
    
    print(f"Loaded {len(policy_data)} states with policy data")
    print(f"Loaded {len(states_gdf)} state geometries")
    
    # Create policy-specific maps
    print("\nCreating policy-specific maps...")
    policy_maps = create_policy_specific_maps(states_gdf, policy_data)
    
    # Save individual policy maps
    save_geojson_maps(policy_maps, output_dir)
    
    # Create and save combined map
    print("\nCreating combined map with all policies...")
    combined_map = create_combined_map(states_gdf, policy_data)
    combined_filepath = Path(output_dir) / 'all_policies_combined.geojson'
    combined_map.to_file(combined_filepath, driver='GeoJSON')
    print(f"Saved combined map to {combined_filepath}")
    
    # Print summary
    print(f"\nGenerated {len(policy_maps) + 1} GeoJSON maps:")
    print(f"  - {len(policy_maps)} policy-specific maps")
    print(f"  - 1 combined map with all policies")
    
    # Show policy types
    print("\nPolicy types mapped:")
    for policy_type in sorted(policy_maps.keys()):
        print(f"  - {policy_type}")

if __name__ == "__main__":
    main()