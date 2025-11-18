#!/usr/bin/env python3
"""
Maasvlakte Pilot: Fixed parking space estimation with proper truck classification
"""

import json
import math
import numpy as np
import requests
from io import BytesIO
from PIL import Image
import cv2
from typing import List, Dict, Optional, Tuple
from shapely.geometry import Polygon, Point
from shapely import affinity

# Constants
METERS_PER_DEGREE_LAT = 111320
METERS_PER_DEGREE_LON = 70000

# Vehicle dimensions (meters)
TRUCK_SPACE_WIDTH = 4.0
TRUCK_SPACE_LENGTH = 15.0
VAN_SPACE_WIDTH = 2.5
VAN_SPACE_LENGTH = 5.0

# Maasvlakte bounding box (Rotterdam port area)
MAASVLAKTE_BOUNDS = {
    'min_lat': 51.90,
    'max_lat': 51.98,
    'min_lon': 4.00,
    'max_lon': 4.15
}

def calculate_polygon_area_m2(coords: List[List[float]], centroid_lat: float) -> float:
    """Calculate polygon area in square meters."""
    if len(coords) < 3:
        return 0.0

    # Shoelace formula
    area_deg2 = 0.0
    n = len(coords)
    for i in range(n):
        j = (i + 1) % n
        area_deg2 += coords[i][0] * coords[j][1]
        area_deg2 -= coords[j][0] * coords[i][1]
    area_deg2 = abs(area_deg2) / 2.0

    # Convert to m²
    lat_m_per_deg = METERS_PER_DEGREE_LAT
    lon_m_per_deg = METERS_PER_DEGREE_LON * math.cos(math.radians(centroid_lat))
    area_m2 = area_deg2 * lat_m_per_deg * lon_m_per_deg

    return area_m2

def fetch_satellite_image(polygon_coords: List[List[float]], buffer_m: float = 20) -> Optional[np.ndarray]:
    """Fetch satellite imagery from PDOK."""
    try:
        lons = [coord[0] for coord in polygon_coords]
        lats = [coord[1] for coord in polygon_coords]
        min_lon, max_lon = min(lons), max(lons)
        min_lat, max_lat = min(lats), max(lats)

        centroid_lat = (min_lat + max_lat) / 2
        lat_buffer = buffer_m / METERS_PER_DEGREE_LAT
        lon_buffer = buffer_m / (METERS_PER_DEGREE_LON * math.cos(math.radians(centroid_lat)))

        # For WMS 1.3.0 with EPSG:4326, axis order is lat,lon!
        bbox = f"{min_lat - lat_buffer},{min_lon - lon_buffer},{max_lat + lat_buffer},{max_lon + lon_buffer}"

        wms_url = "https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0"
        params = {
            'SERVICE': 'WMS',
            'VERSION': '1.3.0',
            'REQUEST': 'GetMap',
            'LAYERS': '2023_orthoHR',
            'CRS': 'EPSG:4326',
            'BBOX': bbox,
            'WIDTH': '512',
            'HEIGHT': '512',
            'FORMAT': 'image/png'
        }

        response = requests.get(wms_url, params=params, timeout=30)
        response.raise_for_status()

        image = Image.open(BytesIO(response.content))
        image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        return image_cv

    except Exception as e:
        print(f"      ⚠ Failed to fetch satellite image: {e}")
        return None

def detect_parking_orientation(image: np.ndarray) -> Optional[float]:
    """Detect parking orientation using computer vision."""
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        binary = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )
        edges = cv2.Canny(binary, 50, 150, apertureSize=3)

        lines = cv2.HoughLinesP(
            edges, rho=1, theta=np.pi/180, threshold=50,
            minLineLength=30, maxLineGap=10
        )

        if lines is None or len(lines) == 0:
            return None

        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
            if angle < 0:
                angle += 180
            angles.append(angle)

        hist, bin_edges = np.histogram(angles, bins=36, range=(0, 180))
        dominant_bin = np.argmax(hist)
        dominant_angle = (bin_edges[dominant_bin] + bin_edges[dominant_bin + 1]) / 2

        # Snap to common angles
        snap_threshold = 10
        common_angles = [0, 45, 90, 135]
        for snap_angle in common_angles:
            if abs(dominant_angle - snap_angle) < snap_threshold:
                dominant_angle = snap_angle
                break

        return dominant_angle

    except Exception as e:
        return None

