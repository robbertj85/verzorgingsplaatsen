#!/usr/bin/env python3
"""
Extract detailed parking space data from OpenStreetMap.

This approach uses OSM's mapped parking spaces instead of computer vision,
then validates with satellite imagery.
"""

import json
import requests
from typing import List, Dict, Tuple
import time

# Maasvlakte Plaza coordinates (from earlier analysis)
MAASVLAKTE_PLAZA_CENTER = (51.929, 4.022)

def query_osm_parking_spaces(lat: float, lon: float, radius_m: int = 500) -> Dict:
    """
    Query OSM Overpass API for parking spaces around a location.

    Args:
        lat: Latitude
        lon: Longitude
        radius_m: Radius in meters

    Returns:
        OSM data with parking spaces
    """
    overpass_url = "https://overpass-api.de/api/interpreter"

    # Overpass QL query for parking spaces
    # Looking for:
    # - amenity=parking with capacity
    # - parking_space nodes
    # - parking areas/ways
    overpass_query = f"""
    [out:json][timeout:60];
    (
      // Parking areas
      way["amenity"="parking"](around:{radius_m},{lat},{lon});
      relation["amenity"="parking"](around:{radius_m},{lat},{lon});

      // Individual parking spaces
      node["amenity"="parking_space"](around:{radius_m},{lat},{lon});
      way["amenity"="parking_space"](around:{radius_m},{lat},{lon});

      // Parking aisles (for structure understanding)
      way["service"="parking_aisle"](around:{radius_m},{lat},{lon});

      // HGV parking specifically
      way["hgv"="designated"](around:{radius_m},{lat},{lon});
      node["hgv"="designated"](around:{radius_m},{lat},{lon});
    );
    out body;
    >;
    out skel qt;
    """

    print(f"Querying OSM Overpass API for parking around {lat}, {lon} (radius: {radius_m}m)...")

    response = requests.post(
        overpass_url,
        data={"data": overpass_query},
        timeout=90
    )

    response.raise_for_status()
    return response.json()

def extract_parking_info(osm_data: Dict) -> Dict:
    """
    Extract parking information from OSM data.

    Returns:
        Dictionary with parking statistics and features
    """
    elements = osm_data.get('elements', [])

    stats = {
        'parking_areas': [],
        'parking_spaces': [],
        'parking_aisles': [],
        'total_capacity': 0,
        'hgv_capacity': 0,
    }

    # Node lookup for building geometries
    nodes = {e['id']: e for e in elements if e['type'] == 'node'}

    for element in elements:
        tags = element.get('tags', {})

        # Parking areas
        if tags.get('amenity') == 'parking':
            capacity = tags.get('capacity', tags.get('capacity:hgv', 0))
            try:
                capacity = int(capacity)
            except (ValueError, TypeError):
                capacity = 0

            parking_area = {
                'id': element['id'],
                'type': element['type'],
                'name': tags.get('name', 'Unnamed'),
                'capacity': capacity,
                'capacity_hgv': tags.get('capacity:hgv', tags.get('capacity:truck', 'N/A')),
                'parking_type': tags.get('parking', 'surface'),
                'operator': tags.get('operator', 'Unknown'),
                'fee': tags.get('fee', 'Unknown'),
                'tags': tags,
            }

            # Get geometry if it's a way
            if element['type'] == 'way':
                node_ids = element.get('nodes', [])
                coords = []
                for node_id in node_ids:
                    if node_id in nodes:
                        node = nodes[node_id]
                        coords.append([node['lon'], node['lat']])
                parking_area['geometry'] = {
                    'type': 'Polygon',
                    'coordinates': [coords]
                }

            stats['parking_areas'].append(parking_area)
            stats['total_capacity'] += capacity

            if tags.get('hgv') == 'designated' or 'truck' in tags.get('name', '').lower():
                stats['hgv_capacity'] += capacity

        # Individual parking spaces
        elif tags.get('amenity') == 'parking_space':
            space = {
                'id': element['id'],
                'type': element['type'],
            }

            if element['type'] == 'node':
                space['geometry'] = {
                    'type': 'Point',
                    'coordinates': [element['lon'], element['lat']]
                }
            elif element['type'] == 'way':
                node_ids = element.get('nodes', [])
                coords = []
                for node_id in node_ids:
                    if node_id in nodes:
                        node = nodes[node_id]
                        coords.append([node['lon'], node['lat']])
                space['geometry'] = {
                    'type': 'Polygon',
                    'coordinates': [coords]
                }

            stats['parking_spaces'].append(space)

        # Parking aisles
        elif tags.get('service') == 'parking_aisle':
            stats['parking_aisles'].append({
                'id': element['id'],
                'type': element['type'],
            })

    return stats

