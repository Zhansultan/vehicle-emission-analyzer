import { useState, useEffect, useCallback } from 'react';
import { UploadForm } from './components/UploadForm';
import { MapView } from './components/MapView';
import { DateFilter } from './components/DateFilter';
import { getMapPoints } from './api/client';
import type { MapPointResponse, AnalysisResultResponse } from './types';
import './App.css';

function App() {
  const [mapPoints, setMapPoints] = useState<MapPointResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch map points with optional date filters
  const fetchMapPoints = useCallback(async (dateFrom?: string, dateTo?: string) => {
    setLoading(true);
    setError(null);
    try {
      const points = await getMapPoints(dateFrom, dateTo);
      // Ensure we always set an array
      setMapPoints(Array.isArray(points) ? points : []);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load map points';
      setError(message);
      setMapPoints([]); // Reset to empty array on error
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchMapPoints();
  }, [fetchMapPoints]);

  // Handle successful upload - refresh map data
  const handleUploadSuccess = (_result: AnalysisResultResponse) => {
    // Refresh map points to include the new analysis
    fetchMapPoints();
  };

  // Handle date filter changes
  const handleDateFilter = (dateFrom?: string, dateTo?: string) => {
    fetchMapPoints(dateFrom, dateTo);
  };

  // Refresh map
  const handleRefresh = () => {
    fetchMapPoints();
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Vehicle Emission Analyzer</h1>
        <p>Analyze vehicle emissions from traffic videos</p>
      </header>

      <main className="app-content">
        {/* Left Panel - Upload Form and Filters */}
        <aside className="left-panel">
          <UploadForm onSuccess={handleUploadSuccess} />
          <hr className="panel-divider" />
          <DateFilter onFilter={handleDateFilter} />
        </aside>

        {/* Right Panel - Map View */}
        <section className="right-panel">
          {error && (
            <div className="error-banner">
              <p>{error}</p>
              <button onClick={handleRefresh}>Retry</button>
            </div>
          )}

          {loading && mapPoints.length === 0 ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>Loading map data...</p>
            </div>
          ) : (
            <MapView points={mapPoints} onRefresh={handleRefresh} />
          )}
        </section>
      </main>

      <footer className="app-footer">
        <p>Vehicle Emission Analyzer - Powered by YOLOv8 & DeepSORT</p>
      </footer>
    </div>
  );
}

export default App;
