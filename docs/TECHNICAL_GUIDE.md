# UrbanInsight AI Technical Guide

[Back to portfolio overview](../README.md) | [简体中文首页](../README.zh-CN.md)

This guide preserves the technical, setup, data, licensing, API, validation, and limitation details for UrbanInsight AI. The release architecture uses Vercel for the frontend and Railway for the backend; no verified public demo URL is currently recorded. The repository excludes the private indicator dataset and all API credentials.

## Project Timeline and Role

- **November 2024 to January 2025:** a three-person academic research project on London's urban quality of life. I served as project lead. The research used PCA for composite evaluation and Moran's I, LISA, and Getis-Ord Gi* analysis for spatial patterns.
- **June 2026:** I independently designed and implemented the product platform, backend data pipeline, PCA-weighted TOPSIS analysis engine, interactive frontend, and provider-agnostic AI decision agent.

PCA-weighted TOPSIS belongs to the 2026 platform phase. It was not part of the original group research methodology.

## What the Product Does

1. Search for, hover over, or select a London borough on an interactive map.
2. Retrieve borough indicators and stored analysis results from FastAPI.
3. Present the overall score, London-wide rank, dimension scores, indicator profile, PCA contributions, and TOPSIS result.
4. Optionally enable AI Insights for the next analysis and ask the configured provider to interpret the supplied statistical result without recalculating it.
5. Continue with contextual questions or borough comparisons, then export a decision-ready PDF or editable Markdown report.

## Core Features

- MapLibre GL JS borough exploration with hover, selection, search, and camera reset
- English and Simplified Chinese interface
- Persisted, per-analysis AI Insights preference with basic-analysis fallback
- SQLite-backed borough, indicator, and analysis-result storage
- Explicit CSV import and database initialization scripts
- PCA-based objective weighting and TOPSIS ranking
- Structured `AnalysisInsights` generation
- Structured contextual chat (`ChatAnswer`) and borough comparison (`CompareAnswer`)
- Non-streaming thinking feedback and retryable chat/comparison errors
- Deterministic conversation PDF export from the current message history
- Charted A4 PDF report generation with Markdown as a secondary export
- OpenAI, Qwen, and DeepSeek provider strategies
- Token-free mock AI mode for UI development
- Responsive map, AI panel, and analysis workspace

## Architecture

```mermaid
flowchart LR
    CSV["Licensed indicator CSV"] --> Import["Python import script"]
    Import --> SQLite["SQLite"]
    SQLite --> Engine["PCA-TOPSIS analysis engine"]
    Engine --> SQLite
    SQLite --> API["FastAPI REST API"]
    API --> UI["React + MapLibre frontend"]
    API --> Context["Context and prompt builders"]
    Context --> Provider["Mock or live AI provider"]
    Provider --> API
```

The frontend never reads SQLite or the indicator CSV directly. The AI layer receives structured, stored results from the backend and is not allowed to calculate PCA, TOPSIS, or rankings.

## Technology Stack

| Layer | Technology |
| --- | --- |
| Frontend | React, TypeScript, Vite, Tailwind CSS, shadcn/ui |
| Mapping | MapLibre GL JS |
| Charts | Recharts |
| Localization | i18next, react-i18next |
| Backend | Python, FastAPI, Pydantic |
| Database | SQLite |
| Analysis | NumPy with a project-owned PCA-TOPSIS pipeline |
| AI | OpenAI Python SDK with OpenAI, Qwen, DeepSeek, and mock strategies |
| Tests | Python `unittest`, FastAPI TestClient, mocked provider calls |

## Data and Analysis

The importer validates this exact 15-column header. It expects one row per borough, with 12 benefit-oriented numeric indicator fields:

```text
Region,LAD code,Region name,GDHI per head of population (pounds),
Business Density per 1,000 Population (firms),
Average House Price/Earnings ratio_reverse,police_mean,
Convenient_service_mean,cultural_mean,meandical_mean,bus_new_mean,
ndvi_mean,wet_mean,landscape_index,Household Waste Recycling Rates (%)
```

The 2026 analysis engine standardizes the indicators, applies PCA to derive objective indicator weights, and uses those weights in TOPSIS to calculate closeness scores and ranks. The source CSV already provides reversed versions of cost-oriented indicators; the engine does not independently reverse those fields.

