#!/usr/bin/env python3
"""
Enhanced parking space detection with vehicle type classification.

This script classifies detected parking spaces by vehicle type based on
standard Dutch (CROW) and European parking dimensions.

Vehicle Type Standards:
- Car/Van: 2.5m × 5.0m (standard EU car parking)
- Standard Truck: 3.75m × 20m (CROW diagonal parking)
- Heavy Truck: 4.0m × 15m (perpendicular parking)
- Large Truck (Type C): 7.0m × 30m (tractor-trailer with semi-trailer)
- LZV (Long Heavy Vehicle): 4.5m × 35m (25.25m vehicle + maneuvering)

Note: Detected spaces are typically parking ROWS containing multiple vehicles,
so individual space dimensions are estimated by dividing row length.
"""

import json
from typing import Dict, List, Tuple
import math

# Vehicle type dimension standards (width × length in meters)
VEHICLE_STANDARDS = {
    'car_van': {
        'width': (2.0, 3.0),      # min, max width
        'length': (4.0, 6.0),      # min, max length
        'area': (8, 18),           # min, max area m²
        'color': '#3b82f6',        # blue
        'label': 'Car/Van'
    },
    'standard_truck': {
        'width': (3.5, 4.5),
        'length': (12.0, 20.0),
        'area': (42, 90),
        'color': '#ef4444',        # red
        'label': 'Standard Truck'
    },
    'heavy_truck': {
        'width': (3.5, 5.0),
        'length': (18.0, 25.0),
        'area': (63, 125),
        'color': '#f97316',        # orange
        'label': 'Heavy Truck'
    },
    'large_truck': {
        'width': (5.0, 8.0),
        'length': (25.0, 35.0),
        'area': (125, 280),
        'color': '#dc2626',        # dark red
        'label': 'Large Truck (Type C)'
    },
    'lzv': {
        'width': (4.0, 6.0),
        'length': (30.0, 45.0),
        'area': (120, 270),
        'color': '#7c2d12',        # dark brown
        'label': 'LZV Parking'
    },
    'parking_row': {
        'width': (3.0, 8.0),
        'length': (40.0, 100.0),   # Very long = multiple spaces
        'area': (120, 800),
        'color': '#10b981',        # green
        'label': 'Parking Row (Multiple Vehicles)'
    }
}

def classify_parking_space(width_m: float, length_m: float, area_m2: float) -> Dict:
    """
    Classify a parking space by vehicle type based on dimensions.

    Args:
        width_m: Width in meters
        length_m: Length in meters
        area_m2: Area in square meters

    Returns:
        Dictionary with classification info
    """
    # Normalize width and length (ensure width <= length)
    w, l = min(width_m, length_m), max(width_m, length_m)

    matches = []

    for vehicle_type, standards in VEHICLE_STANDARDS.items():
        w_min, w_max = standards['width']
        l_min, l_max = standards['length']
        a_min, a_max = standards['area']

        # Check if dimensions fit within this vehicle type
        width_match = w_min <= w <= w_max
        length_match = l_min <= l <= l_max
        area_match = a_min <= area_m2 <= a_max

        # Calculate confidence score
        confidence = 0
        if width_match:
            confidence += 0.33
        if length_match:
            confidence += 0.33
        if area_match:
            confidence += 0.34

        if confidence > 0.5:  # At least 2 out of 3 criteria
            matches.append({
                'type': vehicle_type,
                'confidence': round(confidence, 2),
                'label': standards['label'],
                'color': standards['color']
            })

    # Sort by confidence
    matches.sort(key=lambda x: x['confidence'], reverse=True)

    if matches:
        best_match = matches[0]

        # Additional logic for parking rows
        if l > 40:  # Very long spaces are likely parking rows
            # Estimate number of vehicles that could fit
            estimated_spaces = estimate_vehicles_in_row(w, l)
            best_match['is_parking_row'] = True
            best_match['estimated_vehicles'] = estimated_spaces
        else:
            best_match['is_parking_row'] = False
            best_match['estimated_vehicles'] = 1

        return best_match
    else:
        # Unknown/unclassified
        return {
            'type': 'unknown',
            'confidence': 0.0,
            'label': 'Unknown',
            'color': '#6b7280',
            'is_parking_row': False,
            'estimated_vehicles': 0
        }