def estimate_spaces_in_polygon(
    polygon_coords: List[List[float]],
    capacity: int,
    vehicle_type: str,
    centroid_lat: float,
    centroid_lon: float,
    rotation_angle: Optional[float] = None
) -> List[Dict]:
    """Estimate parking spaces with rotation, keeping within polygon bounds."""

    # Choose dimensions based on vehicle type
    if vehicle_type == 'truck':
        space_width_m = TRUCK_SPACE_WIDTH
        space_length_m = TRUCK_SPACE_LENGTH
    else:
        space_width_m = VAN_SPACE_WIDTH
        space_length_m = VAN_SPACE_LENGTH

    # Convert to degrees
    lat_per_m = 1 / METERS_PER_DEGREE_LAT
    lon_per_m = 1 / (METERS_PER_DEGREE_LON * math.cos(math.radians(centroid_lat)))

    space_width_deg = space_width_m * lon_per_m
    space_length_deg = space_length_m * lat_per_m

    # Create polygon for bounds checking
    parking_polygon = Polygon(polygon_coords)

    # Calculate polygon bounding box
    lons = [coord[0] for coord in polygon_coords]
    lats = [coord[1] for coord in polygon_coords]
    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)

    # Estimate grid dimensions
    width_deg = max_lon - min_lon
    height_deg = max_lat - min_lat

    cols = max(1, int(width_deg / space_width_deg))
    rows = max(1, int(height_deg / space_length_deg))

    # Limit total spaces
    max_spaces = capacity if capacity > 0 else rows * cols
    max_spaces = min(max_spaces, 200)  # Cap at 200 spaces per area

    spaces = []
    space_num = 1

    for row in range(rows):
        for col in range(cols):
            if space_num > max_spaces:
                break

            # Calculate center
            center_lon = min_lon + (col + 0.5) * space_width_deg
            center_lat = min_lat + (row + 0.5) * space_length_deg

            # Create space rectangle
            half_width = space_width_deg / 2
            half_length = space_length_deg / 2

            space_coords = [
                [center_lon - half_width, center_lat - half_length],
                [center_lon + half_width, center_lat - half_length],
                [center_lon + half_width, center_lat + half_length],
                [center_lon - half_width, center_lat + half_length],
                [center_lon - half_width, center_lat - half_length]
            ]

            # Apply rotation if detected
            if rotation_angle is not None and rotation_angle != 0:
                space_polygon = Polygon(space_coords)
                rotated_polygon = affinity.rotate(
                    space_polygon,
                    -rotation_angle,
                    origin=(center_lon, center_lat)
                )
                space_coords = list(rotated_polygon.exterior.coords)

            # Check if space center is within parking area
            point = Point(center_lon, center_lat)
            if not parking_polygon.contains(point):
                continue

            space_data = {
                'space_number': space_num,
                'center_lat': center_lat,
                'center_lon': center_lon,
                'width_m': space_width_m,
                'length_m': space_length_m,
                'area_m2': space_width_m * space_length_m,
                'polygon_coords': space_coords,
                'estimated': True
            }

            if rotation_angle is not None:
                space_data['rotation_angle'] = rotation_angle

            spaces.append(space_data)
            space_num += 1

        if space_num > max_spaces:
            break

    return spaces

def is_facility_in_maasvlakte(lat: float, lon: float) -> bool:
    """Check if facility is in Maasvlakte area."""
    return (MAASVLAKTE_BOUNDS['min_lat'] <= lat <= MAASVLAKTE_BOUNDS['max_lat'] and
            MAASVLAKTE_BOUNDS['min_lon'] <= lon <= MAASVLAKTE_BOUNDS['max_lon'])

def classify_facility_vehicle_type(facility: Dict) -> str:
    """
    Classify facility vehicle type based on facility-level tags.
    For Maasvlakte (port area), default to TRUCK unless explicitly marked as car.
    """
    # Check if facility has individual OSM truck spaces already
    if 'osm_parking_spaces' in facility and len(facility['osm_parking_spaces']) > 0:
        # Check if any are marked as HGV/truck
        for space in facility['osm_parking_spaces']:
            if space.get('classification', {}).get('is_hgv', False):
                return 'truck'
            if space.get('classification', {}).get('vehicle_type') == 'truck':
                return 'truck'

    # Check facility-level tags from parking areas
    for area in facility.get('osm_parking_areas', []):
        tags = area.get('tags', {})

        # Check for HGV designation
        if tags.get('hgv') in ['designated', 'yes']:
            return 'truck'
        if tags.get('capacity:hgv') or tags.get('capacity:truck'):
            return 'truck'
        if 'truck' in tags.get('name', '').lower():
            return 'truck'
        if 'hgv' in tags.get('name', '').lower():
            return 'truck'
        if 'vrachtwagen' in tags.get('name', '').lower():
            return 'truck'

    # Maasvlakte default: TRUCK (it's a port/logistics area)
    return 'truck'

