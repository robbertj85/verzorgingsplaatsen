#!/usr/bin/env python3
"""
Extract all truck parking facilities and parking data for South Holland province.

This script:
1. Queries OSM Overpass API for truck parking in South Holland
2. Extracts all parking-related data (spaces, capacity, facilities)
3. Classifies parking by vehicle type
4. Generates comprehensive GeoJSON for visualization
"""

import json
import requests
from typing import List, Dict
import time

# South Holland province bounding box
SOUTH_HOLLAND_BBOX = {
    'south': 51.8,
    'west': 4.0,
    'north': 52.3,
    'east': 4.9
}

def query_osm_truck_parking_south_holland() -> Dict:
    """
    Query OSM Overpass API for all truck parking facilities in South Holland.

    Returns:
        OSM data with truck parking facilities
    """
    overpass_url = "https://overpass-api.de/api/interpreter"

    bbox_str = f"{SOUTH_HOLLAND_BBOX['south']},{SOUTH_HOLLAND_BBOX['west']},{SOUTH_HOLLAND_BBOX['north']},{SOUTH_HOLLAND_BBOX['east']}"

    overpass_query = f"""
    [out:json][timeout:180][bbox:{bbox_str}];
    (
      // Truck parking facilities
      node["amenity"="parking"]["hgv"="designated"];
      way["amenity"="parking"]["hgv"="designated"];
      relation["amenity"="parking"]["hgv"="designated"];

      node["amenity"="parking"]["hgv"="yes"];
      way["amenity"="parking"]["hgv"="yes"];
      relation["amenity"="parking"]["hgv"="yes"];

      // Rest areas (often have truck parking)
      node["highway"="rest_area"];
      way["highway"="rest_area"];
      relation["highway"="rest_area"];

      node["highway"="services"];
      way["highway"="services"];
      relation["highway"="services"];

      // Truck stops
      node["amenity"="truck_stop"];
      way["amenity"="truck_stop"];

      // Parking with HGV capacity
      node["amenity"="parking"]["capacity:hgv"];
      way["amenity"="parking"]["capacity:hgv"];
      relation["amenity"="parking"]["capacity:hgv"];

      // Parking spaces with HGV designation
      way["amenity"="parking_space"]["hgv"="designated"];
      way["amenity"="parking_space"]["hgv"="yes"];
    );
    out body;
    >;
    out skel qt;
    """

    print(f"Querying OSM for truck parking in South Holland...")
    print(f"Bounding box: {bbox_str}")

    try:
        response = requests.post(
            overpass_url,
            data={"data": overpass_query},
            timeout=240
        )
        response.raise_for_status()
        data = response.json()
        print(f"✓ Retrieved {len(data.get('elements', []))} OSM elements")
        return data
    except Exception as e:
        print(f"✗ Error querying OSM: {e}")
        return {'elements': []}

def extract_parking_features(osm_data: Dict) -> List[Dict]:
    """
    Extract and process parking features from OSM data.

    Args:
        osm_data: Raw OSM data

    Returns:
        List of processed parking features
    """
    elements = osm_data.get('elements', [])
    nodes_dict = {el['id']: el for el in elements if el['type'] == 'node'}

    features = []
    processed_ids = set()

    for element in elements:
        if element['id'] in processed_ids:
            continue

        if element['type'] not in ['node', 'way', 'relation']:
            continue

        tags = element.get('tags', {})

        # Skip if not parking-related
        if not any([
            tags.get('amenity') == 'parking',
            tags.get('highway') in ['rest_area', 'services'],
            tags.get('amenity') == 'truck_stop',
            tags.get('amenity') == 'parking_space'
        ]):
            continue

        # Get coordinates
        lat, lon = None, None
        if element['type'] == 'node':
            lat, lon = element.get('lat'), element.get('lon')
        elif element['type'] == 'way' and 'nodes' in element:
            # Calculate centroid from way nodes
            way_lats = []
            way_lons = []
            for node_id in element['nodes']:
                if node_id in nodes_dict:
                    way_lats.append(nodes_dict[node_id]['lat'])
                    way_lons.append(nodes_dict[node_id]['lon'])
            if way_lats and way_lons:
                lat = sum(way_lats) / len(way_lats)
                lon = sum(way_lons) / len(way_lons)

        if not lat or not lon:
            continue

        # Extract facility info
        feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [lon, lat]
            },
            'properties': {
                'osm_id': element['id'],
                'osm_type': element['type'],
                'name': tags.get('name', f"Parking {element['id']}"),
                'amenity': tags.get('amenity'),
                'highway': tags.get('highway'),
                'hgv': tags.get('hgv'),
                'capacity': tags.get('capacity'),
                'capacity_hgv': tags.get('capacity:hgv', tags.get('capacity:truck')),
                'capacity_car': tags.get('capacity:car'),
                'operator': tags.get('operator'),
                'access': tags.get('access'),
                'parking': tags.get('parking'),
                'surface': tags.get('surface'),
                'fee': tags.get('fee'),
                'supervised': tags.get('supervised'),
                'lat': lat,
                'lon': lon
            }
        }

        features.append(feature)
        processed_ids.add(element['id'])

    return features

def main():
    """Main extraction pipeline for South Holland."""
    print("="*80)
    print("SOUTH HOLLAND TRUCK PARKING EXTRACTION")
    print("="*80)

    # Query OSM
    osm_data = query_osm_truck_parking_south_holland()

    # Extract features
    print("\nProcessing OSM data...")
    features = extract_parking_features(osm_data)

    print(f"✓ Extracted {len(features)} truck parking facilities")

    # Create GeoJSON
    geojson = {
        'type': 'FeatureCollection',
        'features': features
    }

    # Save to file
    output_file = 'south_holland_truck_parking.geojson'
    with open(output_file, 'w') as f:
        json.dump(geojson, f, indent=2)

    print(f"\n✓ Saved to: {output_file}")

    # Summary statistics
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total facilities: {len(features)}")

    # Count by type
    by_type = {}
    for feature in features:
        props = feature['properties']
        ftype = props.get('highway') or props.get('amenity', 'unknown')
        by_type[ftype] = by_type.get(ftype, 0) + 1

    print("\nBy type:")
    for ftype, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
        print(f"  {ftype}: {count}")

    # Facilities with capacity data
    with_capacity = sum(1 for f in features if f['properties'].get('capacity'))
    with_hgv_capacity = sum(1 for f in features if f['properties'].get('capacity_hgv'))
    print(f"\nWith capacity data: {with_capacity}")
    print(f"With HGV capacity data: {with_hgv_capacity}")

if __name__ == "__main__":
    main()
