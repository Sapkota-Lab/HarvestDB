# HarvestDB

HarvestDB (CropCapture) is a web application for agricultural field data collection and harvest-record querying. It consists of a FastAPI backend, a React/Vite frontend, and a PostgreSQL database.

## Features

- Create and list fields and harvest events.
- Create, query, update, and delete harvest records.
- Filter and paginate harvest-record queries.
- Import harvest records from CSV.
- Attach images to harvest records.
- Export harvest records as CSV.

Authentication is not implemented yet; the login endpoint is a placeholder.

## Running Locally

Prerequisites: Python 3.10+, Node.js 18+, and Docker with the Compose plugin.

### 1. Start PostgreSQL

From the repository root:

```bash
docker compose -f db_testing/docker-compose.yml up -d
```

This starts PostgreSQL 15 on `localhost:5432` with database `testing_db`, user `myuser`, and password `testing_password`. To initialize the test schema and sample data, run `bash TEST_DB_SETUP.sh` from the repository root. **The setup script drops and recreates the test tables**, so do not run it if you need to preserve data in those tables. See [TEST_DB_SETUP.md](TEST_DB_SETUP.md) for details.

### 2. Install and start the backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Create `backend/.env`. The settings below point both database connections at the local test database; set `DATABASE_URL` to your application database when using a separate database. `BIRD_API_KEY` and `ALERT_EMAIL_TO` are required settings, even when email alerts are disabled.

```env
DATABASE_URL=postgresql+psycopg://myuser:testing_password@localhost:5432/testing_db
TESTING_DATABASE_URL=postgresql+psycopg://myuser:testing_password@localhost:5432/testing_db
SECRET_KEY=change-me
BIRD_API_KEY=your-key
ALERT_EMAIL_TO=you@example.com
EMAIL_ALERTS=false
```

Start the server from the `backend/` directory:

```bash
uvicorn app.main:app --reload --port 8000
```

The API is available at <http://localhost:8000/api/v1>. The root URL redirects to the interactive API documentation at <http://localhost:8000/docs>. `GET /api/v1/health` checks that the API is running; `GET /api/v1/test-db` checks the test database connection.

Run backend tests from `backend/` with:

```bash
pytest
```

### 3. Install and start the frontend

In another terminal, from the repository root:

```bash
cd frontend
npm install
npm run dev
```

The frontend is served at <http://localhost:5173> and uses `http://localhost:8000/api/v1` by default. Set `VITE_API_BASE_URL` in `frontend/.env` to use a different API URL. The backend CORS configuration allows `http://localhost:5173` and `http://127.0.0.1:5173`.

Run frontend tests from `frontend/` with `npm test`.

## API Endpoints

All routes below are prefixed with `/api/v1`.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | API health check |
| `GET` | `/test-db` | Test-database connection check |
| `POST` | `/auth/login` | Placeholder; authentication is not implemented |
| `POST`, `GET` | `/fields/` | Create a field; list fields |
| `POST`, `GET` | `/harvests/` | Create a harvest event (requires `field_id`); list harvest events (optional `field_id`) |
| `POST` | `/harvest-records/?harvest_event_id={id}` | Create a harvest record |
| `GET` | `/harvest-records/` | List records with optional `harvest_event_id`, `field_id`, `plot_number`, `harvest_date_from`, and `harvest_date_to` filters; supports `page` and `page_size` |
| `PATCH`, `DELETE` | `/harvest-records/{record_id}` | Update or delete a harvest record |
| `POST` | `/harvest-records/upload?harvest_event_id={id}` | Import records from a UTF-8 CSV file and save them |
| `POST`, `GET` | `/harvest-records/{record_id}/images` | Upload images to a record; list its images |
| `GET`, `DELETE` | `/harvest-records/images/{image_id}` | Retrieve or delete an image |
| `GET` | `/exports/harvest-records.csv` | Export records from the application database as CSV |
| `GET` | `/exports/test-harvest-records.csv` | Export records from the test database as CSV; requires that database to be available |

Interactive API documentation at `/docs` includes request and response schemas.

## Project Structure

```text
HarvestDB/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/  # FastAPI route handlers
│   │   ├── core/              # Settings, security, and logging
│   │   ├── db/                # SQLAlchemy base and sessions
│   │   ├── models/            # Fields, harvest events, records, images, users
│   │   ├── schemas/           # API request and response models
│   │   └── services/          # Business logic and import/export
│   ├── scripts/               # Data import utilities
│   ├── tests/                 # Backend tests
│   └── requirements.txt
├── db_testing/                # PostgreSQL Compose file and SQL setup scripts
├── docs/                      # Feature and import documentation
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
│   ├── tests/
│   └── package.json
├── TEST_DB_SETUP.md
└── TEST_DB_SETUP.sh
```

## Data Model

- **Field** represents a physical research location and can have multiple harvest events.
- **Harvest event** belongs to a field and stores the harvest date, optional harvest number, and notes.
- **Harvest record** belongs to a harvest event and stores a plot number and flexible measurement data in PostgreSQL `JSONB`.
- **Record image** stores an image and its metadata for a harvest record.

The harvest event provides the field and date context for each record, while `dynamic_data` holds measurements that may vary by collection or year.
