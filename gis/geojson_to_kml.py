#!/usr/bin/env python3
"""
Convert GeoJSON files to KML format with styled placemarks.
"""

import json
import simplekml
from pathlib import Path
import geopandas as gpd
from typing import Dict, Any, List

def get_policy_color() -> str:
    """Get KML color for states with policy."""
    # KML colors are in AABBGGRR format (alpha, blue, green, red)
    return 'ff00ff00'  # Green with full opacity

def create_description(properties: Dict[str, Any]) -> str:
    """Create HTML description for KML placemark."""
    description = "<![CDATA[<table>"
    
    # Add all properties to description
    for key, value in properties.items():
        if key not in ['geometry', 'id'] and value:
            # Format key for display
            display_key = key.replace('_', ' ').title()
            
            # Handle different value types
            if isinstance(value, bool):
                value_str = "Yes" if value else "No"
            elif isinstance(value, (int, float)):
                value_str = str(value)
            elif value is None:
                value_str = "N/A"
            else:
                value_str = str(value)[:200]  # Limit string length
            
            description += f"<tr><td><b>{display_key}:</b></td><td>{value_str}</td></tr>"
    
    description += "</table>]]>"
    return description

def geojson_to_kml(geojson_file: str, kml_file: str):
    """Convert a GeoJSON file to KML format."""
    print(f"Converting {geojson_file} to KML...")
    
    # Read GeoJSON
    gdf = gpd.read_file(geojson_file)
    
    # Create KML object
    kml = simplekml.Kml(name=Path(geojson_file).stem.replace('_', ' ').title())
    
    # Create a folder for the features
    folder = kml.newfolder(name="States")
    
    # Process each feature
    for idx, row in gdf.iterrows():
        # Get state name
        state_name = row.get('name', row.get('NAME', f'Feature {idx}'))
        
        # Create placemark - use kml.newmultigeometry directly
        multi = kml.newmultigeometry(name=state_name)
        
        # Set description with all properties
        properties = row.to_dict()
        properties.pop('geometry', None)  # Remove geometry from properties
        multi.description = create_description(properties)
        
        # Handle geometry
        geometry = row.geometry
        
        if geometry.geom_type == 'Polygon':
            # Single polygon
            coords = []
            for x, y in geometry.exterior.coords:
                coords.append((x, y))
            
            polygon = multi.newpolygon()
            polygon.outerboundaryis = coords
            
            # Style the polygon
            polygon.style.polystyle.color = get_policy_color()
            polygon.style.polystyle.outline = 1
            polygon.style.linestyle.color = 'ff000000'  # Black outline
            polygon.style.linestyle.width = 2
            
        elif geometry.geom_type == 'MultiPolygon':
            # Multiple polygons
            for poly in geometry.geoms:
                coords = []
                for x, y in poly.exterior.coords:
                    coords.append((x, y))
                
                polygon = multi.newpolygon()
                polygon.outerboundaryis = coords
                
                # Style the polygon
                polygon.style.polystyle.color = get_policy_color()
                polygon.style.polystyle.outline = 1
                polygon.style.linestyle.color = 'ff000000'  # Black outline
                polygon.style.linestyle.width = 2
    
    # Add description
    kml.document.description = "States shown have the specified policy"
    
    # Save KML
    kml.save(kml_file)
    print(f"  Saved to {kml_file}")

def convert_all_geojson_to_kml(geojson_dir: str = 'geojson_maps', kml_dir: str = 'kml_maps'):
    """Convert all GeoJSON files in directory to KML."""
    geojson_path = Path(geojson_dir)
    kml_path = Path(kml_dir)
    
    # Create KML directory if it doesn't exist
    kml_path.mkdir(exist_ok=True)
    
    # Get all GeoJSON files
    geojson_files = list(geojson_path.glob('*.geojson'))
    
    print(f"Found {len(geojson_files)} GeoJSON files to convert")
    
    # Convert each file
    for geojson_file in geojson_files:
        kml_filename = geojson_file.stem + '.kml'
        kml_file = kml_path / kml_filename
        
        try:
            geojson_to_kml(str(geojson_file), str(kml_file))
        except Exception as e:
            print(f"  Error converting {geojson_file.name}: {e}")
    
    print(f"\nConverted {len(geojson_files)} files to KML format")
    print(f"KML files saved in {kml_dir}/")

def main():
    """Main function."""
    convert_all_geojson_to_kml()

if __name__ == "__main__":
    main()