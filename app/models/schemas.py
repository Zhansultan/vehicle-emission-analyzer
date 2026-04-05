"""Pydantic models for request/response validation."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class VehicleType(str, Enum):
    """Supported vehicle types for classification."""

    SEDAN = "sedan"
    SUV = "suv"
    TRUCK = "truck"
    BUS = "bus"
    BIKE = "bike"
    UNKNOWN = "unknown"


class BoundingBox(BaseModel):
    """Bounding box coordinates for detected object."""

    x1: float = Field(..., description="Left coordinate")
    y1: float = Field(..., description="Top coordinate")
    x2: float = Field(..., description="Right coordinate")
    y2: float = Field(..., description="Bottom coordinate")


class VehicleDetection(BaseModel):
    """Single frame vehicle detection result."""

    track_id: int = Field(..., description="Unique tracking ID")
    vehicle_type: VehicleType = Field(..., description="Classified vehicle type")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    bbox: BoundingBox = Field(..., description="Bounding box coordinates")
    frame_number: int = Field(..., description="Frame number where detected")


class VehicleResult(BaseModel):
    """Aggregated result for a single tracked vehicle."""

    id: int = Field(..., alias="id", description="Unique vehicle tracking ID")
    type: str = Field(..., description="Vehicle type classification")
    framesDetected: int = Field(..., description="Number of frames vehicle was detected")
    emissionCO2: float = Field(..., description="Estimated CO2 emission in grams")

    class Config:
        populate_by_name = True


class StatisticsResult(BaseModel):
    """Statistics summary of detected vehicles."""

    totalVehicles: int = Field(..., description="Total number of unique vehicles")
    sedan: int = Field(0, description="Number of sedans detected")
    suv: int = Field(0, description="Number of SUVs detected")
    truck: int = Field(0, description="Number of trucks detected")
    bus: int = Field(0, description="Number of buses detected")
    bike: int = Field(0, description="Number of bikes detected")


class EmissionsResult(BaseModel):
    """Total emissions calculation result."""

    totalCO2: float = Field(..., description="Total CO2 emissions in grams")


class AnalysisResponse(BaseModel):
    """Complete video analysis response."""

    vehicles: list[VehicleResult] = Field(
        ..., description="List of detected vehicles with details"
    )
    statistics: StatisticsResult = Field(
        ..., description="Summary statistics of detections"
    )
    emissions: EmissionsResult = Field(..., description="Total emissions calculation")

    class Config:
        json_schema_extra = {
            "example": {
                "vehicles": [
                    {
                        "id": 1,
                        "type": "sedan",
                        "framesDetected": 45,
                        "emissionCO2": 192.5,
                    },
                    {
                        "id": 2,
                        "type": "truck",
                        "framesDetected": 30,
                        "emissionCO2": 500.0,
                    },
                ],
                "statistics": {
                    "totalVehicles": 2,
                    "sedan": 1,
                    "suv": 0,
                    "truck": 1,
                    "bus": 0,
                    "bike": 0,
                },
                "emissions": {"totalCO2": 692.5},
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service health status")
    version: str = Field(..., description="Application version")


class ErrorResponse(BaseModel):
    """Error response model."""

    detail: str = Field(..., description="Error description")
    code: Optional[str] = Field(None, description="Error code")


class AnalysisResultResponse(BaseModel):
    """Complete video analysis response with database ID."""

    id: int = Field(..., description="Database ID of the analysis result")
    vehicles: list[VehicleResult] = Field(
        ..., description="List of detected vehicles with details"
    )
    statistics: StatisticsResult = Field(
        ..., description="Summary statistics of detections"
    )
    emissions: EmissionsResult = Field(..., description="Total emissions calculation")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 42,
                "vehicles": [
                    {
                        "id": 1,
                        "type": "sedan",
                        "framesDetected": 45,
                        "emissionCO2": 192.5,
                    },
                    {
                        "id": 2,
                        "type": "truck",
                        "framesDetected": 30,
                        "emissionCO2": 500.0,
                    },
                ],
                "statistics": {
                    "totalVehicles": 2,
                    "sedan": 1,
                    "suv": 0,
                    "truck": 1,
                    "bus": 0,
                    "bike": 0,
                },
                "emissions": {"totalCO2": 692.5},
            }
        }


class MapPointResponse(BaseModel):
    """Response model for map visualization points."""

    id: int = Field(..., description="Database ID of the analysis result")
    latitude: float = Field(..., description="Geographic latitude")
    longitude: float = Field(..., description="Geographic longitude")
    recorded_at: datetime = Field(..., description="When the video was recorded")
    total_vehicles: int = Field(..., description="Total vehicles detected")
    total_co2: float = Field(..., description="Total CO2 emissions in grams")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "latitude": 43.238949,
                "longitude": 76.889709,
                "recorded_at": "2024-01-15T14:30:00",
                "total_vehicles": 12,
                "total_co2": 87.4,
            }
        }
