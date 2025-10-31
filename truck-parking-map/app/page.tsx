"use client";

import dynamic from "next/dynamic";

// Import the enhanced map component with no SSR to avoid Leaflet errors
const TruckParkingMapEnhanced = dynamic(() => import("@/components/truck-parking-map-enhanced"), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-screen">
      <p className="text-muted-foreground">Loading map...</p>
    </div>
  ),
});

export default function Home() {
  return <TruckParkingMapEnhanced />;
}
