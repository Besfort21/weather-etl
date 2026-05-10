# 🌤️ Weather ETL Pipeline

[![CI](https://github.com/Besfort21/weather-etl/actions/workflows/ci.yml/badge.svg)](https://github.com/Besfort21/weather-etl/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Docker](https://img.shields.io/badge/docker-ready-2496ED)

An automated ETL pipeline that extracts hourly weather data from the Open-Meteo API,
transforms and enriches it with pandas, stores it in SQLite, and exports CSV reports.
Runs on a configurable schedule via Docker.

---

## Features

- Fetches hourly weather data for multiple cities via the free Open-Meteo API
- Cleans and enriches data with pandas — adds feels-like temperature and weather descriptions
- Stores data in SQLite with duplicate prevention at database level
- Exports filtered data to CSV by city or date
- Runs automatically on a schedule via APScheduler
- Cities and settings fully configurable via `config.yaml` — no code changes needed
- Structured logging for every pipeline run
- Runs in Docker with data and exports mounted as volumes

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| HTTP client | requests |
| Data transformation | pandas |
| Database | SQLite (stdlib) |
| Scheduling | APScheduler |
| Config | YAML (PyYAML) |
| Testing | pytest + pytest-mock |
| Linting | ruff |
| Container | Docker + docker-compose |
| CI | GitHub Actions |

---

## Architecture

Strict ETL separation — each stage is an independent class with one responsibility:

```
Extractor  →  Transformer  →  Loader
   │               │              │
Open-Meteo      pandas        SQLite
   API          DataFrame     + CSV
```

---

## Configuration

Edit `config.yaml` to add or remove cities — no code changes needed:

```yaml
cities:
  - name: Solingen
    latitude: 51.1765
    longitude: 7.0833
  - name: Düsseldorf
    latitude: 51.2217
    longitude: 6.7762

scheduler:
  interval_hours: 1

database:
  path: data/weather.db

exports:
  path: exports/
```

---

## Getting Started

### Option A — Run locally

```bash
git clone https://github.com/USERNAME/weather-etl.git
cd weather-etl

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate.bat

pip install -r requirements.txt

python -m src.main run
```

### Option B — Run with Docker

```bash
docker compose build
docker compose run --rm weather-etl run
```

---

## Usage

```bash
# Run the pipeline once
python -m src.main run

# Start the scheduler (runs every hour, Ctrl+C to stop)
python -m src.main schedule

# Export all data to CSV
python -m src.main export

# Export filtered by city
python -m src.main export --city Solingen

# Export filtered by date
python -m src.main export --date 2026-05-10
```

### Docker equivalents

```bash
docker compose run --rm weather-etl run
docker compose run --rm weather-etl schedule
docker compose run --rm weather-etl export --city Solingen
```

---

## Running Tests

```bash
pytest
pytest --cov=src --cov-report=term-missing
```

Tests use `pytest-mock` to mock all API calls — no real network requests are made during testing.

---

## Design Decisions

**Strict ETL separation** — Extractor, Transformer and Loader are fully independent classes.
The pipeline orchestrator wires them together, but each stage can be tested and replaced
in isolation.

**Resilience by default** — a failing API call for one city never crashes the pipeline.
Each city is fetched independently, errors are caught and logged, and the pipeline
continues with the remaining cities.

**Duplicate prevention at database level** — the `UNIQUE(city, timestamp)` constraint
and `INSERT OR IGNORE` ensure that re-running the pipeline never produces duplicate rows,
even if the same data is fetched multiple times.

**Config-driven cities** — adding a new city requires only a `config.yaml` change,
no code modification. This follows the open/closed principle.

**Mocked tests** — tests never hit the real API. `pytest-mock` patches the extractor
so tests run fast, offline, and with predictable data.