import axios, { AxiosError } from 'axios';
import type { AnalysisResultResponse, MapPointResponse } from '../types';

// Base URL from env variable, fallback to localhost
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Accept': 'application/json',
  },
});

// Error handler helper
function handleApiError(error: unknown): never {
  if (error instanceof AxiosError) {
    const message = error.response?.data?.detail || error.message || 'An error occurred';
    throw new Error(message);
  }
  throw error;
}

/**
 * Upload a video for analysis with geolocation data
 * @param formData - FormData containing video, latitude, longitude, and recorded_at
 * @returns Analysis result with database ID
 */
export async function analyzeVideo(formData: FormData): Promise<AnalysisResultResponse> {
  try {
    const response = await apiClient.post<AnalysisResultResponse>('/analyze-video', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    handleApiError(error);
  }
}

/**
 * Get all analysis results for map visualization
 * @param dateFrom - Optional start date filter (ISO format)
 * @param dateTo - Optional end date filter (ISO format)
 * @returns Array of map points with location and emission data
 */
export async function getMapPoints(
  dateFrom?: string,
  dateTo?: string
): Promise<MapPointResponse[]> {
  try {
    const params = new URLSearchParams();
    if (dateFrom) params.append('date_from', dateFrom);
    if (dateTo) params.append('date_to', dateTo);

    const url = `/map-points${params.toString() ? `?${params.toString()}` : ''}`;
    const response = await apiClient.get<MapPointResponse[]>(url);

    // Ensure we always return an array
    const data = response.data;
    if (!Array.isArray(data)) {
      console.warn('API returned non-array for map-points:', data);
      return [];
    }
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export default apiClient;
