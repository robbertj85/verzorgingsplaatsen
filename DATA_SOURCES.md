# Data Sources Integration Guide

This document describes all integrated truck parking data sources in the application and how to add more.

## 📊 Currently Integrated Data Sources

### 1. Zenodo (Fraunhofer ISI) - Europe-Wide Dataset ✅
- **Type**: Static facility data (research dataset)
- **API Endpoint**: `/api/zenodo`
- **Data Format**: CSV
- **Coverage**: Europe (EU-27, EFTA, UK) - 19,713 facilities
- **Update Frequency**: Static dataset (refreshed on demand)
- **Layer Color**: Orange
- **Cost**: Free (Open Research Data)

**Data Source**:
- CSV: `https://zenodo.org/records/10231359/files/truckParkingLocationsEurope_MediumHigh_v03.csv` (1.6MB)
- DOI: 10.5281/zenodo.10231359
- Published: 2024 (Fraunhofer Institute for Systems and Innovation Research)

**Features**:
- Truck stop category classification
- Precise latitude and longitude coordinates
- Parking area size (when available)
- Country assignment
- Medium-to-high confidence locations (validated from OSM)

**Implementation**:
- File: `truck-parking-map/app/api/zenodo/route.ts`
- Lazy loading: Only fetched when layer is enabled
- Caching: 24 hours (static dataset)
- Coverage: All of Europe with standardized categorization

**Note**: This layer is disabled by default due to the large number of markers (19k+). Enable it to see comprehensive European coverage.

### 2. OpenStreetMap (OSM) - Primary Dataset ✅
- **Type**: Static facility data
- **Location**: `/public/truck_parking_enriched.json` (2.6MB)
- **Coverage**: Netherlands (~1,425 facilities)
- **Data Quality**: 44% high confidence, 6.1% with capacity data
- **Update Frequency**: Manual updates from OSM
- **Layer Color**: Red (truck parking), Blue (service areas), Green (rest areas)

**Features**:
- Facility names and locations
- OSM tags (amenities, operators, opening hours)
- Geocoded location data (municipality, province, highway)
- Classification (truck parking, service area, rest area)
- Capacity data (when available)
- Confidence scores

### 3. NDW (Nationaal Dataportaal Wegverkeer) - Real-Time Data ✅
- **Type**: Live occupancy data
- **API Endpoint**: `/api/ndw`
- **Data Format**: DATEX II XML (v2.3 static, v3.0 dynamic)
- **Coverage**: Netherlands
- **Update Frequency**: Every minute
- **Layer Color**: Green/Orange/Red based on occupancy
- **Cost**: Free (Open Data)

**Data Sources**:
- Static: `https://opendata.ndw.nu/Truckparking_Parking_Table.xml` (44KB)
- Dynamic: `https://opendata.ndw.nu/Truckparking_Parking_Status.xml` (14KB, updates every 60s)

**Features**:
- Real-time vacant/occupied spaces
- Occupancy percentage (0-100%)
- Status (spacesAvailable, full, unknown)
- Facility capacity breakdown (total, lorry, refrigerated, heavy haul)
- Operator information (name, contact)
- Pricing information
- Security features (CCTV, fencing, guards, certification)
- Access information (motorway, junction, distance)
- Amenities (restaurant, shower, toilet, WiFi, fuel)

**Implementation**:
- File: `truck-parking-map/app/api/ndw/route.ts`
- Types: `truck-parking-map/lib/ndw-types.ts`
- Auto-refresh: Every 60 seconds
- Caching: Table cached for 1 hour, status for 1 minute

### 4. EU ETPA (European Access Point for Truck Parking) ✅
- **Type**: Static facility data
- **API Endpoint**: `/api/eu-parking`
- **Data Format**: DATEX II XML
- **Coverage**: Austria, Germany (Schleswig-Holstein)
- **Update Frequency**: Hourly refresh (static data)
- **Layer Color**: Purple
- **Cost**: Free (Open Data)

**Data Sources**:
- Austria: `https://data.europa.eu/euodp/repository/ec/dg-move/etpa/AT-ASFINAG.xml`
- Germany (SH): `https://data.europa.eu/euodp/repository/ec/dg-move/etpa/DE-DE-SH-ITP.xml`

