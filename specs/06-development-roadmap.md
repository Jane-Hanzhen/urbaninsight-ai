# Development Roadmap

## Overview

UrbanInsight AI was developed incrementally.

Milestones 1 through 6 are implemented.

This document records delivered scope and identifies the next valid development boundary.

Every future milestone must preserve deterministic statistical computation, provider-agnostic AI and the current API contracts.

---

# Milestone 1 — Project Foundation

Status

Complete

Delivered

- React 18
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui configuration
- Reusable Button, Card, Badge and Input components
- Application shell
- Design token theme
- Mock analysis model

---

# Milestone 2 — Interactive Map

Status

Complete

Delivered

- MapLibre GL JS
- Local London borough GeoJSON
- 33 borough boundaries
- Hover highlight and glow
- Borough tooltip
- Click selection
- Selected borough styling
- Camera fit
- Home camera reset
- AI Panel synchronization
- Missing-GeoJSON fallback
- Functional borough search

---

# Milestone 3 — Analysis Workspace

Status

Complete

Delivered

- Overview and score card
- Dimension cards
- Radar chart
- Contribution chart
- Indicator cards
- Main drivers
- Strengths
- Weaknesses
- Recommendations
- Report actions
- Responsive grids

---

# Milestone 4 — Backend & Database

Status

Complete

Delivered

- FastAPI backend
- SQLite schema initialization
- Stable database path resolution
- CSV import script
- Repository layer
- Borough endpoints
- Indicator endpoint
- Analysis result endpoint
- Frontend REST integration

The frontend no longer depends on mock borough or indicator data during normal operation.

---

# Milestone 5 — Analysis Engine

Status

Complete

Delivered

- NumPy evaluation pipeline
- Indicator validation
- Standardization
- PCA with 85% cumulative variance threshold
- PCA-derived indicator weights
- TOPSIS overall score
- Economic, Social and Ecological dimension scores
- Ordinal regional ranking
- Indicator and dimension contributions
- Persisted `analysis_results`
- Unit tests

The Analysis Engine runs through an explicit script.

It is not triggered by borough selection.

---

# Milestone 6 — AI Decision Agent

Status

Complete

Delivered

- Provider Strategy Pattern
- OpenAI provider
- Qwen provider through DashScope
- DeepSeek provider
- Mock AI provider
- `AI_MODE=mock|live`
- `AI_PROVIDER=openai|qwen|deepseek`
- Context Builder
- Prompt Builder
- Structured `AnalysisInsights`
- Follow-up chat
- Borough comparison
- Structured `ChatAnswer` and `CompareAnswer` contracts
- AI Panel thinking state and failed-request retry
- Dynamic context-aware Mock chat and comparison responses
- Conversation PDF export
- Markdown report generation
- AI status endpoint
- English and Simplified Chinese AI output
- Sanitized provider error logging
- Provider and endpoint tests with mocked external calls

The AI Agent interprets results rather than calculating them.

---

# Post-Milestone Enhancements

Implemented after Milestone 6

- English and Simplified Chinese fixed UI
- Browser language detection
- Language preference persistence
- Locale-aware AI requests
- Localized indicator labels
- Localized report filenames
- Compact map guidance overlay
- Initial experience polish
- Consistent idle and hover AI Panel structure
- Improved structured conversation-card layout

These enhancements are part of the current Version 1 baseline.

---

# Current Development Workflow

Initial setup

```text
Create Python environment
↓
Install backend requirements
↓
Install frontend packages
↓
Import CSV
↓
Run Analysis Engine
↓
Start FastAPI
↓
Start Vite
```

UI Development

```text
AI_MODE=mock
↓
No external LLM calls
↓
No LLM cost
↓
Stable bilingual responses
```

AI Testing

```text
AI_MODE=live
↓
Select AI_PROVIDER
↓
Configure provider API key
↓
Run real provider requests
```

See `09-configuration.md` for exact commands.

---

# Development Principles

Always follow the specifications under `/specs`.

Normative responsibility

- `00-architecture.md` → system boundaries
- `01-product.md` → user and product goals
- `02-ui.md` → interaction and visual behavior
- `03-data.md` → dataset and analytical data
- `04-design_tokens.md` → reusable visual tokens
- `05-pages.md` → current screen behavior
- `06-development-roadmap.md` → delivered and future scope
- `07-ai.md` → AI contracts
- `08-backend.md` → backend and API contracts
- `09-configuration.md` → environment and startup

When documents overlap, the more specialized specification wins.

Application code must not silently diverge from the specifications.

Documentation synchronization is part of completing a milestone.

---

# Next Milestone Boundary

No Milestone 7 is currently defined.

Potential future work must be specified before implementation.

Examples

- Production deployment
- Authentication and saved sessions
- PDF reporting
- Multi-city data
- Historical trends
- Accessibility audit
- Schema migration tooling
- End-to-end browser tests

These are not approved or implemented by this roadmap.

---

# Success Criteria

Every future milestone should:

- Compile successfully
- Keep frontend and backend independently runnable
- Preserve API compatibility unless explicitly versioned
- Preserve the Analysis Engine as the sole statistical authority
- Avoid exposing provider secrets
- Support Mock AI development
- Include tests proportional to risk
- Update `/specs` before completion
