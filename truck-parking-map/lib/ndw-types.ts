/**
 * TypeScript interfaces for NDW (Nationale Databank Wegverkeersgegevens)
 * Truck Parking data structures
 */

// Parking Table (DATEX II 2.0) - Static facility data
export interface NDWParkingFacility {
  id: string; // e.g., "NL-12_421"
  version: number;
  name: string;
  location: {
    latitude: number;
    longitude: number;
  };
  address?: {
    street?: string;
    houseNumber?: string;
    postalCode?: string;
    city?: string;
  };
  capacity: {
    totalSpaces: number;
    lorrySpaces?: number;
    refrigeratedSpaces?: number;
    heavyHaulSpaces?: number;
  };
  operator?: {
    name?: string;
    email?: string;
    phone?: string;
  };
  pricing?: {
    rate?: number;
    currency?: string;
    website?: string;
  };
  facilities?: string[]; // e.g., ["restaurant", "shower", "toilet", "wifi"]
  security?: {
    cctv?: boolean;
    fencing?: boolean;
    lighting?: boolean;
    guards24h?: boolean;
    patrols?: boolean;
    certified?: boolean;
    certificationLevel?: number;
  };
  access?: {
    motorway?: string;
    junction?: string;
    distance?: number;
    barrierType?: string;
  };
}

// Parking Status (DATEX II 3.0) - Real-time occupancy data
export interface NDWParkingStatus {
  id: string; // References parking facility ID
  vacantSpaces: number;
  occupiedSpaces: number;
  occupancy: number; // Percentage (0-100)
  status: 'spacesAvailable' | 'full' | 'unknown';
  timestamp: string; // ISO 8601 datetime
  groupedStatus?: Array<{
    index: number;
    vacantSpaces: number;
    occupiedSpaces: number;
    occupancy: number;
  }>;
}

// Combined facility with real-time status
export interface NDWEnrichedFacility extends NDWParkingFacility {
  liveStatus?: NDWParkingStatus;
}

// API response structure
export interface NDWDataResponse {
  facilities: NDWEnrichedFacility[];
  lastUpdated: string;
  tableVersion: number;
  totalFacilities: number;
}
