#!/usr/bin/env python3
"""
Collect truck parking facilities data from OpenStreetMap using Overpass API
"""

import requests
import json
import time
from datetime import datetime

def query_overpass_api(query, max_retries=3):
    """Query the Overpass API with retry logic"""
    overpass_url = "https://overpass-api.de/api/interpreter"

    for attempt in range(max_retries):
        try:
            response = requests.post(overpass_url, data={'data': query}, timeout=180)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                raise
    return None

def collect_osm_truck_parking():
    """Collect truck parking facilities from OpenStreetMap"""

    print("Querying OpenStreetMap for truck parking facilities in the Netherlands...")

    # Comprehensive Overpass query for truck parking in the Netherlands
    # Bounding box for Netherlands: [50.7, 3.3, 53.6, 7.2]
    overpass_query = """
    [out:json][timeout:180];
    (
      // Rest areas with truck parking
      node["highway"="rest_area"]["hgv"="yes"](50.7,3.3,53.6,7.2);
      way["highway"="rest_area"]["hgv"="yes"](50.7,3.3,53.6,7.2);
      relation["highway"="rest_area"]["hgv"="yes"](50.7,3.3,53.6,7.2);

      // Service areas with truck parking
      node["highway"="services"]["hgv"="yes"](50.7,3.3,53.6,7.2);
      way["highway"="services"]["hgv"="yes"](50.7,3.3,53.6,7.2);
      relation["highway"="services"]["hgv"="yes"](50.7,3.3,53.6,7.2);

      // Parking areas specifically for trucks
      node["amenity"="parking"]["parking"="surface"]["hgv"="yes"](50.7,3.3,53.6,7.2);
      way["amenity"="parking"]["parking"="surface"]["hgv"="yes"](50.7,3.3,53.6,7.2);
      relation["amenity"="parking"]["parking"="surface"]["hgv"="yes"](50.7,3.3,53.6,7.2);

      node["amenity"="parking"]["hgv"="designated"](50.7,3.3,53.6,7.2);
      way["amenity"="parking"]["hgv"="designated"](50.7,3.3,53.6,7.2);
      relation["amenity"="parking"]["hgv"="designated"](50.7,3.3,53.6,7.2);

      // Truck parking without specific amenity tag
      node["parking"="surface"]["hgv"="designated"](50.7,3.3,53.6,7.2);
      way["parking"="surface"]["hgv"="designated"](50.7,3.3,53.6,7.2);

      // Rest areas that might have truck parking (verzorgingsplaats)
      node["highway"="rest_area"](50.7,3.3,53.6,7.2);
      way["highway"="rest_area"](50.7,3.3,53.6,7.2);
      relation["highway"="rest_area"](50.7,3.3,53.6,7.2);

      // Service areas
      node["highway"="services"](50.7,3.3,53.6,7.2);
      way["highway"="services"](50.7,3.3,53.6,7.2);
      relation["highway"="services"](50.7,3.3,53.6,7.2);
    );
    out body;
    >;
    out skel qt;
    """

    try:
        data = query_overpass_api(overpass_query)

        if not data:
            print("Failed to retrieve data from Overpass API")
            return []

        print(f"Retrieved {len(data.get('elements', []))} raw elements from OSM")

        # Process the data
        facilities = []
        nodes_dict = {}

        # First pass: collect all nodes for way reconstruction
        for element in data.get('elements', []):
            if element['type'] == 'node':
                nodes_dict[element['id']] = {
                    'lat': element['lat'],
                    'lon': element['lon']
                }

        # Second pass: process facilities
        processed_ids = set()

        for element in data.get('elements', []):
            element_id = element['id']

            if element_id in processed_ids:
                continue

            tags = element.get('tags', {})

            # Skip if no relevant tags
            if not tags:
                continue

            facility = {
                'id': f"osm_{element['type']}_{element_id}",
                'osm_id': element_id,
                'osm_type': element['type'],
                'data_source': 'OpenStreetMap',
                'last_updated': datetime.utcnow().isoformat() + 'Z',
                'tags': tags
            }

            # Extract name
            facility['name'] = tags.get('name', tags.get('name:nl', tags.get('ref', 'Unnamed')))

            # Extract location information
            if element['type'] == 'node':
                facility['geometry'] = {
                    'type': 'Point',
                    'coordinates': [element['lon'], element['lat']]
                }
                facility['latitude'] = element['lat']
                facility['longitude'] = element['lon']
            elif element['type'] == 'way':
                # Get way nodes to construct polygon/linestring
                way_nodes = element.get('nodes', [])
                if way_nodes and len(way_nodes) > 0:
                    coordinates = []
                    for node_id in way_nodes:
                        if node_id in nodes_dict:
                            node = nodes_dict[node_id]
                            coordinates.append([node['lon'], node['lat']])

                    if coordinates:
                        # Check if it's a closed polygon
                        if len(coordinates) > 2 and coordinates[0] == coordinates[-1]:
                            facility['geometry'] = {
                                'type': 'Polygon',
                                'coordinates': [coordinates]
                            }
                        else:
                            facility['geometry'] = {
                                'type': 'LineString',
                                'coordinates': coordinates
                            }

                        # Calculate centroid for point location
                        if coordinates:
                            avg_lon = sum(c[0] for c in coordinates) / len(coordinates)
                            avg_lat = sum(c[1] for c in coordinates) / len(coordinates)
                            facility['latitude'] = avg_lat
                            facility['longitude'] = avg_lon

            # Extract capacity information
            capacity_info = {}
            if 'capacity:hgv' in tags:
                capacity_info['truck_spots'] = tags['capacity:hgv']
            if 'capacity' in tags:
                capacity_info['total_spots'] = tags['capacity']
            if capacity_info:
                facility['capacity'] = capacity_info

            # Extract highway information
            location_info = {}
            if 'ref' in tags:
                location_info['ref'] = tags['ref']
            if 'highway' in tags:
                location_info['highway_type'] = tags['highway']
            if location_info:
                facility['location'] = location_info

            # Extract amenities
            amenities = {}
            amenity_tags = ['fuel', 'restaurant', 'cafe', 'toilets', 'shower',
                          'drinking_water', 'wifi', 'atm', 'shop', 'parking:fee']
            for amenity in amenity_tags:
                if amenity in tags:
                    amenities[amenity] = tags[amenity]
            if amenities:
                facility['amenities'] = amenities

            # Extract HGV information
            if 'hgv' in tags:
                facility['hgv'] = tags['hgv']

            # Extract operator and opening hours
            if 'operator' in tags:
                facility['operator'] = tags['operator']
            if 'opening_hours' in tags:
                facility['opening_hours'] = tags['opening_hours']

            # Extract surface and parking type
            if 'surface' in tags:
                facility['surface'] = tags['surface']
            if 'parking' in tags:
                facility['parking_type'] = tags['parking']

            # Extract electricity/charging information
            if 'charging_station' in tags or 'socket:type2' in tags:
                facility['electricity'] = {
                    'charging_available': True
                }
                if 'socket:type2' in tags:
                    facility['electricity']['socket_type2'] = tags['socket:type2']

            # Calculate area for polygons
            if facility.get('geometry', {}).get('type') == 'Polygon':
                coords = facility['geometry']['coordinates'][0]
                area = calculate_polygon_area(coords)
                facility['area_m2'] = area

            # Add confidence score based on completeness
            confidence = calculate_confidence_score(facility)
            facility['confidence_score'] = confidence

            facilities.append(facility)
            processed_ids.add(element_id)

        print(f"Processed {len(facilities)} truck parking facilities from OSM")
        return facilities

    except Exception as e:
        print(f"Error collecting OSM data: {e}")
        import traceback
        traceback.print_exc()
        return []

