#!/usr/bin/env python3
"""
Detect truck parking spaces from satellite imagery for all South Holland facilities.

This script:
1. Loads South Holland truck parking facilities
2. Fetches PDOK aerial imagery for each facility
3. Uses computer vision to detect parking spaces
4. Generates comprehensive GeoJSON overlay
"""

import json
import requests
from PIL import Image
from io import BytesIO
import numpy as np
import cv2
from typing import List, Tuple, Dict
import math
import time

# PDOK WMS service for aerial imagery (Actueel Ortho 25cm resolution)
PDOK_WMS_URL = "https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0"

# Typical truck parking space dimensions (meters)
TRUCK_PARKING_WIDTH = 4.0  # meters
TRUCK_PARKING_LENGTH = 15.0  # meters

# Pixel resolution (PDOK Luchtfoto is 25cm per pixel)
PIXEL_RESOLUTION = 0.25  # meters per pixel

def meters_to_degrees(meters: float, latitude: float) -> float:
    """Convert meters to degrees at given latitude."""
    meters_per_degree_lat = 111320  # roughly constant
    meters_per_degree_lon = 111320 * math.cos(math.radians(latitude))
    return meters / meters_per_degree_lat

def get_bbox(lat: float, lon: float, width_m: float = 200, height_m: float = 200) -> Tuple[float, float, float, float]:
    """Calculate bounding box around a point."""
    lat_offset = meters_to_degrees(height_m / 2, lat)
    lon_offset = meters_to_degrees(width_m / 2, lat)

    return (
        lon - lon_offset,  # minx
        lat - lat_offset,  # miny
        lon + lon_offset,  # maxx
        lat + lat_offset   # maxy
    )

def fetch_aerial_image(lat: float, lon: float, width: int = 800, height: int = 800) -> Image.Image:
    """Fetch aerial imagery from PDOK for given coordinates."""
    bbox = get_bbox(lat, lon, width_m=200, height_m=200)

    params = {
        'SERVICE': 'WMS',
        'VERSION': '1.3.0',
        'REQUEST': 'GetMap',
        'FORMAT': 'image/png',
        'TRANSPARENT': 'false',
        'LAYERS': 'Actueel_orthoHR',
        'CRS': 'EPSG:4326',
        'STYLES': '',
        'WIDTH': str(width),
        'HEIGHT': str(height),
        'BBOX': f'{bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]}'  # miny,minx,maxy,maxx for EPSG:4326
    }

    try:
        response = requests.get(PDOK_WMS_URL, params=params, timeout=30)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except Exception as e:
        print(f"  ⚠ Error fetching image: {e}")
        return None

def detect_parking_spaces(image: Image.Image) -> List[Dict]:
    """Detect parking spaces in aerial image using computer vision."""
    # Convert to numpy array
    img_array = np.array(image)

    # Convert to grayscale
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

    # Apply edge detection
    edges = cv2.Canny(gray, 50, 150)

    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    parking_spaces = []

    for contour in contours:
        # Get bounding rectangle
        x, y, w, h = cv2.boundingRect(contour)

        # Convert pixel dimensions to meters
        width_m = w * PIXEL_RESOLUTION
        length_m = h * PIXEL_RESOLUTION

        # Filter for truck-sized spaces (roughly 3-6m wide, 10-20m long)
        if (3 <= width_m <= 6 and 10 <= length_m <= 20) or \
           (3 <= length_m <= 6 and 10 <= width_m <= 20):

            area_m2 = width_m * length_m

            parking_spaces.append({
                'x': x,
                'y': y,
                'width_px': w,
                'height_px': h,
                'width_m': width_m,
                'length_m': length_m,
                'area_m2': area_m2,
                'contour': contour
            })

    return parking_spaces

def pixel_to_geo(x: int, y: int, lat: float, lon: float, img_width: int, img_height: int) -> Tuple[float, float]:
    """Convert pixel coordinates to geographic coordinates."""
    bbox = get_bbox(lat, lon, width_m=200, height_m=200)

    lon_range = bbox[2] - bbox[0]
    lat_range = bbox[3] - bbox[1]

    geo_lon = bbox[0] + (x / img_width) * lon_range
    geo_lat = bbox[3] - (y / img_height) * lat_range

    return geo_lat, geo_lon

