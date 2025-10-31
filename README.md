# Verzorgingsplaatsen - Netherlands Truck Parking Facilities Database

A comprehensive research project documenting truck parking facilities (verzorgingsplaatsen) along Dutch motorways with definitive jurisdictional authority mapping.

## Overview

This project provides detailed documentation of truck parking facilities across the Netherlands, including:

- Motorway rest areas (verzorgingsplaatsen) with jurisdictional authority structure
- Private secured parking facilities
- Geographic coordinates and interactive mapping
- Facility capacity, operator, and amenity information
- Jurisdictional authority documentation
- Policy context and future developments
- Multiple data formats (JSON, CSV, interactive dashboard)

## Latest Research (October 30, 2025)

**Phase 1 Complete: 18 facilities fully documented**
- Motorway rest areas: 15 facilities (A2, A12, A15, A27)
- Private secured parking: 3 facilities
- Total confirmed truck spaces: 616+
- High confidence data: 7 facilities (39%)
- Additional 100+ facilities identified for Phase 2

## Quick Start

### View Interactive Dashboard

Open `index.html` in your web browser to explore the comprehensive dashboard featuring:
- Interactive map with all documented facilities
- Real-time statistics and charts
- Filter by motorway (A2, A12, A15, A27) or facility type
- Detailed facility information in popups
- Distribution visualizations

### Data Files

The following files are available:

1. **data/verzorgingsplaatsen_database.json** - Complete database with 18 facilities (32 KB)
2. **data/facilities_summary.csv** - Tabular summary for quick reference (2.9 KB)
3. **data/facility_coordinates.json** - Geographic coordinates for all facilities
4. **data/analysis_summary.csv** - Statistical analysis results
5. **docs/executive_summary.md** - Comprehensive research findings (22 KB)
6. **docs/research_methodology.md** - Detailed methodology and sources (32 KB)
7. **docs/analysis_report.txt** - Generated statistical analysis report

## Data Quality Overview

| Metric | Value | Percentage |
|--------|-------|------------|
| Total Facilities Documented | 18 | 100% |
| High Confidence | 7 | 38.9% |
| Medium Confidence | 10 | 55.6% |
| Low Confidence | 1 | 5.6% |
| With Capacity Data | 6 | 33.3% |
| Total Truck Spaces (Confirmed) | 616 | - |
| Average Spaces per Facility | 102.7 | - |

## Facility Distribution

### By Authority Type
- National (Rijkswaterstaat): 15 facilities (83%)
- Private Operators: 3 facilities (17%)

### By Motorway
- A2: 5 facilities
- A12: 2 facilities
- A15: 3 facilities
- A27: 5 facilities

### By Province
- Utrecht: 7 facilities
- Noord-Brabant: 4 facilities
- Zuid-Holland: 3 facilities
- Limburg: 2 facilities
- Gelderland: 1 facility

### Top Operators
- Shell: 3 facilities
- TRE BV (Private): 2 facilities
- TotalEnergies: 1 facility
- BP: 1 facility
- Vissers Energy: 1 facility
- Esso: 1 facility

## Project Structure

```
/Verzorgingsplaatsen
├── index.html                            # Interactive dashboard with map & charts
├── map.html                              # Simple map visualization
├── data/
│   ├── verzorgingsplaatsen_database.json # Complete facility database
│   ├── facilities_summary.csv            # CSV summary
│   ├── facility_coordinates.json         # Geographic coordinates
│   └── analysis_summary.csv              # Statistical analysis
├── docs/
│   ├── executive_summary.md              # Comprehensive findings
│   ├── research_methodology.md           # Research process
│   └── analysis_report.txt               # Generated analysis
├── scripts/
│   └── analyze_data.py                   # Python analysis script
└── README.md                             # This file
```

## File Descriptions

### Output Files (Ready to Use)

**truck_parking_facilities.geojson**
- Standard GeoJSON FeatureCollection
- 1,422 features with geometry
- Polygon boundaries where available
- Complete property data for each facility
- Ready for GIS software, web maps, analysis

