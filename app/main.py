"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise

from app.api.routes import router
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Upload directory: {settings.upload_dir.absolute()}")
    logger.info(f"YOLO model: {settings.yolo_model}")
    logger.info(f"Frame skip: {settings.frame_skip}")

    # Ensure upload directory exists
    settings.upload_dir.mkdir(parents=True, exist_ok=True)

    yield

    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    ## Vehicle Emission Analyzer API

    A production-ready API for detecting vehicles in video footage
    and estimating their CO2 emissions.

    ### Features
    - **Vehicle Detection**: Uses YOLOv8 for accurate vehicle detection
    - **Multi-Object Tracking**: DeepSORT maintains vehicle identity across frames
    - **Vehicle Classification**: Categorizes vehicles (sedan, SUV, truck, bus, bike)
    - **Emission Calculation**: Estimates CO2 emissions based on vehicle types

    ### Emission Factors (g CO2/km)
    | Vehicle Type | Emission Factor |
    |--------------|-----------------|
    | Sedan        | 192             |
    | SUV          | 251             |
    | Truck        | 500             |
    | Bus          | 822             |
    | Bike         | 103             |
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
# Allow frontend dev server and configure for production as needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",
        "http://localhost:3000",  # Alternative dev port
        "*",  # Allow all in development - restrict in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, tags=["Analysis"])

# Configure Tortoise ORM
TORTOISE_ORM = {
    "connections": {"default": settings.database_url},
    "apps": {
        "models": {
            "models": ["app.models.db_models", "aerich.models"],
            "default_connection": "default",
        },
    },
}

register_tortoise(
    app,
    config=TORTOISE_ORM,
    generate_schemas=True,
    add_exception_handlers=True,
)


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint redirect to docs."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
