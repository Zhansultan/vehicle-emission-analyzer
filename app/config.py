"""Application configuration settings."""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application
    app_name: str = "Vehicle Emission Analyzer"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "postgres://postgres:postgres@db:5432/emissions"

    @property
    def db_url(self) -> str:
        """Get database URL compatible with Tortoise ORM.

        Render uses 'postgresql://' but Tortoise ORM expects 'postgres://'.
        """
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgres://", 1)
        return url

    # File Storage
    upload_dir: Path = Path("uploads")
    max_file_size_mb: int = 500
    allowed_extensions: set[str] = {"mp4", "avi", "mov", "mkv", "webm"}

    # Video Processing
    frame_skip: int = 5  # Process every nth frame for performance
    confidence_threshold: float = 0.5

    # YOLOv8 Model
    yolo_model: str = "yolov8n.pt"  # nano model for speed, use yolov8x.pt for accuracy

    # DeepSORT
    max_age: int = 30  # Max frames to keep track without detection
    n_init: int = 3  # Min detections before track is confirmed
    max_cosine_distance: float = 0.3

    # Emission Factors (g CO2 per km)
    emission_factors: dict[str, float] = {
        "sedan": 192.0,
        "suv": 251.0,
        "truck": 500.0,
        "bus": 822.0,
        "bike": 103.0,
    }

    # Assumed average speed for emission calculation (km/h)
    assumed_speed_kmh: float = 30.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Ensure upload directory exists
settings.upload_dir.mkdir(parents=True, exist_ok=True)