**truck_parking_facilities.csv**
- Spreadsheet-compatible format
- 1,425 facilities with key attributes
- Columns: id, name, location, capacity, amenities, classification
- Use in Excel, Python pandas, R, database imports

**truck_parking_database.json**
- Structured JSON with metadata
- Complete facility records
- Statistics summary
- Programming-friendly format

**SUMMARY_REPORT.md**
- Comprehensive analysis (30+ pages)
- Data quality assessment
- Geographic distribution
- Data source evaluation
- Recommendations for improvement
- Usage examples

**map_viewer.html**
- Interactive Leaflet map
- Filter by province, type, confidence
- Popup details for each facility
- Export filtered data
- Works offline (load in browser)

### Data Collection Scripts

**collect_osm_data.py**
- Query OpenStreetMap Overpass API
- Comprehensive tag combinations
- Polygon boundary extraction
- Area calculations
- Confidence scoring

**collect_rws_ndw_data.py**
- Query Rijkswaterstaat APIs
- NDW parking data attempts
- PDOK service queries
- data.overheid.nl searches
- Documents API access results

**enrich_data.py**
- Nominatim reverse geocoding
- Province/municipality enrichment
- Facility classification
- Statistical analysis
- Rate-limited processing

**generate_outputs.py**
- Convert to multiple formats
- GeoJSON generation
- CSV export
- JSON database creation

**generate_report.py**
- Comprehensive markdown report
- Quality metrics analysis
- Gap identification
- Recommendations generation

## Usage Examples

### Python - Load and Analyze GeoJSON

```python
import geopandas as gpd
import pandas as pd

# Load GeoJSON
gdf = gpd.read_file('truck_parking_facilities.geojson')

# Filter high-confidence facilities with capacity
high_quality = gdf[
    (gdf['confidence_score'] >= 0.7) &
    (gdf['truck_spots'].notna())
]

print(f"High quality facilities: {len(high_quality)}")

# Group by province
by_province = gdf['province'].value_counts()
print(by_province)

# Find facilities with amenities
with_amenities = gdf[
    (gdf['has_fuel'] == True) |
    (gdf['has_restaurant'] == True) |
    (gdf['has_toilets'] == True)
]
```

### Python - Load and Analyze CSV

```python
import pandas as pd

# Load CSV
df = pd.read_csv('truck_parking_facilities.csv')

# Basic statistics
print(f"Total facilities: {len(df)}")
print(f"With truck spots: {df['truck_spots'].notna().sum()}")
print(f"Average confidence: {df['confidence_score'].mean():.2f}")

# Filter designated truck parking
truck_parking = df[df['is_truck_parking'] == True]

# Export filtered subset
truck_parking.to_csv('designated_truck_parking.csv', index=False)
```

### JavaScript - Load in Web Map

```javascript
// Leaflet example
fetch('truck_parking_facilities.geojson')
  .then(response => response.json())
  .then(data => {
    L.geoJSON(data, {
      style: feature => ({
        color: getColorByConfidence(feature.properties.confidence_score)
      }),
      onEachFeature: (feature, layer) => {
        layer.bindPopup(`
          <b>${feature.properties.name}</b><br>
          Province: ${feature.properties.province}<br>
          Confidence: ${feature.properties.confidence_score}
        `);
      }
    }).addTo(map);
  });
```

### QGIS

1. Open QGIS
2. Layer > Add Layer > Add Vector Layer
3. Select `truck_parking_facilities.geojson`
4. Style by:
   - confidence_score (graduated colors)
   - is_truck_parking (categorized)
   - province (categorized)
5. Use filter: `"confidence_score" >= 0.7` for high-quality only

## Data Sources

### Successfully Accessed

#### OpenStreetMap (Primary Source)
- **Status:** Successfully accessed and processed
- **Method:** Overpass API query
- **Facilities Retrieved:** 1,425
- **Reliability:** High (community-maintained, regularly updated)
- **Coverage:** Complete Netherlands territory
- **URL:** https://www.openstreetmap.org

#### Nominatim Reverse Geocoding
- **Status:** Successfully used for enrichment
- **Facilities Enriched:** 200 (rate limited at 1 request/second)
- **Purpose:** Province, municipality, and address information
- **Reliability:** High (official administrative boundaries)

