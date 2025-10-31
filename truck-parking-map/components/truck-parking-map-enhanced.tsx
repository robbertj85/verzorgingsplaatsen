"use client";

import { useEffect, useState, useRef } from "react";
import { MapContainer, TileLayer, GeoJSON, useMap, useMapEvents } from "react-leaflet";
import L, { LatLngExpression } from "leaflet";
import "leaflet/dist/leaflet.css";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Truck, MapPin, Search, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import area from "@turf/area";

// Fix Leaflet default icon issue with Next.js
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

interface EnrichedFeature {
  id: string;
  osm_id: number;
  osm_type: string;
  data_source: string;
  last_updated: string;
  tags: any;
  name: string;
  geometry: {
    type: string;
    coordinates: any;
  };
  latitude: number;
  longitude: number;
  location?: {
    highway_type?: string;
    municipality?: string;
    province?: string;
    road?: string;
    postcode?: string;
    highway?: string;
  };
  hgv?: string;
  parking_type?: string;
  confidence_score: number;
  classification: {
    is_truck_parking: boolean;
    is_rest_area: boolean;
    is_service_area: boolean;
    confidence: number;
  };
  capacity?: any;
  facility_type?: string;
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

// Component to handle zoom-based marker resizing
function ZoomHandler({ onZoomChange }: { onZoomChange: (zoom: number) => void }) {
  const map = useMapEvents({
    zoomend: () => {
      onZoomChange(map.getZoom());
    },
  });

  useEffect(() => {
    onZoomChange(map.getZoom());
  }, []);

  return null;
}

export default function TruckParkingMapEnhanced() {
  const [data, setData] = useState<EnrichedFeature[] | null>(null);
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
  const [zoom, setZoom] = useState(8);
  const [hoveredFacility, setHoveredFacility] = useState<string | null>(null);
  const [selectedFacility, setSelectedFacility] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [sidePanelOpen, setSidePanelOpen] = useState(true);
  const [leftPanelOpen, setLeftPanelOpen] = useState(true);
  const [showProvinces, setShowProvinces] = useState(true);
  const [showMunicipalities, setShowMunicipalities] = useState(false);
  const [provinces, setProvinces] = useState<any>(null);
  const [municipalities, setMunicipalities] = useState<any>(null);
  const geoJsonLayerRef = useRef<L.GeoJSON | null>(null);

  useEffect(() => {
    console.log("Fetching enriched truck parking data...");
    fetch("/truck_parking_enriched.json")
      .then((res) => {
        console.log("Response status:", res.status);
        return res.json();
      })
      .then((enrichedData: EnrichedFeature[]) => {
        console.log("Enriched data loaded:", {
          totalFeatures: enrichedData.length,
          firstFeature: enrichedData[0],
        });

        // Transform the data to add facility_type field
        const transformedFeatures = enrichedData.map((feature) => {
          let facility_type = "rest_area";
          if (feature.classification.is_truck_parking) {
            facility_type = "truck_parking";
          } else if (feature.classification.is_service_area) {
            facility_type = "service_area";
          } else if (feature.classification.is_rest_area) {
            facility_type = "rest_area";
          }

          return {
            ...feature,
            facility_type,
          };
        });

        console.log("Data transformed");
        setData(transformedFeatures);

        // Calculate stats
        const statsObj = {
          total: transformedFeatures.length,
          truck_parking: 0,
          service_area: 0,
          rest_area: 0,
        };

        transformedFeatures.forEach((feature) => {
          const type = feature.facility_type as keyof typeof statsObj;
          if (type && type in statsObj) {
            statsObj[type]++;
          }
        });

        console.log("Stats calculated:", statsObj);
        setStats(statsObj);
      })
      .catch((error) => console.error("Error loading data:", error));
  }, []);

  // Fetch administrative boundaries
  useEffect(() => {
    // Simplified Netherlands province boundaries (12 provinces)
    const simplifiedProvinces = {
      type: "FeatureCollection",
      features: [
        // We'll use a public API to get these boundaries
      ]
    };

    // For now, we'll fetch from a public API
    fetch("https://cartomap.github.io/nl/wgs84/provincie_2020.geojson")
      .then((res) => res.json())
      .then((data) => {
        console.log("Provinces loaded:", data);
        setProvinces(data);
      })
      .catch((error) => {
        console.error("Error loading provinces:", error);
        // Fallback to basic provinces if fetch fails
      });

    fetch("https://cartomap.github.io/nl/wgs84/gemeente_2020.geojson")
      .then((res) => res.json())
      .then((data) => {
        console.log("Municipalities loaded:", data);
        setMunicipalities(data);
      })
      .catch((error) => {
        console.error("Error loading municipalities:", error);
      });
  }, []);

  const center: LatLngExpression = [52.1326, 5.2913]; // Center of Netherlands
  const initialZoom = 8;

  const toggleFilter = (type: keyof typeof filters) => {
    setFilters((prev) => ({ ...prev, [type]: !prev[type] }));
  };

  const filteredData = data
    ? data.filter(
        (feature) =>
          filters[feature.facility_type as keyof typeof filters] &&
          (searchTerm === "" ||
            feature.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            feature.location?.municipality?.toLowerCase().includes(searchTerm.toLowerCase()) ||
            feature.location?.province?.toLowerCase().includes(searchTerm.toLowerCase()) ||
            feature.location?.highway?.toLowerCase().includes(searchTerm.toLowerCase()))
      )
    : [];

  // Calculate radius based on zoom level
  const getMarkerRadius = (zoomLevel: number) => {
    if (zoomLevel <= 7) return 4;
    if (zoomLevel <= 9) return 6;
    if (zoomLevel <= 11) return 8;
    if (zoomLevel <= 13) return 10;
    return 12;
  };

  const handleFacilityClick = (facilityId: string) => {
    setSelectedFacility(facilityId);
    const facility = filteredData.find((f) => f.id === facilityId);
    if (facility && geoJsonLayerRef.current) {
      // Find the layer and open popup
      geoJsonLayerRef.current.eachLayer((layer: any) => {
        if (layer.feature?.id === facilityId) {
          layer.openPopup();
        }
      });
    }
  };

  const renderFacilityDetails = (feature: EnrichedFeature) => {
    const tags = feature.tags || {};
    const capacity = feature.capacity || tags;

    return (
      <div className="text-xs space-y-1">
        <p><strong>Name:</strong> {feature.name}</p>
        <p><strong>Type:</strong> {FACILITY_LABELS[feature.facility_type as keyof typeof FACILITY_LABELS]}</p>

        {/* Capacity Information */}
        {capacity?.["capacity:truck"] && (
          <p><strong>🚛 Truck Capacity:</strong> {capacity["capacity:truck"]} spaces</p>
        )}
        {capacity?.capacity && !capacity?.["capacity:truck"] && (
          <p><strong>Capacity:</strong> {capacity.capacity} spaces</p>
        )}

        {/* Location */}
        {feature.location?.highway && (
          <p><strong>Highway:</strong> {feature.location.highway}</p>
        )}
        {feature.location?.municipality && (
          <p><strong>Municipality:</strong> {feature.location.municipality}</p>
        )}
        {feature.location?.province && (
          <p><strong>Province:</strong> {feature.location.province}</p>
        )}
        {feature.location?.postcode && (
          <p><strong>Postcode:</strong> {feature.location.postcode}</p>
        )}

        {/* Additional Tags */}
        {tags.operator && <p><strong>Operator:</strong> {tags.operator}</p>}
        {tags.opening_hours && <p><strong>Hours:</strong> {tags.opening_hours}</p>}
        {feature.hgv && <p><strong>HGV:</strong> {feature.hgv}</p>}
        {feature.parking_type && <p><strong>Parking Type:</strong> {feature.parking_type}</p>}

        {/* Amenities */}
        {(tags.fuel || tags.amenity?.includes("fuel")) && <p>⛽ Fuel available</p>}
        {tags.restaurant && <p>🍴 Restaurant</p>}
        {tags.toilets && <p>🚻 Toilets</p>}
        {tags.wifi && <p>📶 WiFi</p>}

        {/* More capacity details */}
        {capacity?.["capacity:shower"] && <p><strong>Showers:</strong> {capacity["capacity:shower"]}</p>}
        {capacity?.["capacity:toilets"] && <p><strong>Toilets:</strong> {capacity["capacity:toilets"]}</p>}
        {capacity?.["capacity:restaurant"] && <p><strong>Restaurant Capacity:</strong> {capacity["capacity:restaurant"]}</p>}

        <p className="pt-1 border-t mt-1 text-gray-500">
          <strong>Confidence:</strong> {(feature.confidence_score * 100).toFixed(0)}%
        </p>
      </div>
    );
  };

  return (
    <div className="flex h-screen">
      {/* Left Panel - Filters */}
      {leftPanelOpen && (
        <div className="w-80 border-r bg-background overflow-y-auto flex flex-col">
          {/* Header */}
          <div className="p-4 border-b">
            <div className="flex items-center gap-3 mb-2">
              <Truck className="h-6 w-6 text-primary" />
              <div className="flex-1">
                <h2 className="text-lg font-bold">Filters & Layers</h2>
                <p className="text-xs text-muted-foreground">
                  {stats.total.toLocaleString()} facilities
                </p>
              </div>
              <button
                onClick={() => setLeftPanelOpen(false)}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>

          {/* Facility Type Filters */}
          <div className="p-4 border-b">
            <h3 className="font-semibold mb-3 text-sm">Facility Types</h3>
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="truck_parking"
                  checked={filters.truck_parking}
                  onCheckedChange={() => toggleFilter("truck_parking")}
                />
                <Label
                  htmlFor="truck_parking"
                  className="flex items-center gap-2 cursor-pointer text-sm"
                >
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: FACILITY_COLORS.truck_parking }}
                  />
                  {FACILITY_LABELS.truck_parking}
                  <Badge variant="secondary" className="ml-auto">
                    {stats.truck_parking}
                  </Badge>
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
                  className="flex items-center gap-2 cursor-pointer text-sm"
                >
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: FACILITY_COLORS.service_area }}
                  />
                  {FACILITY_LABELS.service_area}
                  <Badge variant="secondary" className="ml-auto">
                    {stats.service_area}
                  </Badge>
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
                  className="flex items-center gap-2 cursor-pointer text-sm"
                >
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: FACILITY_COLORS.rest_area }}
                  />
                  {FACILITY_LABELS.rest_area}
                  <Badge variant="secondary" className="ml-auto">
                    {stats.rest_area}
                  </Badge>
                </Label>
              </div>
            </div>
          </div>

          {/* Administrative Boundaries */}
          <div className="p-4">
            <h3 className="font-semibold mb-3 text-sm">Administrative Boundaries</h3>
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="provinces"
                  checked={showProvinces}
                  onCheckedChange={() => setShowProvinces(!showProvinces)}
                />
                <Label
                  htmlFor="provinces"
                  className="flex items-center gap-2 cursor-pointer text-sm"
                >
                  🗺️ Province Borders
                  <Badge variant="outline" className="ml-auto">
                    12
                  </Badge>
                </Label>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="municipalities"
                  checked={showMunicipalities}
                  onCheckedChange={() => setShowMunicipalities(!showMunicipalities)}
                />
                <Label
                  htmlFor="municipalities"
                  className="flex items-center gap-2 cursor-pointer text-sm"
                >
                  🏘️ Municipal Borders
                  <Badge variant="outline" className="ml-auto">
                    ~350
                  </Badge>
                </Label>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Toggle button when left panel is closed */}
      {!leftPanelOpen && (
        <button
          onClick={() => setLeftPanelOpen(true)}
          className="absolute left-4 top-4 z-[1000] bg-background border rounded-lg p-3 shadow-lg hover:bg-gray-50"
        >
          <MapPin className="h-5 w-5" />
        </button>
      )}

      {/* Main Map Area */}
      <div className="flex-1 flex flex-col">

        {/* Map */}
        <div className="flex-1 relative">
          {data ? (
            <MapContainer
              center={center}
              zoom={initialZoom}
              className="h-full w-full"
              style={{ background: "#f0f0f0" }}
            >
              <ZoomHandler onZoomChange={setZoom} />
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {filteredData.length > 0 && (
                <GeoJSON
                  ref={geoJsonLayerRef}
                  key={`${JSON.stringify(filters)}-${zoom}-${searchTerm}`}
                  data={{
                    type: "FeatureCollection",
                    features: filteredData.map((f) => ({
                      type: "Feature",
                      id: f.id,
                      geometry: f.geometry,
                      properties: f,
                    })),
                  } as any}
                  pointToLayer={(feature, latlng) => {
                    const props = feature.properties as EnrichedFeature;
                    const type = props.facility_type as keyof typeof FACILITY_COLORS;
                    const color = FACILITY_COLORS[type] || "#999";

                    return L.circleMarker(latlng, {
                      radius: getMarkerRadius(zoom),
                      fillColor: color,
                      color: "#fff",
                      weight: 2,
                      opacity: 1,
                      fillOpacity: 0.85,
                    });
                  }}
                  onEachFeature={(feature, layer) => {
                    const props = feature.properties as EnrichedFeature;
                    const tags = props.tags || {};
                    const capacity = props.capacity || tags;

                    // Calculate polygon area
                    let polygonArea = null;
                    if (feature.geometry.type === "Polygon" || feature.geometry.type === "MultiPolygon") {
                      try {
                        const areaInSquareMeters = area(feature.geometry);
                        polygonArea = Math.round(areaInSquareMeters);
                      } catch (e) {
                        console.error("Error calculating area:", e);
                      }
                    }

                    // Extract parking capacities
                    const hgvCapacity = capacity?.["capacity:hgv"] || capacity?.["capacity:truck"] || null;
                    const vanCapacity = capacity?.["capacity:van"] || null;
                    const carCapacity = capacity?.["capacity:car"] || capacity?.capacity;

                    // Check if capacity is a string like "74 hgv"
                    if (typeof carCapacity === "string" && carCapacity.includes("hgv")) {
                      const match = carCapacity.match(/(\d+)\s*hgv/i);
                      if (match && !hgvCapacity) {
                        const extractedHgv = match[1];
                        // Use this as HGV capacity instead
                      }
                    }

                    // Build amenities list
                    const amenities = [];
                    if (tags.fuel || tags.amenity?.includes("fuel")) amenities.push("⛽");
                    if (tags.restaurant) amenities.push("🍴");
                    if (tags.toilets) amenities.push("🚻");
                    if (tags.wifi) amenities.push("📶");
                    if (capacity?.["capacity:shower"]) amenities.push("🚿");

                    const popupContent = `
                      <div style="min-width: 480px; max-width: 600px; font-family: system-ui, -apple-system, sans-serif;">
                        <!-- Header -->
                        <div style="background: ${
                          FACILITY_COLORS[props.facility_type as keyof typeof FACILITY_COLORS] || "#666"
                        }; color: white; padding: 12px 16px; margin: -12px -12px 12px -12px; border-radius: 8px 8px 0 0;">
                          <h3 style="margin: 0; font-size: 18px; font-weight: 600;">
                            ${props.name !== "Unnamed" ? props.name : "Truck Parking Facility"}
                          </h3>
                          <div style="font-size: 13px; opacity: 0.9; margin-top: 2px;">
                            ${FACILITY_LABELS[props.facility_type as keyof typeof FACILITY_LABELS]}
                            ${amenities.length > 0 ? ` • ${amenities.join(" ")}` : ""}
                          </div>
                        </div>

                        <!-- Main Content Grid -->
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; font-size: 13px;">

                          <!-- Left Column -->
                          <div>
                            ${hgvCapacity || vanCapacity || carCapacity || polygonArea ? `
                            <div style="background: #f8fafc; padding: 10px; border-radius: 6px; margin-bottom: 12px;">
                              <div style="font-weight: 600; margin-bottom: 6px; color: #334155;">🚛 Parking Capacity</div>
                              ${hgvCapacity ? `<div style="margin-bottom: 4px;">HGV/Trucks: <strong>${hgvCapacity}</strong> spaces</div>` : ""}
                              ${vanCapacity ? `<div style="margin-bottom: 4px;">Vans: <strong>${vanCapacity}</strong> spaces</div>` : ""}
                              ${carCapacity && !hgvCapacity ? `<div style="margin-bottom: 4px;">Total: <strong>${carCapacity}</strong> spaces</div>` : ""}
                              ${polygonArea ? `<div style="margin-top: 6px; padding-top: 6px; border-top: 1px solid #e2e8f0;">📏 Area: <strong>${polygonArea.toLocaleString()} m²</strong></div>` : ""}
                            </div>
                            ` : ""}

                            ${props.location?.highway || props.location?.municipality ? `
                            <div style="margin-bottom: 12px;">
                              <div style="font-weight: 600; margin-bottom: 6px; color: #334155;">📍 Location</div>
                              ${props.location?.highway ? `<div style="margin-bottom: 3px;">${props.location.highway}</div>` : ""}
                              ${props.location?.municipality ? `<div style="margin-bottom: 3px;">${props.location.municipality}${props.location?.province ? `, ${props.location.province}` : ""}</div>` : ""}
                              ${props.location?.postcode ? `<div>${props.location.postcode}</div>` : ""}
                            </div>
                            ` : ""}
                          </div>

                          <!-- Right Column -->
                          <div>
                            ${tags.operator || tags.opening_hours ? `
                            <div style="background: #f8fafc; padding: 10px; border-radius: 6px; margin-bottom: 12px;">
                              <div style="font-weight: 600; margin-bottom: 6px; color: #334155;">👔 Operations</div>
                              ${tags.operator ? `<div style="margin-bottom: 4px;"><strong>Operator:</strong> ${tags.operator}</div>` : ""}
                              ${tags.opening_hours ? `<div><strong>Hours:</strong> ${tags.opening_hours}</div>` : ""}
                            </div>
                            ` : ""}

                            ${capacity?.["capacity:shower"] || capacity?.["capacity:toilets"] || capacity?.["capacity:restaurant"] ? `
                            <div style="background: #f8fafc; padding: 10px; border-radius: 6px; margin-bottom: 12px;">
                              <div style="font-weight: 600; margin-bottom: 6px; color: #334155;">🏢 Facilities</div>
                              ${capacity["capacity:shower"] ? `<div style="margin-bottom: 3px;">🚿 Showers: ${capacity["capacity:shower"]}</div>` : ""}
                              ${capacity["capacity:toilets"] ? `<div style="margin-bottom: 3px;">🚻 Toilets: ${capacity["capacity:toilets"]}</div>` : ""}
                              ${capacity["capacity:restaurant"] ? `<div>🍴 Restaurant: ${capacity["capacity:restaurant"]}</div>` : ""}
                            </div>
                            ` : ""}

                            ${Object.keys(tags).filter(k => !["operator", "opening_hours", "highway", "name", "amenity", "fuel", "restaurant", "toilets", "wifi"].includes(k) && !k.startsWith("capacity")).length > 0 ? `
                            <div style="margin-bottom: 12px;">
                              <div style="font-weight: 600; margin-bottom: 6px; color: #334155;">🏷️ Tags</div>
                              <div style="font-size: 11px; line-height: 1.6;">
                                ${Object.entries(tags)
                                  .filter(([key]) => !["operator", "opening_hours", "highway", "name", "amenity", "fuel", "restaurant", "toilets", "wifi"].includes(key) && !key.startsWith("capacity"))
                                  .slice(0, 5)
                                  .map(([key, value]) => `<div><span style="color: #64748b;">${key}:</span> ${typeof value === "string" ? value : JSON.stringify(value)}</div>`)
                                  .join("")}
                              </div>
                            </div>
                            ` : ""}
                          </div>
                        </div>

                        <!-- Footer Metadata -->
                        <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #e2e8f0; font-size: 11px; color: #64748b; display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                          <div>
                            <div>ID: ${props.id.split("_").slice(-1)[0]}</div>
                            <div>OSM: ${props.osm_id} (${props.osm_type})</div>
                            <div>Confidence: ${(props.confidence_score * 100).toFixed(0)}%</div>
                          </div>
                          <div style="text-align: right;">
                            <div>${props.latitude.toFixed(5)}, ${props.longitude.toFixed(5)}</div>
                            <div>${new Date(props.last_updated).toLocaleDateString()}</div>
                            <div style="color: #3b82f6; cursor: pointer;" onclick="window.open('https://www.openstreetmap.org/${props.osm_type}/${props.osm_id}', '_blank')">View on OSM →</div>
                          </div>
                        </div>
                      </div>
                    `;
                    layer.bindPopup(popupContent, { maxWidth: 600 });

                    layer.on("click", () => {
                      setSelectedFacility(props.id);
                    });
                  }}
                />
              )}

              {/* Provincial Boundaries */}
              {showProvinces && provinces && (
                <GeoJSON
                  data={provinces}
                  style={{
                    color: "#4B5563",
                    weight: 2,
                    fillOpacity: 0,
                    opacity: 0.6,
                  }}
                  onEachFeature={(feature, layer) => {
                    if (feature.properties?.name) {
                      layer.bindTooltip(feature.properties.name, {
                        permanent: false,
                        direction: "center",
                        className: "province-tooltip",
                      });
                    }
                  }}
                />
              )}

              {/* Municipal Boundaries */}
              {showMunicipalities && municipalities && (
                <GeoJSON
                  data={municipalities}
                  style={{
                    color: "#9CA3AF",
                    weight: 1.5,
                    fillOpacity: 0,
                    opacity: 0.6,
                  }}
                  onEachFeature={(feature, layer) => {
                    if (feature.properties?.name) {
                      layer.bindTooltip(feature.properties.name, {
                        permanent: false,
                        direction: "center",
                        className: "municipality-tooltip",
                      });
                    }
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

      {/* Side Panel */}
      {sidePanelOpen && (
        <div className="w-96 border-l bg-background overflow-hidden flex flex-col">
          <div className="p-4 border-b flex items-center justify-between">
            <div className="flex items-center gap-2">
              <MapPin className="h-5 w-5" />
              <h2 className="font-bold">All Facilities ({filteredData.length})</h2>
            </div>
            <button
              onClick={() => setSidePanelOpen(false)}
              className="p-1 hover:bg-gray-100 rounded"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Search */}
          <div className="p-4 border-b">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Search by name, location..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          {/* Facilities List */}
          <div className="flex-1 overflow-y-auto">
            {filteredData.map((facility) => (
              <div
                key={facility.id}
                className={`p-3 border-b cursor-pointer transition-colors ${
                  hoveredFacility === facility.id
                    ? "bg-blue-50"
                    : selectedFacility === facility.id
                    ? "bg-blue-100"
                    : "hover:bg-gray-50"
                }`}
                onMouseEnter={() => setHoveredFacility(facility.id)}
                onMouseLeave={() => setHoveredFacility(null)}
                onClick={() => handleFacilityClick(facility.id)}
              >
                <div className="flex items-start gap-2">
                  <div
                    className="w-3 h-3 rounded-full mt-1 flex-shrink-0"
                    style={{
                      backgroundColor:
                        FACILITY_COLORS[facility.facility_type as keyof typeof FACILITY_COLORS] ||
                        "#999",
                    }}
                  />
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-sm truncate">
                      {facility.name !== "Unnamed" ? facility.name : `Facility #${facility.osm_id}`}
                    </h3>
                    {hoveredFacility === facility.id ? (
                      <div className="mt-2">
                        {renderFacilityDetails(facility)}
                      </div>
                    ) : (
                      <div className="text-xs text-muted-foreground mt-1">
                        <p>{FACILITY_LABELS[facility.facility_type as keyof typeof FACILITY_LABELS]}</p>
                        {facility.location?.municipality && (
                          <p>{facility.location.municipality}, {facility.location.province}</p>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Toggle button when panel is closed */}
      {!sidePanelOpen && (
        <button
          onClick={() => setSidePanelOpen(true)}
          className="absolute right-4 top-20 z-[1000] bg-background border rounded-lg p-3 shadow-lg hover:bg-gray-50"
        >
          <MapPin className="h-5 w-5" />
        </button>
      )}
    </div>
  );
}
