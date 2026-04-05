// API Response Types matching backend Pydantic schemas

export interface VehicleResult {
  id: number;
  type: string;
  framesDetected: number;
  emissionCO2: number;
}

export interface StatisticsResult {
  totalVehicles: number;
  sedan: number;
  suv: number;
  truck: number;
  bus: number;
  bike: number;
}

export interface EmissionsResult {
  totalCO2: number;
}

export interface AnalysisResultResponse {
  id: number;
  vehicles: VehicleResult[];
  statistics: StatisticsResult;
  emissions: EmissionsResult;
}

export interface MapPointResponse {
  id: number;
  latitude: number;
  longitude: number;
  recorded_at: string;
  total_vehicles: number;
  total_co2: number;
}

// Form data types
export interface UploadFormData {
  video: File;
  latitude: number;
  longitude: number;
  recorded_at: string;
}

// Component props types
export interface DateFilterProps {
  onFilter: (dateFrom?: string, dateTo?: string) => void;
}

export interface MapViewProps {
  points: MapPointResponse[];
  onRefresh: () => void;
}

export interface UploadFormProps {
  onSuccess: (result: AnalysisResultResponse) => void;
}