### Attempted but Unsuccessful

#### NDW (Nationale Databank Wegverkeersgegevens)
- **Status:** API endpoints returned HTTP 404
- **Issue:** API structure may have changed or requires authentication
- **Recommendation:** Contact NDW directly for current API documentation
- **Real-time parking overview:** https://truck-parking.ndw.nu/ (web interface works)

#### Rijkswaterstaat Open Data
- **Status:** No direct parking facility datasets found on data.overheid.nl
- **Issue:** Parking facility data may be in PDF reports or not publicly available
- **Recommendation:** Direct contact with Rijkswaterstaat for official rest area database
- **URL:** https://www.rijkswaterstaat.nl

#### PDOK Services
- **Status:** Services accessible but no parking-specific layers found
- **Issue:** National Road Database (NWB) endpoint returned 404
- **Recommendation:** Monitor PDOK for new parking-related datasets
- **URL:** https://www.pdok.nl

## Data Gaps and Limitations

### Critical Gaps

1. **Capacity Data (High Priority)** - Only 6.1% of facilities have capacity information
   - Most OSM contributors don't tag parking capacity
   - Can be estimated from polygon areas (30-40 m² per truck spot)
   - Requires satellite imagery analysis or field verification

2. **Location Enrichment (High Priority)** - 86% of facilities lack province/municipality data
   - Nominatim geocoding incomplete (only 200 of 1,425 processed)
   - Rate limited to 1 request per second
   - Can be completed with continued processing

3. **Government Data Access (High Priority)**
   - Official Rijkswaterstaat rest area database not publicly accessible
   - NDW real-time parking data API endpoints not working
   - Critical for data validation and occupancy information

4. **Occupancy Data (Medium Priority)**
   - No real-time or historical occupancy data available
   - Essential for understanding parking demand patterns
   - Requires integration with ITS platforms or parking sensors

5. **Charging Infrastructure (Medium Priority)**
   - Minimal EV charging and electricity grid data
   - Only 1 facility has charging information in current dataset
   - Important for electric truck infrastructure planning

### Data Quality Notes

- **OSM Data Variability:** Quality depends on contributor completeness and update frequency
- **Polygon Accuracy:** Areas calculated using approximate geodesic methods; more precise calculations require projected coordinate systems
- **Validation Status:** Data has not been field-validated; satellite imagery verification recommended for high-priority facilities
- **Geographic Coverage:** Dataset includes some facilities just outside Netherlands borders (in Germany and Belgium)

## Recommendations for Data Improvement

### Immediate Actions (0-1 month)

1. **Complete Nominatim Geocoding**
   - Process remaining 1,225 facilities for province/municipality data
   - Respect 1 request/second rate limit (approximately 20 minutes processing time)
   - Priority: High

2. **Estimate Missing Capacity**
   - Calculate truck capacity from polygon areas (30-40 m² per spot)
   - Flag as estimated vs. actual in metadata
   - Priority: High

3. **Query OpenChargeMap API**
   - Cross-reference facilities with EV charging infrastructure database
   - Add charging point data where available
   - Priority: Medium

### Short-term Actions (1-3 months)

1. **Contact Rijkswaterstaat**
   - Request official rest area database
   - Obtain accurate capacity figures
   - Get access to NDW parking data APIs
   - Priority: High

2. **Add Provincial Data**
   - Contact provincial road authorities for regional parking facilities
   - Focus on provinces with limited data (Friesland, Drenthe, Zeeland)
   - Priority: Medium

3. **Satellite Imagery Validation**
   - Verify polygon boundaries for high-priority facilities
   - Count parking spots visually
   - Priority: Medium

### Long-term Actions (3-6 months)

1. **Real-time Integration**
   - Integrate with NDW parking sensors (if access obtained)
   - Add occupancy patterns and availability forecasting
   - Priority: High

2. **Automated Update Pipeline**
   - Schedule regular OSM data refreshes
   - Monitor changes and additions
   - Generate change reports
   - Priority: Medium

