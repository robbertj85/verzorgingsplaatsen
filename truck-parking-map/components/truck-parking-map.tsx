"use client";

import { useEffect, useState, useRef } from "react";
import { MapContainer, TileLayer, GeoJSON, useMap, useMapEvents } from "react-leaflet";
import L, { LatLngExpression } from "leaflet";
import "leaflet/dist/leaflet.css";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Truck, MapPin, Search } from "lucide-react";

// Fix Leaflet default icon issue with Next.js
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

interface TruckParkingFeature {
  type: string;
  properties: {
    id?: string;
    name?: string;
    osm_id?: number;
    facility_type?: string;
    is_truck_parking?: boolean;
    is_rest_area?: boolean;
    is_service_area?: boolean;
    data_source?: string;
    last_updated?: string;
    confidence_score?: number;
    municipality?: string;
    province?: string;
    highway?: string;
    road?: string;
    postcode?: string;
    operator?: string;
    opening_hours?: string;
    hgv?: string;
    has_fuel?: boolean;
    has_restaurant?: boolean;
    has_toilets?: boolean;
    has_wifi?: boolean;
    capacity?: number;
    amenities?: string[];
    [key: string]: any; // Allow additional properties
  };
  geometry: {
    type: string;
    coordinates: any;
  };
}

interface TruckParkingData {
  type: string;
  features: TruckParkingFeature[];
}

const FACILITY_COLORS = {
  truck_parking: "#ef4444",
  service_area: "#3b82f6",
  rest_area: "#10b981",
};

const FACILITY_LABELS = {
  truck_parking: "Truck Parking",
  service_area: "Service Area",
  rest_area: "Rest Area",
};

function MapUpdater({ bounds }: { bounds: any }) {
  const map = useMap();
  useEffect(() => {
    if (bounds) {
      map.fitBounds(bounds);
    }
  }, [bounds, map]);
  return null;
}

