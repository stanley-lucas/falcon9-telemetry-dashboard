# Falcon 9 Launch Telemetry Dashboard

![CI](https://github.com/stanley-lucas/falcon9-telemetry-dashboard/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)

> ETL pipeline and interactive dashboard for historical Falcon 9 launch data.
> Built to demonstrate aerospace data engineering — and to learn the tools used
> by teams building real launch software.

<!-- Replace with actual screenshot once dashboard is running -->
<!-- ![Dashboard preview](docs/dashboard-preview.png) -->

## What This Solves

SpaceX publishes all historical launch data through a public REST API, but there's
no easy way to query it, filter it, or visualize trends across 200+ missions.
This project builds a full data pipeline: fetch → normalize → store → serve → visualize.

The result is a queryable PostgreSQL database of every Falcon 9 launch, a FastAPI
layer that exposes it as a clean REST API, and a Streamlit dashboard for interactive
exploration of landing success rates, core reuse statistics, and mission timelines.

This is relevant to aerospace because data pipelines for telemetry and mission logs
follow the same pattern — the difference is the data source, not the architecture.

## Architecture

```
SpaceX API → ETL Pipeline → PostgreSQL → FastAPI → Streamlit Dashboard
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for a full breakdown of every design decision:
why PostgreSQL over MongoDB, why FastAPI over Django, and the planned migration path
to TimescaleDB.

## Quick Start

```bash
# 1. Clone and configure
git clone https://github.com/stanley-lucas/falcon9-telemetry-dashboard
cd falcon9-telemetry-dashboard
cp .env.example .env

# 2. Start all services
docker-compose up --build

# 3. Seed the database with historical SpaceX data
docker-compose run --rm pipeline

# 4. Open the dashboard
open http://localhost:8501

# 5. Explore the API docs
open http://localhost:8000/docs
```

That's it. One build, one seed, one dashboard.

## Services

| Service | URL | Description |
|---|---|---|
| Dashboard | http://localhost:8501 | Streamlit — interactive charts |
| API | http://localhost:8000/docs | FastAPI — OpenAPI UI |
| Database | localhost:5432 | PostgreSQL — raw + processed tables |

## Development

```bash
# Run tests (against real test DB inside Docker)
docker-compose run --rm api pytest tests/ -v

# Type check
docker-compose run --rm api mypy src/

# Lint
docker-compose run --rm api ruff check src/ tests/
```

## Stack

| Layer | Tool | Why |
|---|---|---|
| API | FastAPI + SQLAlchemy 2.0 | Async-first, typed, auto OpenAPI |
| ETL | Python + Pandas | Readable pipelines, industry standard |
| Storage | PostgreSQL 16 | Relational integrity; TimescaleDB-ready |
| Dashboard | Streamlit + Plotly | Python-native, fast iteration |
| Infrastructure | Docker Compose | Reproducible one-command setup |

## Roadmap

- [x] Project scaffold
- [ ] ETL pipeline (fetch + transform + load)
- [ ] FastAPI with launch and stats endpoints
- [ ] Streamlit dashboard v1
- [ ] TimescaleDB migration + benchmark
- [ ] Blog post series

## License

MIT
