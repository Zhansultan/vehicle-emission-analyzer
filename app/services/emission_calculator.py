"""Emission calculation module for vehicle CO2 emissions."""

import logging
from dataclasses import dataclass

from app.config import settings
from app.models.schemas import VehicleType
from app.services.vehicle_tracker import TrackedVehicle

logger = logging.getLogger(__name__)


@dataclass
class VehicleEmission:
    """Emission calculation result for a single vehicle."""

    track_id: int
    vehicle_type: VehicleType
    frames_detected: int
    time_in_view_seconds: float
    distance_km: float
    emission_co2_grams: float


@dataclass
class EmissionSummary:
    """Summary of all emission calculations."""

    vehicle_emissions: list[VehicleEmission]
    total_co2_grams: float
    emissions_by_type: dict[str, float]


class EmissionCalculator:
    """
    Calculator for vehicle CO2 emissions.

    Estimates emissions based on:
    - Vehicle type and its emission factor (g CO2/km)
    - Time the vehicle was visible (proxy for distance traveled)
    - Assumed average speed
    """

    def __init__(self, fps: float = 30.0):
        """
        Initialize the emission calculator.

        Args:
            fps: Video frames per second for time calculation
        """
        self.fps = fps
        self.emission_factors = settings.emission_factors
        self.assumed_speed_kmh = settings.assumed_speed_kmh

        logger.info(
            f"EmissionCalculator initialized with FPS={fps}, "
            f"assumed speed={self.assumed_speed_kmh} km/h"
        )

    def set_fps(self, fps: float) -> None:
        """
        Update the FPS used for calculations.

        Args:
            fps: New frames per second value
        """
        self.fps = max(fps, 1.0)  # Prevent division by zero
        logger.info(f"FPS updated to {self.fps}")

    def calculate_single_vehicle(
        self,
        vehicle: TrackedVehicle,
        frame_skip: int = 1,
    ) -> VehicleEmission:
        """
        Calculate emissions for a single tracked vehicle.

        Args:
            vehicle: TrackedVehicle object with detection data
            frame_skip: Number of frames skipped during processing

        Returns:
            VehicleEmission with calculated values
        """
        vehicle_type = vehicle.final_type
        frames_detected = vehicle.frames_detected

        # Calculate actual frames (accounting for frame skip)
        actual_frames = frames_detected * frame_skip

        # Time in view (seconds)
        time_in_view = actual_frames / self.fps

        # Distance traveled (km) = speed (km/h) * time (h)
        distance_km = self.assumed_speed_kmh * (time_in_view / 3600)

        # Get emission factor (g CO2/km)
        emission_factor = self.emission_factors.get(
            vehicle_type.value,
            self.emission_factors.get("sedan", 192.0),  # Default to sedan
        )

        # Calculate emissions (g CO2)
        emission_co2 = emission_factor * distance_km

        logger.debug(
            f"Vehicle {vehicle.track_id} ({vehicle_type.value}): "
            f"{frames_detected} frames, {time_in_view:.2f}s, "
            f"{distance_km:.4f}km, {emission_co2:.2f}g CO2"
        )

        return VehicleEmission(
            track_id=vehicle.track_id,
            vehicle_type=vehicle_type,
            frames_detected=frames_detected,
            time_in_view_seconds=time_in_view,
            distance_km=distance_km,
            emission_co2_grams=round(emission_co2, 2),
        )

    def calculate_all(
        self,
        tracked_vehicles: dict[int, TrackedVehicle],
        frame_skip: int = 1,
    ) -> EmissionSummary:
        """
        Calculate emissions for all tracked vehicles.

        Args:
            tracked_vehicles: Dictionary of tracked vehicles
            frame_skip: Number of frames skipped during processing

        Returns:
            EmissionSummary with all calculations
        """
        vehicle_emissions: list[VehicleEmission] = []
        emissions_by_type: dict[str, float] = {}
        total_co2 = 0.0

        for track_id, vehicle in tracked_vehicles.items():
            emission = self.calculate_single_vehicle(vehicle, frame_skip)
            vehicle_emissions.append(emission)
            total_co2 += emission.emission_co2_grams

            # Aggregate by type
            type_key = emission.vehicle_type.value
            emissions_by_type[type_key] = (
                emissions_by_type.get(type_key, 0.0) + emission.emission_co2_grams
            )

        # Round aggregates
        total_co2 = round(total_co2, 2)
        emissions_by_type = {k: round(v, 2) for k, v in emissions_by_type.items()}

        logger.info(
            f"Calculated emissions for {len(vehicle_emissions)} vehicles: "
            f"Total CO2 = {total_co2}g"
        )

        return EmissionSummary(
            vehicle_emissions=vehicle_emissions,
            total_co2_grams=total_co2,
            emissions_by_type=emissions_by_type,
        )

    def get_emission_factor(self, vehicle_type: VehicleType) -> float:
        """
        Get the emission factor for a vehicle type.

        Args:
            vehicle_type: Type of vehicle

        Returns:
            Emission factor in g CO2/km
        """
        return self.emission_factors.get(
            vehicle_type.value,
            self.emission_factors.get("sedan", 192.0),
        )
