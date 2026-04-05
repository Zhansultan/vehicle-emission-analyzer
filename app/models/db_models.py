"""Tortoise ORM database models."""

from tortoise import fields
from tortoise.models import Model


class AnalysisResult(Model):
    """Model for storing video analysis results with geolocation."""

    id = fields.IntField(pk=True)
    latitude = fields.FloatField(description="Geographic latitude of recording location")
    longitude = fields.FloatField(description="Geographic longitude of recording location")
    recorded_at = fields.DatetimeField(description="Timestamp when video was recorded")
    created_at = fields.DatetimeField(auto_now_add=True, description="When analysis was performed")
    total_vehicles = fields.IntField(description="Total number of unique vehicles detected")
    total_co2 = fields.FloatField(description="Total CO2 emissions in grams")
    vehicles_json = fields.JSONField(description="Full vehicles array from analysis")
    statistics_json = fields.JSONField(description="Full statistics object from analysis")

    class Meta:
        table = "analysis_results"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"AnalysisResult(id={self.id}, lat={self.latitude}, lon={self.longitude}, vehicles={self.total_vehicles})"
