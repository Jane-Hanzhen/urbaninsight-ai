# System Architecture

## Overview

UrbanInsight AI is composed of five cooperating modules.

Each module has a single responsibility.

The architecture separates statistical computation from AI interpretation.

Large Language Models are never responsible for mathematical calculations.

SQLite is the authoritative store for borough data, indicators and analysis results.

---

# Architecture

```text
                User
                  │
                  ▼
       React + TypeScript Application
                  │
                  ▼
             FastAPI REST API
          ┌───────┴────────┐
          │                │
          ▼                ▼
       SQLite        AI Decision Agent
          │                │
          ▼                │
   Analysis Engine ────────┘
          │
          ▼
   Persisted Statistical Results
```

The browser never reads SQLite or the indicator CSV directly.

The AI Agent never reads the CSV and never recalculates statistical results.

---

# Module Responsibilities

## React Web Application

Implemented with React, TypeScript and Vite.

Responsibilities

- Interactive London borough map
- Borough search and selection
- AI Panel state machine
- Analysis Workspace
- Charts and indicator cards
- Follow-up conversation
- Borough comparison controls
- Structured chat and comparison rendering
- Thinking, recoverable error and retry states
- Conversation PDF download
- Markdown report download
- English and Simplified Chinese interface

The frontend reads all borough, indicator, statistical and AI data through FastAPI.

The frontend never performs PCA, TOPSIS or ranking.

---

## FastAPI Backend

Responsibilities

- Initialize the SQLite schema at startup
- Expose borough, indicator and analysis REST endpoints
- Build authoritative AI context
- Validate `AnalysisInsights`, `ChatAnswer` and `CompareAnswer` request/response schemas
- Select mock or live AI mode
- Select the configured live provider
- Sanitize provider failures

FastAPI is the only application boundary between the browser and backend data.

---

## SQLite Database

Responsibilities

- Store 33 London borough records
- Store 12 processed indicators per borough
- Store PCA-weighted TOPSIS results
- Store contribution and PCA metadata as JSON

The default database is:

```text
backend/urban_insight.db
```

Relative database paths are resolved against the backend directory rather than the current working directory.

---

## Analysis Engine

Implemented in Python with NumPy.

Responsibilities

- Read indicators from SQLite
- Validate the evaluation matrix
- Standardize indicators
- Fit PCA
- Derive indicator weights
- Run TOPSIS
- Calculate dimension scores
- Generate ordinal rankings
- Calculate indicator and dimension contributions
- Persist results to SQLite

The Analysis Engine is run explicitly through the backend script.

Selecting a borough reads previously persisted results.

It does not run the Analysis Engine on every click.

---

## AI Decision Agent

Responsibilities

- Build selected-borough context
- Interpret immutable analysis results
- Explain rankings
- Compare boroughs
- Interpret indicators
- Identify strengths and weaknesses
- Generate recommendations
- Answer follow-up questions
- Generate deterministic Markdown, analysis PDF and conversation PDF exports

The provider layer uses the Strategy Pattern.

Supported live providers

- OpenAI
- Qwen through Alibaba Cloud DashScope
- DeepSeek

Supported modes

- `mock`
- `live`

See `07-ai.md` for the complete AI contract.

---

# Workflow

Backend data preparation

```text
CSV
↓
Import Script
↓
SQLite indicators
↓
Analysis Engine
↓
SQLite analysis_results
```

Application startup

```text
FastAPI loads backend/.env
↓
Resolve and initialize SQLite
↓
Log the resolved database path
↓
React requests boroughs
↓
Display London map and idle AI Panel
```

Borough interaction

```text
User hovers a borough
↓
Map and AI Panel synchronize hover state
↓
User clicks or searches for a borough
↓
Frontend requests indicators and stored analysis
↓
Frontend posts the frozen AI Insights preference to /ai/analyze
↓
AI disabled: return the basic statistical analysis without provider access
AI enabled: Mock or live provider returns AnalysisInsights
AI unavailable: preserve the basic analysis and return an unavailable status
↓
Analysis Workspace becomes visible
↓
User may ask, compare, retry a failed request, export the conversation or generate an analysis report
```

---

# Source Of Truth

The source-of-truth order is:

1. SQLite for borough, indicator and statistical data
2. Analysis Engine for mathematical computation
3. FastAPI response schemas for runtime contracts
4. AI Agent for interpretation only
5. React state for the current browser interaction

The CSV is the import source.

It is not queried at runtime.

---

# Design Principle

Statistics are deterministic.

AI is interpretative.

Providers are replaceable.

The frontend is provider-agnostic.

The system combines these principles to create an explainable urban analysis platform.