def create_parking_geojson(parking_info: Dict, output_file: str = "maasvlakte_osm_parking.geojson"):
    """Create GeoJSON with all parking features."""
    features = []

    # Add parking areas as features
    for area in parking_info['parking_areas']:
        if 'geometry' in area:
            feature = {
                'type': 'Feature',
                'geometry': area['geometry'],
                'properties': {
                    'type': 'parking_area',
                    'name': area['name'],
                    'capacity': area['capacity'],
                    'capacity_hgv': area['capacity_hgv'],
                    'parking_type': area['parking_type'],
                    'operator': area['operator'],
                    'fee': area['fee'],
                }
            }
            features.append(feature)

    # Add individual parking spaces
    for space in parking_info['parking_spaces']:
        if 'geometry' in space:
            feature = {
                'type': 'Feature',
                'geometry': space['geometry'],
                'properties': {
                    'type': 'parking_space',
                }
            }
            features.append(feature)

    geojson = {
        'type': 'FeatureCollection',
        'features': features
    }

    with open(output_file, 'w') as f:
        json.dump(geojson, f, indent=2)

    print(f"\nGeoJSON saved to {output_file}")
    return geojson

def analyze_maasvlakte_plaza():
    """Main analysis for Maasvlakte Plaza."""
    print("="*80)
    print("MAASVLAKTE PLAZA - OSM PARKING ANALYSIS")
    print("="*80)
    print()

    lat, lon = MAASVLAKTE_PLAZA_CENTER

    # Query OSM with increasing radius if needed
    for radius in [300, 500, 800]:
        print(f"\nAttempt with {radius}m radius...")

        osm_data = query_osm_parking_spaces(lat, lon, radius_m=radius)
        parking_info = extract_parking_info(osm_data)

        print(f"\nResults found:")
        print(f"  Parking areas: {len(parking_info['parking_areas'])}")
        print(f"  Individual parking spaces: {len(parking_info['parking_spaces'])}")
        print(f"  Parking aisles: {len(parking_info['parking_aisles'])}")
        print(f"  Total declared capacity: {parking_info['total_capacity']}")
        print(f"  HGV capacity: {parking_info['hgv_capacity']}")

        if parking_info['parking_areas'] or parking_info['total_capacity'] > 0:
            break

        time.sleep(1)  # Rate limiting

    # Display detailed results
    print("\n" + "="*80)
    print("PARKING AREAS FOUND")
    print("="*80)

    for i, area in enumerate(parking_info['parking_areas'], 1):
        print(f"\n{i}. {area['name']}")
        print(f"   OSM ID: {area['id']} ({area['type']})")
        print(f"   Capacity: {area['capacity']} total")
        print(f"   HGV Capacity: {area['capacity_hgv']}")
        print(f"   Type: {area['parking_type']}")
        print(f"   Operator: {area['operator']}")
        print(f"   Fee: {area['fee']}")
        print(f"   Has geometry: {'Yes' if 'geometry' in area else 'No'}")

    # Create GeoJSON
    geojson = create_parking_geojson(parking_info)

    # Save detailed results
    with open('maasvlakte_osm_analysis.json', 'w') as f:
        json.dump(parking_info, f, indent=2)

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total parking areas mapped in OSM: {len(parking_info['parking_areas'])}")
    print(f"Total individual spaces mapped: {len(parking_info['parking_spaces'])}")
    print(f"Declared total capacity: {parking_info['total_capacity']} spaces")
    print(f"Declared HGV capacity: {parking_info['hgv_capacity']} spaces")
    print()
    print("Files created:")
    print("  - maasvlakte_osm_analysis.json (detailed data)")
    print("  - maasvlakte_osm_parking.geojson (map overlay)")
    print("="*80)

    return parking_info

if __name__ == "__main__":
    analyze_maasvlakte_plaza()