if __name__ == "__main__":
    print("="*80)
    print("MAASVLAKTE PILOT: Fixed Parking Space Estimation")
    print("="*80)

    # Load OSM analysis
    with open("south_holland_osm_parking_analysis.json", "r") as f:
        data = json.load(f)

    # Filter Maasvlakte facilities
    maasvlakte_facilities = []
    for facility in data["facilities"]:
        lat = facility['facility_lat']
        lon = facility['facility_lon']
        if is_facility_in_maasvlakte(lat, lon):
            # Only process if no individual spaces OR parking areas exist
            has_areas = len(facility.get('osm_parking_areas', [])) > 0
            has_spaces = len(facility.get('osm_parking_spaces', [])) > 0

            if has_areas and not has_spaces:
                maasvlakte_facilities.append(facility)

    print(f"\nFound {len(maasvlakte_facilities)} Maasvlakte facilities needing estimation")
    print(f"Bounds: {MAASVLAKTE_BOUNDS}")
    print()

    all_estimated_spaces = []

    for idx, facility in enumerate(maasvlakte_facilities, 1):
        facility_id = facility['facility_id']
        facility_name = facility.get('facility_name', 'Unnamed')

        # Determine vehicle type at facility level
        vehicle_type = classify_facility_vehicle_type(facility)

        print(f"[{idx}/{len(maasvlakte_facilities)}] {facility_name}")
        print(f"  Facility ID: {facility_id}")
        print(f"  Vehicle Type: {vehicle_type.upper()}")
        print(f"  Parking areas: {len(facility['osm_parking_areas'])}")

        for area in facility['osm_parking_areas']:
            coords = area['geometry']['coordinates'][0]
            area_m2 = calculate_polygon_area_m2(coords, facility['facility_lat'])

            print(f"    Area: {area_m2:.1f} m²")

            # Get capacity
            capacity = area.get('capacity', 0)
            if capacity == 0 and facility['total_capacity'] > 0:
                capacity = facility['total_capacity'] // len(facility['osm_parking_areas'])

            if capacity == 0 and area_m2 > 0:
                space_area = TRUCK_SPACE_WIDTH * TRUCK_SPACE_LENGTH if vehicle_type == 'truck' else VAN_SPACE_WIDTH * VAN_SPACE_LENGTH
                capacity = int((area_m2 * 0.5) / space_area)  # 50% efficiency (conservative)

            capacity = min(capacity, 200)  # Cap per area
            print(f"    Capacity: {capacity} spaces")

            # Fetch satellite and detect rotation
            print(f"    📡 Fetching satellite imagery...")
            satellite_image = fetch_satellite_image(coords, buffer_m=20)
            rotation_angle = None

            if satellite_image is not None:
                print(f"    🔍 Detecting orientation...")
                rotation_angle = detect_parking_orientation(satellite_image)

                if rotation_angle is not None:
                    print(f"    ✓ Detected rotation: {rotation_angle:.1f}°")
                else:
                    print(f"    ⚠ Could not detect orientation")

            # Estimate spaces
            spaces = estimate_spaces_in_polygon(
                coords,
                capacity,
                vehicle_type,
                facility['facility_lat'],
                facility['facility_lon'],
                rotation_angle
            )

            print(f"    ✓ Generated: {len(spaces)} {vehicle_type} parking spaces")

            # Create GeoJSON features
            for space in spaces:
                feature = {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Polygon',
                        'coordinates': [space['polygon_coords']]
                    },
                    'properties': {
                        'feature_type': 'estimated_parking_space',
                        'facility_id': facility_id,
                        'facility_name': facility_name,
                        'parking_area_osm_id': area.get('osm_id'),
                        'space_number': space['space_number'],
                        'vehicle_type': vehicle_type,
                        'vehicle_label': 'Truck Parking Space (N2/N3)' if vehicle_type == 'truck' else 'Van/Car Parking Space (N1)',
                        'color': '#ef4444' if vehicle_type == 'truck' else '#3b82f6',
                        'width_m': space['width_m'],
                        'length_m': space['length_m'],
                        'area_m2': space['area_m2'],
                        'estimated': True,
                        'rotation_angle': space.get('rotation_angle'),
                        'satellite_analyzed': satellite_image is not None
                    }
                }
                all_estimated_spaces.append(feature)

        print()

    # Save output
    output = {
        'type': 'FeatureCollection',
        'features': all_estimated_spaces
    }

    output_file = "maasvlakte_estimated_parking_pilot.geojson"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Facilities processed: {len(maasvlakte_facilities)}")
    print(f"Total estimated spaces: {len(all_estimated_spaces)}")

    # Count by vehicle type
    vehicle_counts = {}
    for feat in all_estimated_spaces:
        vtype = feat['properties']['vehicle_type']
        vehicle_counts[vtype] = vehicle_counts.get(vtype, 0) + 1

    print(f"\nBy vehicle type:")
    for vtype, count in vehicle_counts.items():
        print(f"  {vtype}: {count}")

    print(f"\n✓ Saved to: {output_file}")
