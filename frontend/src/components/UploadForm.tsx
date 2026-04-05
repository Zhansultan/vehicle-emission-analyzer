import { useState, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { analyzeVideo } from '../api/client';
import type { AnalysisResultResponse, UploadFormProps } from '../types';

// Fix for default marker icon in react-leaflet
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

delete (L.Icon.Default.prototype as unknown as { _getIconUrl?: unknown })._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
});

// Default center: Almaty, Kazakhstan
const DEFAULT_CENTER: [number, number] = [43.238949, 76.889709];
const DEFAULT_ZOOM = 12;

interface LocationPickerProps {
  onLocationSelect: (lat: number, lng: number) => void;
  selectedLocation: [number, number] | null;
}

function LocationPicker({ onLocationSelect, selectedLocation }: LocationPickerProps) {
  useMapEvents({
    click: (e) => {
      onLocationSelect(e.latlng.lat, e.latlng.lng);
    },
  });

  return selectedLocation ? (
    <Marker position={selectedLocation} />
  ) : null;
}

export function UploadForm({ onSuccess }: UploadFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [location, setLocation] = useState<[number, number] | null>(null);
  const [recordedAt, setRecordedAt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResultResponse | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
    }
  };

  const handleLocationSelect = useCallback((lat: number, lng: number) => {
    setLocation([lat, lng]);
    setError(null);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);

    // Validate inputs
    if (!file) {
      setError('Please select a video file');
      return;
    }
    if (!location) {
      setError('Please click on the map to select a location');
      return;
    }
    if (!recordedAt) {
      setError('Please select the recording date and time');
      return;
    }

    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('video', file);
      formData.append('latitude', location[0].toString());
      formData.append('longitude', location[1].toString());
      formData.append('recorded_at', recordedAt);

      const analysisResult = await analyzeVideo(formData);
      setResult(analysisResult);
      onSuccess(analysisResult);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An error occurred during upload';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const acceptedFormats = '.mp4,.avi,.mov,.mkv,.webm';

  return (
    <div className="upload-form">
      <h2>Upload Video for Analysis</h2>

      <form onSubmit={handleSubmit}>
        {/* File Input */}
        <div className="form-group">
          <label htmlFor="video-file">Video File:</label>
          <input
            type="file"
            id="video-file"
            accept={acceptedFormats}
            onChange={handleFileChange}
            disabled={loading}
          />
          {file && <p className="file-name">Selected: {file.name}</p>}
        </div>

        {/* Location Picker Map */}
        <div className="form-group">
          <label>Recording Location (click on map):</label>
          <div className="location-picker-map">
            <MapContainer
              center={DEFAULT_CENTER}
              zoom={DEFAULT_ZOOM}
              style={{ height: '300px', width: '100%' }}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <LocationPicker
                onLocationSelect={handleLocationSelect}
                selectedLocation={location}
              />
            </MapContainer>
          </div>
          {location && (
            <p className="location-info">
              Selected: {location[0].toFixed(6)}, {location[1].toFixed(6)}
            </p>
          )}
        </div>

        {/* DateTime Input */}
        <div className="form-group">
          <label htmlFor="recorded-at">Recording Date & Time:</label>
          <input
            type="datetime-local"
            id="recorded-at"
            value={recordedAt}
            onChange={(e) => setRecordedAt(e.target.value)}
            disabled={loading}
          />
        </div>

        {/* Error Message */}
        {error && <div className="error-message">{error}</div>}

        {/* Submit Button */}
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? 'Analyzing...' : 'Analyze Video'}
        </button>
      </form>

      {/* Loading Indicator */}
      {loading && (
        <div className="loading-indicator">
          <div className="spinner"></div>
          <p>Processing video... This may take a while.</p>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="analysis-result">
          <h3>Analysis Complete</h3>
          <div className="result-summary">
            <div className="stat-item">
              <span className="stat-label">Total Vehicles:</span>
              <span className="stat-value">{result.statistics.totalVehicles}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Total CO2:</span>
              <span className="stat-value">{result.emissions.totalCO2.toFixed(2)} g</span>
            </div>
          </div>

          <h4>Vehicle Types Detected:</h4>
          <ul className="vehicle-list">
            {result.statistics.sedan > 0 && (
              <li>Sedan: {result.statistics.sedan}</li>
            )}
            {result.statistics.suv > 0 && (
              <li>SUV: {result.statistics.suv}</li>
            )}
            {result.statistics.truck > 0 && (
              <li>Truck: {result.statistics.truck}</li>
            )}
            {result.statistics.bus > 0 && (
              <li>Bus: {result.statistics.bus}</li>
            )}
            {result.statistics.bike > 0 && (
              <li>Bike: {result.statistics.bike}</li>
            )}
          </ul>

          <h4>Individual Vehicles:</h4>
          <ul className="vehicle-details">
            {result.vehicles.map((vehicle) => (
              <li key={vehicle.id}>
                #{vehicle.id} - {vehicle.type} ({vehicle.framesDetected} frames, {vehicle.emissionCO2.toFixed(2)}g CO2)
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