export default function TruckParkingMap() {
  const [data, setData] = useState<TruckParkingData | null>(null);
  const [filters, setFilters] = useState({
    truck_parking: true,
    service_area: true,
    rest_area: true,
  });
  const [stats, setStats] = useState({
    total: 0,
    truck_parking: 0,
    service_area: 0,
    rest_area: 0,
  });

  useEffect(() => {
    console.log("Fetching truck parking data...");
    fetch("/truck_parking_facilities.geojson")
      .then((res) => {
        console.log("Response status:", res.status);
        return res.json();
      })
      .then((geojson: TruckParkingData) => {
        console.log("Data loaded:", {
          totalFeatures: geojson.features.length,
          firstFeature: geojson.features[0],
        });

        // Transform the data to add facility_type field based on boolean flags
        const transformedFeatures = geojson.features.map((feature) => {
          let facility_type = "rest_area"; // default
          if (feature.properties.is_truck_parking) {
            facility_type = "truck_parking";
          } else if (feature.properties.is_service_area) {
            facility_type = "service_area";
          } else if (feature.properties.is_rest_area) {
            facility_type = "rest_area";
          }

          return {
            ...feature,
            properties: {
              ...feature.properties,
              facility_type,
            },
          };
        });

        const transformedData = {
          ...geojson,
          features: transformedFeatures,
        };

        console.log("Data transformed, first feature:", transformedFeatures[0]);
        setData(transformedData);

        // Calculate stats
        const statsObj = {
          total: transformedFeatures.length,
          truck_parking: 0,
          service_area: 0,
          rest_area: 0,
        };

        transformedFeatures.forEach((feature) => {
          const type = feature.properties.facility_type as keyof typeof statsObj;
          if (type && type in statsObj) {
            statsObj[type]++;
          }
        });

        console.log("Stats calculated:", statsObj);
        setStats(statsObj);
      })
      .catch((error) => console.error("Error loading data:", error));
  }, []);

  const center: LatLngExpression = [52.1326, 5.2913]; // Center of Netherlands
  const zoom = 8;

  const toggleFilter = (type: keyof typeof filters) => {
    setFilters((prev) => ({ ...prev, [type]: !prev[type] }));
  };

  const filteredData = data
    ? {
        ...data,
        features: data.features.filter(
          (feature) =>
            filters[feature.properties.facility_type as keyof typeof filters]
        ),
      }
    : null;

  useEffect(() => {
    if (filteredData) {
      console.log("Filtered data updated:", {
        totalFeatures: filteredData.features.length,
        filters,
      });
    }
  }, [filteredData, filters]);

  const bounds = filteredData?.features.length
    ? filteredData.features.map((feature: any) => {
        if (feature.geometry.type === "Point") {
          return [
            feature.geometry.coordinates[1],
            feature.geometry.coordinates[0],
          ];
        }
        return null;
      }).filter(Boolean)
    : null;

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="bg-background border-b p-4">
        <div className="container mx-auto">
          <div className="flex items-center gap-3 mb-4">
            <Truck className="h-8 w-8 text-primary" />
            <div>
              <h1 className="text-2xl font-bold">Dutch Truck Parking Facilities</h1>
              <p className="text-sm text-muted-foreground">
                {stats.total.toLocaleString()} facilities across the Netherlands
              </p>
            </div>
          </div>

          {/* Filters */}
          <div className="flex flex-wrap gap-4">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="truck_parking"
                checked={filters.truck_parking}
                onCheckedChange={() => toggleFilter("truck_parking")}
              />
              <Label
                htmlFor="truck_parking"
                className="flex items-center gap-2 cursor-pointer"
              >
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: FACILITY_COLORS.truck_parking }}
                />
                {FACILITY_LABELS.truck_parking}
                <Badge variant="secondary">{stats.truck_parking}</Badge>
              </Label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="service_area"
                checked={filters.service_area}
                onCheckedChange={() => toggleFilter("service_area")}
              />
              <Label
                htmlFor="service_area"
                className="flex items-center gap-2 cursor-pointer"
              >
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: FACILITY_COLORS.service_area }}
                />
                {FACILITY_LABELS.service_area}
                <Badge variant="secondary">{stats.service_area}</Badge>
              </Label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="rest_area"
                checked={filters.rest_area}
                onCheckedChange={() => toggleFilter("rest_area")}
              />
              <Label
                htmlFor="rest_area"
                className="flex items-center gap-2 cursor-pointer"
              >
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: FACILITY_COLORS.rest_area }}
                />
                {FACILITY_LABELS.rest_area}
                <Badge variant="secondary">{stats.rest_area}</Badge>
              </Label>
            </div>
          </div>
        </div>
      </div>

      {/* Map */}
      <div className="flex-1 relative">
        {data ? (
          <MapContainer
            center={center}
            zoom={zoom}
            className="h-full w-full"
            style={{ background: "#f0f0f0" }}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {filteredData && (
              <GeoJSON
                key={JSON.stringify(filters)}
                data={filteredData as any}
                pointToLayer={(feature, latlng) => {
                  const type = feature.properties
                    .facility_type as keyof typeof FACILITY_COLORS;
                  const color = FACILITY_COLORS[type] || "#999";

                  return L.circleMarker(latlng, {
                    radius: 7,
                    fillColor: color,
                    color: "#fff",
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.85,
                  });
                }}
                style={(feature) => {
                  const type = feature?.properties
                    .facility_type as keyof typeof FACILITY_COLORS;
                  return {
                    color: FACILITY_COLORS[type] || "#999",
                    weight: 2,
                    fillOpacity: 0.5,
                  };
                }}
                onEachFeature={(feature, layer) => {
                  const props = feature.properties;

                  // Build amenities list
                  const amenities = [];
                  if (props.has_fuel) amenities.push("⛽ Fuel");
                  if (props.has_restaurant) amenities.push("🍴 Restaurant");
                  if (props.has_toilets) amenities.push("🚻 Toilets");
                  if (props.has_wifi) amenities.push("📶 WiFi");

                  // Calculate area if polygon
                  let areaInfo = "";
                  if (feature.geometry.type === "Polygon" || feature.geometry.type === "MultiPolygon") {
                    try {
                      const area = L.GeometryUtil ? L.GeometryUtil.geodesicArea(feature.geometry.coordinates[0]) : null;
                      if (area) {
                        areaInfo = `<p><strong>Area:</strong> ${Math.round(area)} m²</p>`;
                      }
                    } catch (e) {
                      // Ignore area calculation errors
                    }
                  }

                  const popupContent = `
                    <div class="p-3" style="min-width: 280px; max-width: 400px;">
                      <h3 class="font-bold text-lg mb-3 pb-2 border-b" style="color: ${FACILITY_COLORS[props.facility_type as keyof typeof FACILITY_COLORS] || "#666"}">
                        ${props.name && props.name !== "Unnamed" ? props.name : "Truck Parking Facility"}
                      </h3>

                      <div class="space-y-2 text-sm">
                        <!-- Facility Info -->
                        <div class="mb-3">
                          <p class="mb-1"><strong>📍 Type:</strong> ${FACILITY_LABELS[props.facility_type as keyof typeof FACILITY_LABELS] || props.facility_type}</p>
                          ${props.capacity ? `<p class="mb-1"><strong>🚛 Capacity:</strong> ${props.capacity} parking spaces</p>` : ""}
                          ${props.hgv ? `<p class="mb-1"><strong>🚚 HGV:</strong> ${props.hgv}</p>` : ""}
                        </div>

                        <!-- Location Info -->
                        ${props.highway || props.road || props.municipality || props.province || props.postcode ? `
                        <div class="mb-3 pb-2 border-t pt-2">
                          <p class="font-semibold mb-1">📍 Location</p>
                          ${props.highway ? `<p class="ml-2 mb-1"><strong>Highway:</strong> ${props.highway}</p>` : ""}
                          ${props.road && props.road !== props.highway ? `<p class="ml-2 mb-1"><strong>Road:</strong> ${props.road}</p>` : ""}
                          ${props.municipality ? `<p class="ml-2 mb-1"><strong>Municipality:</strong> ${props.municipality}</p>` : ""}
                          ${props.province ? `<p class="ml-2 mb-1"><strong>Province:</strong> ${props.province}</p>` : ""}
                          ${props.postcode ? `<p class="ml-2 mb-1"><strong>Postcode:</strong> ${props.postcode}</p>` : ""}
                        </div>
                        ` : ""}

                        <!-- Operator & Hours -->
                        ${props.operator || props.opening_hours ? `
                        <div class="mb-3 pb-2 border-t pt-2">
                          ${props.operator ? `<p class="mb-1"><strong>👔 Operator:</strong> ${props.operator}</p>` : ""}
                          ${props.opening_hours ? `<p class="mb-1"><strong>🕐 Hours:</strong> ${props.opening_hours}</p>` : ""}
                        </div>
                        ` : ""}

                        <!-- Amenities -->
                        ${amenities.length > 0 ? `
                        <div class="mb-3 pb-2 border-t pt-2">
                          <p class="font-semibold mb-1">🏪 Amenities</p>
                          <p class="ml-2">${amenities.join(" • ")}</p>
                        </div>
                        ` : ""}

                        <!-- Area Info -->
                        ${areaInfo ? `
                        <div class="mb-3 pb-2 border-t pt-2">
                          ${areaInfo}
                        </div>
                        ` : ""}

                        <!-- Metadata -->
                        <div class="mt-3 pt-2 border-t text-xs" style="color: #666;">
                          ${props.id ? `<p class="mb-1"><strong>ID:</strong> ${props.id}</p>` : ""}
                          ${props.osm_id ? `<p class="mb-1"><strong>OSM ID:</strong> ${props.osm_id}</p>` : ""}
                          ${props.data_source ? `<p class="mb-1"><strong>Source:</strong> ${props.data_source}</p>` : ""}
                          ${props.confidence_score ? `<p class="mb-1"><strong>Confidence:</strong> ${(props.confidence_score * 100).toFixed(0)}%</p>` : ""}
                          ${props.last_updated ? `<p class="mb-1"><strong>Updated:</strong> ${new Date(props.last_updated).toLocaleDateString()}</p>` : ""}
                        </div>
                      </div>
                    </div>
                  `;
                  layer.bindPopup(popupContent, { maxWidth: 400 });
                }}
              />
            )}
          </MapContainer>
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-muted-foreground">Loading map data...</p>
          </div>
        )}
      </div>
    </div>
  );
}
