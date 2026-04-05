"""Video processing pipeline orchestrating detection, tracking, and emission calculation."""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncGenerator, Optional

import cv2
import numpy as np

from app.config import settings
from app.models.schemas import (
    AnalysisResponse,
    EmissionsResult,
    StatisticsResult,
    VehicleResult,
    VehicleType,
)
from app.services.emission_calculator import EmissionCalculator
from app.services.vehicle_detector import VehicleDetector
from app.services.vehicle_tracker import VehicleTracker

logger = logging.getLogger(__name__)


@dataclass
class VideoMetadata:
    """Metadata extracted from video file."""

    path: Path
    width: int
    height: int
    fps: float
    total_frames: int
    duration_seconds: float


@dataclass
class ProcessingProgress:
    """Progress information during video processing."""

    current_frame: int
    total_frames: int
    percentage: float
    vehicles_detected: int


class VideoProcessor:
    """
    Main video processing pipeline.

    Orchestrates the complete flow:
    1. Video loading and frame extraction
    2. Vehicle detection using YOLOv8
    3. Vehicle tracking using DeepSORT
    4. Emission calculation
    5. Result aggregation
    """

    def __init__(self):
        """Initialize the video processor with all required components."""
        self.detector = VehicleDetector()
        self.tracker = VehicleTracker()
        self.emission_calculator = EmissionCalculator()
        self.frame_skip = settings.frame_skip

        logger.info("VideoProcessor initialized")

    def get_video_metadata(self, video_path: Path) -> VideoMetadata:
        """
        Extract metadata from video file.

        Args:
            video_path: Path to video file

        Returns:
            VideoMetadata object

        Raises:
            ValueError: If video cannot be opened
        """
        cap = cv2.VideoCapture(str(video_path))

        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {video_path}")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0

        cap.release()

        metadata = VideoMetadata(
            path=video_path,
            width=width,
            height=height,
            fps=fps,
            total_frames=total_frames,
            duration_seconds=duration,
        )

        logger.info(
            f"Video metadata: {width}x{height}, {fps:.2f} FPS, "
            f"{total_frames} frames, {duration:.2f}s"
        )

        return metadata

    def extract_frames(
        self, video_path: Path, frame_skip: Optional[int] = None
    ) -> AsyncGenerator[tuple[int, np.ndarray], None]:
        """
        Generator that yields frames from video.

        Args:
            video_path: Path to video file
            frame_skip: Process every nth frame (default from settings)

        Yields:
            Tuple of (frame_number, frame_data)
        """
        skip = frame_skip or self.frame_skip
        cap = cv2.VideoCapture(str(video_path))

        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        frame_number = 0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_number % skip == 0:
                    yield frame_number, frame

                frame_number += 1
        finally:
            cap.release()

    async def process_video(
        self,
        video_path: Path,
        progress_callback: Optional[callable] = None,
    ) -> AnalysisResponse:
        """
        Process a video file and return analysis results.

        Args:
            video_path: Path to the video file
            progress_callback: Optional callback for progress updates

        Returns:
            AnalysisResponse with all detection and emission data
        """
        logger.info(f"Starting video processing: {video_path}")

        # Get video metadata
        metadata = self.get_video_metadata(video_path)
        self.emission_calculator.set_fps(metadata.fps)

        # Initialize tracker
        self.tracker.initialize()

        # Load detector model
        self.detector.load_model()

        # Process frames
        frame_count = 0
        processed_count = 0

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_count % self.frame_skip == 0:
                    # Detect vehicles
                    bboxes, confidences, vehicle_types = (
                        self.detector.get_detections_for_tracking(frame)
                    )

                    # Update tracker
                    self.tracker.update(frame, bboxes, confidences, vehicle_types)
                    processed_count += 1

                    # Progress callback
                    if progress_callback and processed_count % 10 == 0:
                        progress = ProcessingProgress(
                            current_frame=frame_count,
                            total_frames=metadata.total_frames,
                            percentage=(frame_count / metadata.total_frames) * 100,
                            vehicles_detected=len(self.tracker.tracked_vehicles),
                        )
                        await progress_callback(progress)

                frame_count += 1

        finally:
            cap.release()

        logger.info(f"Processed {processed_count} frames, found {len(self.tracker.tracked_vehicles)} vehicles")

        # Calculate emissions
        emission_summary = self.emission_calculator.calculate_all(
            self.tracker.tracked_vehicles,
            frame_skip=self.frame_skip,
        )

        # Build response
        return self._build_response(emission_summary)

    def _build_response(self, emission_summary) -> AnalysisResponse:
        """
        Build the final API response from emission summary.

        Args:
            emission_summary: EmissionSummary from calculator

        Returns:
            AnalysisResponse object
        """
        # Build vehicle results
        vehicles: list[VehicleResult] = []
        for emission in emission_summary.vehicle_emissions:
            vehicles.append(
                VehicleResult(
                    id=emission.track_id,
                    type=emission.vehicle_type.value,
                    framesDetected=emission.frames_detected,
                    emissionCO2=emission.emission_co2_grams,
                )
            )

        # Build statistics
        stats_data = {
            "totalVehicles": len(vehicles),
            "sedan": 0,
            "suv": 0,
            "truck": 0,
            "bus": 0,
            "bike": 0,
        }

        for vehicle in vehicles:
            if vehicle.type in stats_data:
                stats_data[vehicle.type] += 1

        statistics = StatisticsResult(**stats_data)

        # Build emissions result
        emissions = EmissionsResult(totalCO2=emission_summary.total_co2_grams)

        return AnalysisResponse(
            vehicles=vehicles,
            statistics=statistics,
            emissions=emissions,
        )

    async def cleanup(self, video_path: Path) -> None:
        """
        Clean up temporary files after processing.

        Args:
            video_path: Path to the processed video
        """
        try:
            if video_path.exists():
                os.remove(video_path)
                logger.info(f"Cleaned up video file: {video_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up {video_path}: {e}")
