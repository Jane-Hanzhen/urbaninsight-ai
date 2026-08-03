# UrbanInsight AI Deployment Guide

This guide documents the two deployment approaches implemented for UrbanInsight AI without embedding credentials or publishing the private indicator dataset:

- **Current public demo — ModelScope Studio:** a single-container deployment serving the React frontend and FastAPI backend from the same origin.
- **Decoupled full-stack deployment — Vercel + Railway:** the React frontend is deployed on Vercel, while the FastAPI backend runs on Railway.

Both approaches deploy the same product and core functionality. ModelScope is used as the current public-facing demo, while the Vercel + Railway setup is retained as an implemented reference architecture.

## Deployment Overview

| Deployment        | Architecture                            | Role                             |
| ----------------- | --------------------------------------- | -------------------------------- |
| ModelScope Studio | React + FastAPI in one Docker container | Current public demo              |
| Vercel + Railway  | Vercel frontend + Railway backend       | Implemented decoupled deployment |

## Vercel + Railway Architecture

```text
Vercel
  React + Vite frontend
  public/data/london_boroughs.geojson
        ↓ HTTPS
Railway
  FastAPI + Uvicorn
  precomputed SQLite analysis database
        ↓ optional
Mock, DeepSeek, or Qwen provider
```

The current public demo uses the ModelScope single-container deployment documented below.

The Vercel + Railway configuration remains available as the decoupled deployment option:

- Frontend: Vercel
- Backend: Railway
- Database: generated, read-mostly SQLite
- AI: `AI_MODE=mock` by default

## Prerequisites

- Node.js 22.13 or later
- pnpm 11.18.0
- Python 3.11 or later
- Private indicator CSV matching the documented schema
- London borough GeoJSON from the attributed public source
- A public HTTPS domain for the backend
- A public HTTPS domain for the frontend

Do not commit the private indicator CSV. The browser-served borough boundary must retain the upstream attribution and MIT licence notice described below.

## Frontend Deployment

### Framework and build

| Setting             | Value            |
| ------------------- | ---------------- |
| Framework           | React + Vite     |
| Install command     | `pnpm install`   |
| Build command       | `pnpm run build` |
| Output directory    | `dist`           |
| Recommended runtime | Node.js 22.13+   |

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

### Railway service settings

| Setting           | Value                             |
| ----------------- | --------------------------------- |
| Root Directory    | `backend`                         |
| Build Command     | `pip install -r requirements.txt` |
| Start Command     | `bash start.sh`                   |
| Health Check Path | `/health`                         |

Railway supplies `PORT` at runtime. The startup script requires it and binds Uvicorn to `0.0.0.0:$PORT`.

### Runtime and commands

| Setting      | Value                      |
| ------------ | -------------------------- |
| Runtime      | Python 3.11+               |
| Requirements | `backend/requirements.txt` |
| Health check | `GET /health`              |
| Application  | `app.main:app`             |

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

The public GitHub repository does not contain `london_indicators.csv`. Inject the private dataset through a Railway Volume/private file workflow, or use the Base64 variable option below. Never add the source CSV to the repository or a frontend variable.

#### Railway Base64 injection

If a Railway Volume or private file mount is unavailable, store the small
portfolio CSV as a private Railway service variable instead of committing it to
GitHub:

```env
URBANINSIGHT_DATA_PATH=/data/london_indicators.csv
URBANINSIGHT_DB_PATH=/data/urban_insight.db
URBANINSIGHT_DATA_BASE64=<base64-encoded CSV>
```

When `URBANINSIGHT_DATA_BASE64` is present, `backend/start.sh` decodes it to
`URBANINSIGHT_DATA_PATH` before running the existing import and analysis flow.
If the variable is absent, startup continues to use the file already available
at `URBANINSIGHT_DATA_PATH`.

Generate a single-line value locally without modifying the source CSV:

```bash
python -c 'import base64, pathlib; print(base64.b64encode(pathlib.Path("data/london_indicators.csv").read_bytes()).decode())'
```

