# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an interactive web application for visualizing truck parking facilities (verzorgingsplaatsen) in the Netherlands. The application displays comprehensive data about truck parking locations along Dutch motorways using an interactive Leaflet map.

## Project Structure

```
Verzorgingsplaatsen/
├── truck-parking-map/          # Next.js web application
│   ├── app/                    # Next.js app directory
│   │   ├── page.tsx           # Main map page (uses dynamic import)
│   │   └── layout.tsx         # Root layout
│   ├── components/            # React components
│   │   ├── truck-parking-map-enhanced.tsx  # Main map component
│   │   └── ui/                # shadcn/ui components
│   ├── lib/                   # Utilities (cn helper)
│   └── public/                # Static files
│       └── truck_parking_enriched.json  # Facility data (2.6MB)
├── .git/                      # Version control
├── .gitignore                 # Git configuration
└── CLAUDE.md                  # This file
```

## Development Commands

All commands should be run from the `truck-parking-map/` directory:

```bash
cd truck-parking-map

# Development server (localhost:3000, or 3001 if 3000 is in use)
npm run dev

# Production build
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

## Technical Architecture

### Stack

- **Framework**: Next.js 16 with App Router
- **React**: Version 19.2.0 (Client components only - uses `"use client"`)
- **Styling**: Tailwind CSS 3.4 with PostCSS 4.1
- **UI Components**: shadcn/ui with Radix UI primitives
- **Mapping**: Leaflet 1.9.4 + react-leaflet 5.0
- **Geospatial**: Turf.js for area calculations and bounding boxes

### Critical Patterns

#### Leaflet SSR Handling (IMPORTANT!)
The map component uses dynamic imports with `ssr: false` to avoid Leaflet's window/document dependencies during server-side rendering:

```typescript
// app/page.tsx
const TruckParkingMapEnhanced = dynamic(
  () => import("@/components/truck-parking-map-enhanced"),
  { ssr: false, loading: () => <div>Loading map...</div> }
);
```

**Note**: This causes an expected "BAILOUT_TO_CLIENT_SIDE_RENDERING" message in development - this is normal and not an error!

#### Leaflet Icon Fix for Next.js
Leaflet default icons don't work out of the box with Next.js. The map component includes this fix:

```typescript
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png"
});
```

#### Client-Only Components
All interactive map components must use `"use client"` directive since Leaflet requires browser APIs.

## Data Schema

### EnrichedFeature (public/truck_parking_enriched.json)

The app loads facility data from `/truck_parking_enriched.json` via fetch. Each facility has:

- `osm_id`, `osm_type`: OpenStreetMap identifiers
- `name`: Facility name
- `geometry`: GeoJSON geometry (Point or Polygon)
- `latitude`, `longitude`: Coordinates
- `location`: Geocoded data (municipality, province, highway, road)
- `classification`: Confidence-scored categorization
  - `is_truck_parking`: Boolean
  - `is_rest_area`: Boolean
  - `is_service_area`: Boolean
  - `confidence`: 0-1 score
- `capacity`: Parking capacity data (when available)
- `tags`: Raw OSM tags (amenities, facilities, operators)
- `confidence_score`: Overall data quality score

### Facility Types & Colors
- **truck_parking**: Dedicated truck parking (red #ef4444)
- **service_area**: Full service areas (blue #3b82f6)
- **rest_area**: Basic rest areas (green #10b981)

## Domain Context

### Dutch Truck Parking System

**National Motorway Rest Areas** follow a three-tier public-private model:

1. **Land Ownership**: Rijksstaat (Dutch National Government)
2. **Infrastructure Management**: Rijkswaterstaat (manages motorway network)
3. **Property Management**: Rijksvastgoedbedrijf (handles concessions)
4. **Operations**: Private concessionaires (Shell, BP, Total, Esso) via 15-year leases

**Key Terms**:
- **Verzorgingsplaats (VZP)**: Rest area with facilities
- **Rijkswaterstaat (RWS)**: National road infrastructure agency
- **LZV**: Longer and heavier trucks (up to 25.25m)

**Data Context**:
- ~1,425 facilities in database (from OpenStreetMap)
- 44% high confidence facilities
- Only 6.1% have capacity data (major data gap)
- National shortage of ~4,400 truck parking spaces

## Common Development Tasks

### Updating Map Component
The main map component is at `truck-parking-map/components/truck-parking-map-enhanced.tsx`:
- Uses GeoJSON layer for rendering facilities
- Implements zoom-based marker sizing via `ZoomHandler` component
- Includes filtering by facility type
- Has search functionality

### Working with Data
- Data file: `truck-parking-map/public/truck_parking_enriched.json` (2.6MB)
- Loaded via fetch at `/truck_parking_enriched.json` (public path)
- To update data: replace the JSON file in `public/` directory

### Styling
- Uses Tailwind utility classes
- shadcn/ui components in `components/ui/`
- Custom colors defined in `FACILITY_COLORS` constant

## File Naming Conventions
- React components: `kebab-case.tsx` for file names
- Component names: `PascalCase`
- UI components from shadcn: lowercase with hyphens (e.g., `button.tsx`)
