#!/usr/bin/env python3
"""Find truck parking facilities in Rotterdam port area."""

import json

# Load the data
with open('truck-parking-map/public/truck_parking_enriched.json', 'r') as f:
    data = json.load(f)

# Filter for Rotterdam area (including port)
# Rotterdam port area is roughly: lat 51.8-52.0, lon 4.0-4.5
rotterdam_facilities = []

for facility in data:
    lat = facility.get('latitude')
    lon = facility.get('longitude')

    if lat is None or lon is None:
        continue

    # Rotterdam port area coordinates
    if 51.8 <= lat <= 52.0 and 4.0 <= lon <= 4.5:
        municipality = facility.get('location', {}).get('municipality', '')
        rotterdam_facilities.append({
            'id': facility['id'],
            'name': facility['name'],
            'latitude': lat,
            'longitude': lon,
            'municipality': municipality,
            'highway': facility.get('location', {}).get('highway', ''),
            'is_truck_parking': facility['classification']['is_truck_parking'],
            'capacity': facility.get('capacity', {}),
            'tags': facility.get('tags', {})
        })

print(f"Found {len(rotterdam_facilities)} facilities in Rotterdam port area\n")

# Show first 15
for i, fac in enumerate(rotterdam_facilities[:15], 1):
    capacity = fac['capacity'].get('capacity:truck', fac['capacity'].get('capacity:hgv', 'N/A'))
    print(f"{i}. {fac['name']}")
    print(f"   Location: {fac['municipality']} - {fac['highway']}")
    print(f"   Coords: {fac['latitude']:.5f}, {fac['longitude']:.5f}")
    print(f"   Truck parking: {fac['is_truck_parking']}")
    print(f"   Capacity: {capacity}")
    print()

# Save to file for processing
with open('rotterdam_facilities.json', 'w') as f:
    json.dump(rotterdam_facilities, f, indent=2)

print(f"\nSaved {len(rotterdam_facilities)} facilities to rotterdam_facilities.json")
