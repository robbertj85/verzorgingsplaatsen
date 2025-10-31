#!/usr/bin/env python3
"""
Data Analysis Script for Dutch Truck Parking Facilities
Generates statistics, reports, and visualizations from the database
"""

import json
import csv
from collections import defaultdict
from pathlib import Path

def load_database():
    """Load the main database JSON file"""
    db_path = Path(__file__).parent.parent / 'data' / 'verzorgingsplaatsen_database.json'
    with open(db_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_coordinates():
    """Load facility coordinates"""
    coord_path = Path(__file__).parent.parent / 'data' / 'facility_coordinates.json'
    with open(coord_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_facilities(database):
    """Perform comprehensive analysis of all facilities"""

    facilities = database.get('facilities', [])
    private_facilities = database.get('secured_private_facilities', [])
    all_facilities = facilities + private_facilities

    stats = {
        'total_facilities': len(all_facilities),
        'motorway_facilities': len(facilities),
        'private_facilities': len(private_facilities),
        'by_motorway': defaultdict(int),
        'by_province': defaultdict(int),
        'by_operator': defaultdict(int),
        'by_confidence': defaultdict(int),
        'truck_spaces': {
            'total_confirmed': 0,
            'facilities_with_data': 0,
            'average_per_facility': 0
        }
    }

    # Analyze motorway facilities
    for facility in facilities:
        motorway = facility.get('motorway', 'Unknown')
        stats['by_motorway'][motorway] += 1

        province = facility.get('location', {}).get('province', 'Unknown')
        stats['by_province'][province] += 1

        operator = facility.get('facilities', {}).get('fuel_station', {}).get('operator', 'Unknown')
        if operator != 'Not specified':
            stats['by_operator'][operator] += 1

        confidence = facility.get('confidence_level', 'Unknown')
        stats['by_confidence'][confidence] += 1

        # Truck spaces
        spaces = facility.get('parking_capacity', {}).get('truck_spaces')
        if isinstance(spaces, int):
            stats['truck_spaces']['total_confirmed'] += spaces
            stats['truck_spaces']['facilities_with_data'] += 1

    # Analyze private facilities
    for facility in private_facilities:
        province = facility.get('location', {}).get('province', 'Unknown')
        stats['by_province'][province] += 1

        operator = facility.get('operator', 'Unknown')
        stats['by_operator'][operator] += 1

        confidence = facility.get('confidence_level', 'Unknown')
        stats['by_confidence'][confidence] += 1

        spaces = facility.get('parking_capacity', {}).get('truck_spaces')
        if isinstance(spaces, int):
            stats['truck_spaces']['total_confirmed'] += spaces
            stats['truck_spaces']['facilities_with_data'] += 1

    # Calculate average
    if stats['truck_spaces']['facilities_with_data'] > 0:
        stats['truck_spaces']['average_per_facility'] = round(
            stats['truck_spaces']['total_confirmed'] / stats['truck_spaces']['facilities_with_data'],
            1
        )

    return stats

def generate_report(stats, database):
    """Generate a comprehensive text report"""

    report = []
    report.append("=" * 80)
    report.append("DUTCH TRUCK PARKING FACILITIES - DATA ANALYSIS REPORT")
    report.append("=" * 80)
    report.append("")

    report.append("OVERVIEW STATISTICS")
    report.append("-" * 80)
    report.append(f"Total Facilities Documented:     {stats['total_facilities']}")
    report.append(f"  - Motorway Rest Areas:         {stats['motorway_facilities']}")
    report.append(f"  - Private Secured Parking:     {stats['private_facilities']}")
    report.append("")

    report.append("TRUCK PARKING CAPACITY")
    report.append("-" * 80)
    report.append(f"Total Confirmed Truck Spaces:    {stats['truck_spaces']['total_confirmed']}")
    report.append(f"Facilities with Capacity Data:   {stats['truck_spaces']['facilities_with_data']} / {stats['total_facilities']}")
    report.append(f"Average Spaces per Facility:     {stats['truck_spaces']['average_per_facility']}")
    report.append(f"Data Completeness:               {round(stats['truck_spaces']['facilities_with_data'] / stats['total_facilities'] * 100, 1)}%")
    report.append("")

    report.append("DISTRIBUTION BY MOTORWAY")
    report.append("-" * 80)
    for motorway, count in sorted(stats['by_motorway'].items()):
        report.append(f"  {motorway:10s} {count:3d} facilities")
    report.append("")

    report.append("DISTRIBUTION BY PROVINCE")
    report.append("-" * 80)
    for province, count in sorted(stats['by_province'].items(), key=lambda x: -x[1]):
        report.append(f"  {province:30s} {count:3d} facilities")
    report.append("")

    report.append("TOP OPERATORS")
    report.append("-" * 80)
    top_operators = sorted(stats['by_operator'].items(), key=lambda x: -x[1])[:10]
    for operator, count in top_operators:
        report.append(f"  {operator:40s} {count:3d} facilities")
    report.append("")

    report.append("DATA CONFIDENCE LEVELS")
    report.append("-" * 80)
    for confidence, count in sorted(stats['by_confidence'].items()):
        percentage = round(count / stats['total_facilities'] * 100, 1)
        report.append(f"  {confidence:10s} {count:3d} facilities ({percentage}%)")
    report.append("")

    report.append("JURISDICTIONAL AUTHORITY STRUCTURE")
    report.append("-" * 80)
    report.append(f"National (Rijkswaterstaat):      {stats['motorway_facilities']} facilities (83%)")
    report.append(f"Private Operators:               {stats['private_facilities']} facilities (17%)")
    report.append("")

    report.append("POLICY CONTEXT")
    report.append("-" * 80)
    policy = database.get('policy_context', {})
    shortage = policy.get('parking_shortage', {})
    report.append(f"Estimated National Shortage:     {shortage.get('estimated_deficit', 'Unknown')}")
    report.append("")

    report.append("=" * 80)
    report.append(f"Report generated from database version {database['metadata']['version']}")
    report.append(f"Last updated: {database['metadata']['last_updated']}")
    report.append("=" * 80)

    return "\n".join(report)

def export_analysis_csv(stats):
    """Export analysis results to CSV"""

    output_path = Path(__file__).parent.parent / 'data' / 'analysis_summary.csv'

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Write overview
        writer.writerow(['Category', 'Metric', 'Value'])
        writer.writerow(['Overview', 'Total Facilities', stats['total_facilities']])
        writer.writerow(['Overview', 'Motorway Facilities', stats['motorway_facilities']])
        writer.writerow(['Overview', 'Private Facilities', stats['private_facilities']])
        writer.writerow([])

        # Write motorway distribution
        writer.writerow(['Motorway', 'Facility Count'])
        for motorway, count in sorted(stats['by_motorway'].items()):
            writer.writerow([motorway, count])
        writer.writerow([])

        # Write province distribution
        writer.writerow(['Province', 'Facility Count'])
        for province, count in sorted(stats['by_province'].items(), key=lambda x: -x[1]):
            writer.writerow([province, count])
        writer.writerow([])

        # Write operator distribution
        writer.writerow(['Operator', 'Facility Count'])
        for operator, count in sorted(stats['by_operator'].items(), key=lambda x: -x[1]):
            writer.writerow([operator, count])

    return output_path

def main():
    """Main execution function"""

    print("Loading database...")
    database = load_database()
    coordinates = load_coordinates()

    print("Analyzing facilities...")
    stats = analyze_facilities(database)

    print("\nGenerating report...")
    report = generate_report(stats, database)

    # Save report to file
    report_path = Path(__file__).parent.parent / 'docs' / 'analysis_report.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"Report saved to: {report_path}")

    # Export CSV
    csv_path = export_analysis_csv(stats)
    print(f"Analysis CSV saved to: {csv_path}")

    # Print report to console
    print("\n" + report)

    # Coordinate accuracy summary
    print("\nCOORDINATE ACCURACY SUMMARY")
    print("-" * 80)
    accuracy_counts = defaultdict(int)
    for facility_id, coord_data in coordinates['facilities'].items():
        accuracy = coord_data.get('accuracy', 'unknown')
        accuracy_counts[accuracy] += 1

    for accuracy, count in sorted(accuracy_counts.items()):
        percentage = round(count / len(coordinates['facilities']) * 100, 1)
        print(f"  {accuracy:10s} {count:3d} facilities ({percentage}%)")

if __name__ == '__main__':
    main()
