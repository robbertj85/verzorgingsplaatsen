#!/usr/bin/env python3
"""
Generate comprehensive summary report
"""

import json
from collections import defaultdict
from datetime import datetime

def load_data():
    """Load data and statistics"""
    with open('/Users/robbertjanssen/Documents/dev/Verzorgingsplaatsen/truck_parking_enriched.json', 'r') as f:
        facilities = json.load(f)

    with open('/Users/robbertjanssen/Documents/dev/Verzorgingsplaatsen/analysis_stats.json', 'r') as f:
        stats = json.load(f)

    return facilities, stats

def analyze_data_quality(facilities):
    """Analyze data quality and completeness"""
    quality_metrics = {
        'total_facilities': len(facilities),
        'with_name': sum(1 for f in facilities if f.get('name') and f['name'] != 'Unnamed'),
        'with_coordinates': sum(1 for f in facilities if f.get('latitude') and f.get('longitude')),
        'with_polygons': sum(1 for f in facilities if f.get('geometry', {}).get('type') == 'Polygon'),
        'with_capacity': sum(1 for f in facilities if f.get('capacity')),
        'with_truck_capacity': sum(1 for f in facilities if f.get('capacity', {}).get('truck_spots')),
        'with_amenities': sum(1 for f in facilities if f.get('amenities')),
        'with_operator': sum(1 for f in facilities if f.get('operator')),
        'with_hours': sum(1 for f in facilities if f.get('opening_hours')),
        'with_province': sum(1 for f in facilities if f.get('location', {}).get('province', 'Unknown') != 'Unknown'),
        'with_municipality': sum(1 for f in facilities if f.get('location', {}).get('municipality')),
        'high_confidence': sum(1 for f in facilities if f.get('confidence_score', 0) >= 0.7),
        'designated_truck': sum(1 for f in facilities if f.get('classification', {}).get('is_truck_parking')),
    }

    # Calculate percentages
    total = quality_metrics['total_facilities']
    quality_percentages = {
        key: (value / total * 100) if total > 0 else 0
        for key, value in quality_metrics.items()
    }

    return quality_metrics, quality_percentages

def identify_gaps(facilities):
    """Identify data gaps and issues"""
    gaps = {
        'missing_capacity': [],
        'missing_location': [],
        'low_confidence': [],
        'no_polygon': [],
        'incomplete_amenities': []
    }

    for facility in facilities:
        facility_id = facility.get('id', 'unknown')
        name = facility.get('name', 'Unnamed')

        # Missing capacity
        if not facility.get('capacity'):
            gaps['missing_capacity'].append({'id': facility_id, 'name': name})

        # Missing location details
        if facility.get('location', {}).get('province', 'Unknown') == 'Unknown':
            gaps['missing_location'].append({'id': facility_id, 'name': name})

        # Low confidence
        if facility.get('confidence_score', 0) < 0.5:
            gaps['low_confidence'].append({
                'id': facility_id,
                'name': name,
                'score': facility.get('confidence_score', 0)
            })

        # No polygon
        if facility.get('geometry', {}).get('type') != 'Polygon':
            gaps['no_polygon'].append({'id': facility_id, 'name': name})

        # Check if designated truck parking but missing amenities
        if facility.get('classification', {}).get('is_truck_parking') and not facility.get('amenities'):
            gaps['incomplete_amenities'].append({'id': facility_id, 'name': name})

    return gaps

