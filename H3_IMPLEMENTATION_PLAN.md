# AgroAI H3 Hexagonal GIS Implementation Plan

## Project Status
- **Backend**: FastAPI + SQLAlchemy + SQLite/PostgreSQL + Alembic
- **Database**: PostGIS schema in `database/schema/`, SQLAlchemy models in `backend/app/db/models.py`
- **Frontend**: Next.js 16 + React 19, custom CSS (no Tailwind), SVG-based FarmMap (no Leaflet)
- **Mobile**: Expo SDK 58 + React Native, custom schematic maps, `expo-location` for GPS
- **ML**: YOLOv11x (plant disease) and YOLO11s (IP102 pest) packages in `ml/`
- **Weather**: Open-Meteo client in `database/ingestion/openmeteo_client.py`

## Implementation Phases

### Phase 1: H3 Installation & Geospatial Utilities
- Pure Python H3-compatible utility module (`backend/app/geo/h3_utils.py`)
- H3 configuration settings (`backend/app/core/h3_config.py`)
- Coordinate-to-H3 conversion, H3-to-boundary, neighbors, parent/child, area

### Phase 2: Database Entities & Migrations
- New SQL tables: `h3_cells`, `farm_hexagon_assignments`, `geo_observations`, `disease_reports`, `pest_reports`, `hotspot_clusters`, `hotspot_history`, `regional_risk_scores`, `weather_cell_records`, `inspection_tasks`, `task_assignments`, `task_status_history`, `field_agent_profiles`, `user_task_availability`, `inspection_results`, `expert_verifications`, `recovery_monitoring_records`
- Alembic migration
- SQLAlchemy ORM models

### Phase 3: Hexagonal Grid APIs & Farm-to-Cell Assignment
- `GET /api/v1/hexagons` - List H3 cells with bounds
- `GET /api/v1/hexagons/{cell_id}` - Cell details
- `GET /api/v1/hexagons/{cell_id}/neighbours` - Neighboring cells
- `POST /api/v1/hexagons/assign-farm` - Assign farm to H3 cell
- `GET /api/v1/maps/regional-overview` - Regional overview

### Phase 4: OpenStreetMap & H3 Frontend Visualization
- Add Leaflet + react-leaflet to frontend
- H3 polygon overlay component
- Hexagon click intelligence panel
- Resolution switching, filters, search

### Phase 5: Pest & Disease Hotspot Intelligence Engine
- Hotspot calculation service
- Classification: LOW/MODERATE/HIGH/CRITICAL
- Unique farm deduplication
- Separate tracking for disease/pest/crop

### Phase 6: Weather-Based Hexagon Risk Integration
- Integrate existing Open-Meteo client
- Weather risk at hexagon level
- Weather-supported risk indicators

### Phase 7: Uber-Style Task Generation & Intelligent Assignment
- Task model and lifecycle (CREATED → AVAILABLE → ASSIGNED → ACCEPTED → IN_PROGRESS → SUBMITTED → UNDER_REVIEW → VERIFIED → COMPLETED)
- Assignment algorithm (distance, availability, role, expertise, workload)
- Auto-assignment for urgent, voluntary for routine

### Phase 8: Farmer, Field Agent & Expert Workflows
- Task acceptance/submission
- Photo/video capture
- Expert verification
- Recovery monitoring

### Phase 9: Mobile Integration (Expo/React Native)
- H3 hexagonal map component
- Nearby hotspots
- Task acceptance
- Field photo/video capture
- Offline sync

### Phase 10: Testing, Performance, Security, Documentation
- Unit tests for H3 functions, hotspot classification, task assignment
- Migration tests
- Security review
- Documentation

## Key Design Decisions
1. **Pure Python H3 fallback**: Works immediately; swappable with `pip install h3` when C compiler available
2. **Layer separation**: No merged "risk" layer (consistent with existing mapping module)
3. **Privacy**: Aggregated hexagon-level data for public maps; exact coordinates protected
4. **Backward compatible**: Existing modules unchanged; new modules extend existing patterns
5. **Demo-first**: All seed data marked `is_demo=true`
