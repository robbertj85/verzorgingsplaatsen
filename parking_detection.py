#!/usr/bin/env python3
"""
Detect and count truck parking spaces from PDOK aerial imagery.

This script:
1. Fetches high-resolution aerial imagery from PDOK (Netherlands)
2. Uses computer vision to detect parking spaces
3. Estimates parking space dimensions (typical truck parking: 4m x 15m)
4. Generates GeoJSON overlay for visualization
"""

import json
import requests
from PIL import Image
from io import BytesIO
import numpy as np
import cv2
from typing import List, Tuple, Dict
import math

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
    """
    Calculate bounding box around a point.

    Args:
        lat: Latitude
        lon: Longitude
        width_m: Width in meters
        height_m: Height in meters

    Returns:
        (minx, miny, maxx, maxy) in EPSG:28992 (RD New)
    """
    # For simplicity, we'll use WGS84 and convert to RD coordinates
    # PDOK uses EPSG:28992 (Rijksdriehoekscoördinaten)
    # We'll request in EPSG:4326 (WGS84) and let PDOK handle conversion

    lat_offset = meters_to_degrees(height_m / 2, lat)
    lon_offset = meters_to_degrees(width_m / 2, lat)

    return (
        lon - lon_offset,  # minx
        lat - lat_offset,  # miny
        lon + lon_offset,  # maxx
        lat + lat_offset   # maxy
    )

def fetch_aerial_image(lat: float, lon: float, width: int = 800, height: int = 800) -> Image.Image:
    """
    Fetch aerial imagery from PDOK for given coordinates.

    Args:
        lat: Latitude
        lon: Longitude
        width: Image width in pixels
        height: Image height in pixels

    Returns:
        PIL Image
    """
    bbox = get_bbox(lat, lon, width_m=200, height_m=200)

    params = {
        'SERVICE': 'WMS',
        'VERSION': '1.3.0',
        'REQUEST': 'GetMap',
        'LAYERS': 'Actueel_orthoHR',  # High resolution orthophoto
        'STYLES': '',
        'CRS': 'EPSG:4326',
        'BBOX': f'{bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]}',  # WMS 1.3.0 uses lat,lon order
        'WIDTH': str(width),
        'HEIGHT': str(height),
        'FORMAT': 'image/png',
    }

    print(f"Fetching imagery for {lat}, {lon}...")
    print(f"BBOX: {bbox}")

    response = requests.get(PDOK_WMS_URL, params=params, timeout=30)
    response.raise_for_status()

    return Image.open(BytesIO(response.content))