def generate_recommendations(quality_metrics, gaps, stats):
    """Generate recommendations for data improvement"""
    recommendations = []

    # Capacity data
    missing_capacity_pct = (len(gaps['missing_capacity']) / quality_metrics['total_facilities'] * 100)
    if missing_capacity_pct > 50:
        recommendations.append({
            'priority': 'High',
            'category': 'Capacity Data',
            'issue': f"{missing_capacity_pct:.1f}% of facilities missing capacity information",
            'action': 'Estimate capacity from polygon areas (typical: 30-40 m² per truck spot) or aerial imagery analysis',
            'affected_facilities': len(gaps['missing_capacity'])
        })

    # Location data
    missing_location_pct = (len(gaps['missing_location']) / quality_metrics['total_facilities'] * 100)
    if missing_location_pct > 50:
        recommendations.append({
            'priority': 'High',
            'category': 'Location Data',
            'issue': f"{missing_location_pct:.1f}% of facilities missing province/municipality information",
            'action': 'Continue Nominatim reverse geocoding for remaining facilities (rate limited to 1 req/sec)',
            'affected_facilities': len(gaps['missing_location'])
        })

    # Polygon boundaries
    missing_polygon_pct = (len(gaps['no_polygon']) / quality_metrics['total_facilities'] * 100)
    if missing_polygon_pct > 10:
        recommendations.append({
            'priority': 'Medium',
            'category': 'Polygon Boundaries',
            'issue': f"{missing_polygon_pct:.1f}% of facilities only have point coordinates",
            'action': 'Enhance OSM data or use satellite imagery to map actual parking boundaries',
            'affected_facilities': len(gaps['no_polygon'])
        })

    # Government data sources
    recommendations.append({
        'priority': 'High',
        'category': 'Additional Data Sources',
        'issue': 'Government APIs (NDW, Rijkswaterstaat) not accessible or changed',
        'action': 'Contact Rijkswaterstaat/NDW directly for official datasets or API credentials',
        'affected_facilities': 'N/A'
    })

    # Real-time occupancy
    recommendations.append({
        'priority': 'Medium',
        'category': 'Occupancy Data',
        'issue': 'No real-time occupancy data currently available',
        'action': 'Investigate NDW parking sensors, ITS platforms, or commercial parking data providers',
        'affected_facilities': quality_metrics['total_facilities']
    })

    # Electricity/charging infrastructure
    if quality_metrics['total_facilities'] > 0:
        recommendations.append({
            'priority': 'Medium',
            'category': 'Charging Infrastructure',
            'issue': 'Limited electricity grid and charging station data',
            'action': 'Query OpenChargeMap API, grid operator databases, and EV charging networks',
            'affected_facilities': quality_metrics['total_facilities']
        })

    # Low confidence facilities
    if len(gaps['low_confidence']) > 0:
        recommendations.append({
            'priority': 'Low',
            'category': 'Data Verification',
            'issue': f"{len(gaps['low_confidence'])} facilities have low confidence scores (<0.5)",
            'action': 'Manual verification through satellite imagery or field validation',
            'affected_facilities': len(gaps['low_confidence'])
        })

    return recommendations