Add the output as the private `URBANINSIGHT_DATA_BASE64` variable in Railway.
Do not paste the encoded value into Git, logs, documentation, or frontend
variables. Base64 is an encoding, not encryption; its confidentiality depends
on Railway variable access controls.

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
{ "status": "ok" }
```

### Backend environment variables

```env
AI_MODE=mock
AI_PROVIDER=deepseek
BACKEND_CORS_ORIGINS=https://urbaninsight-ai.vercel.app
URBANINSIGHT_DATA_PATH=/data/london_indicators.csv
URBANINSIGHT_DB_PATH=/data/urban_insight.db
PORT=8000
```

Railway normally injects `PORT`; the shown value is only an example for local parity. Add `URBANINSIGHT_DATA_BASE64` when using variable-based CSV injection. Live mode additionally requires the selected provider's API key, model, and optional base URL.

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
URBANINSIGHT_DATA_PATH=/data/london_indicators.csv
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
- follow-up chat and comparison use dynamic local responses derived from the current borough contexts and supported question intent;
- Markdown and PDF exports render deterministically from the completed analysis and do not call an LLM;
- the selected Provider name remains in response metadata for UI continuity;
- the response model is reported as `urbaninsight-mock`;
- no Provider-unavailable warning is expected from missing keys;
- no paid model request is made.

Mock responses follow the same structured `ChatAnswer` and `CompareAnswer` contracts as Live mode. This keeps thinking, retry, comparison cards, and conversation export testable without provider tokens.

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

| File                                  | Purpose                                                    | Must be public?                                                      | Git status | Deployment and licensing notes                                                                                          |
| ------------------------------------- | ---------------------------------------------------------- | -------------------------------------------------------------------- | ---------- | ----------------------------------------------------------------------------------------------------------------------- |
| `data/london_indicators.csv`          | Backend import source for borough indicators               | Not as a direct download, but its values are exposed through the API | Ignored    | Redistribution and derived-data exposure require a provenance and rights review before a public demo.                   |
| `data/london_boroughs.geojson`        | Canonical local borough-boundary working copy              | No                                                                   | Ignored    | Local duplicate of the attributed browser boundary.                                                                     |
| `public/data/london_boroughs.geojson` | Browser-served map geometry                                | Yes, because Vercel serves it to every visitor                       | Tracked    | Source: `radoi90/housequest-data`; the adjacent upstream MIT notice is retained.                                        |
| `backend/urban_insight.db`            | Generated borough, indicator, and analysis-result database | Not as a downloadable file                                           | Ignored    | May be generated during deployment or stored on a volume; public API responses still require source-data rights review. |

Current conclusions:

- the processed indicator CSV remains private and untracked;
- the canonical working GeoJSON is ignored; the browser-served copy and its upstream notice are tracked;
- the borough boundary source is [`radoi90/housequest-data`](https://github.com/radoi90/housequest-data), published under its upstream MIT licence;
- deployment must inject the private CSV and prepare the attributed browser GeoJSON before build/startup;
- third-party data remains outside the scope of any UrbanInsight AI software licence.

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

- [ ] Inject the private indicator CSV without committing it.
- [ ] Confirm the tracked frontend GeoJSON and `LICENSE.housequest-data.txt` are present in the Vercel build.
- [ ] Initialize SQLite with `import_data` and `run_analysis`.
- [ ] Set `URBANINSIGHT_DB_PATH` to the generated or mounted database.
- [ ] Deploy the backend and verify `/health`.
- [ ] Set `VITE_API_URL` to the backend HTTPS URL.
- [ ] Add the final frontend Origin to `BACKEND_CORS_ORIGINS`.
- [ ] Deploy the frontend and verify API requests in a browser.
- [ ] Keep the public demo on `AI_MODE=mock` with no real keys.
- [ ] Verify analysis, structured chat, structured comparison, retry, analysis PDF, conversation PDF, and Markdown flows.
- [ ] Keep the public demo link and deployment status consistent across the project README and Portfolio website.

## ModelScope Docker Deployment — Current Public Demo

The current public-facing UrbanInsight AI demo uses this single-container ModelScope deployment.

The multi-stage `Dockerfile` builds the Vite frontend with Node, installs the FastAPI runtime with Python, and copies only the compiled frontend into the final image. Uvicorn listens on `0.0.0.0:7860`; FastAPI serves both the API and the React SPA, so the production frontend uses same-origin API requests.

### Required ModelScope variable

Configure the compressed value as four separate secrets in the ModelScope Space
settings. All four variables are required for chunked mode:

```env
URBANINSIGHT_DATA_GZIP_BASE64_PART_1=<characters 1-1000>
URBANINSIGHT_DATA_GZIP_BASE64_PART_2=<characters 1001-2000>
URBANINSIGHT_DATA_GZIP_BASE64_PART_3=<characters 2001-3000>
URBANINSIGHT_DATA_GZIP_BASE64_PART_4=<characters 3001-4000>
```

If any PART variable is configured, all four must be present; incomplete PART
configuration fails safely instead of falling back. When all four are present,
they are joined strictly in PART_1 through PART_4 order.

`URBANINSIGHT_DATA_GZIP_BASE64` remains supported as the second-priority
single-secret compressed format. `URBANINSIGHT_DATA_BASE64` remains supported
only as the final backward-compatible uncompressed fallback.

On macOS, run this command from the repository root to compress the ignored
private CSV and copy each segment directly to the clipboard without printing
secret content in Terminal. Run one command, paste the clipboard into its
matching ModelScope variable, then continue with the next command:

```bash
gzip -c data/london_indicators.csv | base64 | tr -d '\n' | cut -c 1-1000 | pbcopy
gzip -c data/london_indicators.csv | base64 | tr -d '\n' | cut -c 1001-2000 | pbcopy
gzip -c data/london_indicators.csv | base64 | tr -d '\n' | cut -c 2001-3000 | pbcopy
gzip -c data/london_indicators.csv | base64 | tr -d '\n' | cut -c 3001-4000 | pbcopy
```

Each segment is at most 1000 characters. Concatenating the four clipboard values
in order reproduces the complete gzip Base64 value exactly. Do not paste any
segment into source files, shell scripts, documentation, build arguments, or
logs.

Do not add the CSV, compressed data, either Base64 value, a `.env` file, SQLite
database, or any AI credential to the repository. The startup script decodes
and decompresses the CSV to
`/tmp/urbaninsight/london_indicators.csv`, recreates
`/tmp/urbaninsight/urban_insight.db`, runs PCA-TOPSIS, and then starts the app.
Neither secret value nor CSV contents are written to logs. Invalid compressed
data fails before the destination CSV is replaced.

The image defaults to:

```env
AI_MODE=mock
URBANINSIGHT_DATA_PATH=/tmp/urbaninsight/london_indicators.csv
URBANINSIGHT_DB_PATH=/tmp/urbaninsight/urban_insight.db
URBANINSIGHT_FRONTEND_DIST=/app/frontend_dist
```

No `VITE_API_URL`, CORS origin, real AI key, or `PORT` variable is required for
ModelScope. Keep `AI_MODE=mock`; the container always listens on port 7860.
For local Vite development, an unset `VITE_API_URL` still targets
`http://127.0.0.1:8000`; it may be overridden locally when needed.

### Local Docker verification

Build and run with the private dataset supplied only through the environment:

```bash
docker build -t urbaninsight-modelscope:local .
docker run --rm -p 7860:7860 \
  -e URBANINSIGHT_DATA_GZIP_BASE64='<compressed Base64 value>' \
  urbaninsight-modelscope:local
```

Verify `/health`, `/`, an API route such as `/boroughs`, and a client-side route
such as `/workspace`. Stop the test container when verification is complete.

### ModelScope upload

Create a Docker-based Space, then upload the project files while preserving
`.dockerignore` and `.gitignore`. Do not upload ignored private or generated
files. Add all four `URBANINSIGHT_DATA_GZIP_BASE64_PART_1` through
`URBANINSIGHT_DATA_GZIP_BASE64_PART_4` variables in the Space secret settings
and trigger the Docker build. The platform should route traffic to container
port 7860.