def detect_parking_spaces_opencv(image: Image.Image) -> List[Dict]:
    """
    Detect parking spaces using OpenCV edge detection and contour analysis.

    Args:
        image: PIL Image of parking lot

    Returns:
        List of detected parking spaces with coordinates and dimensions
    """
    # Convert PIL to OpenCV format
    img_array = np.array(image)
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

    # Convert to grayscale
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Edge detection
    edges = cv2.Canny(blurred, 50, 150)

    # Morphological operations to connect edges
    kernel = np.ones((3, 3), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=2)
    eroded = cv2.erode(dilated, kernel, iterations=1)

    # Find contours
    contours, _ = cv2.findContours(eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    parking_spaces = []

    # Expected dimensions in pixels (assuming 25cm per pixel)
    expected_width_px = TRUCK_PARKING_WIDTH / PIXEL_RESOLUTION  # ~16 pixels
    expected_length_px = TRUCK_PARKING_LENGTH / PIXEL_RESOLUTION  # ~60 pixels

    for contour in contours:
        # Get bounding rectangle
        x, y, w, h = cv2.boundingRect(contour)

        # Calculate aspect ratio
        aspect_ratio = max(w, h) / min(w, h) if min(w, h) > 0 else 0

        # Filter based on size and shape
        # Truck parking spaces should be elongated rectangles
        min_area = (expected_width_px * 0.5) * (expected_length_px * 0.5)
        max_area = (expected_width_px * 2) * (expected_length_px * 2)
        area = cv2.contourArea(contour)

        if min_area < area < max_area and 2.5 < aspect_ratio < 6:
            # This might be a parking space
            # Get more accurate rectangle (rotated rectangle)
            rect = cv2.minAreaRect(contour)
            box = cv2.boxPoints(rect)
            box = np.int32(box)

            # Calculate center
            center_x = int(rect[0][0])
            center_y = int(rect[0][1])

            # Calculate dimensions in meters
            width_m = min(rect[1][0], rect[1][1]) * PIXEL_RESOLUTION
            length_m = max(rect[1][0], rect[1][1]) * PIXEL_RESOLUTION

            parking_spaces.append({
                'center_px': (center_x, center_y),
                'bbox_px': box.tolist(),
                'width_m': round(width_m, 2),
                'length_m': round(length_m, 2),
                'area_m2': round(width_m * length_m, 2),
                'angle': rect[2]
            })

    return parking_spaces

def create_annotated_image(image: Image.Image, parking_spaces: List[Dict]) -> Image.Image:
    """Create an annotated image showing detected parking spaces."""
    img_array = np.array(image)
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

    for i, space in enumerate(parking_spaces):
        # Draw parking space outline
        box = np.array(space['bbox_px'])
        cv2.drawContours(img_bgr, [box], 0, (0, 255, 0), 2)

        # Add label
        center = space['center_px']
        label = f"#{i+1}: {space['length_m']}m x {space['width_m']}m"
        cv2.putText(img_bgr, label, (center[0] - 50, center[1]),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)

    # Add summary
    summary = f"Detected: {len(parking_spaces)} spaces"
    cv2.putText(img_bgr, summary, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(img_rgb)

def pixel_to_geo(center_px: Tuple[int, int], lat: float, lon: float,
                 image_width: int, image_height: int, bbox_width_m: float = 200) -> Tuple[float, float]:
    """
    Convert pixel coordinates to geographic coordinates.

    Args:
        center_px: (x, y) pixel coordinates
        lat: Center latitude
        lon: Center longitude
        image_width: Image width in pixels
        image_height: Image height in pixels
        bbox_width_m: Bounding box width in meters

    Returns:
        (latitude, longitude)
    """
    # Calculate offset from center in pixels
    offset_x_px = center_px[0] - (image_width / 2)
    offset_y_px = (image_height / 2) - center_px[1]  # Y is inverted

    # Convert to meters
    offset_x_m = offset_x_px * PIXEL_RESOLUTION * (bbox_width_m / (image_width * PIXEL_RESOLUTION))
    offset_y_m = offset_y_px * PIXEL_RESOLUTION * (bbox_width_m / (image_width * PIXEL_RESOLUTION))

    # Convert to degrees
    offset_lat = meters_to_degrees(offset_y_m, lat)
    offset_lon = meters_to_degrees(offset_x_m, lat)

    return (lat + offset_lat, lon + offset_lon)

def bbox_to_geo_polygon(bbox_px: List, lat: float, lon: float,
                        image_width: int, image_height: int, bbox_width_m: float = 200) -> List[List[float]]:
    """Convert pixel bounding box to geographic polygon."""
    polygon = []
    for point in bbox_px:
        geo_coords = pixel_to_geo((point[0], point[1]), lat, lon, image_width, image_height, bbox_width_m)
        polygon.append([geo_coords[1], geo_coords[0]])  # GeoJSON uses [lon, lat]

    # Close the polygon
    polygon.append(polygon[0])
    return polygon

def analyze_facility(facility: Dict, output_dir: str = "parking_analysis") -> Dict:
    """
    Analyze a single facility for parking spaces.

    Args:
        facility: Facility data from rotterdam_facilities.json
        output_dir: Directory to save output images

    Returns:
        Analysis results including detected parking spaces
    """
    import os
    os.makedirs(output_dir, exist_ok=True)

    lat = facility['latitude']
    lon = facility['longitude']
    facility_id = facility['id']

    print(f"\n{'='*80}")
    print(f"Analyzing: {facility['name']} (ID: {facility_id})")
    print(f"Location: {lat}, {lon}")
    print(f"Municipality: {facility['municipality']}")

    try:
        # Fetch aerial imagery
        image = fetch_aerial_image(lat, lon)

        # Save original image
        image.save(f"{output_dir}/{facility_id}_original.png")
        print(f"Saved original image")

        # Detect parking spaces
        parking_spaces = detect_parking_spaces_opencv(image)
        print(f"Detected {len(parking_spaces)} potential parking spaces")

        # Convert pixel coordinates to geo coordinates
        for space in parking_spaces:
            space['center_geo'] = pixel_to_geo(
                space['center_px'], lat, lon,
                image.width, image.height
            )
            space['polygon_geo'] = bbox_to_geo_polygon(
                space['bbox_px'], lat, lon,
                image.width, image.height
            )

        # Create annotated image
        annotated = create_annotated_image(image, parking_spaces)
        annotated.save(f"{output_dir}/{facility_id}_detected.png")
        print(f"Saved annotated image")

        # Calculate statistics
        if parking_spaces:
            avg_width = sum(s['width_m'] for s in parking_spaces) / len(parking_spaces)
            avg_length = sum(s['length_m'] for s in parking_spaces) / len(parking_spaces)
            total_area = sum(s['area_m2'] for s in parking_spaces)
        else:
            avg_width = avg_length = total_area = 0

        results = {
            'facility_id': facility_id,
            'name': facility['name'],
            'latitude': lat,
            'longitude': lon,
            'municipality': facility['municipality'],
            'detected_spaces': len(parking_spaces),
            'parking_spaces': parking_spaces,
            'statistics': {
                'avg_width_m': round(avg_width, 2),
                'avg_length_m': round(avg_length, 2),
                'total_area_m2': round(total_area, 2)
            }
        }

        return results

    except Exception as e:
        print(f"Error analyzing facility: {e}")
        return {
            'facility_id': facility_id,
            'name': facility['name'],
            'latitude': lat,
            'longitude': lon,
            'error': str(e),
            'detected_spaces': 0
        }

def create_geojson_overlay(results: List[Dict], output_file: str = "parking_spaces_overlay.geojson"):
    """
    Create GeoJSON file with detected parking spaces for map overlay.

    Args:
        results: List of analysis results
        output_file: Output GeoJSON file path
    """
    features = []

    for result in results:
        if 'parking_spaces' not in result:
            continue

        for i, space in enumerate(result['parking_spaces']):
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [space['polygon_geo']]
                },
                'properties': {
                    'facility_id': result['facility_id'],
                    'facility_name': result['name'],
                    'space_number': i + 1,
                    'width_m': space['width_m'],
                    'length_m': space['length_m'],
                    'area_m2': space['area_m2'],
                    'angle': space['angle']
                }
            }
            features.append(feature)

    geojson = {
        'type': 'FeatureCollection',
        'features': features
    }

    with open(output_file, 'w') as f:
        json.dump(geojson, f, indent=2)

    print(f"\nCreated GeoJSON overlay with {len(features)} parking spaces")
    print(f"Saved to: {output_file}")

