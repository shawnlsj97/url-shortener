# Relay

Relay is a production-minded URL shortener built with Python and FastAPI. It supports
public shortening, optional accounts for link ownership, custom aliases, expiry,
basic click metrics, and a responsive management dashboard.

## Assignment coverage

| Assessment goal | Relay implementation |
| --- | --- |
| Create short URLs | Responsive web UI and `POST /api/links` create public, shareable links. |
| Resolve short URLs | `GET /{code}` looks up the destination and returns `302 Found`. |
| Attractive, mobile-friendly UI | Accessible, server-rendered interface with responsive layouts and touch-friendly controls. |
| Persistent storage | PostgreSQL with SQLAlchemy and versioned Alembic migrations. |
| Public deployment | Live Docker deployment on Render. |
| Tests and canary | Automated unit/functional tests, GitHub Actions CI, and a scheduled API canary covering health, creation, and redirect behavior. |

## Technology choices

| Area | Choice | Why |
| --- | --- | --- |
| Backend | Python 3.12, FastAPI, Pydantic | Familiar, strongly typed request validation with concise, explicit HTTP handlers. |
| Application design | Modular monolith | Keeps routes, business services, and persistence boundaries clear without premature distributed-system complexity. |
| Frontend | Jinja templates, vanilla JavaScript, CSS | No client build pipeline; the full user flow is straightforward to trace, modify, and keep responsive. |
| Data | PostgreSQL, SQLAlchemy | Relational ownership plus transactionally enforced uniqueness make link creation and management reliable. |
| Schema changes | Alembic | Versioned, repeatable database migrations for local and deployed environments. |
| Delivery | Docker, GitHub Actions, Render | Reproducible runtime, automated quality checks, and a public review deployment. |

## Live demo

[Open Relay](https://relay-url-shortener.onrender.com)

*The free-tier service may take a moment to wake after inactivity.*

## Features

- Create public `http`/`https` short links.
- Redirect active links with `302 Found`.
- Register and log in to own and manage links.
- Create custom aliases and optional expiry dates.
- Disable owned links without reusing their codes.
- View per-link and account-wide click totals.
- Responsive, accessible server-rendered UI and JSON API.
- PostgreSQL persistence, Alembic migrations, Docker, CI, linting, typing, and tests.

## Run locally

Choose the path that best fits your environment.

### Option A — Docker + PostgreSQL (recommended)

Requires Docker Desktop. This starts the FastAPI application and PostgreSQL together,
then applies migrations automatically.

```bash
docker compose up --build
```

Open [http://localhost:8000](http://localhost:8000). Stop the stack with
`docker compose down`.

### Option B — Python + SQLite (no Docker)

Requires Python 3.12 or later. This is the fastest way to inspect or modify the
application without starting PostgreSQL.

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000). Direct execution uses the local
SQLite database at `var/ogp.db` by default. Set `DATABASE_URL` to connect to another
PostgreSQL instance instead.

## Quality checks

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy app
.venv/bin/pytest
```

GitHub Actions runs the same checks on pushes and pull requests.

## API

| Method | Route | Description |
| --- | --- | --- |
| `POST` | `/api/links` | Create a public or owned short link |
| `GET` | `/{code}` | Resolve a link |
| `POST` | `/api/auth/register` | Register and start a session |
| `POST` | `/api/auth/login` | Log in and start a session |
| `POST` | `/api/auth/logout` | Revoke the current session |
| `GET` | `/api/links` | List the current user's links and metrics |
| `DELETE` | `/api/links/{code}` | Disable an owned link |
| `GET` | `/healthz` | Application/database health check |

Interactive OpenAPI documentation is available at `/docs`.

Example:

```bash
curl -X POST http://localhost:8000/api/links \
  -H 'content-type: application/json' \
  -d '{"original_url":"https://open.gov.sg/","custom_alias":"open-gov"}'
```

## Design notes

The application is a modular monolith: FastAPI routes call focused services,
which use SQLAlchemy repositories and PostgreSQL. A unique database constraint
is the final guard against short-code collisions. Random Base62 codes are generated
with Python's `secrets` module; no third-party shortening service is used.

PostgreSQL is deliberate: it provides transactionally enforced uniqueness,
ownership foreign keys, migrations, and straightforward local/deployed
operation at this application's expected scale. The system can evolve by adding
Redis cache-aside for hot redirects and replacing the atomic metric update with
queue-backed aggregation if redirect volume warrants it.

Browser sessions use opaque random tokens, stored only as HMAC hashes in the
database. Passwords use Argon2. State-changing authenticated requests require
CSRF header/cookie verification. Security headers and no-store caching protect
authenticated pages.

Short URLs are generated from `PUBLIC_BASE_URL`, rather than the request's
`Host` header. This keeps links correct behind a reverse proxy and makes a
future custom domain a configuration change.

## Intentional limits

This project does not include email verification/reset, OAuth, private links,
destination scanning, distributed rate limiting, or a queue-backed analytics
pipeline. These are deliberate follow-on concerns rather than partially
implemented features.
