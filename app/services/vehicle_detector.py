"""Vehicle detection module using YOLOv8."""

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
import torch
from ultralytics import YOLO

from app.config import settings
from app.models.schemas import VehicleType

logger = logging.getLogger(__name__)


@dataclass
class Detection:
    """Raw detection result from YOLO."""

    bbox: tuple[float, float, float, float]  # x1, y1, x2, y2
    confidence: float
    class_id: int
    class_name: str


class VehicleDetector:
    """
    Vehicle detection service using YOLOv8.

    Detects vehicles in frames and classifies them into categories.
    """

    # COCO class IDs for vehicles
    VEHICLE_CLASSES: dict[int, str] = {
        2: "car",      # car -> sedan/suv
        3: "bike",     # motorcycle
        5: "bus",      # bus
        7: "truck",    # truck
    }

    # Mapping from COCO classes to our vehicle types
    CLASS_TO_VEHICLE_TYPE: dict[str, VehicleType] = {
        "car": VehicleType.SEDAN,  # Default cars to sedan
        "bike": VehicleType.BIKE,
        "bus": VehicleType.BUS,
        "truck": VehicleType.TRUCK,
    }

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the vehicle detector.

        Args:
            model_path: Path to YOLO model weights. Defaults to config setting.
        """
        self.model_path = model_path or settings.yolo_model
        self.confidence_threshold = settings.confidence_threshold
        self.model: Optional[YOLO] = None
        self.device = self._get_device()
        logger.info(f"Initializing VehicleDetector with device: {self.device}")

    def _get_device(self) -> str:
        """Determine the best available device for inference."""
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    def load_model(self) -> None:
        """Load the YOLO model into memory."""
        if self.model is None:
            logger.info(f"Loading YOLO model: {self.model_path}")
            self.model = YOLO(self.model_path)
            self.model.to(self.device)
            logger.info("YOLO model loaded successfully")

    def detect(self, frame: np.ndarray) -> list[Detection]:
        """
        Detect vehicles in a single frame.

        Args:
            frame: BGR image as numpy array (OpenCV format)

        Returns:
            List of Detection objects for vehicles found
        """
        if self.model is None:
            self.load_model()

        # Run inference
        results = self.model(
            frame,
            conf=self.confidence_threshold,
            classes=list(self.VEHICLE_CLASSES.keys()),
            verbose=False,
        )

        detections: list[Detection] = []

        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue

            for i in range(len(boxes)):
                box = boxes[i]
                class_id = int(box.cls[0].item())
                confidence = float(box.conf[0].item())

                # Get bounding box coordinates
                xyxy = box.xyxy[0].cpu().numpy()
                bbox = (float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3]))

                class_name = self.VEHICLE_CLASSES.get(class_id, "unknown")

                detections.append(
                    Detection(
                        bbox=bbox,
                        confidence=confidence,
                        class_id=class_id,
                        class_name=class_name,
                    )
                )

        logger.debug(f"Detected {len(detections)} vehicles in frame")
        return detections

    def classify_vehicle(self, detection: Detection, bbox_width: float, bbox_height: float) -> VehicleType:
        """
        Classify a detected vehicle into specific type.

        Uses detection class and bounding box dimensions for classification.

        Args:
            detection: Raw detection from YOLO
            bbox_width: Width of bounding box
            bbox_height: Height of bounding box

        Returns:
            Classified vehicle type
        """
        base_type = self.CLASS_TO_VEHICLE_TYPE.get(
            detection.class_name, VehicleType.UNKNOWN
        )

        # Refine car classification based on aspect ratio
        if base_type == VehicleType.SEDAN:
            aspect_ratio = bbox_width / max(bbox_height, 1)
            # SUVs tend to be taller relative to width
            if aspect_ratio < 1.3 and bbox_height > 100:
                return VehicleType.SUV

        return base_type

    def get_detections_for_tracking(
        self, frame: np.ndarray
    ) -> tuple[list[tuple[float, float, float, float]], list[float], list[VehicleType]]:
        """
        Get detections formatted for DeepSORT tracker.

        Args:
            frame: BGR image as numpy array

        Returns:
            Tuple of (bboxes, confidences, vehicle_types)
        """
        detections = self.detect(frame)

        bboxes: list[tuple[float, float, float, float]] = []
        confidences: list[float] = []
        vehicle_types: list[VehicleType] = []

        for det in detections:
            x1, y1, x2, y2 = det.bbox
            width = x2 - x1
            height = y2 - y1

            # Convert to [x, y, w, h] format for DeepSORT
            bbox_ltwh = (x1, y1, width, height)
            bboxes.append(bbox_ltwh)
            confidences.append(det.confidence)

            vehicle_type = self.classify_vehicle(det, width, height)
            vehicle_types.append(vehicle_type)

        return bboxes, confidences, vehicle_types
