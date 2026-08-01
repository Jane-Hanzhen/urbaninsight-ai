# Backend Specification

## Overview

The UrbanInsight backend is a synchronous FastAPI application backed by SQLite.

It exposes runtime data, stored statistical analysis and AI interpretation through REST endpoints.

Source root

```text
backend/
```

---

# Technology

- Python 3
- FastAPI 0.116.1
- Uvicorn 0.35.0
- SQLite from the Python standard library
- NumPy 2.3.2
- OpenAI Python SDK 2.x
- Pydantic through FastAPI

Dependencies are pinned in:

```text
backend/requirements.txt
```

---

# Project Structure

```text
backend/
├── analysis/
│   └── engine.py
├── app/
│   ├── ai/
│   ├── database.py
│   ├── main.py
│   └── repository.py
├── scripts/
│   ├── import_data.py
│   └── run_analysis.py
├── tests/
├── .env
├── .env.example
├── requirements.txt
└── urban_insight.db
```

Responsibilities

- `database.py` → path resolution, connections and schema
- `repository.py` → typed query boundary
- `main.py` → FastAPI routes, CORS and error mapping
- `analysis/engine.py` → deterministic analysis
- `scripts/import_data.py` → CSV pipeline

The public repository does not distribute the local source CSV because the compiled
artifact's redistribution rights have not been fully verified. Developers must supply
an appropriately licensed file matching the documented schema at
`data/london_indicators.csv`.
- `scripts/run_analysis.py` → analysis command
- `app/ai/` → context, prompts, schemas and providers

---

# Application Startup

FastAPI loads:

```text
backend/.env
```

The file is resolved relative to the backend project.

During application lifespan startup:

1. Resolve the database path
2. Create its parent directory when needed
3. Open SQLite
4. Enable foreign keys
5. Execute idempotent schema creation
6. Log the final absolute database path

Startup does not:

- Import CSV data
- Run PCA
- Run TOPSIS
- Call an AI provider

---

# Database Path Resolution

Default path

```text
backend/urban_insight.db
```

Environment variable

```text
URBANINSIGHT_DB_PATH
```

Rules

- Absolute paths remain absolute
- `urban_insight.db` resolves inside `backend/`
- `backend/urban_insight.db` resolves from the project root
- Resolution never depends on the process working directory
- Starting from project root or backend directory uses the same file

The resolved path is logged at startup.

This prevents accidental duplicate databases.

---

# SQLite Schema

Tables

- `boroughs`
- `indicators`
- `analysis_results`

Foreign keys are enabled for every connection.

Both dependent tables use:

```text
ON DELETE CASCADE
```

The schema is idempotent.

The current project does not use a migration framework.

See `03-data.md` for full field definitions.

---

# Repository Layer

The repository provides:

- `list_boroughs()`
- `get_borough(borough_id)`
- `get_indicators(borough_id)`
- `get_analysis_result(borough_id)`

Rows are returned as dictionaries.

`contribution_json` is deserialized before returning an analysis result.

Queries use parameter binding for borough IDs.

---

# REST API

Default base URL

```text
http://127.0.0.1:8000
```

OpenAPI documentation

```text
http://127.0.0.1:8000/docs
```

## GET /health

Response

```json
{
  "status": "ok"
}
```

## GET /boroughs

Returns all boroughs ordered by name.

Current database result count

```text
33
```

Response item

```json
{
  "id": "E09000007",
  "name": "Camden",
  "region": "London",
  "geometry_reference": "/data/london_boroughs.geojson#Camden",
  "created_at": "timestamp"
}
```

## GET /boroughs/{borough_id}

Returns one borough.

Errors

- `404 Borough not found`

## GET /indicators/{borough_id}

Returns all 12 processed indicators and `updated_at`.

Errors

- `404 Indicators not found`

## GET /analysis/{borough_id}

Returns:

```json
{
  "borough_id": "E09000007",
  "result": {}
}
```

`result` may be `null` when the borough exists but analysis has not been run.

Errors

- `404 Borough not found`

## GET /ai/status

Returns active AI configuration metadata.

See `07-ai.md`.

## POST /ai/analyze

Returns structured `AnalysisInsights`.

## POST /ai/chat

Returns `ChatResponse` containing a compatibility `content` summary and a
schema-validated structured `ChatAnswer`.

## POST /ai/compare

Returns `CompareResponse` containing a compatibility `content` summary and a
schema-validated structured `CompareAnswer`.

## POST /ai/report

Returns Markdown as text content.

The active frontend request includes completed analysis metadata, structured
`AnalysisInsights` and the current `analysis_result` snapshot. The backend reloads
the authoritative SQLite context and renders Markdown locally. This path performs
no LLM request and no statistical recalculation. Requests without the snapshot
remain supported by the legacy provider path for backwards compatibility.

## POST /reports/pdf

