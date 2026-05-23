# Architecture Decision Record

This document explains every significant architectural choice behind the Falcon 9
Telemetry Dashboard. It is written for engineers evaluating the project — and for
my own reference when extending the system.

The question I try to answer for each decision: **why this, and not something else?**

---

## 1. Why PostgreSQL? (Phase 1)

**Decision:** Plain PostgreSQL 16 with targeted indexes on time and flight number columns.

The launch data has clear relational structure:

- A `launch` belongs to one `launchpad`
- A `launch` involves one or more `cores` (via `launch_cores`)
- Each `core` has a reuse and landing history

JOINs across these entities are the primary query pattern — "which cores landed
successfully and how many times had they flown before?" This is a relational question.
A document store would require denormalizing the data and make this query harder, not easier.

**Rejected: MongoDB**
The schema is well-defined and stable (SpaceX API v4 has been unchanged for years).
There's no benefit to schema flexibility here, and we'd lose JOINs.

**Rejected: InfluxDB or TimescaleDB (Phase 1)**
Operationally heavier, more complex to set up, and the dataset (~220 launches) fits
comfortably in plain PostgreSQL. Choosing a time-series database before measuring a
bottleneck is premature optimization.

**Index strategy:**
```sql
-- Most queries filter or sort by mission date
CREATE INDEX ON launches (date_utc);

-- Sequential lookup by mission number
CREATE INDEX ON launches (flight_number);

-- Primary join path: launch → booster details
CREATE INDEX ON launch_cores (launch_id);
```

---

## 2. Why TimescaleDB? (Phase 2)

> This section will be completed after the Phase 1 → Phase 2 migration.
> The hypothesis driving it:

As we add simulated per-second telemetry data (altitude, velocity, downrange distance,
dynamic pressure), the volume becomes genuinely time-series: one row per second per
mission ≈ tens of millions of rows.

At that scale, plain PostgreSQL struggles with:
- **Range queries over time**: `WHERE timestamp BETWEEN t1 AND t2` without partitioning
  becomes a full table scan
- **Time-bucketing aggregations**: computing average velocity per 10-second window
  requires a verbose SQL workaround vs TimescaleDB's `time_bucket()` function
- **Compression**: TimescaleDB's columnar compression can achieve 20x storage reduction
  on time-series data

TimescaleDB runs as a PostgreSQL *extension* — the migration is incremental:
1. `CREATE EXTENSION IF NOT EXISTS timescaledb`
2. Convert the telemetry table to a hypertable: `SELECT create_hypertable('telemetry', 'timestamp')`
3. Add compression policy

The application code (SQLAlchemy queries) requires minimal changes because TimescaleDB
is still PostgreSQL underneath.

**We will benchmark `SELECT` latency and storage size before and after — the post
documenting this migration will be data-driven, not opinion-driven.**

---

## 3. Why FastAPI? (Not Django)

**Decision:** FastAPI with SQLAlchemy 2.0 async and asyncpg driver.

This project has a Django background. The switch is intentional and worth understanding:

| Concern | Django | FastAPI |
|---|---|---|
| Async I/O | Bolted on (ASGI support added in 3.1) | Async by design |
| Schema validation | DRF Serializers (implicit) | Pydantic (explicit, at the type level) |
| API docs | drf-spectacular (extra package) | Built-in from type annotations |
| Dependency injection | Middleware, mixins (implicit) | `Depends()` — explicit, per-route |
| ORM | Django ORM (magical) | SQLAlchemy (explicit, composable) |

The async benefit is real here: the ETL pipeline fetches three SpaceX API endpoints
concurrently with `asyncio.gather()`. A synchronous Django view would serialize those
requests, tripling fetch time.

**Django would be the right choice if:** we needed the admin panel, full-stack HTML
views, a large ecosystem integration (Celery, channels), or a team already using it.
For a pure data API that needs to be self-documenting, Django is unnecessary weight.