**Features**:
- Facility names and locations
- Total and HGV-specific capacity
- Security certification levels
- Facilities and amenities
- Country identification

**Implementation**:
- File: `truck-parking-map/app/api/eu-parking/route.ts`
- Auto-refresh: Every 60 minutes
- Extensible: Easy to add more countries

## 🔍 Investigated But Not Integrated

### Truck Parking Europe API ❌
- **Status**: Requires authentication
- **Access**: Token-based with provider approval
- **Cost**: Free tier available, but requires registration
- **Reason for exclusion**: Not freely accessible without authentication

### Rijkswaterstaat VILD Database ⏳
- **URL**: https://maps.rijkswaterstaat.nl/dataregister/
- **Status**: Could be integrated for cross-validation
- **Note**: Would complement existing Dutch data

## 📝 How to Add More EU Countries

The EU ETPA repository contains DATEX II data for multiple European countries. To add more:

1. **Find Available Countries**
   - Visit: `https://data.europa.eu/data/datasets/etpa`
   - Repository: `https://data.europa.eu/euodp/repository/ec/dg-move/etpa/`

2. **Add Country to API Route**
   - Edit: `truck-parking-map/app/api/eu-parking/route.ts`
   - Add to `EU_DATA_SOURCES` array:
   ```typescript
   {
     country: 'BE',
     name: 'Belgium',
     url: 'https://data.europa.eu/euodp/repository/ec/dg-move/etpa/BE-*.xml'
   }
   ```

3. **Update UI Label**
   - Edit: `truck-parking-map/components/truck-parking-map-enhanced.tsx`
   - Update the country list in the EU layer panel (around line 808)

4. **Test**
   - The layer will automatically refresh with new data
   - Purple markers will appear for new facilities

## 🌍 Potential Additional Data Sources

### 1. National Data Portals
- **data.overheid.nl**: Dutch government open data portal
- **Status**: Additional datasets may be available for facilities, capacity, regulations

## 🛠️ API Endpoints

### `/api/zenodo`
Returns Zenodo (Fraunhofer ISI) facilities for all of Europe.

**Response**:
```json
{
  "facilities": [
    {
      "id": "zenodo-DE-12345",
      "name": "Parking Name",
      "category": "parking",
      "location": { "latitude": 52.xxx, "longitude": 13.xxx },
      "country": "DE",
      "area": 15000,
      "source": "Zenodo (Fraunhofer ISI)"
    }
  ],
  "totalFacilities": 19713,
  "countries": 30,
  "countryStats": {
    "DE": 5234,
    "FR": 3821,
    "IT": 2103,
    ...
  },
  "lastUpdated": "2025-11-17T23:30:00Z",
  "source": "Zenodo (Fraunhofer ISI)",
  "doi": "10.5281/zenodo.10231359",
  "dataset": "European Truck Parking Locations (Medium-High Confidence)"
}
```

### `/api/facilities`
Returns filtered OSM facilities based on viewport and search criteria.

**Query Parameters**:
- `bounds`: Viewport bounds (`minLat,minLng,maxLat,maxLng`)
- `types`: Facility types (`truck_parking,service_area,rest_area`)
- `search`: Search term
- `limit`: Max results (default: 1000)
- `offset`: Pagination offset (default: 0)

**Response**:
```json
{
  "facilities": [...],
  "stats": {
    "total": 1425,
    "truck_parking": 627,
    "service_area": 298,
    "rest_area": 500
  },
  "total": 1425,
  "offset": 0,
  "limit": 1000
}
```

### `/api/ndw`
Returns NDW facilities with real-time occupancy data.

**Response**:
```json
{
  "facilities": [
    {
      "id": "NL-12_421",
      "name": "Parking Name",
      "location": { "latitude": 52.xxx, "longitude": 5.xxx },
      "capacity": { "totalSpaces": 100, "lorrySpaces": 80 },
      "liveStatus": {
        "vacantSpaces": 25,
        "occupiedSpaces": 75,
        "occupancy": 75,
        "status": "spacesAvailable",
        "timestamp": "2025-11-17T23:25:00Z"
      },
      // ... more fields
    }
  ],
  "totalFacilities": 50,
  "lastUpdated": "2025-11-17T23:25:00Z",
  "tableVersion": 1
}
```