The original 2024-2025 research used POI, land use, Landsat, official statistics, and administrative-boundary inputs. Its spatial analysis included Global Moran's I, LISA, and Getis-Ord Gi*. Those spatial statistics informed the research project but are not recalculated by the current web platform.

### Data Licensing and Repository Policy

The research report references OpenStreetMap/Overpass Turbo, Impact Observatory/Esri Living Atlas land cover, USGS Landsat, London Datastore/ONS statistics, and UK Data Service boundary data. These upstream sources use different licences and attribution requirements.

The processed indicator CSV is private analytical data and is intentionally excluded from the public repository. The London borough boundary GeoJSON is sourced from [`radoi90/housequest-data`](https://github.com/radoi90/housequest-data), whose repository publishes the file under the MIT licence. Retain the upstream copyright and licence notice when redistributing the boundary file. Neither dataset is covered by any licence that may later be applied to the project software.

To run the complete analysis pipeline, prepare the private indicator data and local
working boundary at:

```text
data/london_indicators.csv
data/london_boroughs.geojson
```

The tracked browser copy is `public/data/london_boroughs.geojson`, accompanied by `public/data/LICENSE.housequest-data.txt`. The two GeoJSON paths currently contain the same `FeatureCollection`: `data/` is the canonical working copy and `public/data/` is the browser-served copy. Each feature must use `Polygon` or `MultiPolygon` geometry and include a `properties.name` value matching `Region name`. Missing browser GeoJSON is handled without crashing, but map polygons will not be available.

Relevant upstream terms should be checked before preparing data:

- [OpenStreetMap copyright and ODbL attribution](https://www.openstreetmap.org/copyright/en)
- [Impact Observatory Maps for Good, CC BY 4.0](https://docs.impactobservatory.com/lulc-maps/maps-for-good.html)
- [USGS Landsat public-domain guidance](https://www.usgs.gov/faqs/are-landsat-data-cloud-still-considered-be-within-public-domain)
- [ONS geography licences](https://www.ons.gov.uk/methodology/geography/licences)
- [UK Data Service 2011 Census geography boundaries](https://statistics.ukdataservice.ac.uk/dataset/2011-census-geography-boundaries-uk)

## AI Decision Agent

The provider layer implements a common strategy interface for structured analysis, chat, comparison, and plain-text legacy/report responses. The web AI switch selects basic analysis or AI Insights for the next analysis; the adjacent selector chooses DeepSeek or Qwen. `AI_PROVIDER` supplies the default when a request omits the provider. `AI_MODE=mock` prevents all external LLM calls, including explicit web AI requests; `AI_MODE=live` uses the selected configured provider.

Follow-up chat returns `ChatAnswer` with a response type, headline, summary, up to four key points, and optional bottom-line and limitation fields. Borough comparison returns `CompareAnswer` with both boroughs' advantages and positioning, a decision note, and up to three evidence rows. The frontend retains `content` for compatibility but renders the structured `answer` object when present.

Mock chat and comparison are dynamic rather than one fixed paragraph. The Mock builder reads the same server-built borough context, recognizes supported question intents such as strengths, weaknesses, ranking, and development direction, and creates evidence-bounded structured responses without an external call.

During a non-streaming chat or comparison request, the AI Panel displays a thinking state. If the request fails, the pending request is retained and the panel exposes a retry action. Retrying repeats that failed chat or comparison request without restarting the borough analysis.

For structured analysis, chat, and comparison, the provider is instructed to return JSON, the response is parsed defensively, and Pydantic validates it as `AnalysisInsights`, `ChatAnswer`, or `CompareAnswer`. The response envelopes retain plain `content` summaries where required for compatibility.

PDF export is a separate deterministic ReportLab pipeline. It combines the completed analysis metadata and structured insights already held by the frontend with authoritative indicators and persisted PCA/TOPSIS results reloaded by the backend. It does not make another LLM call. English reports use the standard PDF font stack; Simplified Chinese reports embed Noto Sans CJK SC, distributed under the font's included SIL Open Font License.

Conversation export posts the current ordered message history and any structured answer payloads to `POST /conversations/pdf`. ReportLab renders a bilingual conversation PDF and does not call the provider or recalculate analysis.

Markdown export follows the same completed-result principle. The frontend sends
completed metadata, structured insights and the current analysis-result snapshot to
`POST /ai/report`; the backend reloads authoritative SQLite context and renders the
Markdown locally without a second provider request. The legacy request shape remains
available for backwards compatibility, but the current UI does not use it.

The principal hallucination controls are:

- statistical results are loaded from SQLite, not invented by the model;
- the prompt clearly separates evidence from interpretation;
- the model is prohibited from recalculating scores or rankings;
- structured output is schema-validated;
- borough context is rebuilt server-side for each request;
- provider errors are sanitized before reaching the frontend.

These controls reduce risk but do not guarantee factual correctness. AI recommendations remain interpretive output and should be reviewed before use in real planning decisions.

## Project Structure

```text
backend/
  analysis/             PCA-TOPSIS analysis engine
  app/
    ai/                 agent, prompts, context, schemas, provider strategies
    database.py         SQLite connection and path resolution
    main.py             FastAPI application and routes
    repository.py       database queries
  scripts/              CSV import and analysis runners
  tests/                backend and provider tests
data/                   private indicator data and local geographic working copy
public/data/            attributed browser-served GeoJSON and upstream notice
specs/                  product, UI, data, backend, AI, and configuration specs
src/
  app/                  application orchestration and state
  components/           map, search, AI panel, analysis workspace, UI primitives
  i18n/                 English and Simplified Chinese resources
  lib/                  API client and utilities
  styles/               design tokens and global styles
  types/                shared frontend types
```

## Local Setup

### Prerequisites

- Node.js 20 or later
- pnpm
- Python 3.11 or later

### Frontend

```bash
pnpm install
pnpm run dev
```

The Vite development server normally runs at `http://127.0.0.1:5173`.

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

From the project root, initialize and import the database:

```bash
backend/.venv/bin/python -m backend.scripts.import_data \
  --csv data/london_indicators.csv
backend/.venv/bin/python -m backend.scripts.run_analysis
```

Start FastAPI from either location:

```bash
# Project root
backend/.venv/bin/python -m uvicorn app.main:app --app-dir backend --reload

# Or backend/
.venv/bin/python -m uvicorn app.main:app --reload
```

Both commands resolve the default database to `backend/urban_insight.db`.

## Environment Configuration

Use `backend/.env.example` as the template. Never expose keys through Vite variables or commit a populated `.env`.

```dotenv
AI_MODE=mock
AI_PROVIDER=deepseek
BACKEND_CORS_ORIGINS=
PORT=8000

OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini

DASHSCOPE_API_KEY=
QWEN_MODEL=
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

DEEPSEEK_API_KEY=
DEEPSEEK_MODEL=
DEEPSEEK_BASE_URL=https://api.deepseek.com

URBANINSIGHT_DB_PATH=
URBANINSIGHT_DATA_PATH=
URBANINSIGHT_DATA_BASE64=
```

Recommended workflow:

```text
UI development -> AI_MODE=mock -> no external LLM cost
AI integration testing -> AI_MODE=live -> configured provider
```

## Validation

```bash
# Frontend TypeScript compilation and production build
pnpm run build

# Backend compilation
backend/.venv/bin/python -m compileall backend

# Backend tests
PYTHONPATH=backend backend/.venv/bin/python -m unittest discover \
  -s backend/tests -v
```

External LLM calls are mocked in automated tests.

## API Summary

Core data endpoints:

- `GET /boroughs`
- `GET /boroughs/{id}`
- `GET /indicators/{borough_id}`
- `GET /analysis/{borough_id}`

AI endpoints:

- `GET /ai/status`
- `POST /ai/analyze`
- `POST /ai/chat`
- `POST /ai/compare`
- `POST /ai/report`
- `POST /reports/pdf`
- `POST /conversations/pdf`

Interactive API documentation is available at `http://127.0.0.1:8000/docs` while the backend is running.

## Current Limitations

- The processed indicator dataset is private, so a complete local setup requires that CSV to be supplied separately.
- The repository documents Vercel + Railway deployment, but does not currently record a verified public demo URL; the product is not production-hardened.
- SQLite and the local import workflow are intended for a single-user demonstration.
- Live AI behavior depends on provider availability, model access, quota, and supplied credentials.
- AI recommendations are decision support, not a substitute for domain review.
- The platform does not currently execute Moran's I, LISA, or hotspot analysis.
- No project software licence has been selected yet.

## Screenshots

No public screenshots are included yet. A future portfolio update can add verified application captures under [`docs/screenshots/`](./screenshots/).
