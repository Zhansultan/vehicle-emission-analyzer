"""Vehicle tracking module using DeepSORT."""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from deep_sort_realtime.deepsort_tracker import DeepSort

from app.config import settings
from app.models.schemas import BoundingBox, VehicleDetection, VehicleType

logger = logging.getLogger(__name__)


@dataclass
class TrackedVehicle:
    """Represents a tracked vehicle across multiple frames."""

    track_id: int
    vehicle_type: VehicleType
    frame_detections: list[int] = field(default_factory=list)
    type_votes: dict[VehicleType, int] = field(default_factory=lambda: defaultdict(int))
    last_bbox: Optional[BoundingBox] = None
    last_confidence: float = 0.0

    @property
    def frames_detected(self) -> int:
        """Number of frames this vehicle was detected in."""
        return len(self.frame_detections)

    @property
    def final_type(self) -> VehicleType:
        """Get the most voted vehicle type."""
        if not self.type_votes:
            return self.vehicle_type
        return max(self.type_votes.keys(), key=lambda k: self.type_votes[k])


class VehicleTracker:
    """
    Vehicle tracking service using DeepSORT.

    Maintains identity of vehicles across frames using deep appearance features.
    """

    def __init__(self):
        """Initialize the DeepSORT tracker."""
        self.tracker: Optional[DeepSort] = None
        self.tracked_vehicles: dict[int, TrackedVehicle] = {}
        self._frame_count = 0

        logger.info("Initializing VehicleTracker")

    def initialize(self) -> None:
        """Initialize or reset the DeepSORT tracker."""
        self.tracker = DeepSort(
            max_age=settings.max_age,
            n_init=settings.n_init,
            max_cosine_distance=settings.max_cosine_distance,
            nn_budget=100,
            embedder="mobilenet",
            half=True,
            embedder_gpu=True,
        )
        self.tracked_vehicles = {}
        self._frame_count = 0
        logger.info("DeepSORT tracker initialized")

    def update(
        self,
        frame: np.ndarray,
        bboxes: list[tuple[float, float, float, float]],
        confidences: list[float],
        vehicle_types: list[VehicleType],
    ) -> list[VehicleDetection]:
        """
        Update tracker with new detections.

        Args:
            frame: Current video frame (BGR format)
            bboxes: List of bounding boxes in [x, y, w, h] format
            confidences: List of detection confidences
            vehicle_types: List of vehicle type classifications

        Returns:
            List of VehicleDetection objects with assigned track IDs
        """
        if self.tracker is None:
            self.initialize()

        self._frame_count += 1
        detections_for_tracker: list[VehicleDetection] = []

        if not bboxes:
            # Update tracker with empty detections to maintain tracks
            self.tracker.update_tracks([], frame=frame)
            return detections_for_tracker

        # Format detections for DeepSORT: ([x, y, w, h], confidence, class)
        raw_detections = []
        for bbox, conf, vtype in zip(bboxes, confidences, vehicle_types):
            # DeepSORT expects [left, top, width, height]
            raw_detections.append((list(bbox), conf, vtype.value))

        # Update tracks
        tracks = self.tracker.update_tracks(raw_detections, frame=frame)

        # Process confirmed tracks
        for track in tracks:
            if not track.is_confirmed():
                continue

            track_id = track.track_id
            ltrb = track.to_ltrb()  # [left, top, right, bottom]

            # Get the detection info
            det_class = track.det_class if hasattr(track, "det_class") else None
            det_conf = track.det_conf if hasattr(track, "det_conf") else 0.5

            # Determine vehicle type from detection or use default
            if det_class and det_class in [vt.value for vt in VehicleType]:
                vehicle_type = VehicleType(det_class)
            else:
                vehicle_type = VehicleType.SEDAN

            bbox = BoundingBox(
                x1=float(ltrb[0]),
                y1=float(ltrb[1]),
                x2=float(ltrb[2]),
                y2=float(ltrb[3]),
            )

            # Update or create tracked vehicle
            if track_id not in self.tracked_vehicles:
                self.tracked_vehicles[track_id] = TrackedVehicle(
                    track_id=track_id,
                    vehicle_type=vehicle_type,
                )

            tracked = self.tracked_vehicles[track_id]
            tracked.frame_detections.append(self._frame_count)
            tracked.type_votes[vehicle_type] += 1
            tracked.last_bbox = bbox
            tracked.last_confidence = det_conf if det_conf else 0.5

            detection = VehicleDetection(
                track_id=track_id,
                vehicle_type=tracked.final_type,
                confidence=tracked.last_confidence,
                bbox=bbox,
                frame_number=self._frame_count,
            )
            detections_for_tracker.append(detection)

        logger.debug(
            f"Frame {self._frame_count}: {len(detections_for_tracker)} active tracks"
        )
        return detections_for_tracker

    def get_all_tracked_vehicles(self) -> dict[int, TrackedVehicle]:
        """
        Get all tracked vehicles.

        Returns:
            Dictionary mapping track IDs to TrackedVehicle objects
        """
        return self.tracked_vehicles.copy()

    def get_statistics(self) -> dict[str, int]:
        """
        Get detection statistics.

        Returns:
            Dictionary with vehicle type counts
        """
        stats: dict[str, int] = defaultdict(int)
        for vehicle in self.tracked_vehicles.values():
            stats[vehicle.final_type.value] += 1
        stats["total"] = len(self.tracked_vehicles)
        return dict(stats)

    def reset(self) -> None:
        """Reset the tracker state."""
        self.tracked_vehicles = {}
        self._frame_count = 0
        if self.tracker:
            self.initialize()
        logger.info("Tracker reset")
