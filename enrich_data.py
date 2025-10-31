#!/usr/bin/env python3
"""
Enrich collected parking facility data with additional information
"""

import json
import requests
import time
from collections import defaultdict

def load_osm_data():
    """Load OSM data"""
    with open('/Users/robbertjanssen/Documents/dev/Verzorgingsplaatsen/osm_truck_parking_raw.json', 'r') as f:
        return json.load(f)

def enrich_with_nominatim(facilities):
    """
    Enrich facilities with location data from Nominatim reverse geocoding
    """
    print("Enriching facilities with location data from Nominatim...")

    enriched_count = 0
    for i, facility in enumerate(facilities):
        # Only process facilities that need enrichment and have coordinates
        if facility.get('latitude') and facility.get('longitude'):
            # Check if we already have detailed location info
            if not facility.get('location', {}).get('municipality'):
                try:
                    lat = facility['latitude']
                    lon = facility['longitude']

                    # Query Nominatim reverse geocoding
                    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"

                    headers = {
                        'User-Agent': 'TruckParkingNL/1.0 (Data Collection Project)'
                    }

                    response = requests.get(url, headers=headers, timeout=10)

                    if response.status_code == 200:
                        data = response.json()
                        address = data.get('address', {})

                        # Extract location information
                        if not facility.get('location'):
                            facility['location'] = {}

                        location = facility['location']

                        if address.get('municipality'):
                            location['municipality'] = address['municipality']
                        elif address.get('city'):
                            location['municipality'] = address['city']
                        elif address.get('town'):
                            location['municipality'] = address['town']
                        elif address.get('village'):
                            location['municipality'] = address['village']

                        if address.get('state'):
                            location['province'] = address['state']

                        if address.get('road'):
                            location['road'] = address['road']

                        if address.get('postcode'):
                            location['postcode'] = address['postcode']

                        # Extract highway information
                        if 'road' in address and ('A' in address['road'] or 'N' in address['road']):
                            location['highway'] = address['road']

                        enriched_count += 1

                        # Rate limiting - Nominatim allows 1 request per second
                        time.sleep(1.1)

                        # Progress indicator
                        if (i + 1) % 10 == 0:
                            print(f"Processed {i + 1}/{len(facilities)} facilities...")

                except Exception as e:
                    if i < 10:  # Only print errors for first 10
                        print(f"Error enriching facility {facility.get('name', 'unknown')}: {e}")

        # Only process first 200 to respect rate limits and time constraints
        if i >= 199:
            print(f"Stopping after {i + 1} facilities to respect rate limits")
            break

    print(f"Enriched {enriched_count} facilities with location data")
    return facilities

def filter_and_classify_facilities(facilities):
    """
    Filter and classify facilities to identify true truck parking locations
    """
    print("\nClassifying and filtering facilities...")

    classified = []

    for facility in facilities:
        tags = facility.get('tags', {})
        classification = {
            'is_truck_parking': False,
            'is_rest_area': False,
            'is_service_area': False,
            'confidence': facility.get('confidence_score', 0.5)
        }

        # Determine if it's designated for trucks
        hgv_tag = tags.get('hgv', '').lower()
        if hgv_tag in ['yes', 'designated']:
            classification['is_truck_parking'] = True
            classification['confidence'] = min(classification['confidence'] + 0.2, 1.0)

        # Check for rest area
        highway_tag = tags.get('highway', '').lower()
        if highway_tag in ['rest_area', 'services']:
            if highway_tag == 'rest_area':
                classification['is_rest_area'] = True
            else:
                classification['is_service_area'] = True
            classification['confidence'] = min(classification['confidence'] + 0.1, 1.0)

        # Check amenity tag
        amenity_tag = tags.get('amenity', '').lower()
        if amenity_tag == 'parking':
            parking_tag = tags.get('parking', '').lower()
            if parking_tag in ['surface', 'layby']:
                classification['confidence'] = min(classification['confidence'] + 0.05, 1.0)

        facility['classification'] = classification

        # Filter criteria: keep if it's likely truck parking or rest area
        keep = False

        if classification['is_truck_parking']:
            keep = True
        elif classification['is_rest_area'] or classification['is_service_area']:
            keep = True
        elif hgv_tag:  # Has any HGV tag
            keep = True
        elif facility.get('capacity', {}).get('truck_spots'):
            keep = True

        if keep:
            classified.append(facility)

    print(f"Filtered from {len(facilities)} to {len(classified)} truck-relevant facilities")

    return classified