3. **Commercial Data Sources**
   - Investigate TomTom, HERE Maps APIs (may require licensing)
   - Consider partnerships with logistics companies for validation
   - Priority: Low

## Additional Data Sources to Explore

1. **Provincial Road Authorities** - Each province may maintain parking facility databases
2. **OpenChargeMap API** - EV charging infrastructure at parking locations
3. **Truck Parking Europe** - Commercial parking database (app.truckparkingeurope.com)
4. **Transport Organizations** - TLN, EVO may have industry databases
5. **Parking Operators** - Direct contact with Shell, BP, TotalEnergies for their facilities
6. **Municipal Open Data** - Amsterdam, Rotterdam, Utrecht, The Hague portals
7. **Academic Research** - TU Delft transport studies may contain facility inventories
8. **ITS Platforms** - Talking Traffic and smart mobility platforms for real-time data

## Technical Specifications

### Coordinate System
- **CRS:** WGS84 (EPSG:4326)
- **Format:** Decimal degrees
- **Precision:** 6-7 decimal places (typical)
- **Bounding Box:** Netherlands (50.7°N to 53.6°N, 3.3°E to 7.2°E)

### Area Calculations
- **Method:** Shoelace formula with geodesic approximation
- **Latitude Factor:** 111,320 meters per degree
- **Longitude Factor:** ~70,000 meters per degree at 52°N
- **Note:** Approximations suitable for Netherlands; use projected CRS for higher precision

### Confidence Scoring
- Base score: 0.5
- Named facility: +0.1
- Capacity data: +0.15
- Polygon boundary: +0.1
- Amenities info: +0.05
- Operator info: +0.05
- HGV designated: +0.05
- Maximum score: 1.0

## Running the Data Collection Scripts

### Requirements
```bash
pip install requests
```

### Collect Fresh Data
```bash
# Collect OSM data (takes ~2 minutes)
python3 collect_osm_data.py

# Attempt government APIs (documents results)
python3 collect_rws_ndw_data.py

# Enrich with location data (takes ~4 minutes for 200 facilities)
python3 enrich_data.py

# Generate output files
python3 generate_outputs.py

# Generate comprehensive report
python3 generate_report.py
```

### View Results
```bash
# Open interactive map in browser
open map_viewer.html

# Or start a local server
python3 -m http.server 8000
# Then visit http://localhost:8000/map_viewer.html
```

## Data Collection Date

**October 30, 2025**

All data current as of this date. OpenStreetMap data refreshed from live API.

## License and Attribution

### Data Sources
- **OpenStreetMap:** Data © OpenStreetMap contributors, available under Open Database License (ODbL)
- **Nominatim:** Geocoding service © OpenStreetMap Foundation
- **This Dataset:** Compilation and analysis provided as-is for research and planning purposes

### Usage
This dataset is provided for:
- Infrastructure planning and analysis
- Research and academic purposes
- Logistics and transportation optimization
- Policy development and evaluation

### Attribution
When using this data, please attribute:
- OpenStreetMap contributors for the underlying facility data
- This project for the compilation, enrichment, and analysis

## Contributing

To improve this dataset:

1. **Update OpenStreetMap** - Add or correct truck parking facilities at openstreetmap.org
2. **Report Issues** - Document inaccuracies or missing facilities
3. **Share Data Sources** - Provide links to official datasets or APIs
4. **Contribute Code** - Improve collection or analysis scripts
5. **Validate Facilities** - Field-verify capacity and amenities

## Acknowledgments

This project was made possible by:
- **OpenStreetMap contributors** - For maintaining detailed parking facility data
- **Nominatim service** - For reverse geocoding infrastructure
- **Overpass API** - For enabling efficient OSM data queries
- **Dutch road infrastructure community** - For ongoing facility documentation

## Project History

**October 30, 2025** - Comprehensive data collection phase
- Collected 1,425 truck parking facilities from OpenStreetMap
- Generated GeoJSON, CSV, and JSON outputs
- Created interactive map visualization
- Produced detailed analysis report
- Documented all data sources and gaps

---

**For questions, suggestions, or data updates, please use the project repository issues or contact the maintainer.**
