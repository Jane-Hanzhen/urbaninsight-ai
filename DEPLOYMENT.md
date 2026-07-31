# UrbanInsight AI Deployment Guide

This guide prepares the portfolio demo for deployment without embedding credentials or redistributing unreviewed data. It does not represent an active deployment.

## Deployment Architecture

```text
Vercel
  React + Vite frontend
  public/data/london_boroughs.geojson
        ↓ HTTPS
Python web service
  FastAPI + Uvicorn
  precomputed SQLite analysis database
        ↓ optional
Mock, DeepSeek, or Qwen provider
```

Recommended first public-demo configuration:

- Frontend: Vercel
- Backend: Render or another Python ASGI host
- Database: precomputed, read-mostly SQLite
- AI: `AI_MODE=mock`

## Prerequisites

- Node.js 20 or later
- pnpm
- Python 3.11 or later
- Appropriately licensed indicator CSV and borough GeoJSON
- A public HTTPS domain for the backend
- A public HTTPS domain for the frontend

Do not deploy the current local data until its provenance, attribution, and redistribution rights have been confirmed.

## Frontend Deployment

### Framework and build

| Setting | Value |
| --- | --- |
| Framework | React + Vite |
| Install command | `pnpm install` |
| Build command | `pnpm run build` |
| Output directory | `dist` |
| Recommended runtime | Node.js 20+ |

The production build reads the backend base URL from:

```env
VITE_API_URL=https://your-backend.example.com
```

Do not include a trailing slash. Vite injects this value at build time, so changing it requires a new frontend deployment.

If `VITE_API_URL` is omitted, the client falls back to `http://127.0.0.1:8000`, which is not valid for a public deployment.

### Vercel steps

1. Import the GitHub repository into Vercel.
2. Select the Vite framework preset.
3. Keep the repository root as the project root.
4. Confirm `pnpm run build` and output directory `dist`.
5. Add `VITE_API_URL` for Preview and Production as appropriate.
6. Ensure an approved `public/data/london_boroughs.geojson` exists in the deployment build context.
7. Deploy only after the backend is reachable over HTTPS.
8. Add the final Vercel Origin to `BACKEND_CORS_ORIGINS` and restart the backend.

The map fetches `/data/london_boroughs.geojson` from the frontend origin. The backend does not serve this file.

## Backend Deployment

### Runtime and commands

| Setting | Value |
| --- | --- |
| Runtime | Python 3.11+ |
| Requirements | `backend/requirements.txt` |
| Health check | `GET /health` |
| Application | `app.main:app` |

From the repository root, install dependencies with:

```bash
pip install -r backend/requirements.txt
```

Start the service with:

```bash
bash backend/start.sh
```

The startup script resolves the backend directory independently of the process
working directory, validates its required environment variables, and runs the
deployment pipeline in order:

```text
Private CSV
    ↓
SQLite generation
    ↓
PCA-TOPSIS
    ↓
FastAPI
```

If importing or analyzing the dataset fails, `set -e` prevents FastAPI from
starting.

### Private Dataset Configuration

The public GitHub repository does not contain `london_indicators.csv`. Provide
the private dataset to the Render backend as a Secret File instead of adding it
to the repository.

Configure the Secret File in the Render Dashboard with:

```text
Filename:
london_indicators.csv

Runtime path:
/etc/secrets/london_indicators.csv
```

Point the import process at the runtime file:

```env
URBANINSIGHT_DATA_PATH=/etc/secrets/london_indicators.csv
```

At startup, `backend/start.sh` runs the private-data pipeline in order:

```text
Private CSV
    ↓
SQLite generation
    ↓
PCA-TOPSIS analysis
    ↓
FastAPI API
```

Configure the platform health-check path as:

```text
/health
```

Expected response:

```json
{"status":"ok"}
```

### Backend environment variables

```env
AI_MODE=mock
AI_PROVIDER=deepseek
BACKEND_CORS_ORIGINS=https://urbaninsight-ai.vercel.app
URBANINSIGHT_DATA_PATH=/etc/secrets/london_indicators.csv
URBANINSIGHT_DB_PATH=urban_insight.db
```

`BACKEND_CORS_ORIGINS` accepts a comma-separated list of exact HTTP or HTTPS Origins:

```env
BACKEND_CORS_ORIGINS=https://urbaninsight-ai.vercel.app,https://preview.example.com
```

Rules:

- local development Origins remain enabled automatically;
- `*` is rejected;
- paths, queries, and fragments are rejected;
- replace the example domain with the actual frontend Origin;
- do not add a trailing slash.

## Database

### Current strategy

The backend uses SQLite. Application startup creates missing tables, but it does not import indicators or calculate analysis results.

The startup script performs the complete initialization order:

```bash
bash backend/start.sh
```

