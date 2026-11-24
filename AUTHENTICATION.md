# HarvestDB (CropCapture) Authentication

## Overview

HarvestDB uses email and password authentication to restrict access to authorized research lab members. Accounts are manually provisioned by trusted developers or administrators. There is no public registration endpoint or page.

Lab members can use their university or personal email address, but must create a separate HarvestDB password. Google, Microsoft, and Duo authentication are not required by the current implementation.

## How authentication works

1. A user enters their email address and password on the React login page.
2. The frontend sends the credentials to `POST /api/v1/auth/login`.
3. FastAPI looks up the email in PostgreSQL, verifies the Argon2 password hash, and checks whether the account is active.
4. If the credentials are valid, the backend returns a signed JSON Web Token (JWT).
5. The frontend stores the token in browser `sessionStorage` and attaches it to protected API requests as `Authorization: Bearer <token>`.
6. The backend verifies the token signature and expiration and checks the user's active status in the database on protected requests.
7. Logging out removes the token from browser storage and returns the user to the login page. A rejected session also returns the user to the login page when a protected API request receives a 401 response.

The default token lifetime is 60 minutes unless changed in the backend configuration. Passwords are stored as hashes, not plaintext.

## Local development setup

Run the following from the HarvestDB repository root. These instructions assume Python, Node.js, Docker, and the project's existing local development configuration are available.

### 1. Start PostgreSQL

```bash
cd db_testing
docker compose up -d
docker ps
cd ..
```

The development database is `testing_db` in the `local-pg` container. The backend connects through port `5432` on the host. If another PostgreSQL instance is using that port, resolve the conflict before starting the container. Do not run `docker compose down -v` unless you intentionally want to remove the database volume.

### 2. Install backend dependencies

From the repository root, create a virtual environment if one does not already exist:

```bash
python3 -m venv .venv
```

Activate it and install the backend requirements:

```bash
source .venv/bin/activate
cd backend
python -m pip install -r requirements.txt
```

Authentication requires `pwdlib[argon2]`, `email-validator`, and the project's existing JWT dependency, `python-jose`. These should be included in `backend/requirements.txt`.

### 3. Configure backend environment variables

Keep the project's existing `backend/.env` settings, including database and notification configuration. For local development, ensure the database URLs point to the intended local database. Example values (replace the password placeholder with the local Compose database password):

```dotenv
DATABASE_URL=postgresql+psycopg://myuser:YOUR_LOCAL_DB_PASSWORD@localhost:5432/testing_db
TESTING_DATABASE_URL=postgresql+psycopg://myuser:YOUR_LOCAL_DB_PASSWORD@localhost:5432/testing_db
SECRET_KEY=YOUR_GENERATED_SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Generate a unique signing key locally:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output into `SECRET_KEY`. Do not commit the real `.env`, signing key, passwords, or database backups to GitHub. Do not use the example placeholder as an actual key. Changing the signing key invalidates existing tokens.

The two URLs above are for running the application locally against the existing development database. Before running any automated tests that reset or modify tables, configure a separate disposable test database.

### 4. Create the users table

From `backend/`, with the virtual environment activated, run this one-time setup command against the intended local database:

```bash
python - <<'PY'
from app.db.session import engine
from app.models.user import User

User.__table__.create(bind=engine, checkfirst=True)
print("Users table is ready.")
PY
```

This creates the `users` table if it does not already exist. It does not drop or recreate the existing harvest or seed inventory tables. It is not a substitute for a migration if an existing users table has a different schema.

## Adding authorized lab members

From the repository root:

```bash
source .venv/bin/activate
cd backend
python -m app.scripts.create_user
```

The script prompts for an email address, password, and password confirmation:

```text
Enter lab member email:
Enter password:
Confirm password:
```

The current local development minimum password length is eight characters. Use a strong, unique password of at least 15 characters where possible; never reuse a university or Microsoft account password. Password entry is hidden in the terminal. The script checks for an existing email and stores the password as an Argon2 hash.

Run the script once per authorized account. Each developer with their own local PostgreSQL database must create an account in that database. Local accounts are not distributed through Git. For a shared or deployed database, only a trusted administrator should run the provisioning script; ordinary lab members should not receive database credentials or server access.

### Verify accounts (administrator/developer only)

From `backend/`:

```bash
python - <<'PY'
from app.db.session import SessionLocal
from app.models.user import User

