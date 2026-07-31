# UrbanInsight AI — Public Project Archive

[Portfolio overview](../README.md) | [简体中文首页](../README.zh-CN.md) | [Technical Guide](./TECHNICAL_GUIDE.md)

## Document Scope

This is the public, portfolio-safe project archive for UrbanInsight AI. It consolidates the product context, design rationale, delivery scope, technical evolution, contribution boundaries, and current limitations that are supported by the repository.

The original internal working archive and research materials remain outside the public repository. They are not reproduced here because some historical statements are outdated and the source research report and compiled datasets require separate publication and redistribution review.

## Executive Summary

UrbanInsight AI is a map-first urban decision intelligence platform for London borough exploration and comparison. It turns borough-level indicators and deterministic statistical results into an experience that combines spatial discovery, evidence review, AI interpretation, contextual comparison, and exportable reports.

The core product principle is:

> **Evidence first, interpretation second.**

The statistical engine owns calculations. The AI layer explains supplied results but cannot recalculate PCA or TOPSIS, invent ranks, or replace the evidence used to produce them.

## Project Evolution and Ownership

### November 2024 to January 2025 — academic research

- Three-person project on London's urban quality of life
- My role: project lead
- Methods included PCA for composite evaluation and Moran's I, LISA, and Getis-Ord Gi* for spatial analysis
- Inputs included POI, land use, Landsat, official statistics, and administrative boundaries

This work established the research and indicator foundation. It must not be represented as an individually completed project.

### June 2026 — independent productization

I independently designed and implemented:

- product strategy and end-to-end workflow;
- UX, interaction model, and bilingual experience;
- backend import and persistence pipeline;
- PCA-weighted TOPSIS analysis engine;
- React and MapLibre frontend;
- provider-agnostic AI decision agent;
- contextual chat and borough comparison;
- deterministic PDF and editable Markdown reporting.

PCA-weighted TOPSIS belongs to this 2026 productization phase. TOPSIS was not part of the original group research methodology.

## Problem Definition

Traditional regional analysis often requires separate steps for data preparation, statistical modelling, mapping, interpretation, comparison, and report writing. This creates several product problems:

- data and evidence are fragmented across tools;
- statistical methods are difficult for non-specialists to interpret;
- a composite score explains the outcome but not necessarily its drivers;
- comparison workflows are manual and inconsistent;
- dense dashboards can increase cognitive load;
- report preparation happens outside the analysis experience.

The product question was:

> How might complex urban indicators become an understandable, comparable, and decision-ready exploration experience?

## Product Strategy

### Map-first discovery

The map supplies spatial context and makes borough discovery and selection the natural first action.

### Progressive evidence

The interface reveals scores, ranks, dimensions, indicators, and contributions after a borough is selected instead of presenting a static wall of metrics.

### Deterministic analysis

PCA-weighted TOPSIS runs independently of the LLM. Results are persisted so the same underlying analysis can be reused consistently by the API, frontend, and AI layer.

### AI-guided interpretation

AI translates structured evidence into strengths, weaknesses, comparisons, and interpretive recommendations while remaining bounded by the supplied context.

### Decision-ready output

The workflow ends in exportable reports rather than stopping at exploration.

## Intended Users and Tasks

The current portfolio concept is relevant to:

- urban and regional analysts;
- planning and public-sector teams;
- researchers and students;
- commercial or strategy analysts working with location evidence.

The repository does not claim these groups as validated production customers. Their core tasks are represented in the implemented workflow:

- find and select a borough;
- understand its score, rank, and dimensional profile;
- identify influential indicators and contributions;
- ask contextual follow-up questions;
- compare two boroughs on the same evidence basis;
- export an analysis report.

## Implemented Product Experience

```text
Explore the map
→ Select or search for a borough
→ Load stored analysis evidence
→ Review score, rank, dimensions, and indicators
→ Choose basic analysis or enable live AI interpretation
→ Ask follow-up questions
→ Compare boroughs
→ Export PDF or Markdown
```

Implemented capabilities include:

- MapLibre borough map with hover, selection, search, and reset;
- responsive analysis workspace;
- English and Simplified Chinese localization;
- persisted per-analysis AI preference with a basic-analysis fallback;
- dimension, indicator, PCA contribution, TOPSIS score, and ranking views;
- structured `AnalysisInsights` responses;
- contextual chat and borough comparison;
- Qwen, DeepSeek, OpenAI-compatible, and Mock provider strategies;
- deterministic charted A4 PDF generation;
- editable Markdown report export.