The private CSV path and generated database path are configured with:

```env
URBANINSIGHT_DATA_PATH=/etc/secrets/london_indicators.csv
URBANINSIGHT_DB_PATH=urban_insight.db
```

Relative paths are resolved against `backend/`. An absolute path can be used for a mounted volume:

```env
URBANINSIGHT_DB_PATH=/var/data/urban_insight.db
```

### Public-demo options

#### Build-time SQLite

Best for a read-only portfolio demo when an approved dataset is available during the build:

1. install dependencies;
2. provide the licensed CSV securely in the build context;
3. run `import_data`;
4. run `run_analysis`;
5. start the API with the generated database.

The database is regenerated on each deployment. No runtime persistence is required if the application remains read-only.

#### Persistent-volume SQLite

Use a persistent volume if data will be updated at runtime or must survive independent service rebuilds. Point `URBANINSIGHT_DB_PATH` at the mounted path and initialize it once after the volume is available.

Do not run multiple writable application replicas against one SQLite file. A future multi-instance or write-heavy version should migrate to a managed relational database, which is outside the current portfolio-demo scope.

## AI Configuration

### Public demo: Mock mode

```env
AI_MODE=mock
AI_PROVIDER=deepseek
```

Do not configure real Provider keys for the Mock deployment.

In Mock mode:

- selecting Qwen or DeepSeek in the UI does not create an external API client;
- structured AI analysis uses local Mock responses;
- follow-up chat, comparison, and Markdown reports use local Mock responses;
- the selected Provider name remains in response metadata for UI continuity;
- the response model is reported as `urbaninsight-mock`;
- no Provider-unavailable warning is expected from missing keys;
- no paid model request is made.

### Live mode: DeepSeek

```env
AI_MODE=live
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=
DEEPSEEK_MODEL=
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

### Live mode: Qwen

```env
AI_MODE=live
AI_PROVIDER=qwen
DASHSCOPE_API_KEY=
QWEN_MODEL=
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

The Qwen credential is named `DASHSCOPE_API_KEY`, not `QWEN_API_KEY`.

Provider keys must be entered in the backend hosting platform's secret manager. Never expose them through Vite variables, frontend code, Git, logs, or documentation.

If the public UI should demonstrate switching between Qwen and DeepSeek in Live mode, configure both providers. Otherwise, an unconfigured Live provider safely falls back to basic analysis for the initial analysis request.

## Data deployment checklist

| File | Purpose | Must be public? | Git status | Deployment and licensing notes |
| --- | --- | --- | --- | --- |
| `data/london_indicators.csv` | Backend import source for borough indicators | Not as a direct download, but its values are exposed through the API | Ignored | Redistribution and derived-data exposure require a provenance and rights review before a public demo. |
| `data/london_boroughs.geojson` | Canonical local borough-boundary working copy | No, if the approved browser copy is prepared separately | Ignored | Current compiled artifact lacks sufficient field-level licensing metadata for publication. |
| `public/data/london_boroughs.geojson` | Browser-served map geometry | Yes, because Vercel serves it to every visitor | Ignored | A reviewed, appropriately licensed copy with required attribution is mandatory for the public map. |
| `backend/urban_insight.db` | Generated borough, indicator, and analysis-result database | Not as a downloadable file | Ignored | May be generated during deployment or stored on a volume; public API responses still require source-data rights review. |

Current conclusions:

- all three source-data files exist locally;
- none is tracked by Git;
- no file was downloaded, replaced, or modified during deployment preparation;
- the existing compiled artifacts are not yet approved for public deployment;
- a public demo remains blocked until an appropriately licensed dataset is prepared.

## Local Validation

Backend:

```bash
cd backend
../backend/.venv/bin/python -m pytest tests -v
```

Or from the repository root:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests -v
```

Frontend:

```bash
pnpm run build
```

Automated tests use Mock Provider calls and must not contact paid LLM APIs.

## Pre-deployment checklist

- [ ] Confirm CSV and GeoJSON redistribution rights and attribution.
- [ ] Provide an approved frontend GeoJSON build artifact.
- [ ] Initialize SQLite with `import_data` and `run_analysis`.
- [ ] Set `URBANINSIGHT_DB_PATH` to the generated or mounted database.
- [ ] Deploy the backend and verify `/health`.
- [ ] Set `VITE_API_URL` to the backend HTTPS URL.
- [ ] Add the final frontend Origin to `BACKEND_CORS_ORIGINS`.
- [ ] Deploy the frontend and verify API requests in a browser.
- [ ] Keep the public demo on `AI_MODE=mock` with no real keys.
- [ ] Verify analysis, chat, comparison, PDF, and Markdown flows.
- [ ] Add the verified demo URL to both portfolio READMEs.