def estimate_vehicles_in_row(width_m: float, length_m: float) -> Dict[str, int]:
    """
    Estimate how many vehicles of each type could fit in a parking row.

    Args:
        width_m: Width of parking row
        length_m: Length of parking row

    Returns:
        Dictionary with estimated counts for each vehicle type
    """
    estimates = {}

    # Standard truck: ~15m per vehicle
    estimates['standard_trucks'] = int(length_m / 15)

    # Heavy truck: ~20m per vehicle
    estimates['heavy_trucks'] = int(length_m / 20)

    # LZV: ~35m per vehicle
    estimates['lzv'] = int(length_m / 35)

    # Cars/vans: ~5m per vehicle
    estimates['cars'] = int(length_m / 5)

    return estimates

def analyze_maasvlakte_data():
    """
    Analyze Maasvlakte parking detection results with vehicle type classification.
    """
    # Load Maasvlakte detection results
    try:
        with open('maasvlakte_detection_results.json', 'r') as f:
            results = json.load(f)
    except FileNotFoundError:
        print("Error: maasvlakte_detection_results.json not found")
        print("Please run analyze_maasvlakte.py first")
        return

    print("=" * 80)
    print("VEHICLE TYPE CLASSIFICATION ANALYSIS - MAASVLAKTE PORT AREA")
    print("=" * 80)

    # Statistics by vehicle type
    type_stats = {
        'car_van': {'count': 0, 'total_area': 0, 'spaces': []},
        'standard_truck': {'count': 0, 'total_area': 0, 'spaces': []},
        'heavy_truck': {'count': 0, 'total_area': 0, 'spaces': []},
        'large_truck': {'count': 0, 'total_area': 0, 'spaces': []},
        'lzv': {'count': 0, 'total_area': 0, 'spaces': []},
        'parking_row': {'count': 0, 'total_area': 0, 'spaces': []},
        'unknown': {'count': 0, 'total_area': 0, 'spaces': []}
    }

    total_estimated_capacity = {
        'standard_trucks': 0,
        'heavy_trucks': 0,
        'lzv': 0,
        'cars': 0
    }

    enhanced_results = []

    for facility_result in results:
        if 'parking_spaces' not in facility_result:
            continue

        print(f"\nFacility: {facility_result['name']}")
        print(f"Location: {facility_result['latitude']:.5f}, {facility_result['longitude']:.5f}")
        print(f"Total detected spaces: {len(facility_result['parking_spaces'])}")
        print("-" * 80)

        enhanced_spaces = []

        for i, space in enumerate(facility_result['parking_spaces']):
            # Classify the space
            classification = classify_parking_space(
                space['width_m'],
                space['length_m'],
                space['area_m2']
            )

            # Add classification to space data
            enhanced_space = {**space, 'classification': classification}
            enhanced_spaces.append(enhanced_space)

            # Update statistics
            vehicle_type = classification['type']
            type_stats[vehicle_type]['count'] += 1
            type_stats[vehicle_type]['total_area'] += space['area_m2']
            type_stats[vehicle_type]['spaces'].append(space)

            # If it's a parking row, estimate capacity
            if classification.get('is_parking_row'):
                estimates = estimate_vehicles_in_row(space['width_m'], space['length_m'])
                for vtype, count in estimates.items():
                    total_estimated_capacity[vtype] += count
            else:
                # Single vehicle space
                if vehicle_type in ['standard_truck', 'heavy_truck']:
                    total_estimated_capacity['standard_trucks'] += 1
                elif vehicle_type == 'lzv':
                    total_estimated_capacity['lzv'] += 1
                elif vehicle_type == 'car_van':
                    total_estimated_capacity['cars'] += 1

            print(f"  Space #{i+1}: {space['length_m']}m × {space['width_m']}m "
                  f"({space['area_m2']} m²) → {classification['label']} "
                  f"(confidence: {classification['confidence']})")

            if classification.get('is_parking_row'):
                estimates = classification['estimated_vehicles']
                print(f"    Estimated capacity: {estimates['standard_trucks']} standard trucks OR "
                      f"{estimates['heavy_trucks']} heavy trucks OR "
                      f"{estimates['lzv']} LZVs")

        # Add enhanced spaces to results
        facility_result['parking_spaces_classified'] = enhanced_spaces
        enhanced_results.append(facility_result)

    # Print summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY BY VEHICLE TYPE")
    print("=" * 80)

    for vehicle_type, stats in type_stats.items():
        if stats['count'] > 0:
            label = VEHICLE_STANDARDS.get(vehicle_type, {}).get('label', vehicle_type)
            avg_area = stats['total_area'] / stats['count']
            print(f"\n{label}:")
            print(f"  Detected zones: {stats['count']}")
            print(f"  Total area: {stats['total_area']:.0f} m²")
            print(f"  Average zone size: {avg_area:.0f} m²")

    print("\n" + "=" * 80)
    print("ESTIMATED PARKING CAPACITY")
    print("=" * 80)
    print(f"Standard Trucks: {total_estimated_capacity['standard_trucks']} spaces")
    print(f"Heavy Trucks: {total_estimated_capacity['heavy_trucks']} spaces")
    print(f"LZV (Long Heavy Vehicles): {total_estimated_capacity['lzv']} spaces")
    print(f"Cars/Vans: {total_estimated_capacity['cars']} spaces")

    # Save enhanced results
    with open('maasvlakte_classified_results.json', 'w') as f:
        json.dump({
            'facilities': enhanced_results,
            'summary': {
                'type_statistics': {k: {'count': v['count'], 'total_area': v['total_area']}
                                   for k, v in type_stats.items()},
                'estimated_capacity': total_estimated_capacity
            }
        }, f, indent=2)

    print(f"\nSaved enhanced results to: maasvlakte_classified_results.json")

    # Create enhanced GeoJSON overlay
    create_classified_overlay(enhanced_results)

