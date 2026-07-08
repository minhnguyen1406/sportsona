# Sportsona

Personalised, multi-sport companion app. F1-first; more sports coming. The icon
is an italic dreamsicle **S** on a warm-cocoa tile (`backend/web/static/favicon.svg`).

```
sportsona/
├── backend/   FastAPI + SQLAlchemy + Alembic + Postgres
├── web/       SvelteKit 2 + Svelte 5 (runes) + Tailwind v4 + Vite 6
└── docker-compose.yml
```

## Quick start

Three commands gets the whole stack running.

```bash
# 1. From the repo root: start Postgres + backend in Docker.
docker compose up -d

# 2. (Once, after the DB comes up) seed F1 data for a season.
docker compose exec sportsona-backend \
  python -m scripts.sync_f1_data --year 2025 --results --standings

# 3. From web/: start the frontend dev server.
cd web && yarn install && yarn dev
```

Then open <http://localhost:4000>.

### Services + ports

| Service          | URL / port              | Started by                 |
|------------------|-------------------------|----------------------------|
| Frontend (Vite)  | http://localhost:4000   | `yarn dev` in `web/`       |
| Backend (FastAPI)| http://localhost:8000   | `docker compose up -d`     |
| API docs (Swagger)| http://localhost:8000/docs | (backend)              |
| Postgres         | localhost:5432          | `docker compose up -d`     |

## Test credentials

⚠️ **Local development only — never use these credentials anywhere else.**

A single pre-seeded user is used by the auth smoke tests, the `try_recap.py`
script, and ad-hoc browsing.

| Field    | Value                       |
|----------|-----------------------------|
| Email    | `smoketest@example.com`     |
| Username | `smoketester`               |
| Password | `testpw1234`                |

The user is **not** auto-created on a fresh DB. After a reset, recreate with:

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"smoketest@example.com","username":"smoketester","password":"testpw1234"}'
```

To verify the user exists:

```bash
docker compose exec sportsona-db psql -U sportsona_user -d sportsona \
  -c "SELECT id, email, username FROM users WHERE email = 'smoketest@example.com';"
```

### Database credentials (local)

| Field     | Value              |
|-----------|--------------------|
| Host      | localhost          |
| Port      | 5432               |
| Database  | sportsona          |
| User      | sportsona_user     |
| Password  | dev_password_123   |

Override per-shell with `POSTGRES_USER` / `POSTGRES_PASSWORD` env vars (see
`docker-compose.yml`).

## Common tasks

### Seed F1 data

```bash
# Drivers, constructors, races, results, standings for one season
docker compose exec sportsona-backend \
  python -m scripts.sync_f1_data --year 2025 --results --standings
```

Repeat per year. The sync is idempotent — existing rows are skipped, only new
data is added.

### Clean up duplicates & normalise countries

If you ever sync from an older data source (which used short-form ids like
`hamilton` instead of `lewis_hamilton`), run the consolidator:

```bash
docker compose exec -T sportsona-db psql -U sportsona_user -d sportsona \
  < backend/scripts/cleanup_data_dupes.sql
```

The script is **idempotent** — re-running on clean data is a no-op. It:
- Merges duplicate drivers (long-form id wins)
- Merges duplicate constructors (`haas_f1_team`, `alfa_romeo`)
- Normalises driver nationality (`GBR` → `British`, etc.)
- Normalises circuit country (`UK` → `United Kingdom`)
- Fills in missing constructor nationalities (Ferrari → Italian, etc.)

### Dark mode

The site has a built-in **light / dark / system** toggle in the header (icon
between the nav and the auth buttons). Selection persists in `localStorage`.
The bootstrap script in `web/src/app.html` applies the saved theme **before**
hydration so there's no flash of the wrong palette.

### Run backend tests

```bash
docker compose exec sportsona-backend poetry run pytest -q
```

### Apply migrations

```bash
docker compose exec sportsona-backend alembic upgrade head
```

## More detail

- Backend reference & migration recipes: [`backend/README.md`](backend/README.md)
- Frontend reference & yarn-only commands: [`web/README.md`](web/README.md)
- Project plan: [`SPORTSONA_PROJECT_PLAN.md`](SPORTSONA_PROJECT_PLAN.md)

## Branding

- Mark: italic Inter Black **S** on cocoa gradient `#3B1F12 → #150804`,
  dreamsicle `#F47B3F` accents
- Tokens live in `web/src/app.css` (`--mark-cocoa`, etc.)
- Source SVGs in `web/static/favicon.svg`, `web/static/logo-mark.svg`,
  `web/static/logos/d-mark-wordmark.svg`
- Svelte component: `web/src/lib/components/Logo.svelte`
