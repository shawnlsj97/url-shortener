# Relay

Relay is a production-minded URL shortener built with Python and FastAPI. It supports
public shortening, optional accounts for link ownership, custom aliases, expiry,
basic click metrics, and a responsive management dashboard.

## Features

- Create public `http`/`https` short links.
- Redirect active links with `302 Found`.
- Register and log in to own and manage links.
- Create custom aliases and optional expiry dates.
- Disable owned links without reusing their codes.
- View per-link and account-wide click totals.
- Responsive, accessible server-rendered UI and JSON API.
- PostgreSQL persistence, Alembic migrations, Docker, CI, linting, typing, and tests.

## Quick start

The simplest setup uses Docker and PostgreSQL:

```bash
docker compose up --build
```

Open [http://localhost:8000](http://localhost:8000). The app applies migrations
when the development container starts.

To run directly with a local Python environment:

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload
```

By default, direct local execution uses `var/ogp.db`. Set `DATABASE_URL` to use
PostgreSQL instead. `.env.example` uses that same SQLite default; Docker Compose
overrides it with its Postgres service automatically.

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
is the final guard against short-code collisions. Random Base62 codes are
generated with Python's `secrets` module.

PostgreSQL is deliberate: it provides transactionally enforced uniqueness,
ownership foreign keys, migrations, and straightforward local/deployed
operation at this application's expected scale. The system can evolve by adding
Redis cache-aside for hot redirects and replacing the atomic metric update with
queue-backed aggregation if redirect volume warrants it.

Browser sessions use opaque random tokens, stored only as HMAC hashes in the
database. Passwords use Argon2. State-changing authenticated requests require
CSRF header/cookie verification.

Short URLs are generated from `PUBLIC_BASE_URL`, rather than the request's
`Host` header. This keeps links correct behind a reverse proxy and makes a
future custom domain a configuration change.

## Intentional limits

This project does not include email verification/reset, OAuth, private links,
destination scanning, distributed rate limiting, or a queue-backed analytics
pipeline. These are deliberate follow-on concerns rather than partially
implemented features.
