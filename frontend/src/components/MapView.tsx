import { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, CircleMarker, Tooltip, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.heat';
import { format } from 'date-fns';
import type { MapPointResponse, MapViewProps } from '../types';

// Default center: Almaty, Kazakhstan
const DEFAULT_CENTER: [number, number] = [43.238949, 76.889709];
const DEFAULT_ZOOM = 12;

interface HeatmapLayerProps {
  points: MapPointResponse[];
}

function HeatmapLayer({ points }: HeatmapLayerProps) {
  const map = useMap();
  const heatLayerRef = useRef<L.Layer | null>(null);

  useEffect(() => {
    // Remove existing heat layer if it exists
    if (heatLayerRef.current) {
      map.removeLayer(heatLayerRef.current);
    }

    if (points.length === 0) return;

    // Find max CO2 for normalization
    const maxCO2 = Math.max(...points.map((p) => p.total_co2));

    // Create heat data: [lat, lng, intensity]
    const heatData: [number, number, number][] = points.map((point) => [
      point.latitude,
      point.longitude,
      point.total_co2 / maxCO2, // Normalize intensity
    ]);

    // Create and add heat layer
    const heatLayer = L.heatLayer(heatData, {
      radius: 25,
      blur: 15,
      maxZoom: 17,
      max: 1.0,
      gradient: {
        0.0: 'green',
        0.25: 'yellow',
        0.5: 'orange',
        0.75: 'red',
        1.0: 'darkred',
      },
    });

    heatLayer.addTo(map);
    heatLayerRef.current = heatLayer;

    return () => {
      if (heatLayerRef.current) {
        map.removeLayer(heatLayerRef.current);
      }
    };
  }, [map, points]);

  return null;
}

export function MapView({ points }: MapViewProps) {
  // Format date for tooltip display
  const formatDate = (dateStr: string) => {
    try {
      return format(new Date(dateStr), 'MMM d, yyyy HH:mm');
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="map-view">
      <h2>Emission Heatmap</h2>
      <div className="map-container">
        <MapContainer
          center={DEFAULT_CENTER}
          zoom={DEFAULT_ZOOM}
          style={{ height: '60vh', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* Heatmap Layer */}
          <HeatmapLayer points={points} />

          {/* Circle Markers with Tooltips */}
          {points.map((point) => (
            <CircleMarker
              key={point.id}
              center={[point.latitude, point.longitude]}
              radius={8}
              pathOptions={{
                color: '#1a73e8',
                fillColor: '#1a73e8',
                fillOpacity: 0.6,
                weight: 2,
              }}
            >
              <Tooltip>
                <div className="marker-tooltip">
                  <p><strong>Date:</strong> {formatDate(point.recorded_at)}</p>
                  <p><strong>Vehicles:</strong> {point.total_vehicles}</p>
                  <p><strong>CO2:</strong> {point.total_co2.toFixed(2)} g</p>
                </div>
              </Tooltip>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>

      {/* Legend */}
      <div className="map-legend">
        <span className="legend-title">CO2 Intensity:</span>
        <div className="legend-gradient">
          <span className="legend-low">Low</span>
          <div className="gradient-bar"></div>
          <span className="legend-high">High</span>
        </div>
      </div>

      {/* Stats Summary */}
      {points.length > 0 && (
        <div className="map-stats">
          <p>Showing {points.length} analysis point{points.length !== 1 ? 's' : ''}</p>
          <p>
            Total CO2: {points.reduce((sum, p) => sum + p.total_co2, 0).toFixed(2)} g
          </p>
        </div>
      )}
    </div>
  );
}
