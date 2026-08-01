# Configuration Specification

## Overview

UrbanInsight AI has independent frontend and backend configuration.

Backend configuration is loaded from:

```text
backend/.env
```

Existing process environment values take precedence over values in this file.

The safe template is:

```text
backend/.env.example
```

Frontend configuration uses Vite environment variables.

Never commit real secrets.

---

# Backend Environment Variables

## AI_MODE

Allowed values

- `mock`
- `live`

Default

```text
live
```

Recommended development value

```text
mock
```

Mock mode prevents every external LLM call, including an explicit web
`/ai/analyze` request with `include_ai_insights=true`. The backend returns local Mock
insights while preserving the request provider in response metadata for UI
continuity. This is the required mode for token-free UI development and demos.

## AI_PROVIDER

Allowed live values

- `openai`
- `qwen`
- `deepseek`

Default in live mode

```text
openai
```

This value does not create a live client in Mock mode, but remains the default
provider label when the request omits `ai_provider`.

In Live mode, `AI_PROVIDER` is the default when the request does not include
`ai_provider`. The public UI may explicitly select `deepseek` or `qwen`; the backend
strategy layer also retains OpenAI support.

---

# OpenAI Configuration

## OPENAI_API_KEY

Required when:

```text
AI_MODE=live
AI_PROVIDER=openai
```

## OPENAI_MODEL

Default

```text
gpt-4o-mini
```

OpenAI uses the SDK default API base URL.

---

# Qwen Configuration

## DASHSCOPE_API_KEY

Required when:

```text
AI_MODE=live
AI_PROVIDER=qwen
```

This is the only Qwen API key variable used by the implementation.

`QWEN_API_KEY` is obsolete and ignored.

## QWEN_MODEL

Default

```text
qwen3.7-plus
```

## QWEN_BASE_URL

Default

```text
https://dashscope.aliyuncs.com/compatible-mode/v1
```

---

# DeepSeek Configuration

## DEEPSEEK_API_KEY

Required when:

```text
AI_MODE=live
AI_PROVIDER=deepseek
```

## DEEPSEEK_MODEL

Default

```text
deepseek-v4-flash
```

## DEEPSEEK_BASE_URL

Default

```text
https://api.deepseek.com
```

---

# Database Configuration

## URBANINSIGHT_DB_PATH

Default

```text
backend/urban_insight.db
```

Recommended value in `backend/.env`

```text
urban_insight.db
```

Relative values resolve against the backend directory.

These values resolve to the same file:

```text
urban_insight.db
backend/urban_insight.db
```

Absolute paths are supported.

The final absolute path is logged during FastAPI startup.

---

# Frontend Configuration

## VITE_API_URL

Default

```text
http://127.0.0.1:8000
```

Use this variable when the backend runs elsewhere.

Example

```text
VITE_API_URL=http://127.0.0.1:8011
```

Vite exposes variables prefixed with `VITE_` to the browser.

Never place provider API keys in a `VITE_` variable.

---

# Recommended .env Template

```dotenv
AI_MODE=mock
AI_PROVIDER=deepseek

OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini

DASHSCOPE_API_KEY=
QWEN_MODEL=qwen3.7-plus
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

DEEPSEEK_API_KEY=
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_BASE_URL=https://api.deepseek.com

URBANINSIGHT_DB_PATH=urban_insight.db
```

`AI_PROVIDER` may remain set while `AI_MODE=mock`.

It is ignored until live mode is enabled.

---

# Initial Setup

## Backend Environment

From the project root:

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
```

Create local configuration:

```bash
cp backend/.env.example backend/.env
```

Do not overwrite an existing `.env` containing local secrets.

## Frontend Packages

The repository uses a pnpm lockfile.

Recommended:

```bash
pnpm install
```

`npm install` is also possible but should not replace or churn the committed lockfile without an explicit package-manager decision.

---

# Data Preparation

Import the current CSV:

The CSV is a local runtime input and is excluded from the public repository pending
verification of redistribution rights. Prepare an appropriately licensed file matching
the schema in `03-data.md` before running this command.

```bash
backend/.venv/bin/python backend/scripts/import_data.py
```

Run statistical analysis:

```bash
backend/.venv/bin/python backend/scripts/run_analysis.py
```

Expected Version 1 state:

- 33 borough rows
- 33 indicator rows
- 33 analysis result rows

These scripts should be rerun when the source CSV changes.

---

# Start Backend

From project root:

```bash
backend/.venv/bin/python -m uvicorn app.main:app \
  --app-dir backend \
  --host 127.0.0.1 \
  --port 8000 \
  --reload
```

From `backend/` with the environment activated:

```bash
uvicorn app.main:app \
  --host 127.0.0.1 \
  --port 8000 \
  --reload
```

Health check:

```text
http://127.0.0.1:8000/health
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

---

# Start Frontend

From project root:

```bash
pnpm run dev
```

The Vite server is configured as:

```text
host: 127.0.0.1
port: 5173
strictPort: true
```

Frontend URL:

```text
http://127.0.0.1:5173
```

Because `strictPort` is enabled, Vite exits instead of silently switching ports when 5173 is occupied.

---

# UI Development Mode

Use:

```dotenv
AI_MODE=mock
```

Workflow

```text
Start FastAPI
↓
Start Vite
↓
Select boroughs
↓
Receive realistic mock AI responses
↓
No external LLM calls
↓
No LLM cost
```

Mock mode still requires:

- Valid SQLite borough data
- Valid indicator data
- Persisted analysis results

The Context Builder runs before the Mock Provider.

---

# Live AI Testing Mode

Use:

```dotenv
AI_MODE=live
AI_PROVIDER=deepseek
```

or:

```dotenv
AI_MODE=live
AI_PROVIDER=qwen
```

or:

```dotenv
AI_MODE=live
AI_PROVIDER=openai
```

Set only the API key required by the active provider.

Restart FastAPI after changing backend environment variables.

Verify configuration:

```text
GET /ai/status
```

Live mode may consume paid provider tokens.

---

# Production Mode

The documented release architecture uses Vercel for the React frontend and Railway
for the FastAPI backend. Railway uses root directory `backend`, build command
`pip install -r requirements.txt`, and start command `bash start.sh`.

Production configuration must specify:

- Process manager
- Reverse proxy or hosting platform
- Production frontend API URL
- CORS origins
- Secret storage
- HTTPS
- Authentication requirements
- Rate limiting
- Database backup strategy
- SQLite concurrency expectations
- Logging and monitoring

The current portfolio deployment does not add authentication, rate limiting, a
managed database, or multi-instance SQLite writes. See `DEPLOYMENT.md` for the
authoritative platform configuration and private-data injection workflow.

---

# Validation Commands

Frontend build and TypeScript:

```bash
pnpm run build
```

Backend compilation:

```bash
backend/.venv/bin/python -m compileall -q backend/app backend/analysis backend/scripts
```

Backend tests:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m unittest discover \
  -s backend/tests \
  -v
```

There are currently no separate frontend `lint` or `typecheck` scripts.

The frontend build includes:

```text
tsc -b
```

---

# Security Rules

- Keep `backend/.env` local
- Keep real API keys out of source
- Keep keys out of tests
- Never expose keys through the frontend
- Never add keys to `VITE_` variables
- Use `.env.example` with empty placeholders
- Review logs before sharing them
- Prefer Mock AI for routine frontend development