def calculate_polygon_area(coordinates):
    """Calculate area of polygon in square meters using Shoelace formula"""
    from math import radians, cos

    if len(coordinates) < 3:
        return 0

    # Convert to meters approximately (at Netherlands latitude ~52°)
    lat_to_m = 111320  # meters per degree latitude
    lon_to_m = 111320 * cos(radians(52))  # meters per degree longitude at 52°N

    area = 0
    for i in range(len(coordinates) - 1):
        x1, y1 = coordinates[i][0] * lon_to_m, coordinates[i][1] * lat_to_m
        x2, y2 = coordinates[i + 1][0] * lon_to_m, coordinates[i + 1][1] * lat_to_m
        area += x1 * y2 - x2 * y1

    return abs(area) / 2

def calculate_confidence_score(facility):
    """Calculate confidence score based on data completeness"""
    score = 0.5  # Base score

    # Add points for various attributes
    if facility.get('name') and facility['name'] != 'Unnamed':
        score += 0.1
    if facility.get('capacity'):
        score += 0.15
    if facility.get('geometry', {}).get('type') == 'Polygon':
        score += 0.1
    if facility.get('amenities'):
        score += 0.05
    if facility.get('operator'):
        score += 0.05
    if facility.get('hgv') in ['yes', 'designated']:
        score += 0.05

    return min(score, 1.0)

if __name__ == "__main__":
    facilities = collect_osm_truck_parking()

    # Save to JSON
    output_file = '/Users/robbertjanssen/Documents/dev/Verzorgingsplaatsen/osm_truck_parking_raw.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(facilities, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(facilities)} facilities to {output_file}")

    # Print summary statistics
    print("\n=== OSM Data Summary ===")
    print(f"Total facilities: {len(facilities)}")

    with_capacity = sum(1 for f in facilities if f.get('capacity'))
    print(f"Facilities with capacity data: {with_capacity}")

    with_polygons = sum(1 for f in facilities if f.get('geometry', {}).get('type') == 'Polygon')
    print(f"Facilities with polygon boundaries: {with_polygons}")

    with_amenities = sum(1 for f in facilities if f.get('amenities'))
    print(f"Facilities with amenity information: {with_amenities}")

    avg_confidence = sum(f.get('confidence_score', 0) for f in facilities) / len(facilities) if facilities else 0
    print(f"Average confidence score: {avg_confidence:.2f}")