def generate_markdown_report(facilities, stats, quality_metrics, quality_percentages, gaps, recommendations):
    """Generate comprehensive markdown report"""

    report = f"""# Truck Parking Facilities in the Netherlands - Data Collection Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Project:** Verzorgingsplaatsen Database
**Version:** 1.0

---

## Executive Summary

This report summarizes the comprehensive data collection effort to identify and catalog truck parking facilities (verzorgingsplaatsen) in the Netherlands. The project successfully collected and processed data from multiple sources, with OpenStreetMap as the primary data provider.

### Key Findings

- **Total Facilities Collected:** {quality_metrics['total_facilities']:,}
- **High Confidence Facilities:** {quality_metrics['high_confidence']:,} ({quality_percentages['high_confidence']:.1f}%)
- **Facilities with Capacity Data:** {quality_metrics['with_capacity']:,} ({quality_percentages['with_capacity']:.1f}%)
- **Facilities with Polygon Boundaries:** {quality_metrics['with_polygons']:,} ({quality_percentages['with_polygons']:.1f}%)
- **Designated Truck Parking:** {quality_metrics['designated_truck']:,}
- **Total Known Truck Parking Capacity:** {stats.get('total_truck_parking_capacity', 0):,} spots

---

## Data Sources

### Successfully Accessed

#### 1. OpenStreetMap (Primary Source)
- **Status:** Successfully accessed and processed
- **Method:** Overpass API query
- **Coverage:** Netherlands (bbox: 50.7°N - 53.6°N, 3.3°E - 7.2°E)
- **Facilities Retrieved:** {quality_metrics['total_facilities']:,}
- **Reliability:** High (community-maintained, regularly updated)
- **Data Quality:** Variable (depends on contributor completeness)

**Query Criteria:**
- Rest areas with HGV designation
- Service areas with truck parking
- Parking areas designated for heavy goods vehicles
- All highway rest areas and service areas in the Netherlands

**Data Extracted:**
- Facility names and locations (coordinates)
- Polygon boundaries where available
- Capacity information (where tagged)
- Amenities (fuel, restaurants, toilets, etc.)
- Operating hours and operators
- HGV designation status

#### 2. Nominatim Reverse Geocoding
- **Status:** Successfully used for enrichment
- **Facilities Enriched:** 200 (rate limited at 1 request/second)
- **Purpose:** Province, municipality, and address information
- **Reliability:** High (official administrative boundaries)

### Attempted but Unsuccessful

#### 1. NDW (Nationale Databank Wegverkeersgegevens)
- **Status:** API endpoints not accessible (HTTP 404)
- **Attempted Endpoints:**
  - http://opendata.ndw.nu/PARKING.xml.gz
  - http://opendata.ndw.nu/PARKINGDATA.xml.gz
  - https://data.ndw.nu/api/rest/storedquery/ParkingFacilities
- **Issue:** API structure may have changed or requires authentication
- **Recommendation:** Contact NDW directly for current API documentation

#### 2. Rijkswaterstaat Open Data
- **Status:** No direct parking facility datasets found
- **Searched:** data.overheid.nl portal
- **Issue:** Parking facility data may be in PDF reports or not publicly available
- **Recommendation:** Direct contact with Rijkswaterstaat for official rest area database

#### 3. PDOK Services
- **Status:** Services accessible but no parking-specific layers found
- **Checked Services:**
  - National Road Database (NWB) - returned 404
  - Cadastral parcels - accessible but not relevant for parking facilities
- **Recommendation:** Monitor PDOK for new parking-related datasets

---

## Data Quality Analysis

### Completeness Metrics

| Metric | Count | Percentage |
|--------|-------|------------|
| Total Facilities | {quality_metrics['total_facilities']:,} | 100.0% |
| With Name | {quality_metrics['with_name']:,} | {quality_percentages['with_name']:.1f}% |
| With Coordinates | {quality_metrics['with_coordinates']:,} | {quality_percentages['with_coordinates']:.1f}% |
| With Polygon Boundaries | {quality_metrics['with_polygons']:,} | {quality_percentages['with_polygons']:.1f}% |
| With Capacity Data | {quality_metrics['with_capacity']:,} | {quality_percentages['with_capacity']:.1f}% |
| With Truck Capacity | {quality_metrics['with_truck_capacity']:,} | {quality_percentages['with_truck_capacity']:.1f}% |
| With Amenities Info | {quality_metrics['with_amenities']:,} | {quality_percentages['with_amenities']:.1f}% |
| With Operator | {quality_metrics['with_operator']:,} | {quality_percentages['with_operator']:.1f}% |
| With Opening Hours | {quality_metrics['with_hours']:,} | {quality_percentages['with_hours']:.1f}% |
| With Province | {quality_metrics['with_province']:,} | {quality_percentages['with_province']:.1f}% |
| With Municipality | {quality_metrics['with_municipality']:,} | {quality_percentages['with_municipality']:.1f}% |
| High Confidence (≥0.7) | {quality_metrics['high_confidence']:,} | {quality_percentages['high_confidence']:.1f}% |
| Designated Truck Parking | {quality_metrics['designated_truck']:,} | {quality_percentages['designated_truck']:.1f}% |

### Confidence Score Distribution

The confidence score (0-1) is calculated based on data completeness:
- Base score: 0.5
- Named facility: +0.1
- Capacity data: +0.15
- Polygon boundary: +0.1
- Amenities info: +0.05
- Operator info: +0.05
- HGV designated: +0.05

**Results:**
- High Confidence (≥0.7): {quality_metrics['high_confidence']:,} facilities
- Medium Confidence (0.5-0.7): {quality_metrics['total_facilities'] - quality_metrics['high_confidence'] - len(gaps['low_confidence']):,} facilities
- Low Confidence (<0.5): {len(gaps['low_confidence']):,} facilities

---

## Geographic Distribution

### By Province

"""

    # Add province distribution
    provinces = stats.get('by_province', {})
    # Filter out Unknown and German/Belgian provinces for summary
    nl_provinces = {k: v for k, v in provinces.items()
                   if k not in ['Unknown', 'Nordrhein-Westfalen', 'Oost-Vlaanderen', 'Antwerpen', 'Limburg (BE)']}

    report += "| Province | Facilities | Percentage |\n"
    report += "|----------|------------|------------|\n"

    for province, count in sorted(nl_provinces.items(), key=lambda x: x[1], reverse=True):
        pct = (count / quality_metrics['total_facilities'] * 100)
        report += f"| {province} | {count} | {pct:.1f}% |\n"

    if 'Unknown' in provinces:
        report += f"| Unknown/Not Yet Geocoded | {provinces['Unknown']} | {(provinces['Unknown']/quality_metrics['total_facilities']*100):.1f}% |\n"

    report += f"""

### By Highway

Top 15 highways by number of facilities:

"""

    highways = stats.get('by_highway', {})
    highway_list = sorted(highways.items(), key=lambda x: x[1], reverse=True)[:15]

    report += "| Highway | Facilities |\n"
    report += "|---------|------------|\n"

    for highway, count in highway_list:
        if highway != 'Unknown':
            report += f"| {highway} | {count} |\n"

    report += f"""

### By Type

"""

    types = stats.get('by_type', {})
    report += "| Type | Count | Percentage |\n"
    report += "|------|-------|------------|\n"

    for type_name, count in sorted(types.items(), key=lambda x: x[1], reverse=True):
        pct = (count / quality_metrics['total_facilities'] * 100)
        report += f"| {type_name} | {count} | {pct:.1f}% |\n"

    report += f"""

---

## Data Gaps and Issues

### Summary of Gaps

"""

    report += f"- **Missing Capacity Data:** {len(gaps['missing_capacity']):,} facilities ({len(gaps['missing_capacity'])/quality_metrics['total_facilities']*100:.1f}%)\n"
    report += f"- **Missing Location Details:** {len(gaps['missing_location']):,} facilities ({len(gaps['missing_location'])/quality_metrics['total_facilities']*100:.1f}%)\n"
    report += f"- **Low Confidence:** {len(gaps['low_confidence']):,} facilities\n"
    report += f"- **No Polygon Boundaries:** {len(gaps['no_polygon']):,} facilities ({len(gaps['no_polygon'])/quality_metrics['total_facilities']*100:.1f}%)\n"
    report += f"- **Incomplete Amenities:** {len(gaps['incomplete_amenities']):,} designated truck parking facilities\n"

    report += """

### Critical Gaps

1. **Capacity Data (High Priority)**
   - Only """ + f"{quality_percentages['with_capacity']:.1f}" + """% of facilities have capacity information
   - Only """ + f"{quality_percentages['with_truck_capacity']:.1f}" + """% have specific truck parking capacity
   - This is essential for parking availability analysis

2. **Location Enrichment (High Priority)**
   - """ + f"{(len(gaps['missing_location']) / quality_metrics['total_facilities'] * 100):.1f}" + """% of facilities still lack province/municipality data
   - Required for regional analysis and filtering
   - Can be addressed through continued Nominatim geocoding

3. **Government Data Access (High Priority)**
   - Official Rijkswaterstaat rest area database not accessible
   - NDW real-time parking data not available
   - Critical for data validation and real-time occupancy

4. **Charging Infrastructure (Medium Priority)**
   - Minimal electricity grid and EV charging data
   - Increasingly important for electric truck infrastructure planning

5. **Occupancy Data (Medium Priority)**
   - No real-time or historical occupancy data
   - Essential for understanding parking demand and patterns

---

## Recommendations

"""

    for i, rec in enumerate(recommendations, 1):
        report += f"""
### {i}. {rec['category']} ({rec['priority']} Priority)

**Issue:** {rec['issue']}

**Recommended Action:** {rec['action']}

**Affected Facilities:** {rec['affected_facilities']}

"""

    report += """
---

## Additional Data Sources to Explore

### Recommended for Future Investigation

1. **Provincial Road Authorities**
   - Each province may maintain their own parking facility databases
   - Contact: Noord-Holland, Zuid-Holland, Gelderland, Noord-Brabant road departments

2. **Transport & Logistics Organizations**
   - TLN (Transport en Logistiek Nederland)
   - EVO (vereniging van verladers en logistieke dienstverleners)
   - May have industry databases of preferred parking locations

3. **Commercial Navigation Providers**
   - TomTom Professional
   - HERE Maps
   - Garmin Professional
   - May offer datasets or APIs (typically commercial licenses)

4. **Parking Operators**
   - Direct contact with operators like Aral, Shell, BP, Q8
   - Truck parking facility operators (e.g., SecurParking)

5. **EV Charging Networks**
   - OpenChargeMap API
   - Fastned, Shell Recharge, Allego
   - E-laad database for charging points

6. **ITS and Smart Mobility Platforms**
   - Talking Traffic
   - Smart mobility platforms operated by provinces
   - May have real-time parking availability data

7. **Municipal Open Data Portals**
   - Amsterdam, Rotterdam, Utrecht, The Hague data portals
   - May contain local parking facility information

8. **Academic and Research Data**
   - TU Delft transport research
   - CROW (knowledge platform for infrastructure)
   - May have parking studies with facility inventories

---

## Output Files

The following files have been generated:

### 1. GeoJSON Format
**File:** `truck_parking_facilities.geojson`
- Standard GeoJSON FeatureCollection
- Includes polygon boundaries where available
- Comprehensive properties for each facility
- Ready for use in GIS software and web mapping libraries

### 2. CSV Format
**File:** `truck_parking_facilities.csv`
- Spreadsheet-compatible format
- All facilities with key attributes
- Suitable for analysis in Excel, Python pandas, R, etc.

### 3. JSON Database
**File:** `truck_parking_database.json`
- Structured JSON with metadata
- Complete facility records with all attributes
- Programming-friendly format

### 4. Raw Data
**File:** `osm_truck_parking_raw.json`
- Unprocessed OSM data
- Includes all original tags
- Useful for custom analysis

### 5. Enriched Data
**File:** `truck_parking_enriched.json`
- Processed and enriched facility data
- Includes classification and confidence scores
- Geocoded location information

### 6. Statistics
**File:** `analysis_stats.json`
- Detailed statistics in JSON format
- Provincial and highway distributions
- Data quality metrics

---

## Technical Notes

### Data Collection Methodology

1. **OpenStreetMap Query**
   - Used Overpass API with comprehensive query
   - Searched for multiple tag combinations (highway=rest_area, amenity=parking, hgv tags)
   - Retrieved 21,240 raw elements, processed into 1,425 facilities
   - Bounding box: Netherlands (50.7°N to 53.6°N, 3.3°E to 7.2°E)

2. **Data Processing**
   - Deduplicated by OSM element ID
   - Constructed polygons from way nodes
   - Calculated polygon areas using approximate geodesic methods
   - Extracted and normalized tags

3. **Classification**
   - Categorized as rest areas, service areas, or truck parking
   - Identified HGV-designated facilities
   - Calculated confidence scores based on completeness

4. **Enrichment**
   - Reverse geocoding using Nominatim (rate limited)
   - Extracted administrative boundaries
   - Added highway and road names

### Data Limitations

1. **OSM Data Quality**
   - Varies by contributor and region
   - May include outdated information
   - Completeness depends on mapping coverage

2. **Capacity Data**
   - Often not tagged in OSM
   - When present, may not distinguish truck vs. car spots
   - May be outdated

3. **Geographic Coverage**
   - Only 200 facilities have been fully geocoded (rate limiting)
   - Remaining facilities need location enrichment

4. **Real-time Data**
   - No occupancy information available
   - No dynamic pricing or availability data

5. **Validation**
   - Data has not been field-validated
   - Satellite imagery verification recommended for high-priority facilities

### Coordinate System

- **Coordinate Reference System:** WGS84 (EPSG:4326)
- **Format:** Decimal degrees
- **Precision:** Varies by source (typically 6-7 decimal places)

### Area Calculations

- Polygon areas calculated using Shoelace formula
- Approximate conversion to meters using latitude/longitude scaling
- Netherlands latitude (~52°N) used for longitude meter conversion
- Areas are approximations; more precise calculations require projected coordinate systems

---

## Usage Examples

### Loading GeoJSON in Python

```python
import json
import geopandas as gpd

# Load GeoJSON
gdf = gpd.read_file('truck_parking_facilities.geojson')

# Filter high-confidence facilities
high_conf = gdf[gdf['confidence_score'] >= 0.7]

# Filter by province
gelderland = gdf[gdf['province'] == 'Gelderland']
```

### Loading CSV in Python

```python
import pandas as pd

# Load CSV
df = pd.read_csv('truck_parking_facilities.csv')

# Filter truck parking with capacity
truck_parking = df[
    (df['is_truck_parking'] == True) &
    (df['truck_spots'].notna())
]
```

### Using in QGIS

1. Open QGIS
2. Layer > Add Layer > Add Vector Layer
3. Select `truck_parking_facilities.geojson`
4. Style by confidence_score or facility type

### Using in Web Maps

```javascript
// Leaflet example
fetch('truck_parking_facilities.geojson')
  .then(response => response.json())
  .then(data => {
    L.geoJSON(data, {
      onEachFeature: function(feature, layer) {
        layer.bindPopup(feature.properties.name);
      }
    }).addTo(map);
  });
```

---

## Conclusion

This project has successfully collected and processed **{quality_metrics['total_facilities']:,} truck parking facilities** across the Netherlands, primarily from OpenStreetMap data. While this represents a substantial dataset, there are significant opportunities for improvement through:

1. **Government data access** - Obtaining official Rijkswaterstaat and NDW datasets
2. **Capacity enrichment** - Filling the {:.1f}% capacity data gap through estimation or imagery analysis
3. **Location completion** - Geocoding the remaining {:.1f}% of facilities
4. **Real-time integration** - Adding occupancy and availability data
5. **Validation** - Field verification or satellite imagery confirmation

The dataset is immediately usable for:
- Geographic analysis and visualization
- Planning and logistics applications
- Research into truck parking infrastructure
- Base layer for future data enrichment

### Next Steps

**Immediate (0-1 month):**
1. Complete Nominatim geocoding for all facilities
2. Estimate capacity from polygon areas where missing
3. Query OpenChargeMap for charging infrastructure

**Short-term (1-3 months):**
1. Contact Rijkswaterstaat for official dataset
2. Investigate NDW API access requirements
3. Add provincial road authority data
4. Field validate sample of high-priority facilities

**Long-term (3-6 months):**
1. Integrate real-time occupancy data if available
2. Add historical usage patterns
3. Include electricity grid connection data
4. Create automated update pipeline

---

## Appendices

### A. Data Source Registry

| Source | Type | Status | Coverage | Reliability |
|--------|------|--------|----------|-------------|
| OpenStreetMap | Open API | Active | Netherlands | High |
| Nominatim | Open API | Active | Worldwide | High |
| NDW | Gov. API | Failed | Netherlands | N/A |
| Rijkswaterstaat | Gov. Data | Not Found | Netherlands | N/A |
| PDOK | Gov. API | Partial | Netherlands | Medium |

### B. Field Definitions

**Core Fields:**
- `id`: Unique identifier (format: osm_type_id)
- `name`: Facility name
- `latitude`, `longitude`: WGS84 coordinates
- `geometry`: GeoJSON geometry (Point or Polygon)

**Location Fields:**
- `province`: Dutch province
- `municipality`: Municipality/city
- `highway`: Highway designation (e.g., "A1")
- `road`: Road name
- `postcode`: Postal code

**Capacity Fields:**
- `truck_spots`: Number of truck parking spaces
- `total_spots`: Total parking spaces (all vehicle types)
- `area_m2`: Parking area in square meters

**Classification Fields:**
- `is_truck_parking`: Boolean, designated truck parking
- `is_rest_area`: Boolean, highway rest area
- `is_service_area`: Boolean, service area with facilities
- `confidence_score`: 0-1 score indicating data quality

**Amenity Fields:**
- `has_fuel`: Fuel station present
- `has_restaurant`: Restaurant/cafe present
- `has_toilets`: Toilets available
- `has_wifi`: WiFi available
- `has_charging`: EV charging available

**Operational Fields:**
- `operator`: Operating company
- `opening_hours`: Operating hours in OSM format
- `hgv`: HGV designation (yes/designated/no)

### C. Statistics Summary

"""

    report += f"""
- **Total Facilities:** {quality_metrics['total_facilities']:,}
- **Data Sources Accessed:** 5 (1 successful, 4 unsuccessful)
- **High Confidence Facilities:** {quality_metrics['high_confidence']:,}
- **Facilities with Capacity:** {quality_metrics['with_capacity']:,}
- **Facilities with Polygons:** {quality_metrics['with_polygons']:,}
- **Average Confidence Score:** {sum(f.get('confidence_score', 0) for f in facilities) / len(facilities):.2f}
- **Known Truck Parking Capacity:** {stats.get('total_truck_parking_capacity', 0):,} spots
- **Provinces Covered:** {len([p for p in provinces.keys() if p not in ['Unknown', 'Nordrhein-Westfalen', 'Oost-Vlaanderen', 'Antwerpen']])}
- **Highways Represented:** {len([h for h in highways.keys() if h != 'Unknown'])}

---

**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Project:** Verzorgingsplaatsen - Netherlands Truck Parking Database
**Version:** 1.0
**Contact:** Data Collection Project

---
"""

    return report

def main():
    """Main execution"""
    print("=" * 80)
    print("GENERATING COMPREHENSIVE SUMMARY REPORT")
    print("=" * 80)

    facilities, stats = load_data()

    print(f"Loaded {len(facilities)} facilities")

    # Analyze data quality
    quality_metrics, quality_percentages = analyze_data_quality(facilities)
    print("Analyzed data quality")

    # Identify gaps
    gaps = identify_gaps(facilities)
    print("Identified data gaps")

    # Generate recommendations
    recommendations = generate_recommendations(quality_metrics, gaps, stats)
    print(f"Generated {len(recommendations)} recommendations")

    # Generate report
    report = generate_markdown_report(facilities, stats, quality_metrics,
                                     quality_percentages, gaps, recommendations)

    # Save report
    report_file = '/Users/robbertjanssen/Documents/dev/Verzorgingsplaatsen/SUMMARY_REPORT.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\nSaved comprehensive report to {report_file}")

    print("\n" + "=" * 80)
    print("REPORT GENERATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