def main():
    """Main analysis pipeline."""
    # Load Rotterdam facilities
    with open('rotterdam_facilities.json', 'r') as f:
        facilities = json.load(f)

    # Filter for truck parking and a small sample
    truck_facilities = [f for f in facilities if f['is_truck_parking']]

    print(f"Total facilities in Rotterdam area: {len(facilities)}")
    print(f"Truck parking facilities: {len(truck_facilities)}")

    # Start with a small sample (first 3 truck parking facilities)
    sample = truck_facilities[:3] if truck_facilities else facilities[:3]

    print(f"\nAnalyzing {len(sample)} sample facilities...")

    results = []
    for facility in sample:
        result = analyze_facility(facility)
        results.append(result)

    # Save results
    with open('parking_detection_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    # Create GeoJSON overlay
    create_geojson_overlay(results)

    # Print summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    total_detected = sum(r.get('detected_spaces', 0) for r in results)
    print(f"Total parking spaces detected: {total_detected}")

    for result in results:
        if result.get('detected_spaces', 0) > 0:
            stats = result.get('statistics', {})
            print(f"\n{result['name']}:")
            print(f"  Spaces detected: {result['detected_spaces']}")
            print(f"  Avg dimensions: {stats.get('avg_length_m', 0)}m x {stats.get('avg_width_m', 0)}m")
            print(f"  Total area: {stats.get('total_area_m2', 0)} m²")

if __name__ == "__main__":
    main()