def analyze_facilities(facilities):
    """
    Analyze facilities and generate statistics
    """
    print("\nAnalyzing facilities...")

    stats = {
        'total': len(facilities),
        'by_province': defaultdict(int),
        'by_highway': defaultdict(int),
        'by_type': defaultdict(int),
        'with_capacity': 0,
        'with_amenities': 0,
        'with_electricity': 0,
        'with_polygons': 0,
        'total_truck_capacity': 0,
        'high_confidence': 0
    }

    for facility in facilities:
        # Province distribution
        province = facility.get('location', {}).get('province', 'Unknown')
        stats['by_province'][province] += 1

        # Highway distribution
        highway = facility.get('location', {}).get('highway', 'Unknown')
        if highway and highway != 'Unknown':
            # Extract highway number (e.g., "A1" from various formats)
            import re
            match = re.search(r'[AN]\d+', highway)
            if match:
                highway = match.group(0)
        stats['by_highway'][highway] += 1

        # Type classification
        classification = facility.get('classification', {})
        if classification.get('is_rest_area'):
            stats['by_type']['Rest Area'] += 1
        elif classification.get('is_service_area'):
            stats['by_type']['Service Area'] += 1
        elif classification.get('is_truck_parking'):
            stats['by_type']['Truck Parking'] += 1
        else:
            stats['by_type']['Other'] += 1

        # Capacity
        if facility.get('capacity'):
            stats['with_capacity'] += 1
            truck_spots = facility.get('capacity', {}).get('truck_spots', 0)
            try:
                if isinstance(truck_spots, str):
                    truck_spots = int(truck_spots)
                stats['total_truck_capacity'] += truck_spots
            except (ValueError, TypeError):
                pass

        # Amenities
        if facility.get('amenities'):
            stats['with_amenities'] += 1

        # Electricity
        if facility.get('electricity'):
            stats['with_electricity'] += 1

        # Polygons
        if facility.get('geometry', {}).get('type') == 'Polygon':
            stats['with_polygons'] += 1

        # Confidence
        if facility.get('confidence_score', 0) >= 0.7:
            stats['high_confidence'] += 1

    return stats

def main():
    """Main execution"""
    print("=" * 80)
    print("DATA ENRICHMENT AND ANALYSIS")
    print("=" * 80)

    # Load OSM data
    facilities = load_osm_data()
    print(f"Loaded {len(facilities)} facilities from OSM")

    # Enrich with Nominatim (limited to avoid rate limiting)
    facilities = enrich_with_nominatim(facilities)

    # Filter and classify
    facilities = filter_and_classify_facilities(facilities)

    # Analyze
    stats = analyze_facilities(facilities)

    # Save enriched data
    output_file = '/Users/robbertjanssen/Documents/dev/Verzorgingsplaatsen/truck_parking_enriched.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(facilities, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(facilities)} enriched facilities to {output_file}")

    # Save statistics
    stats_output = {
        'total_facilities': stats['total'],
        'facilities_with_capacity_data': stats['with_capacity'],
        'facilities_with_amenities': stats['with_amenities'],
        'facilities_with_electricity': stats['with_electricity'],
        'facilities_with_polygons': stats['with_polygons'],
        'high_confidence_facilities': stats['high_confidence'],
        'total_truck_parking_capacity': stats['total_truck_capacity'],
        'by_province': dict(stats['by_province']),
        'by_highway': dict(sorted(stats['by_highway'].items(), key=lambda x: x[1], reverse=True)[:20]),
        'by_type': dict(stats['by_type'])
    }

    stats_file = '/Users/robbertjanssen/Documents/dev/Verzorgingsplaatsen/analysis_stats.json'
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats_output, f, indent=2, ensure_ascii=False)

    print(f"\n=== STATISTICS ===")
    print(f"Total facilities: {stats['total']}")
    print(f"High confidence (>0.7): {stats['high_confidence']}")
    print(f"With capacity data: {stats['with_capacity']}")
    print(f"With polygon boundaries: {stats['with_polygons']}")
    print(f"With amenities: {stats['with_amenities']}")
    print(f"With electricity: {stats['with_electricity']}")
    print(f"Total truck parking capacity: {stats['total_truck_capacity']} spots")

    print(f"\nTop provinces:")
    for province, count in sorted(stats['by_province'].items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {province}: {count}")

    print(f"\nTop highways:")
    for highway, count in sorted(stats['by_highway'].items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {highway}: {count}")

    print(f"\nBy type:")
    for type_name, count in sorted(stats['by_type'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {type_name}: {count}")

if __name__ == "__main__":
    main()
