"""API route definitions."""

import logging
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status

from app.config import settings
from app.models.db_models import AnalysisResult
from app.models.schemas import (
    AnalysisResultResponse,
    ErrorResponse,
    HealthResponse,
    MapPointResponse,
)
from app.services.video_processor import VideoProcessor
from app.utils.helpers import (
    generate_unique_filename,
    get_upload_path,
    save_upload_file,
    validate_video_file,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Singleton video processor instance
_video_processor: VideoProcessor | None = None


def get_video_processor() -> VideoProcessor:
    """Get or create the video processor singleton."""
    global _video_processor
    if _video_processor is None:
        _video_processor = VideoProcessor()
    return _video_processor


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check if the service is running and healthy.",
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns service status and version information.
    """
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
    )


@router.post(
    "/analyze-video",
    response_model=AnalysisResultResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        413: {"model": ErrorResponse, "description": "File too large"},
        415: {"model": ErrorResponse, "description": "Unsupported media type"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Analyze Video for Vehicle Emissions",
    description="""
    Upload a video file for vehicle detection and emission analysis.

    The system will:
    1. Extract frames from the video
    2. Detect vehicles using YOLOv8
    3. Track vehicles across frames using DeepSORT
    4. Classify vehicles (sedan, suv, truck, bus, bike)
    5. Calculate CO2 emissions based on vehicle types
    6. Save results with geolocation to database

    **Supported formats:** MP4, AVI, MOV, MKV, WebM

    **Maximum file size:** 500MB
    """,
)
async def analyze_video(
    video: UploadFile = File(..., description="Video file to analyze"),
    latitude: float = Form(..., description="Geographic latitude of recording location"),
    longitude: float = Form(..., description="Geographic longitude of recording location"),
    recorded_at: str = Form(..., description="ISO 8601 datetime when video was recorded"),
) -> AnalysisResultResponse:
    """
    Analyze a video for vehicle detection and emission calculation.

    Args:
        video: Uploaded video file (multipart/form-data)
        latitude: Geographic latitude of recording location
        longitude: Geographic longitude of recording location
        recorded_at: ISO 8601 datetime string (e.g., "2024-01-15T14:30:00")

    Returns:
        AnalysisResultResponse with id, detected vehicles, statistics, and emissions
    """
    logger.info(f"Received video for analysis: {video.filename}")
    logger.info(f"Location: ({latitude}, {longitude}), recorded_at: {recorded_at}")

    # Parse recorded_at datetime
    try:
        recorded_datetime = datetime.fromisoformat(recorded_at)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid recorded_at format. Use ISO 8601 format (e.g., '2024-01-15T14:30:00')",
        )

    # Validate the uploaded file
    validate_video_file(video)

    # Generate unique filename and save
    unique_filename = generate_unique_filename(video.filename)
    video_path = get_upload_path(unique_filename)

    processor = get_video_processor()

    try:
        # Save uploaded file
        await save_upload_file(video, video_path)
        logger.info(f"Video saved to: {video_path}")

        # Process the video
        result = await processor.process_video(video_path)

        logger.info(
            f"Analysis complete: {result.statistics.totalVehicles} vehicles, "
            f"{result.emissions.totalCO2}g CO2"
        )

        # Convert vehicles to JSON-serializable format
        vehicles_data = [
            {
                "id": v.id,
                "type": v.type,
                "framesDetected": v.framesDetected,
                "emissionCO2": v.emissionCO2,
            }
            for v in result.vehicles
        ]

        # Convert statistics to JSON-serializable format
        statistics_data = {
            "totalVehicles": result.statistics.totalVehicles,
            "sedan": result.statistics.sedan,
            "suv": result.statistics.suv,
            "truck": result.statistics.truck,
            "bus": result.statistics.bus,
            "bike": result.statistics.bike,
        }

        # Save to database
        db_result = await AnalysisResult.create(
            latitude=latitude,
            longitude=longitude,
            recorded_at=recorded_datetime,
            total_vehicles=result.statistics.totalVehicles,
            total_co2=result.emissions.totalCO2,
            vehicles_json=vehicles_data,
            statistics_json=statistics_data,
        )

        logger.info(f"Analysis result saved to database with id: {db_result.id}")

        return AnalysisResultResponse(
            id=db_result.id,
            vehicles=result.vehicles,
            statistics=result.statistics,
            emissions=result.emissions,
        )

    except ValueError as e:
        logger.error(f"Video processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Unexpected error during video analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during video analysis. Please try again.",
        )
    finally:
        # Clean up uploaded file
        await processor.cleanup(video_path)


@router.get(
    "/map-points",
    response_model=list[MapPointResponse],
    summary="Get Map Points",
    description="""
    Get all saved analysis results for map visualization.

    Optionally filter by date range using date_from and date_to query parameters.
    """,
)
async def get_map_points(
    date_from: Optional[str] = Query(
        None,
        description="Filter start date (ISO format, e.g., '2024-01-01')",
    ),
    date_to: Optional[str] = Query(
        None,
        description="Filter end date (ISO format, e.g., '2024-01-31')",
    ),
) -> list[MapPointResponse]:
    """
    Get all analysis results for map visualization.

    Args:
        date_from: Optional ISO date string for filter start
        date_to: Optional ISO date string for filter end

    Returns:
        List of MapPointResponse with location and emission data
    """
    query = AnalysisResult.all()

    # Apply date filters if provided
    if date_from:
        try:
            from_date = datetime.fromisoformat(date_from)
            query = query.filter(recorded_at__gte=from_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date_from format. Use ISO format (e.g., '2024-01-01')",
            )

    if date_to:
        try:
            # Add one day to include the entire end date
            to_date = datetime.fromisoformat(date_to)
            # Set to end of day
            to_date = to_date.replace(hour=23, minute=59, second=59)
            query = query.filter(recorded_at__lte=to_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date_to format. Use ISO format (e.g., '2024-01-31')",
            )

    results = await query.order_by("-recorded_at")

    return [
        MapPointResponse(
            id=r.id,
            latitude=r.latitude,
            longitude=r.longitude,
            recorded_at=r.recorded_at,
            total_vehicles=r.total_vehicles,
            total_co2=r.total_co2,
        )
        for r in results
    ]


@router.get(
    "/emission-factors",
    summary="Get Emission Factors",
    description="Get the emission factors used for CO2 calculations.",
)
async def get_emission_factors() -> dict[str, float]:
    """
    Get the emission factors for each vehicle type.

    Returns:
        Dictionary mapping vehicle types to emission factors (g CO2/km)
    """
    return settings.emission_factors
