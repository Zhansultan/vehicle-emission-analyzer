# Vehicle Emission Analyzer - Project Context Summary

**Date:** 2026-04-05
**Project Path:** `/home/zhabenov/university/kmp/diploma/vehicle-emission-analyzer`

---

## 1. Project Overview

A FastAPI backend application that:
- Detects vehicles in uploaded videos using **YOLOv8**
- Tracks vehicles across frames using **DeepSORT**
- Classifies vehicles (sedan, SUV, truck, bus, bike)
- Calculates CO2 emissions based on vehicle types
- **NEW:** Stores results with geolocation in PostgreSQL
- **NEW:** Provides a React frontend with map visualization

---

## 2. Changes Made in This Session

### 2.1 Backend Changes

#### Dependencies Added (`requirements.txt`)
```
tortoise-orm[asyncpg]==0.21.7
aerich==0.7.2
```

#### New Files Created

| File | Description |
|------|-------------|
| `app/models/db_models.py` | Tortoise ORM model `AnalysisResult` |
| `pyproject.toml` | Aerich migration config |
| `aerich.ini` | Aerich migration config |
| `migrations/.gitkeep` | Migrations directory |
| `.env` | Local environment variables |

#### Modified Files

| File | Changes |
|------|---------|
| `app/config.py` | Added `database_url` setting |
| `.env.example` | Added `DATABASE_URL` |
| `app/main.py` | Added Tortoise ORM initialization, updated CORS |
| `app/models/schemas.py` | Added `AnalysisResultResponse`, `MapPointResponse` |
| `app/models/__init__.py` | Export new schemas and db model |
| `app/api/routes.py` | Modified `/analyze-video`, added `/map-points` |
| `docker-compose.yml` | Added `db`, `frontend` services |

#### Database Model (`app/models/db_models.py`)
```python
class AnalysisResult(Model):
    id = fields.IntField(pk=True)
    latitude = fields.FloatField()
    longitude = fields.FloatField()
    recorded_at = fields.DatetimeField()
    created_at = fields.DatetimeField(auto_now_add=True)
    total_vehicles = fields.IntField()
    total_co2 = fields.FloatField()
    vehicles_json = fields.JSONField()
    statistics_json = fields.JSONField()
```

#### API Endpoints

| Endpoint | Method | Changes |
|----------|--------|---------|
| `/analyze-video` | POST | Now accepts `latitude`, `longitude`, `recorded_at` form fields; saves to DB; returns `id` |
| `/map-points` | GET | **NEW** - Returns all analysis results for map; supports `date_from`, `date_to` filters |

### 2.2 Frontend Created (`frontend/`)

Complete React + TypeScript + Vite application.

#### Structure
```
frontend/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── index.html
├── .env.example
├── .gitignore
├── public/
│   └── vite.svg
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── App.css
    ├── index.css
    ├── vite-env.d.ts
    ├── declarations.d.ts      # leaflet.heat types
    ├── api/
    │   └── client.ts          # axios API client
    ├── components/
    │   ├── index.ts
    │   ├── UploadForm.tsx     # Video upload + location picker
    │   ├── MapView.tsx        # Heatmap visualization
    │   └── DateFilter.tsx     # Date range filter
    └── types/
        └── index.ts           # TypeScript interfaces
```

#### Dependencies
- react, react-dom
- axios
- leaflet, react-leaflet, @types/leaflet
- leaflet.heat
- date-fns

#### Features
- Two-panel layout (35% left / 65% right)
- **UploadForm:** File input, embedded map for location picking, datetime input
- **MapView:** Leaflet map with heatmap layer (leaflet.heat) + circle markers with tooltips
- **DateFilter:** Date range filtering for map points
- Default center: Almaty, Kazakhstan (43.238949, 76.889709)

### 2.3 Docker Configuration (`docker-compose.yml`)

Three services:
1. **db** - PostgreSQL 15 (port 5432)
2. **app** - FastAPI backend (port 8000), depends on db
3. **frontend** - Node 20 running Vite dev server (port 5173)

---

## 3. Environment Configuration

### Local Development (`.env`)
```
DATABASE_URL=postgres://postgres:postgres@localhost:5432/emissions
```

### Docker (set in docker-compose.yml)
```
DATABASE_URL=postgres://postgres:postgres@db:5432/emissions
```

### Frontend (`.env.example`)
```
VITE_API_URL=http://localhost:8000
```

---

## 4. Issues Resolved

### Issue 1: Database Connection Error
**Error:** `socket.gaierror: [Errno -2] Name or service not known`
**Cause:** Default DATABASE_URL used `db` hostname (Docker) but running locally
**Solution:** Created `.env` file with `DATABASE_URL=postgres://postgres:postgres@localhost:5432/emissions`

### Issue 2: npm Installation Conflict (Arch Linux)
**Error:** `conflicting files` with libgcc, libstdc++
**Solution:** `sudo pacman -S npm --overwrite '*'`

### Issue 3: pkg_resources Module Not Found
**Error:** `ModuleNotFoundError: No module named 'pkg_resources'`
**Cause:** setuptools 82.0.1 removed pkg_resources (Python 3.14 compatibility)
**Solution:** Downgrade setuptools: `pip install 'setuptools<70.0'`

---

## 5. How to Run

### Option A: Local Development

1. Start PostgreSQL (via Docker):
   ```bash
   docker-compose up -d db
   ```

2. Activate venv and run backend:
   ```bash
   source venv/bin/activate
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. Run frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. Access:
   - Backend API: http://localhost:8000/docs
   - Frontend: http://localhost:5173

### Option B: Full Docker

```bash
docker-compose up --build
```

---

## 6. Current State

- **Backend:** Fully implemented with PostgreSQL integration
- **Frontend:** Fully implemented, ready for testing
- **Database:** Schema auto-generated by Tortoise ORM on startup
- **Last tested:** Video upload was working (after setuptools fix)

---

## 7. Next Steps (if any)

1. Test full video upload flow through frontend
2. Verify data appears on the heatmap after upload
3. Test date filtering functionality
4. Consider adding:
   - Analysis result detail view (click on map point)
   - Export functionality
   - User authentication (if needed)

---

## 8. Key File Locations

| Purpose | Path |
|---------|------|
| FastAPI entry | `app/main.py` |
| API routes | `app/api/routes.py` |
| DB models | `app/models/db_models.py` |
| Pydantic schemas | `app/models/schemas.py` |
| Config | `app/config.py` |
| Frontend app | `frontend/src/App.tsx` |
| API client | `frontend/src/api/client.ts` |
| Map component | `frontend/src/components/MapView.tsx` |
| Upload form | `frontend/src/components/UploadForm.tsx` |

---

## 9. Technology Stack

| Layer | Technology |
|-------|------------|
| Backend Framework | FastAPI |
| Database | PostgreSQL 15 |
| ORM | Tortoise ORM |
| Migrations | Aerich |
| Object Detection | YOLOv8 (ultralytics) |
| Object Tracking | DeepSORT |
| Frontend | React 18 + TypeScript |
| Build Tool | Vite |
| Maps | Leaflet + react-leaflet |
| Heatmap | leaflet.heat |
| HTTP Client | Axios |
| Containerization | Docker + docker-compose |

---

*This document was generated to preserve session context for future continuation.*
