#!/usr/bin/env python3
"""Analyze Maasvlakte area truck parking facilities."""

import json
from parking_detection import analyze_facility, create_geojson_overlay

def main():
    # Load Maasvlakte facilities
    with open('maasvlakte_facilities.json', 'r') as f:
        facilities = json.load(f)

    print(f"{'='*80}")
    print("MAASVLAKTE AREA PARKING ANALYSIS")
    print(f"{'='*80}")
    print(f"\nTotal facilities to analyze: {len(facilities)}\n")

    results = []

    # Analyze all Maasvlakte facilities
    for i, facility in enumerate(facilities, 1):
        print(f"\n[{i}/{len(facilities)}] Analyzing facility...")
        result = analyze_facility(facility, output_dir="maasvlakte_analysis")
        results.append(result)

    # Save results
    with open('maasvlakte_detection_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    # Create GeoJSON overlay
    create_geojson_overlay(results, output_file="maasvlakte_parking_overlay.geojson")

    # Generate summary report
    print(f"\n{'='*80}")
    print("MAASVLAKTE ANALYSIS SUMMARY")
    print(f"{'='*80}\n")

    total_spaces = sum(r.get('detected_spaces', 0) for r in results)
    total_area = sum(r.get('statistics', {}).get('total_area_m2', 0) for r in results)

    print(f"Facilities analyzed: {len(facilities)}")
    print(f"Total parking spaces detected: {total_spaces}")
    print(f"Total parking area: {total_area:,.0f} m²")
    print(f"Average spaces per facility: {total_spaces / len(facilities):.1f}")

    print(f"\n{'='*80}")
    print("DETAILED RESULTS BY FACILITY")
    print(f"{'='*80}\n")

    for result in results:
        if result.get('detected_spaces', 0) > 0:
            stats = result.get('statistics', {})
            print(f"Facility: {result['name']}")
            print(f"  Location: {result['latitude']:.5f}, {result['longitude']:.5f}")
            print(f"  Detected spaces: {result['detected_spaces']}")
            print(f"  Avg dimensions: {stats.get('avg_length_m', 0):.1f}m × {stats.get('avg_width_m', 0):.1f}m")
            print(f"  Total area: {stats.get('total_area_m2', 0):,.0f} m²")
            print(f"  Estimated individual spaces: {stats.get('total_area_m2', 0) / 60:.0f}")  # 60m² per truck
            print()

    # Calculate parking capacity estimate
    print(f"{'='*80}")
    print("CAPACITY ESTIMATE")
    print(f"{'='*80}\n")

    # Assuming average truck parking space is 4m × 15m = 60 m²
    estimated_capacity = int(total_area / 60)

    print(f"Total parking area: {total_area:,.0f} m²")
    print(f"Assuming 60 m² per truck space (4m × 15m)")
    print(f"Estimated truck capacity: ~{estimated_capacity} trucks")
    print()
    print("Note: This is the area-based estimate. Actual capacity may vary")
    print("based on layout, aisles, and facility configuration.")

    print(f"\n{'='*80}")
    print(f"Analysis complete! Images saved to maasvlakte_analysis/")
    print(f"GeoJSON overlay: maasvlakte_parking_overlay.geojson")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