Returns a generated A4 PDF as `application/pdf`.

Request fields:

- `borough_id`
- `locale`
- frozen analysis metadata: `analysis_mode`, `ai_insights_requested`,
  `ai_insights_applied`, `ai_provider`, `ai_model`, `ai_error`
- completed structured `AnalysisInsights`

The route reloads borough indicators and persisted PCA/TOPSIS results from SQLite.
ReportLab renders the cover, vector charts, tables, narrative sections, methodology,
disclaimer, headers and page numbers. Simplified Chinese output embeds the bundled
Noto Sans CJK SC font under its own SIL Open Font License.

The route performs no statistical recalculation and no LLM request.

## POST /conversations/pdf

Returns the current conversation as `application/pdf`.

Request fields:

- `borough_id`
- `locale`
- `messages` containing one to 100 ordered user/assistant entries
- optional structured `ChatAnswer` or `CompareAnswer` on assistant entries

The route reloads borough context for report identity, preserves message order, and
renders structured response sections through ReportLab. It does not call an AI
provider or rerun the Analysis Engine.

AI endpoint details are normative in `07-ai.md`.

---

# AI Request Models

Base analysis request

```json
{
  "borough_id": "E09000007",
  "include_ai_insights": false,
  "ai_provider": null,
  "previous_context": [],
  "locale": "en"
}
```

`include_ai_insights` is a per-analysis user preference. When true, `ai_provider`
selects the request-level live strategy. Supported values are `deepseek`, `qwen` and
the legacy-compatible `openai`; the current web UI offers DeepSeek and Qwen only.

Selection priority:

1. Request `ai_provider`
2. Environment `AI_PROVIDER`
3. Existing backend default

Unknown request values fail Pydantic validation with `422`.

Chat adds:

```json
{
  "question": "What stands out?",
  "compare_borough_id": null
}
```

Comparison adds:

```json
{
  "compare_borough_id": "E09000033"
}
```

Supported locales

- `en`
- `zh-CN`

English is the backward-compatible default.

---

# HTTP Errors

Data not found

```text
404
```

Pydantic request validation

```text
422
```

AI configuration failure

```text
503
```

External provider or invalid provider response

```text
502
```

Provider error details remain in sanitized backend logs.

Frontend responses remain generic.

---

# CORS

Allowed origins

```text
http://127.0.0.1:5173
http://localhost:5173
```

Allowed methods

- `GET`
- `POST`

Allowed headers

- All

Credentials

```text
false
```

Production deployment requires explicit CORS review.

---

# CSV Import

Command from project root

```bash
backend/.venv/bin/python backend/scripts/import_data.py
```

The script initializes the schema and upserts borough and indicator rows.

It validates the exact current CSV header.

See `03-data.md` for the transformation contract.

---

# Analysis Engine

Command from project root

```bash
backend/.venv/bin/python backend/scripts/run_analysis.py
```

The engine:

- Reads all current indicator rows
- Performs PCA-weighted TOPSIS
- Persists one result per borough
- Removes stale analysis rows
- Prints a run summary

The browser does not invoke this script.

Data should be imported and analyzed before starting normal application testing.

---

# Backend Startup

From project root

```bash
backend/.venv/bin/python -m uvicorn app.main:app \
  --app-dir backend \
  --host 127.0.0.1 \
  --port 8000 \
  --reload
```

From backend directory

```bash
.venv/bin/python -m uvicorn app.main:app \
  --host 127.0.0.1 \
  --port 8000 \
  --reload
```

When the virtual environment is activated inside `backend/`, this is also valid:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Both working directories resolve to the same default database.

---

# Frontend Integration

The frontend API base URL is:

```text
VITE_API_URL
```

Default

```text
http://127.0.0.1:8000
```

The frontend uses:

- `GET /boroughs` at startup
- `GET /indicators/{id}` after selection
- `GET /analysis/{id}` after selection
- `POST /ai/analyze` after selection
- AI conversation and report endpoints after completion

---

# Testing

Backend test command

```bash
PYTHONPATH=backend backend/.venv/bin/python -m unittest discover \
  -s backend/tests \
  -v
```

Current test areas

- Database path resolution
- Standardization
- TOPSIS behavior
- Full analysis persistence
- Provider configuration
- Provider switching
- Structured response validation
- Mock endpoints
- Bilingual AI behavior
- Sanitized errors

Automated tests use temporary databases and mocked external clients.

---

# Operational Limitations

The current backend:

- Uses synchronous route functions
- Creates provider strategies per generation call
- Does not persist AI conversations
- Does not persist reports
- Generates PDF reports synchronously in the request process
- Does not implement authentication
- Does not implement rate limiting
- Does not run schema migrations
- Does not trigger analysis automatically after CSV import
- Does not expose an API endpoint to run the Analysis Engine

These are current implementation facts, not implied future commitments.