## Analysis Model Boundary

The current platform performs the following deterministic workflow:

1. import and validate the indicator CSV;
2. store borough and indicator records in SQLite;
3. standardize the indicator matrix;
4. apply PCA to derive objective indicator weights;
5. use those weights in TOPSIS;
6. calculate closeness scores and ranks;
7. calculate dimension and contribution outputs;
8. persist the completed results for API retrieval.

The 2024–2025 spatial research included Moran's I, LISA, and Getis-Ord Gi*. The current web platform does not execute those spatial statistics. The distinction is explicit to prevent the original research scope from being confused with the implemented 2026 platform.

## AI Product Boundary

AI may:

- explain supplied scores, indicators, and contributions;
- summarize strengths and weaknesses;
- compare supplied borough contexts;
- provide interpretive recommendations;
- produce structured insights and report prose.

AI may not:

- recompute PCA or TOPSIS;
- create unsupported scores or ranks;
- treat model output as source evidence;
- replace human or domain review.

Controls include server-built context, explicit prompt boundaries, Pydantic validation for structured output, sanitized provider errors, deterministic analysis persistence, and automated tests with mocked external calls.

## Data and Rights Boundary

The source research references data from OpenStreetMap/Overpass Turbo, Impact Observatory/Esri Living Atlas, USGS Landsat, London Datastore/ONS, and UK Data Service boundary sources. Their licences and attribution requirements differ.

The compiled local CSV and GeoJSON artifacts do not yet contain sufficient field-level provenance and licensing metadata to establish redistribution rights. They are intentionally excluded from GitHub:

```text
data/london_indicators.csv
data/london_boroughs.geojson
public/data/london_boroughs.geojson
```

The repository publishes the source code and analysis workflow, not the compiled third-party data. Local users must prepare appropriately licensed replacements according to the [Technical Guide](./TECHNICAL_GUIDE.md).

## Technical Delivery

| Area | Implementation |
| --- | --- |
| Frontend | React, TypeScript, Vite, Tailwind CSS, MapLibre GL JS, Recharts |
| Backend | Python, FastAPI, Pydantic |
| Persistence | SQLite |
| Analysis | NumPy, pandas, scikit-learn, PCA-weighted TOPSIS |
| AI | Provider strategy layer for Qwen, DeepSeek, OpenAI-compatible, and Mock modes |
| Reports | ReportLab PDF pipeline and Markdown export |
| Quality | TypeScript production build and Python automated tests |

Detailed setup, configuration, APIs, data preparation, and validation commands are maintained in the [Technical Guide](./TECHNICAL_GUIDE.md). Detailed product and engineering decisions remain available in [`specs/`](../specs/).

## Current Publication Status

- Source repository: public
- Default branch: `main`
- Product deployment: not yet public
- Public demo data: not provided
- Public screenshots: not yet provided
- Project software licence: not selected
- Bundled font licence: the font retains its included SIL Open Font License

Publishing the source repository does not mean the application is deployed or production-ready.

## Validation Baseline

The repository provides repeatable validation commands for:

- TypeScript compilation and the Vite production build;
- Python bytecode compilation;
- backend, provider, analysis, database, and PDF report tests.

External LLM calls are mocked in automated tests. Live provider credentials are not required for the test suite and must never be committed.

## Current Limitations

- Appropriately licensed local data must be prepared before the full map and analysis workflow can run.
- The application has not been publicly deployed or production-hardened.
- SQLite and the import workflow target a single-user portfolio demonstration.
- Live AI depends on external provider availability, model access, quota, and supplied credentials.
- AI recommendations are interpretive decision support, not planning authority.
- The web platform does not currently execute Moran's I, LISA, or hotspot analysis.
- Verified public screenshots and a live demo URL are not yet available.
- No project software licence has been selected.

## Portfolio Evidence Map

- Product positioning and recruiter-facing summary: [`README.md`](../README.md)
- Chinese portfolio summary: [`README.zh-CN.md`](../README.zh-CN.md)
- Technical implementation and setup: [`TECHNICAL_GUIDE.md`](./TECHNICAL_GUIDE.md)
- Architecture and product specifications: [`specs/`](../specs/)
- Source implementation: [`src/`](../src/) and [`backend/`](../backend/)
- Future verified screenshots: [`docs/screenshots/`](./screenshots/)
