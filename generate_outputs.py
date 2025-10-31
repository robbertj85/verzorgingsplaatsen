#!/usr/bin/env python3
"""
Generate final output files in multiple formats (JSON, CSV, GeoJSON)
"""

import json
import csv
from datetime import datetime

def load_data():
    """Load enriched data"""
    with open('/Users/robbertjanssen/Documents/dev/Verzorgingsplaatsen/truck_parking_enriched.json', 'r') as f:
        return json.load(f)

def generate_geojson(facilities):
    """Generate GeoJSON FeatureCollection"""
    print("Generating GeoJSON output...")

    features = []

    for facility in facilities:
        # Get geometry
        geometry = facility.get('geometry')
        if not geometry and facility.get('latitude') and facility.get('longitude'):
            # Create point geometry if no polygon available
            geometry = {
                'type': 'Point',
                'coordinates': [facility['longitude'], facility['latitude']]
            }

        if not geometry:
            continue  # Skip facilities without geometry

        # Build properties
        properties = {
            'id': facility.get('id'),
            'name': facility.get('name', 'Unnamed'),
            'osm_id': facility.get('osm_id'),
            'data_source': facility.get('data_source', 'OpenStreetMap'),
            'last_updated': facility.get('last_updated'),
            'confidence_score': facility.get('confidence_score', 0)
        }

        # Add location details
        location = facility.get('location', {})
        if location:
            properties['municipality'] = location.get('municipality', '')
            properties['province'] = location.get('province', '')
            properties['highway'] = location.get('highway', '')
            properties['road'] = location.get('road', '')
            properties['postcode'] = location.get('postcode', '')

        # Add capacity
        capacity = facility.get('capacity', {})
        if capacity:
            properties['truck_spots'] = capacity.get('truck_spots', '')
            properties['total_spots'] = capacity.get('total_spots', '')

        # Add classification
        classification = facility.get('classification', {})
        if classification:
            properties['is_truck_parking'] = classification.get('is_truck_parking', False)
            properties['is_rest_area'] = classification.get('is_rest_area', False)
            properties['is_service_area'] = classification.get('is_service_area', False)

        # Add amenities summary
        amenities = facility.get('amenities', {})
        if amenities:
            properties['has_fuel'] = amenities.get('fuel') == 'yes'
            properties['has_restaurant'] = amenities.get('restaurant') == 'yes'
            properties['has_toilets'] = amenities.get('toilets') == 'yes'
            properties['has_wifi'] = amenities.get('wifi') == 'yes'

        # Add electricity info
        if facility.get('electricity'):
            properties['has_charging'] = True

        # Add area
        if facility.get('area_m2'):
            properties['area_m2'] = facility.get('area_m2')

        # Add operator and hours
        if facility.get('operator'):
            properties['operator'] = facility.get('operator')
        if facility.get('opening_hours'):
            properties['opening_hours'] = facility.get('opening_hours')

        # Add HGV designation
        if facility.get('hgv'):
            properties['hgv'] = facility.get('hgv')

        feature = {
            'type': 'Feature',
            'geometry': geometry,
            'properties': properties
        }

        features.append(feature)

    geojson = {
        'type': 'FeatureCollection',
        'metadata': {
            'title': 'Truck Parking Facilities in the Netherlands',
            'description': 'Comprehensive database of truck parking facilities, rest areas, and service areas',
            'generated': datetime.utcnow().isoformat() + 'Z',
            'source': 'OpenStreetMap',
            'count': len(features)
        },
        'features': features
    }

    output_file = '/Users/robbertjanssen/Documents/dev/Verzorgingsplaatsen/truck_parking_facilities.geojson'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, indent=2, ensure_ascii=False)

    print(f"Saved GeoJSON with {len(features)} features to {output_file}")
    return geojson

