# Vehicle Emission Analyzer

A production-ready backend service for detecting vehicles in video footage and estimating their CO2 emissions using computer vision and deep learning.

## Features

- **Vehicle Detection**: YOLOv8-based object detection for accurate vehicle identification
- **Multi-Object Tracking**: DeepSORT algorithm maintains vehicle identity across frames
- **Vehicle Classification**: Categorizes vehicles into sedan, SUV, truck, bus, and bike
- **Emission Calculation**: Estimates CO2 emissions based on vehicle types and time in view
- **REST API**: FastAPI-based async API with OpenAPI documentation
- **Production Ready**: Docker support, proper error handling, and logging

## Tech Stack

- Python 3.10+
- FastAPI + Uvicorn
- OpenCV
- Ultralytics YOLOv8
- DeepSORT (deep-sort-realtime)
- PyTorch
- Pydantic

## Project Structure

```
vehicle-emission-analyzer/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration settings
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py           # API endpoints
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydantic models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── video_processor.py  # Main processing pipeline
│   │   ├── vehicle_detector.py # YOLOv8 detection module
│   │   ├── vehicle_tracker.py  # DeepSORT tracking module
│   │   └── emission_calculator.py  # Emission calculations
│   └── utils/
│       ├── __init__.py
│       └── helpers.py          # Utility functions
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api.py
│   └── test_emission_calculator.py
├── uploads/                    # Uploaded video storage
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## Installation

### Local Development

1. **Clone the repository**
   ```bash
   cd vehicle-emission-analyzer
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   .\venv\Scripts\activate   # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env as needed
   ```

5. **Run the server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Docker

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Or build manually**
   ```bash
   docker build -t vehicle-emission-analyzer .
   docker run -p 8000:8000 -v $(pwd)/uploads:/app/uploads vehicle-emission-analyzer
   ```

## API Documentation

Once running, access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Health Check

```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### Analyze Video

```
POST /analyze-video
Content-Type: multipart/form-data
```

**Request:**
- `video`: Video file (MP4, AVI, MOV, MKV, WebM)

**Response:**
```json
{
  "vehicles": [
    {
      "id": 1,
      "type": "sedan",
      "framesDetected": 45,
      "emissionCO2": 4.8
    },
    {
      "id": 2,
      "type": "truck",
      "framesDetected": 30,
      "emissionCO2": 8.33
    }
  ],
  "statistics": {
    "totalVehicles": 2,
    "sedan": 1,
    "suv": 0,
    "truck": 1,
    "bus": 0,
    "bike": 0
  },
  "emissions": {
    "totalCO2": 13.13
  }
}
```

### Get Emission Factors

```
GET /emission-factors
```

**Response:**
```json
{
  "sedan": 192.0,
  "suv": 251.0,
  "truck": 500.0,
  "bus": 822.0,
  "bike": 103.0
}
```

## Example Usage

### cURL

```bash
# Health check
curl http://localhost:8000/health

# Analyze video
curl -X POST "http://localhost:8000/analyze-video" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "video=@/path/to/your/video.mp4"

# Get emission factors
curl http://localhost:8000/emission-factors
```

### Python

```python
import requests

# Analyze video
url = "http://localhost:8000/analyze-video"
files = {"video": open("traffic_video.mp4", "rb")}
response = requests.post(url, files=files)
result = response.json()

print(f"Total vehicles: {result['statistics']['totalVehicles']}")
print(f"Total CO2: {result['emissions']['totalCO2']}g")
```

## Emission Factors

The following emission factors are used (grams CO2 per kilometer):

| Vehicle Type | Emission Factor (g/km) |
|--------------|------------------------|
| Sedan        | 192                    |
| SUV          | 251                    |
| Truck        | 500                    |
| Bus          | 822                    |
| Bike         | 103                    |

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug mode |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `UPLOAD_DIR` | `uploads` | Directory for uploaded videos |
| `MAX_FILE_SIZE_MB` | `500` | Maximum file size in MB |
| `FRAME_SKIP` | `5` | Process every Nth frame |
| `CONFIDENCE_THRESHOLD` | `0.5` | Detection confidence threshold |
| `YOLO_MODEL` | `yolov8n.pt` | YOLO model to use |
| `ASSUMED_SPEED_KMH` | `30.0` | Assumed vehicle speed for emission calc |

## Testing

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=html
```

## Architecture

### Processing Pipeline

1. **Video Upload**: Receive and validate video file
2. **Frame Extraction**: Extract frames using OpenCV (with configurable frame skip)
3. **Vehicle Detection**: Detect vehicles using YOLOv8
4. **Vehicle Tracking**: Maintain vehicle identity across frames using DeepSORT
5. **Vehicle Classification**: Classify detected vehicles into categories
6. **Emission Calculation**: Calculate CO2 emissions based on vehicle type and time in view
7. **Result Aggregation**: Aggregate results and return JSON response

### Key Components

- **VehicleDetector**: Wraps YOLOv8 for vehicle detection
- **VehicleTracker**: Wraps DeepSORT for multi-object tracking
- **EmissionCalculator**: Calculates CO2 emissions based on vehicle types
- **VideoProcessor**: Orchestrates the complete pipeline

## Performance Considerations

- Use `FRAME_SKIP` to balance accuracy vs processing speed
- Choose appropriate YOLO model size (`yolov8n.pt` for speed, `yolov8x.pt` for accuracy)
- GPU acceleration is automatically used when available
- Consider using GPU-enabled Docker image for production

## License

MIT License