def analyze_facility(facility: Dict) -> Dict:
    """Analyze a single facility for parking spaces."""
    facility_id = facility['properties']['osm_id']
    name = facility['properties']['name']
    coords = facility['geometry']['coordinates']
    lon, lat = coords[0], coords[1]

    print(f"\n  Analyzing: {name}")
    print(f"    Coordinates: {lat:.5f}, {lon:.5f}")

    try:
        # Fetch aerial image
        image = fetch_aerial_image(lat, lon)
        if image is None:
            return {
                'facility_id': facility_id,
                'name': name,
                'latitude': lat,
                'longitude': lon,
                'error': 'Failed to fetch image',
                'detected_spaces': 0
            }

        # Detect parking spaces
        spaces = detect_parking_spaces(image)

        print(f"    Detected: {len(spaces)} parking spaces")

        # Convert to geographic coordinates
        parking_spaces_geo = []
        for i, space in enumerate(spaces):
            center_x = space['x'] + space['width_px'] / 2
            center_y = space['y'] + space['height_px'] / 2

            center_lat, center_lon = pixel_to_geo(
                center_x, center_y, lat, lon,
                image.width, image.height
            )

            # Create polygon for the parking space
            half_w = space['width_m'] / 2
            half_l = space['length_m'] / 2

            lat_offset_w = meters_to_degrees(half_w, center_lat)
            lon_offset_l = meters_to_degrees(half_l, center_lat)

            polygon = [
                [center_lon - lon_offset_l, center_lat - lat_offset_w],
                [center_lon + lon_offset_l, center_lat - lat_offset_w],
                [center_lon + lon_offset_l, center_lat + lat_offset_w],
                [center_lon - lon_offset_l, center_lat + lat_offset_w],
                [center_lon - lon_offset_l, center_lat - lat_offset_w]
            ]

            parking_spaces_geo.append({
                'space_number': i + 1,
                'center_lat': center_lat,
                'center_lon': center_lon,
                'width_m': space['width_m'],
                'length_m': space['length_m'],
                'area_m2': space['area_m2'],
                'polygon_geo': polygon
            })

        return {
            'facility_id': facility_id,
            'name': name,
            'latitude': lat,
            'longitude': lon,
            'detected_spaces': len(spaces),
            'parking_spaces': parking_spaces_geo,
            'statistics': {
                'total_area_m2': sum(s['area_m2'] for s in spaces),
                'avg_width_m': sum(s['width_m'] for s in spaces) / len(spaces) if spaces else 0,
                'avg_length_m': sum(s['length_m'] for s in spaces) / len(spaces) if spaces else 0
            }
        }

    except Exception as e:
        print(f"    ✗ Error: {e}")
        return {
            'facility_id': facility_id,
            'name': name,
            'latitude': lat,
            'longitude': lon,
            'error': str(e),
            'detected_spaces': 0
        }

def create_geojson_overlay(results: List[Dict], output_file: str):
    """Create GeoJSON overlay with detected parking spaces."""
    features = []

    for result in results:
        if 'parking_spaces' not in result or not result['parking_spaces']:
            continue

        for space in result['parking_spaces']:
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [space['polygon_geo']]
                },
                'properties': {
                    'facility_id': result['facility_id'],
                    'facility_name': result['name'],
                    'space_number': space['space_number'],
                    'width_m': space['width_m'],
                    'length_m': space['length_m'],
                    'area_m2': space['area_m2']
                }
            }
            features.append(feature)

    geojson = {
        'type': 'FeatureCollection',
        'features': features
    }

    with open(output_file, 'w') as f:
        json.dump(geojson, f, indent=2)

    print(f"\n✓ Created GeoJSON overlay with {len(features)} parking spaces")
    print(f"  Saved to: {output_file}")

def main():
    """Main detection pipeline for South Holland."""
    print("="*80)
    print("SOUTH HOLLAND PARKING SPACE DETECTION FROM SATELLITE IMAGERY")
    print("="*80)

    # Load South Holland facilities
    print("\nLoading South Holland truck parking facilities...")
    with open('south_holland_truck_parking.geojson', 'r') as f:
        geojson_data = json.load(f)

    facilities = geojson_data['features']
    print(f"✓ Loaded {len(facilities)} facilities")

    # Process all facilities (no interactive prompt)
    print(f"\nAnalyzing all {len(facilities)} facilities")
    print(f"Estimated time: ~{len(facilities) * 5} seconds (~{len(facilities) * 5 / 60:.1f} minutes)")
    print("This includes downloading satellite imagery and running computer vision.")

    sample = facilities

    print(f"\n{'='*80}")
    print(f"Analyzing {len(sample)} facilities...")
    print(f"{'='*80}")

    results = []
    for i, facility in enumerate(sample, 1):
        print(f"\n[{i}/{len(sample)}] Processing...")
        result = analyze_facility(facility)
        results.append(result)

        # Rate limiting to avoid overwhelming PDOK
        if i < len(sample):
            time.sleep(2)

    # Save results
    output_file = 'south_holland_parking_detection_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Saved results to: {output_file}")

    # Create GeoJSON overlay
    geojson_file = 'south_holland_parking_spaces_overlay.geojson'
    create_geojson_overlay(results, geojson_file)

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    total_spaces = sum(r.get('detected_spaces', 0) for r in results)
    facilities_with_spaces = sum(1 for r in results if r.get('detected_spaces', 0) > 0)

    print(f"Facilities analyzed: {len(results)}")
    print(f"Facilities with detected spaces: {facilities_with_spaces}")
    print(f"Total parking spaces detected: {total_spaces}")

    if total_spaces > 0:
        total_area = sum(r.get('statistics', {}).get('total_area_m2', 0) for r in results)
        print(f"Total parking area: {total_area:.0f} m²")

if __name__ == "__main__":
    main()