**Django → FastAPI mental model:**
- `APIRouter` ≈ `urls.py` + view, combined
- `Pydantic BaseModel` ≈ DRF Serializer with runtime validation
- `Depends(get_db)` ≈ `get_queryset()` but explicit and composable
- `lifespan` ≈ `AppConfig.ready()`

---

## 4. Why Streamlit? (Not Grafana or Dash)

**Decision:** Streamlit consuming the FastAPI layer.

**Rejected: Grafana**
Grafana connects directly to databases using JSON config — there's no Python code,
no API contract tested, no reusable logic. It's the right tool for infrastructure
monitoring dashboards; it's the wrong tool for demonstrating software engineering.

**Rejected: Plotly Dash**
More powerful and more production-suitable than Streamlit, but requires callback
decorators and layout objects that add boilerplate. For Month 1–2, Streamlit's
simplicity (a chart is 3 lines of Python) is the right trade-off.

**Why Streamlit → FastAPI (and not Streamlit → DB directly):**
Connecting Streamlit to the database directly would be simpler — but it would collapse
two architectural layers into one and remove the value of having the API at all.
The dashboard consuming the API is the pattern used in real systems: a frontend
consuming a backend service over HTTP. This is the version worth demonstrating.

---

## 5. Why Docker Compose?

**Decision:** All services containerized. One `docker-compose up --build` to start.

The principle: if running locally requires more than one command, it will rot.
Developers stop running it, tests stop getting run, the README becomes a lie.

Docker Compose guarantees:
- PostgreSQL version is identical everywhere (16-alpine)
- Python version is identical (3.12-slim)
- Environment variables are documented in `.env.example`
- CI and local environments are mirrors of each other

**Rejected: manual venv + local Postgres**
Works for one developer on one machine. Breaks the moment someone else clones the repo
or you upgrade your local Postgres. Not a credible portfolio choice.

**Not Kubernetes:**
K8s is the right answer for multi-region, auto-scaling production services. It would
be the wrong answer here — demonstrating that you know when *not* to use a tool is
also part of the engineering signal.

---

## 6. ETL Idempotency

The pipeline is designed to be re-run safely at any time without side effects.

**Why this matters:** The SpaceX API occasionally updates historical data — a launch
outcome that was listed as `null` gets updated to `true` or `false` weeks later.
Re-running the pipeline should silently incorporate those updates.

**How it's achieved:**
- **Launches, launchpads, cores**: `INSERT ... ON CONFLICT DO UPDATE` (upsert). If the
  row already exists, update it with the latest data.
- **Launch cores** (the junction table): delete-and-reinsert per launch on each run.
  Simpler than a composite upsert, and the table is small relative to the parent.

This means: run the pipeline daily, weekly, or after a new launch — it always converges
to the correct state.

---

## 7. AI-Assisted Development

This project was built with Claude Code (claude-sonnet-4-6) as a pair programming partner.

**The collaboration model:**
- Architecture decisions were made jointly — Claude proposed trade-offs, I chose
- Code was scaffolded by Claude, reviewed and extended by me
- This document was drafted collaboratively

**Why document this:**
Building reliable systems with AI assistance is a skill, not a shortcut. The decisions
in this document are mine — I can defend each one in an interview. Claude accelerated
the implementation; the understanding is my own.

For engineers evaluating this project: the "AI wrote it" framing misses the point.
A senior engineer using AI to move faster while maintaining quality is exactly the
model SpaceX and other advanced engineering shops are building toward.

---

## Points of Failure and Mitigations

| Failure mode | Mitigation |
|---|---|
| SpaceX API is down during ETL | `httpx` retry with exponential backoff; pipeline is re-runnable |
| Malformed API response | Pydantic validation rejects bad data loudly; pipeline fails fast |
| DB constraint violation | Upsert semantics mean constraint violations are resolved, not raised |
| Dashboard can't reach API | Docker Compose healthcheck ensures API is ready before dashboard starts |
| Schema drift (SpaceX API change) | Transformer tests catch missing fields before data reaches the DB |
