# CropCapture

CropCapture is a modular CRUD platform for agricultural field data collection and in-office querying.

## Proposed Project Structure

```text
CropCapture/
	backend/
		app/
			api/v1/endpoints/ (fields, harvests, harvest records, auth, exports)
			core/
			db/
			models/ (field, harvest_event, harvest_record)
			schemas/ (field, harvest_event, harvest_record)
			services/
			main.py
		tests/
		requirements.txt
	frontend/
		src/
			components/
			pages/
			services/
			App.jsx
			main.jsx
		package.json
		.env.example
	infra/
		docker-compose.yml
	docs/
		architecture.md
		decisions.md
		open-questions.md
```

## What Each Folder Does

### Top-level

- `backend/`: FastAPI application code, API contracts, business logic, and tests.
- `frontend/`: React user interface for field entry and in-office querying.

### Backend (`backend/app`)

- `api/`: HTTP layer. Defines routes and request/response wiring.
- `api/v1/endpoints/`: Versioned endpoint modules (fields, harvests, harvest records, auth, exports).
- `core/`: Cross-cutting app concerns like config and security helpers.
- `db/`: SQLAlchemy base and database session lifecycle.
- `models/`: ORM table/entity definitions for persistence.
- `schemas/`: Pydantic request/response models for validation and serialization.
- `services/`: Business logic layer called by endpoints.
- `main.py`: FastAPI app factory and router registration.

### Other Backend Files

- `backend/tests/`: Backend test suite.
- `backend/requirements.txt`: Python dependency list.
- `backend/.env.example`: Example backend environment variables.

### Frontend (`frontend/src`)

- `components/`: Reusable UI pieces used across pages.
- `pages/`: Screen-level route/view composition.
- `services/`: API client functions and data fetching logic.
- `App.jsx`: App shell and high-level view orchestration.
- `main.jsx`: Frontend entry point and React bootstrap.

## Database Structure

The database is organized around the physical field first, followed by each data collection event and the individual records collected during that event.

### Field

Represents a physical research location, such as `Lexington`. A field can have many harvest events over time.

Typical fields:

- `id`
- `name`
- `location`
- `description`

### HarvestEvent

Represents one collection session for a field. The harvest date belongs here because it describes when that field was measured. This also allows multiple fields to have events on the same date.

Typical fields:

- `id`
- `field_id` (foreign key to `Field`)
- `harvest_date`
- `harvest_number`
- `notes`

### HarvestRecord

Represents one row of measurements collected during a harvest event. For the Lexington field, this contains values such as genotype, serial number, location, harvest, marketable weights/counts, and unmarketable weights/counts.

Typical fields:

- `id`
- `harvest_event_id` (foreign key to `HarvestEvent`)
- `serial_number`
- `genotype`
- `location`
- `harvest`
- `grade_1_marketable_weight`
- `grade_1_marketable_count`
- `unmarketable_weight`
- `unmarketable_count`
- `sample_weight_marketable`
- `sample_weight_unmarketable`

Measurement fields are optional so another field can record fewer values without requiring a separate database table immediately. If future fields introduce entirely new measurement types, a separate flexible measurements table can be added later.

## Current Skeleton Endpoints

- `GET /api/v1/health`
- `POST /api/v1/auth/login` (placeholder)
- `POST /api/v1/fields/` (stub)
- `GET /api/v1/fields/` (stub)
- `POST /api/v1/harvests/?field_id={field_id}` (stub)
- `GET /api/v1/harvests/?field_id={field_id}` (stub)
- `POST /api/v1/harvest-records/?harvest_event_id={harvest_event_id}` (stub)
- `GET /api/v1/harvest-records/?harvest_event_id={harvest_event_id}` (stub)
- `POST /api/v1/harvest-records/upload?harvest_event_id={harvest_event_id}` (CSV bulk import; parses and prints rows, does not persist yet — see issue #3)
- `GET /api/v1/exports/harvest-records.csv` (placeholder)

## Architecture Notes

- Keep route handlers thin. Move business logic into `backend/app/services`.
- Keep persistence concerns in models/session and avoid DB calls in frontend.
- Organize records by field first, then harvest event/date, then individual measurements.
- Keep field-specific measurements optional until each field's collection template is finalized.
- API versioning starts at `v1` for compatibility as requirements evolve.

## Next Implementation Steps

1. Finalize auth approach (OAuth vs local JWT user system).
2. Confirm ORM and migration workflow (SQLAlchemy + Alembic recommended).
3. Implement repository and service logic for real crop CRUD.
4. Add filtering/sorting/pagination for query workflows.
5. Implement CSV export with streaming response.
6. Add offline/low-connectivity strategy if required for field usage.