### `/api/eu-parking`
Returns EU ETPA facilities from configured countries.

**Response**:
```json
{
  "facilities": [
    {
      "id": "AT-12345",
      "country": "AT",
      "name": "Parkplatz Name",
      "location": { "latitude": 48.xxx, "longitude": 16.xxx },
      "capacity": { "totalSpaces": 150, "hgvSpaces": 120 },
      "security": { "certified": true, "certificationLevel": "Level 3" },
      "facilities": ["restaurant", "shower", "toilet"],
      "source": "Austria"
    }
  ],
  "totalFacilities": 200,
  "sources": [
    { "country": "AT", "name": "Austria" },
    { "country": "DE", "name": "Germany (Schleswig-Holstein)" }
  ],
  "lastUpdated": "2025-11-17T23:00:00Z"
}
```

## 🎨 Map Layer Controls

All data sources can be toggled on/off via the left sidebar:

1. **Facility Types** (OSM Data)
   - Truck Parking (Red)
   - Service Areas (Blue)
   - Rest Areas (Green)

2. **NDW Live Data** (Blue panel)
   - Real-time occupancy indicators
   - Color-coded by availability (green/orange/red)
   - Auto-refreshes every minute
   - ~50 facilities with live status

3. **EU Data (ETPA)** (Purple panel)
   - European facilities (Austria, Germany)
   - Purple markers
   - Refreshes hourly
   - ~200+ certified facilities

4. **Zenodo Europe-Wide** (Orange panel)
   - 19,713 facilities across EU-27, EFTA, UK
   - Orange markers
   - Disabled by default (enable to load 1.6MB dataset)
   - Comprehensive European coverage
   - Validated research data

5. **Additional Overlays**
   - Province borders
   - Municipal borders
   - Detected parking spaces (AI analysis)

## 📊 Data Statistics

| Source | Facilities | Coverage | Update Frequency | Real-Time |
|--------|-----------|----------|------------------|-----------|
| Zenodo | 19,713 | EU-27, EFTA, UK | Static (24h cache) | No |
| OSM | ~1,425 | Netherlands | Manual | No |
| NDW | ~50 | Netherlands | 60 seconds | Yes |
| EU ETPA | ~200+ | AT, DE (SH) | 1 hour | No |
| **Total** | **~21,600+** | **Europe-wide** | **Mixed** | **Partial** |

## 🔗 Useful Links

- **Zenodo Dataset**: https://zenodo.org/records/10231359
- **Zenodo DOI**: https://doi.org/10.5281/zenodo.10231359
- **Fraunhofer ISI**: https://www.isi.fraunhofer.de/
- **ScienceDirect Publication**: https://www.sciencedirect.com/science/article/pii/S2352340924002464
- **NDW Documentation**: https://docs.ndw.nu/producten/truckparking/
- **NDW Open Data Portal**: https://opendata.ndw.nu/
- **EU ETPA Dataset**: https://data.europa.eu/data/datasets/etpa
- **DATEX II Standard**: https://datex2.eu/
- **OpenStreetMap**: https://www.openstreetmap.org/

## 📅 Update Schedule

- **Zenodo Data**: Static dataset, cached for 24 hours (lazy loaded when enabled)
- **OSM Data**: Manual updates required (check OSM for changes)
- **NDW Static Data**: Cached for 1 hour, auto-refresh
- **NDW Dynamic Data**: Cached for 1 minute, auto-refresh
- **EU Data**: Cached for 1 hour, auto-refresh

## 💡 Contributing New Data Sources

To add a new data source:

1. Create an API route in `truck-parking-map/app/api/[source-name]/route.ts`
2. Parse the data into a consistent format (see existing routes as examples)
3. Add state management in `truck-parking-map/components/truck-parking-map-enhanced.tsx`
4. Add UI controls in the sidebar
5. Add GeoJSON layer rendering
6. Update this documentation
7. Test the integration

For DATEX II sources, reuse the XML parser and helper functions from the NDW route.
