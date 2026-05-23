# Falcon 9 Launch Telemetry Dashboard

## Project Mission
ETL pipeline and interactive dashboard that collects, processes, and visualizes
historical Falcon 9 launch data from the SpaceX public API. Portfolio project
targeting aerospace/systems engineering roles — code quality matters as much as
functionality. Every architectural decision is documented publicly (LinkedIn + blog).

## Architecture Overview

```
SpaceX REST API (r-spacex/SpaceX-API v4)
        │
   [Fetcher]       src/pipeline/fetcher.py       — HTTP client, pagination, retry logic
        │
   [Transformer]   src/pipeline/transformer.py   — Pandas, unit normalization, validation
        │
   [PostgreSQL]    raw + processed tables         — Phase 1: plain PG + indexes
        │                                           Phase 2: TimescaleDB hypertables
   [FastAPI]       src/api/                       — serves processed data via REST
        │
   [Streamlit]     src/dashboard/                 — consumes FastAPI, renders charts
```

Phase 1 → Phase 2 is intentional. We start with plain PostgreSQL and good indexing,
measure where it hurts, then migrate to TimescaleDB. The migration is documented
as a blog post — that progression is more credible than choosing TimescaleDB blindly.

## Stack & Why These Choices

| Tool | Why | Rejected alternative |
|---|---|---|
| FastAPI | Async-first, auto OpenAPI docs, Pydantic validation | Flask (no async/validation), Django (too much for a data API) |
| PostgreSQL | Relational integrity, great index tooling, TimescaleDB-compatible | MongoDB (no relational joins across launch/core/pad data) |
| TimescaleDB (Phase 2) | Native time-series compression + time_bucket() queries | InfluxDB (separate ecosystem), plain PG (measured bottleneck) |
| Pandas | Industry standard for aerospace data wrangling | Polars (valid but less recognizable on a resume) |
| Streamlit | Python-native, fast iteration, no JS | Dash (more powerful but overkill), Grafana (not Python) |
| Docker Compose | Single-command reproducibility | Manual setup (not reproducible), K8s (overkill for Month 1–2) |

## Repository Structure

```
falcon9-telemetry-dashboard/
├── README.md
├── ARCHITECTURE.md
├── CLAUDE.md
├── src/
│   ├── config.py          # All constants — units in the name (MAX_ALTITUDE_KM)
│   ├── api/               # FastAPI app — routers, schemas, dependencies
│   ├── pipeline/          # ETL — fetcher, transformer, loader, run
│   ├── models/            # SQLAlchemy ORM models + Pydantic response schemas
│   └── dashboard/         # Streamlit app — consumes FastAPI
├── tests/
│   ├── conftest.py        # Fixtures: test DB engine, session, API client
│   ├── test_pipeline/
│   └── test_api/
├── docker-compose.yml
├── Dockerfile
├── Dockerfile.dashboard
├── .env.example
├── .github/workflows/ci.yml
└── requirements.txt
```

## Code Conventions

- **Type hints on every function** — no exceptions
- **Pydantic models** for all API request/response shapes (never bare dicts)
- **Async FastAPI routes** by default; sync only when wrapping blocking I/O explicitly
- **No bare dicts** for data across pipeline stages — dataclasses or Pydantic models
- **Constants with units** in the name: `MAX_ALTITUDE_KM`, `BURN_DURATION_S`
- **Idempotent ETL** — running the pipeline twice must produce the same result
- **No silent failures** — exceptions are logged and re-raised, never swallowed

## FastAPI ↔ Django Analogies

The developer knows Django well. When introducing FastAPI patterns, use these analogies:

| FastAPI | Django equivalent |
|---|---|
| `APIRouter` | `urls.py` + view combined |
| `Pydantic BaseModel` | DRF Serializer with runtime validation |
| `Depends()` | Middleware/mixins, but explicit and per-route |
| `asyncpg` / SQLAlchemy Core | Django ORM (but no ORM by default) |
| `lifespan` context manager | `AppConfig.ready()` |

## Development Workflow

```bash
# Start all services
docker-compose up --build

# Seed the database with historical SpaceX data
docker-compose run --rm pipeline

# Run tests (against real test DB inside Docker)
docker-compose run --rm api pytest tests/ -v

# Type check
docker-compose run --rm api mypy src/

# Lint + format
docker-compose run --rm api ruff check src/ tests/
docker-compose run --rm api ruff format src/ tests/
```

Never run outside Docker. `.env` is gitignored — copy `.env.example` and fill in values.

## Testing Standards

- **pytest** only — no unittest
- **No DB mocks** — tests run against a real PostgreSQL test database via Docker
- Fixtures in `tests/conftest.py` handle DB setup/teardown
- Every pipeline transform function has a unit test
- Every API route has an integration test
- CI runs on every push (GitHub Actions)

## Claude's Role in This Project

- **Explain WHY before implementing** — learning-first project. Introduce the concept
  and design decision before writing the code.
- **Flag trade-offs** when multiple valid approaches exist — especially PG vs TimescaleDB
  decisions, since those become blog posts.
- **Aerospace reliability mindset:** pipelines are idempotent, APIs return meaningful
  HTTP status codes, nothing silently fails.
- **Document AI-assisted development:** significant architectural suggestions adopted from
  Claude should be noted in ARCHITECTURE.md. Demonstrating thoughtful AI collaboration
  is a differentiator for SpaceX.
- **Portfolio awareness:** this code will be read by SpaceX engineers. Prefer explicitness
  and clarity over cleverness.

## Content Milestones (Blog / LinkedIn)

| Milestone | Post topic |
|---|---|
| DB schema done | "Modeling aerospace launch data in PostgreSQL" |
| ETL pipeline running | "Building an idempotent ETL pipeline from scratch" |
| FastAPI live | "FastAPI vs Django: what I learned switching stacks" |
| TimescaleDB migration | "Why we migrated from PostgreSQL to TimescaleDB (with benchmarks)" |
| Docker Compose done | "One-command deploys: containerizing a Python data app" |
| Dashboard live | "Visualizing Falcon 9 telemetry with Streamlit + FastAPI" |

## Out of Scope (Month 1–2)

- Real-time telemetry (historical data only)
- Authentication on the API
- Frontend beyond Streamlit
- ML / predictions
- TimescaleDB (Phase 2 only — plain PG first, measure, then migrate)

## Data Sources

- SpaceX REST API v4: `https://github.com/r-spacex/SpaceX-API`
- Endpoints: `/v4/launches`, `/v4/rockets`, `/v4/launchpads`, `/v4/cores`
- All data is public and read-only — no API key required