def generate_csv(facilities):
    """Generate CSV output"""
    print("Generating CSV output...")

    csv_file = '/Users/robbertjanssen/Documents/dev/Verzorgingsplaatsen/truck_parking_facilities.csv'

    fieldnames = [
        'id', 'name', 'latitude', 'longitude',
        'province', 'municipality', 'highway', 'road', 'postcode',
        'truck_spots', 'total_spots', 'area_m2',
        'is_truck_parking', 'is_rest_area', 'is_service_area',
        'has_fuel', 'has_restaurant', 'has_toilets', 'has_wifi', 'has_charging',
        'operator', 'opening_hours', 'hgv',
        'confidence_score', 'osm_id', 'data_source'
    ]

    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()

        for facility in facilities:
            row = {
                'id': facility.get('id', ''),
                'name': facility.get('name', ''),
                'latitude': facility.get('latitude', ''),
                'longitude': facility.get('longitude', ''),
                'osm_id': facility.get('osm_id', ''),
                'data_source': facility.get('data_source', ''),
                'confidence_score': facility.get('confidence_score', ''),
                'hgv': facility.get('hgv', ''),
                'operator': facility.get('operator', ''),
                'opening_hours': facility.get('opening_hours', ''),
                'area_m2': facility.get('area_m2', '')
            }

            # Location
            location = facility.get('location', {})
            row['province'] = location.get('province', '')
            row['municipality'] = location.get('municipality', '')
            row['highway'] = location.get('highway', '')
            row['road'] = location.get('road', '')
            row['postcode'] = location.get('postcode', '')

            # Capacity
            capacity = facility.get('capacity', {})
            row['truck_spots'] = capacity.get('truck_spots', '')
            row['total_spots'] = capacity.get('total_spots', '')

            # Classification
            classification = facility.get('classification', {})
            row['is_truck_parking'] = classification.get('is_truck_parking', False)
            row['is_rest_area'] = classification.get('is_rest_area', False)
            row['is_service_area'] = classification.get('is_service_area', False)

            # Amenities
            amenities = facility.get('amenities', {})
            row['has_fuel'] = amenities.get('fuel') == 'yes'
            row['has_restaurant'] = amenities.get('restaurant') == 'yes'
            row['has_toilets'] = amenities.get('toilets') == 'yes'
            row['has_wifi'] = amenities.get('wifi') == 'yes'

            # Electricity
            row['has_charging'] = bool(facility.get('electricity'))

            writer.writerow(row)

    print(f"Saved CSV with {len(facilities)} facilities to {csv_file}")

def generate_json_summary(facilities):
    """Generate structured JSON summary"""
    print("Generating JSON summary...")

    summary = {
        'metadata': {
            'title': 'Truck Parking Facilities in the Netherlands - Database',
            'generated': datetime.utcnow().isoformat() + 'Z',
            'version': '1.0',
            'total_facilities': len(facilities)
        },
        'statistics': {
            'total': len(facilities),
            'with_capacity': sum(1 for f in facilities if f.get('capacity')),
            'with_polygons': sum(1 for f in facilities if f.get('geometry', {}).get('type') == 'Polygon'),
            'with_amenities': sum(1 for f in facilities if f.get('amenities')),
            'with_electricity': sum(1 for f in facilities if f.get('electricity')),
            'high_confidence': sum(1 for f in facilities if f.get('confidence_score', 0) >= 0.7)
        },
        'facilities': []
    }

    for facility in facilities:
        # Create simplified facility record
        record = {
            'id': facility.get('id'),
            'name': facility.get('name'),
            'coordinates': {
                'lat': facility.get('latitude'),
                'lon': facility.get('longitude')
            },
            'location': facility.get('location', {}),
            'capacity': facility.get('capacity', {}),
            'classification': facility.get('classification', {}),
            'amenities': facility.get('amenities', {}),
            'confidence_score': facility.get('confidence_score')
        }

        # Add geometry type
        if facility.get('geometry'):
            record['geometry_type'] = facility['geometry'].get('type')

        if facility.get('area_m2'):
            record['area_m2'] = facility.get('area_m2')

        summary['facilities'].append(record)

    output_file = '/Users/robbertjanssen/Documents/dev/Verzorgingsplaatsen/truck_parking_database.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"Saved JSON database to {output_file}")

def main():
    """Main execution"""
    print("=" * 80)
    print("GENERATING OUTPUT FILES")
    print("=" * 80)

    facilities = load_data()
    print(f"Loaded {len(facilities)} facilities")

    # Generate outputs
    generate_geojson(facilities)
    generate_csv(facilities)
    generate_json_summary(facilities)

    print("\n" + "=" * 80)
    print("OUTPUT GENERATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
