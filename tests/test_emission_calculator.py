"""Tests for emission calculator module."""

import pytest
from collections import defaultdict

from app.models.schemas import VehicleType
from app.services.emission_calculator import EmissionCalculator
from app.services.vehicle_tracker import TrackedVehicle


class TestEmissionCalculator:
    """Test cases for EmissionCalculator."""

    @pytest.fixture
    def calculator(self):
        """Create an EmissionCalculator instance."""
        return EmissionCalculator(fps=30.0)

    @pytest.fixture
    def sample_vehicle(self):
        """Create a sample tracked vehicle."""
        vehicle = TrackedVehicle(
            track_id=1,
            vehicle_type=VehicleType.SEDAN,
        )
        # Simulate 90 frames of detection (3 seconds at 30fps)
        vehicle.frame_detections = list(range(90))
        vehicle.type_votes[VehicleType.SEDAN] = 90
        return vehicle

    def test_emission_factor_sedan(self, calculator):
        """Test emission factor retrieval for sedan."""
        factor = calculator.get_emission_factor(VehicleType.SEDAN)
        assert factor == 192.0

    def test_emission_factor_truck(self, calculator):
        """Test emission factor retrieval for truck."""
        factor = calculator.get_emission_factor(VehicleType.TRUCK)
        assert factor == 500.0

    def test_emission_factor_bus(self, calculator):
        """Test emission factor retrieval for bus."""
        factor = calculator.get_emission_factor(VehicleType.BUS)
        assert factor == 822.0

    def test_calculate_single_vehicle(self, calculator, sample_vehicle):
        """Test emission calculation for a single vehicle."""
        emission = calculator.calculate_single_vehicle(sample_vehicle, frame_skip=1)

        assert emission.track_id == 1
        assert emission.vehicle_type == VehicleType.SEDAN
        assert emission.frames_detected == 90
        assert emission.time_in_view_seconds == 3.0  # 90 frames / 30 fps
        assert emission.distance_km > 0
        assert emission.emission_co2_grams > 0

    def test_calculate_all_vehicles(self, calculator):
        """Test emission calculation for multiple vehicles."""
        vehicles = {}

        # Create sedan
        sedan = TrackedVehicle(track_id=1, vehicle_type=VehicleType.SEDAN)
        sedan.frame_detections = list(range(60))
        sedan.type_votes[VehicleType.SEDAN] = 60
        vehicles[1] = sedan

        # Create truck
        truck = TrackedVehicle(track_id=2, vehicle_type=VehicleType.TRUCK)
        truck.frame_detections = list(range(30))
        truck.type_votes[VehicleType.TRUCK] = 30
        vehicles[2] = truck

        summary = calculator.calculate_all(vehicles, frame_skip=1)

        assert len(summary.vehicle_emissions) == 2
        assert summary.total_co2_grams > 0
        assert "sedan" in summary.emissions_by_type
        assert "truck" in summary.emissions_by_type

    def test_fps_update(self, calculator):
        """Test FPS update functionality."""
        calculator.set_fps(60.0)
        assert calculator.fps == 60.0

    def test_fps_minimum(self, calculator):
        """Test that FPS cannot be set below 1."""
        calculator.set_fps(0.0)
        assert calculator.fps == 1.0