def create_classified_overlay(results: List[Dict]):
    """
    Create GeoJSON overlay with vehicle type classifications.

    Args:
        results: List of facility results with classified parking spaces
    """
    features = []

    for facility in results:
        if 'parking_spaces_classified' not in facility:
            continue

        for i, space in enumerate(facility['parking_spaces_classified']):
            classification = space['classification']

            # Create feature
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [space['polygon_geo']]
                },
                'properties': {
                    'facility_id': facility['facility_id'],
                    'facility_name': facility['name'],
                    'space_number': i + 1,
                    'width_m': space['width_m'],
                    'length_m': space['length_m'],
                    'area_m2': space['area_m2'],
                    'angle': space['angle'],
                    # Classification info
                    'vehicle_type': classification['type'],
                    'vehicle_label': classification['label'],
                    'classification_confidence': classification['confidence'],
                    'is_parking_row': classification.get('is_parking_row', False),
                    'color': classification['color']
                }
            }

            # Add estimated vehicles if it's a parking row
            if classification.get('is_parking_row'):
                estimates = classification['estimated_vehicles']
                feature['properties']['estimated_standard_trucks'] = estimates['standard_trucks']
                feature['properties']['estimated_heavy_trucks'] = estimates['heavy_trucks']
                feature['properties']['estimated_lzv'] = estimates['lzv']
                feature['properties']['estimated_cars'] = estimates['cars']

            features.append(feature)

    geojson = {
        'type': 'FeatureCollection',
        'features': features
    }

    # Save to file
    with open('maasvlakte_parking_classified.geojson', 'w') as f:
        json.dump(geojson, f, indent=2)

    print(f"\nCreated classified GeoJSON overlay: maasvlakte_parking_classified.geojson")
    print(f"Total features: {len(features)}")

    # Also copy to public directory for web app
    import shutil
    import os

    public_dir = 'truck-parking-map/public'
    if os.path.exists(public_dir):
        shutil.copy('maasvlakte_parking_classified.geojson',
                   f'{public_dir}/maasvlakte_parking_classified.geojson')
        print(f"Copied to: {public_dir}/maasvlakte_parking_classified.geojson")

def main():
    """Main entry point."""
    print("Vehicle Type Classification for Maasvlakte Parking Spaces")
    print("=" * 80)
    print("\nVehicle Type Standards (CROW/EU):")
    print("-" * 80)
    for vtype, standards in VEHICLE_STANDARDS.items():
        print(f"{standards['label']}:")
        print(f"  Width: {standards['width'][0]}-{standards['width'][1]}m")
        print(f"  Length: {standards['length'][0]}-{standards['length'][1]}m")
        print(f"  Area: {standards['area'][0]}-{standards['area'][1]} m²")
        print()

    analyze_maasvlakte_data()

if __name__ == "__main__":
    main()