with SessionLocal() as db:
    for user in db.query(User).all():
        print(user.id, user.email, user.is_active)
PY
```

This lists account IDs, emails, and active status without displaying password hashes.

## Start and log in to HarvestDB

With PostgreSQL running, start FastAPI from `backend/`:

```bash
uvicorn app.main:app --reload --port 8000
```

In another terminal, from the repository root:

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173> and enter the email and password created with the provisioning script. Use the hostname `localhost` consistently. The current development login service uses the backend at `http://localhost:8000`.

Swagger API documentation is available at <http://localhost:8000/docs>. To test a protected endpoint there, execute the login endpoint, copy the returned access token, and enter it in Swagger's **Authorize** dialog (without adding the `Bearer` prefix). Do not share tokens or passwords in screenshots or logs.

## Authentication endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/api/v1/auth/login` | Verify email and password and issue a JWT |
| GET | `/api/v1/auth/me` | Return the current authenticated user's details |

Protected endpoints include fields, harvest events, harvest records, record images, CSV exports, seed inventory, and existing health/database diagnostics. Missing, invalid, expired, or inactive-account credentials are rejected with HTTP 401. Invalid request formats can return HTTP 422.

## User database model

The existing `users` model is used as the account allowlist.

| Column | Purpose |
| --- | --- |
| `id` | Unique user identifier used as the JWT subject |
| `email` | Unique login email address |
| `hashed_password` | Argon2 password hash |
| `is_active` | Whether the account is authorized to access HarvestDB |
| `created_at` | Account creation timestamp |

Trusted administrators can revoke access by marking the appropriate account inactive. The backend checks this field on protected requests, including requests using previously issued tokens. No administrator management UI is currently implemented.

## Key implementation files

| File | Responsibility |
| --- | --- |
| `backend/app/core/config.py` | Authentication settings and signing key configuration |
| `backend/app/core/security.py` | Password hashing, token generation, and token validation |
| `backend/app/models/user.py` | User database model |
| `backend/app/scripts/create_user.py` | Manual account provisioning |
| `backend/app/api/v1/endpoints/auth.py` | Login and current-user endpoints |
| `backend/app/api/v1/router.py` | Authentication requirements for API route groups |
| `frontend/src/services/authService.js` | Login, token storage, and local logout |
| `frontend/src/services/api.js` | Authenticated API requests |
| `frontend/src/pages/LoginPage.jsx` | Login form |
| `frontend/src/App.jsx` | Authentication state and conditional page rendering |
| `frontend/src/components/Navbar.jsx` | Account display and logout button |

## Manual verification before merging

- [ ] An approved account can log in and view existing records.
- [ ] Incorrect passwords and unknown emails are rejected.
- [ ] A protected API endpoint returns 401 without a token.
- [ ] A protected API endpoint succeeds with a valid token.
- [ ] Refreshing the page preserves a valid session.
- [ ] Logout returns to the login page and refresh does not restore the session.
- [ ] Field Entry, Query Records, and Seed Inventory load while authenticated.
- [ ] Frontend production build succeeds (`npm run build`).

## Known limitations and future improvements

The authentication feature is intended for local development and team review at this stage, not production deployment.

- Add automated tests for login, invalid credentials, token expiration, disabled accounts, and protected endpoints. Update existing endpoint tests to use authenticated test accounts and an isolated database.
- Add the `users` table to the repeatable database initialization or migration workflow if not already included.
- Complete authenticated record-image display and check CSV download links; direct browser image or download URLs cannot automatically attach bearer tokens.
- Consolidate frontend API base URL configuration instead of hardcoding the development authentication URL.
- Add login rate limiting, password reset and change workflows, and secure account deactivation tooling. Enforce a stronger password minimum (at least 15 characters for password-only authentication) before deployment.
- Require HTTPS, review CORS and browser token storage, and consider secure HttpOnly cookies with CSRF protection or a server-managed session design. Currently, logout clears the browser token but does not revoke a copied JWT on the server; it remains valid until expiration unless the account is disabled or the signing key changes.
- Review all routes, uploads, exports, and any static file serving for authorization gaps before deploying to the lab.
