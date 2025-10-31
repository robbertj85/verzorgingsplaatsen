# Truck Parking Facilities in the Netherlands - Data Collection Report

**Generated:** 2025-10-30 16:13:50
**Project:** Verzorgingsplaatsen Database
**Version:** 1.0

---

## Executive Summary

This report summarizes the comprehensive data collection effort to identify and catalog truck parking facilities (verzorgingsplaatsen) in the Netherlands. The project successfully collected and processed data from multiple sources, with OpenStreetMap as the primary data provider.

### Key Findings

- **Total Facilities Collected:** 1,425
- **High Confidence Facilities:** 627 (44.0%)
- **Facilities with Capacity Data:** 87 (6.1%)
- **Facilities with Polygon Boundaries:** 1,252 (87.9%)
- **Designated Truck Parking:** 566
- **Total Known Truck Parking Capacity:** 485 spots

---

## Data Sources

### Successfully Accessed

#### 1. OpenStreetMap (Primary Source)
- **Status:** Successfully accessed and processed
- **Method:** Overpass API query
- **Coverage:** Netherlands (bbox: 50.7°N - 53.6°N, 3.3°E - 7.2°E)
- **Facilities Retrieved:** 1,425
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
| Total Facilities | 1,425 | 100.0% |
| With Name | 558 | 39.2% |
| With Coordinates | 1,422 | 99.8% |
| With Polygon Boundaries | 1,252 | 87.9% |
| With Capacity Data | 87 | 6.1% |
| With Truck Capacity | 10 | 0.7% |
| With Amenities Info | 293 | 20.6% |
| With Operator | 64 | 4.5% |
| With Opening Hours | 22 | 1.5% |
| With Province | 200 | 14.0% |
| With Municipality | 200 | 14.0% |
| High Confidence (≥0.7) | 627 | 44.0% |
| Designated Truck Parking | 566 | 39.7% |

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
- High Confidence (≥0.7): 627 facilities
- Medium Confidence (0.5-0.7): 798 facilities
- Low Confidence (<0.5): 0 facilities

---

## Geographic Distribution

### By Province

| Province | Facilities | Percentage |
|----------|------------|------------|
| Zuid-Holland | 35 | 2.5% |
| Overijssel | 21 | 1.5% |
| Gelderland | 16 | 1.1% |
| Limburg | 15 | 1.1% |
| Noord-Holland | 13 | 0.9% |
| Noord-Brabant | 9 | 0.6% |
| Fryslân | 7 | 0.5% |
| Utrecht | 6 | 0.4% |
| Zeeland | 5 | 0.4% |
| Vlaams-Brabant | 3 | 0.2% |
| Niedersachsen | 2 | 0.1% |
| Groningen | 2 | 0.1% |
| Brabant wallon | 1 | 0.1% |
| Unknown/Not Yet Geocoded | 1225 | 86.0% |


### By Highway

Top 15 highways by number of facilities:

| Highway | Facilities |
|---------|------------|
| A 57 | 7 |
| A 43 | 5 |
| Nijverdalseweg | 4 |
| Aldewei | 3 |
| A 3 | 3 |
| A1 | 2 |
| A67 | 2 |
| A58 | 2 |
| A 44 | 2 |
| A 46 | 2 |
| Nijverheidsstraat | 2 |
| Autoroute des Ardennes | 1 |
| Afsluitdijk | 1 |
| Neuenhauser Straße | 1 |


### By Type

| Type | Count | Percentage |
|------|-------|------------|
| Truck Parking | 558 | 39.2% |
| Service Area | 495 | 34.7% |
| Rest Area | 372 | 26.1% |


---

## Data Gaps and Issues

### Summary of Gaps

- **Missing Capacity Data:** 1,338 facilities (93.9%)
- **Missing Location Details:** 1,225 facilities (86.0%)
- **Low Confidence:** 0 facilities
- **No Polygon Boundaries:** 173 facilities (12.1%)
- **Incomplete Amenities:** 563 designated truck parking facilities


### Critical Gaps

1. **Capacity Data (High Priority)**
   - Only 6.1% of facilities have capacity information
   - Only 0.7% have specific truck parking capacity
   - This is essential for parking availability analysis

2. **Location Enrichment (High Priority)**
   - 86.0% of facilities still lack province/municipality data
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


### 1. Capacity Data (High Priority)

**Issue:** 93.9% of facilities missing capacity information

**Recommended Action:** Estimate capacity from polygon areas (typical: 30-40 m² per truck spot) or aerial imagery analysis

**Affected Facilities:** 1338


### 2. Location Data (High Priority)

**Issue:** 86.0% of facilities missing province/municipality information

**Recommended Action:** Continue Nominatim reverse geocoding for remaining facilities (rate limited to 1 req/sec)

**Affected Facilities:** 1225


### 3. Polygon Boundaries (Medium Priority)

**Issue:** 12.1% of facilities only have point coordinates

**Recommended Action:** Enhance OSM data or use satellite imagery to map actual parking boundaries

**Affected Facilities:** 173


### 4. Additional Data Sources (High Priority)

**Issue:** Government APIs (NDW, Rijkswaterstaat) not accessible or changed

**Recommended Action:** Contact Rijkswaterstaat/NDW directly for official datasets or API credentials

**Affected Facilities:** N/A


### 5. Occupancy Data (Medium Priority)

**Issue:** No real-time occupancy data currently available

**Recommended Action:** Investigate NDW parking sensors, ITS platforms, or commercial parking data providers

**Affected Facilities:** 1425


### 6. Charging Infrastructure (Medium Priority)

**Issue:** Limited electricity grid and charging station data

**Recommended Action:** Query OpenChargeMap API, grid operator databases, and EV charging networks

**Affected Facilities:** 1425


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


- **Total Facilities:** 1,425
- **Data Sources Accessed:** 5 (1 successful, 4 unsuccessful)
- **High Confidence Facilities:** 627
- **Facilities with Capacity:** 87
- **Facilities with Polygons:** 1,252
- **Average Confidence Score:** 0.67
- **Known Truck Parking Capacity:** 485 spots
- **Provinces Covered:** 13
- **Highways Represented:** 19

---

**Report Generated:** 2025-10-30 16:13:50
**Project:** Verzorgingsplaatsen - Netherlands Truck Parking Database
**Version:** 1.0
**Contact:** Data Collection Project

---
