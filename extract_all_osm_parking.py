#!/usr/bin/env python3
"""
Extract parking space data from OSM for all truck parking facilities,
with vehicle type classification.

This script:
1. Loads all truck parking facilities from the dataset
2. Queries OSM Overpass API for each facility
3. Extracts parking space data and capacity information
4. Classifies parking by vehicle type (car/van, truck, LZV)
5. Generates comprehensive GeoJSON overlay with classifications
"""

import json
import requests
from typing import List, Dict, Optional
import time
from pathlib import Path

# Rotterdam area bounding box (can be expanded)
ROTTERDAM_BBOX = {
    'south': 51.8,
    'west': 4.0,
    'north': 52.0,
    'east': 4.5
}

def query_osm_parking_for_facility(lat: float, lon: float, facility_name: str, radius_m: int = 300) -> Dict:
    """
    Query OSM Overpass API for parking spaces around a facility.

    Args:
        lat: Facility latitude
        lon: Facility longitude
        facility_name: Name of the facility
        radius_m: Search radius in meters

    Returns:
        OSM data with parking spaces
    """
    overpass_url = "https://overpass-api.de/api/interpreter"

    overpass_query = f"""
    [out:json][timeout:60];
    (
      // Parking areas
      way["amenity"="parking"](around:{radius_m},{lat},{lon});
      relation["amenity"="parking"](around:{radius_m},{lat},{lon});

      // Individual parking spaces
      way["amenity"="parking_space"](around:{radius_m},{lat},{lon});

      // Parking aisles
      way["service"="parking_aisle"](around:{radius_m},{lat},{lon});

      // HGV parking specifically
      way["hgv"="designated"](around:{radius_m},{lat},{lon});
      way["hgv"="yes"](around:{radius_m},{lat},{lon});
    );
    out body;
    >;
    out skel qt;
    """

    try:
        response = requests.post(
            overpass_url,
            data={"data": overpass_query},
            timeout=90
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  ⚠ Error querying OSM for {facility_name}: {e}")
        return {'elements': []}

def classify_parking_from_osm(tags: Dict) -> Dict:
    """
    Classify parking type from OSM tags.

    Args:
        tags: OSM element tags

    Returns:
        Classification info
    """
    # Check for HGV/truck designation
    is_hgv = (
        tags.get('hgv') in ['designated', 'yes'] or
        tags.get('capacity:hgv') or
        tags.get('capacity:truck') or
        'truck' in tags.get('name', '').lower() or
        'hgv' in tags.get('name', '').lower() or
        'vrachtwagen' in tags.get('name', '').lower()
    )

    # Check capacity tags
    capacity = tags.get('capacity', 0)
    capacity_hgv = tags.get('capacity:hgv', tags.get('capacity:truck', 0))
    capacity_car = tags.get('capacity:car', 0)

    try:
        capacity = int(capacity)
    except (ValueError, TypeError):
        capacity = 0

    try:
        capacity_hgv = int(capacity_hgv)
    except (ValueError, TypeError):
        capacity_hgv = 0

    try:
        capacity_car = int(capacity_car)
    except (ValueError, TypeError):
        capacity_car = 0

    # Determine vehicle type
    if is_hgv or capacity_hgv > 0:
        # Check if it could be LZV based on name or tags
        is_lzv = (
            'lzv' in tags.get('name', '').lower() or
            'lang zwaar' in tags.get('name', '').lower() or
            tags.get('maxlength', '0') == '25.25'
        )

        if is_lzv:
            vehicle_type = 'lzv'
            label = 'LZV Parking'
            color = '#7c2d12'  # dark brown
        else:
            vehicle_type = 'truck'
            label = 'Truck Parking'
            color = '#ef4444'  # red
    elif capacity_car > 0:
        vehicle_type = 'car'
        label = 'Car/Van Parking'
        color = '#3b82f6'  # blue
    else:
        # Default to truck if in our truck parking dataset
        vehicle_type = 'truck'
        label = 'Truck Parking'
        color = '#ef4444'

    return {
        'vehicle_type': vehicle_type,
        'label': label,
        'color': color,
        'capacity_total': capacity,
        'capacity_hgv': capacity_hgv,
        'capacity_car': capacity_car,
        'is_hgv': is_hgv
    }

def extract_parking_from_osm(osm_data: Dict, facility_id: str) -> Dict:
    """
    Extract and classify parking data from OSM response.

    Args:
        osm_data: OSM API response
        facility_id: ID of the facility being analyzed

    Returns:
        Structured parking data
    """
    elements = osm_data.get('elements', [])

    result = {
        'facility_id': facility_id,
        'osm_parking_areas': [],
        'osm_parking_spaces': [],
        'total_capacity': 0,
        'truck_capacity': 0,
        'car_capacity': 0,
        'lzv_capacity': 0,
        'has_osm_data': False
    }

    # Build node lookup for geometry construction
    nodes = {e['id']: e for e in elements if e['type'] == 'node'}

    for element in elements:
        tags = element.get('tags', {})

        # Parking areas
        if tags.get('amenity') == 'parking':
            result['has_osm_data'] = True
            classification = classify_parking_from_osm(tags)

            parking_area = {
                'osm_id': element['id'],
                'osm_type': element['type'],
                'name': tags.get('name', 'Unnamed Parking'),
                'operator': tags.get('operator', 'Unknown'),
                'fee': tags.get('fee', 'unknown'),
                'opening_hours': tags.get('opening_hours', '24/7'),
                'surface': tags.get('surface', 'paved'),
                'classification': classification,
                'tags': tags
            }

            # Extract geometry for ways
            if element['type'] == 'way' and 'nodes' in element:
                coords = []
                for node_id in element['nodes']:
                    if node_id in nodes:
                        node = nodes[node_id]
                        coords.append([node['lon'], node['lat']])

                if len(coords) >= 3:
                    parking_area['geometry'] = {
                        'type': 'Polygon',
                        'coordinates': [coords]
                    }

            result['osm_parking_areas'].append(parking_area)

            # Update capacity counts
            result['total_capacity'] += classification['capacity_total']

            if classification['vehicle_type'] == 'truck':
                result['truck_capacity'] += classification['capacity_total']
            elif classification['vehicle_type'] == 'lzv':
                result['lzv_capacity'] += classification['capacity_total']
                result['truck_capacity'] += classification['capacity_total']  # LZV can also be counted as truck
            elif classification['vehicle_type'] == 'car':
                result['car_capacity'] += classification['capacity_total']

        # Individual parking spaces
        elif tags.get('amenity') == 'parking_space':
            result['has_osm_data'] = True

            space = {
                'osm_id': element['id'],
                'osm_type': element['type']
            }

            # Extract geometry
            if element['type'] == 'way' and 'nodes' in element:
                coords = []
                for node_id in element['nodes']:
                    if node_id in nodes:
                        node = nodes[node_id]
                        coords.append([node['lon'], node['lat']])

                if len(coords) >= 3:
                    space['geometry'] = {
                        'type': 'Polygon',
                        'coordinates': [coords]
                    }

            result['osm_parking_spaces'].append(space)

    return result

def analyze_all_rotterdam_facilities():
    """
    Analyze all truck parking facilities in Rotterdam area using OSM data.
    """
    print("="*80)
    print("OSM PARKING EXTRACTION - ROTTERDAM AREA")
    print("="*80)
    print()

    # Load Rotterdam facilities
    try:
        with open('rotterdam_facilities.json', 'r') as f:
            facilities = json.load(f)
    except FileNotFoundError:
        print("Error: rotterdam_facilities.json not found")
        print("Please run find_rotterdam_facilities.py first")
        return

    # Filter for truck parking
    truck_facilities = [f for f in facilities if f.get('is_truck_parking', False)]

    print(f"Total facilities in Rotterdam area: {len(facilities)}")
    print(f"Truck parking facilities: {len(truck_facilities)}")
    print()

    results = []
    total_stats = {
        'facilities_with_osm_data': 0,
        'facilities_without_osm_data': 0,
        'total_parking_areas': 0,
        'total_parking_spaces': 0,
        'total_capacity': 0,
        'truck_capacity': 0,
        'lzv_capacity': 0,
        'car_capacity': 0
    }

    print("Processing facilities...")
    print("-" * 80)

    for i, facility in enumerate(truck_facilities, 1):
        facility_id = facility['id']
        facility_name = facility['name']
        lat = facility['latitude']
        lon = facility['longitude']

        print(f"\n[{i}/{len(truck_facilities)}] {facility_name}")
        print(f"  Location: {lat:.5f}, {lon:.5f}")
        print(f"  Querying OSM...", end=" ", flush=True)

        # Query OSM
        osm_data = query_osm_parking_for_facility(lat, lon, facility_name)
        parking_data = extract_parking_from_osm(osm_data, facility_id)

        # Add facility info
        parking_data['facility_name'] = facility_name
        parking_data['facility_lat'] = lat
        parking_data['facility_lon'] = lon

        # Update stats
        if parking_data['has_osm_data']:
            total_stats['facilities_with_osm_data'] += 1
            total_stats['total_parking_areas'] += len(parking_data['osm_parking_areas'])
            total_stats['total_parking_spaces'] += len(parking_data['osm_parking_spaces'])
            total_stats['total_capacity'] += parking_data['total_capacity']
            total_stats['truck_capacity'] += parking_data['truck_capacity']
            total_stats['lzv_capacity'] += parking_data['lzv_capacity']
            total_stats['car_capacity'] += parking_data['car_capacity']

            print(f"✓ Found!")
            print(f"    Parking areas: {len(parking_data['osm_parking_areas'])}")
            print(f"    Individual spaces: {len(parking_data['osm_parking_spaces'])}")
            print(f"    Total capacity: {parking_data['total_capacity']}")
            print(f"    Truck capacity: {parking_data['truck_capacity']}")
            if parking_data['lzv_capacity'] > 0:
                print(f"    LZV capacity: {parking_data['lzv_capacity']}")
        else:
            total_stats['facilities_without_osm_data'] += 1
            print("✗ No OSM data")

        results.append(parking_data)

        # Rate limiting (Overpass API allows ~2 requests/second)
        time.sleep(0.6)

    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total facilities analyzed: {len(truck_facilities)}")
    print(f"Facilities with OSM data: {total_stats['facilities_with_osm_data']}")
    print(f"Facilities without OSM data: {total_stats['facilities_without_osm_data']}")
    print(f"Coverage: {total_stats['facilities_with_osm_data']/len(truck_facilities)*100:.1f}%")
    print()
    print(f"Total parking areas mapped: {total_stats['total_parking_areas']}")
    print(f"Total individual spaces mapped: {total_stats['total_parking_spaces']}")
    print()
    print(f"CAPACITY BY VEHICLE TYPE:")
    print(f"  Total: {total_stats['total_capacity']} spaces")
    print(f"  Truck: {total_stats['truck_capacity']} spaces")
    print(f"  LZV: {total_stats['lzv_capacity']} spaces")
    print(f"  Car/Van: {total_stats['car_capacity']} spaces")

    # Save results
    output = {
        'summary': total_stats,
        'facilities': results
    }

    with open('rotterdam_osm_parking_analysis.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nDetailed results saved to: rotterdam_osm_parking_analysis.json")

    # Create GeoJSON overlay
    create_comprehensive_geojson(results)

    return output

def create_comprehensive_geojson(facility_results: List[Dict]):
    """
    Create comprehensive GeoJSON overlay with all parking data.

    Args:
        facility_results: List of facility parking data
    """
    features = []

    for facility in facility_results:
        if not facility['has_osm_data']:
            continue

        # Add parking areas
        for area in facility['osm_parking_areas']:
            if 'geometry' not in area:
                continue

            classification = area['classification']

            feature = {
                'type': 'Feature',
                'geometry': area['geometry'],
                'properties': {
                    'feature_type': 'parking_area',
                    'facility_id': facility['facility_id'],
                    'facility_name': facility['facility_name'],
                    'osm_id': area['osm_id'],
                    'osm_type': area['osm_type'],
                    'name': area['name'],
                    'operator': area['operator'],
                    'fee': area['fee'],
                    'opening_hours': area['opening_hours'],
                    'surface': area['surface'],
                    # Classification
                    'vehicle_type': classification['vehicle_type'],
                    'vehicle_label': classification['label'],
                    'color': classification['color'],
                    'capacity_total': classification['capacity_total'],
                    'capacity_hgv': classification['capacity_hgv'],
                    'capacity_car': classification['capacity_car'],
                    'is_hgv': classification['is_hgv']
                }
            }
            features.append(feature)

        # Add individual parking spaces
        for space in facility['osm_parking_spaces']:
            if 'geometry' not in space:
                continue

            feature = {
                'type': 'Feature',
                'geometry': space['geometry'],
                'properties': {
                    'feature_type': 'parking_space',
                    'facility_id': facility['facility_id'],
                    'facility_name': facility['facility_name'],
                    'osm_id': space['osm_id'],
                    'osm_type': space['osm_type'],
                    'color': '#10b981'  # green for individual spaces
                }
            }
            features.append(feature)

    geojson = {
        'type': 'FeatureCollection',
        'features': features
    }

    # Save to file
    output_file = 'rotterdam_osm_parking.geojson'
    with open(output_file, 'w') as f:
        json.dump(geojson, f, indent=2)

    print(f"\nGeoJSON overlay created: {output_file}")
    print(f"Total features: {len(features)}")

    # Copy to public directory
    public_dir = Path('truck-parking-map/public')
    if public_dir.exists():
        public_file = public_dir / output_file
        with open(public_file, 'w') as f:
            json.dump(geojson, f, indent=2)
        print(f"Copied to: {public_file}")

def main():
    """Main entry point."""
    analyze_all_rotterdam_facilities()

if __name__ == "__main__":
    main()
