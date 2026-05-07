# Sportsona Backend

FastAPI backend for Sportsona sports aggregator platform.

## Tech Stack

- **FastAPI** - Web framework
- **SQLAlchemy** - ORM
- **Alembic** - Database migrations
- **PostgreSQL** - Database
- **Poetry** - Dependency management

## Quick Start

```bash
# From project root directory
docker compose up -d
```

This starts:
- **API** at http://localhost:8000
- **API Docs** at http://localhost:8000/docs
- **PostgreSQL** at localhost:5432

## Commands

### Start/Stop Services

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# View logs
docker compose logs -f sportsona-backend

# Check status
docker compose ps
```

### Database Migrations

```bash
# Apply all pending migrations
docker compose exec sportsona-backend alembic upgrade head

# Create new migration after model changes
docker compose exec sportsona-backend alembic revision --autogenerate -m "Description"

# View migration history
docker compose exec sportsona-backend alembic history
```

### Connect to Database

```bash
# Via psql in container
docker compose exec sportsona-db psql -U sportsona_user -d sportsona

# Common psql commands
\dt          # List tables
\d+ users    # Describe table
\q           # Quit
```

### Local Development (without Docker)

```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload
```

## Database Credentials

| Field | Value |
|-------|-------|
| Host | localhost |
| Port | 5432 |
| Database | sportsona |
| User | sportsona_user |
| Password | dev_password_123 |

## Test User (local dev)

A pre-seeded user used by the auth smoke tests, the `try_recap.py` script,
and ad-hoc local browsing. **Local development only — never use these
credentials anywhere else.**

| Field | Value |
|-------|-------|
| Email | `smoketest@example.com` |
| Username | `smoketester` |
| Password | `testpw1234` |

The user is **not** created automatically on a fresh database. To recreate
after a DB reset, start the backend and run:

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"smoketest@example.com","username":"smoketester","password":"testpw1234"}'
```

To verify it exists:

```bash
docker compose exec sportsona-db psql -U sportsona_user -d sportsona \
  -c "SELECT id, email, username FROM users WHERE email = 'smoketest@example.com';"
```

## Project Structure

```
backend/
├── app/
│   ├── core/           # Config, database setup
│   ├── models/         # SQLAlchemy models
│   ├── routers/        # API endpoints
│   ├── schemas/        # Pydantic schemas
│   ├── services/       # Business logic
│   └── main.py         # FastAPI app
├── alembic/            # Database migrations
├── Dockerfile
└── pyproject.toml
```
