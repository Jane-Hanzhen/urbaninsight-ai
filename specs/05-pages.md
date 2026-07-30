# Page Specification

## Overview

UrbanInsight AI is a single-page React application.

Users never navigate to another frontend route.

The experience revolves around three core areas:

- Interactive Map
- AI Panel
- Analysis Workspace

The current screen is rendered by:

```text
src/app/App.tsx
```

---

# Page Layout

The application consists of three visible page bands.

```text
Sticky Header
↓
Interactive Map + AI Panel
↓
Analysis Workspace when completed
```

Desktop layout

```text
┌────────────────────────────────────────────────┐
│ Product        Borough Search        Language  │
├──────────────────────────────┬─────────────────┤
│                              │                 │
│ London Map                   │ AI Panel        │
│                              │                 │
├──────────────────────────────┴─────────────────┤
│ Analysis Workspace when analysis completes    │
└────────────────────────────────────────────────┘
```

The content width is capped at 1600px.

The map and AI Panel use a 7:3 grid at 1024px and above.

Below 1024px they stack vertically.

---

# Top Navigation

Purpose

Provide identity, borough discovery and language selection.

Left

- Product mark
- UrbanInsight AI

Center

- Borough search combobox

Right

- English / Simplified Chinese switcher

There is no separate Run Analysis button.

There is no settings or account workflow.

Selecting a borough triggers analysis directly.

---

# Interactive Map

The map is the visual center of the initial experience.

Library

```text
MapLibre GL JS
```

Data

```text
/data/london_boroughs.geojson
```

Default State

- London camera
- No selected borough
- Compact translucent guidance card
- Zoom controls
- Home control

Hover Interaction

- Highlight borough
- Show soft line glow
- Show official borough name tooltip
- Update AI Panel to hover state

Click Interaction

- Persist selected borough
- Mute other boroughs
- Fit camera to selected geometry
- Clear previous AI conversation and insights
- Request indicators
- Request stored analysis
- Post AI analysis request

Search selection invokes the same selection handler.

Home Interaction

- Reset center, zoom, bearing and pitch
- Preserve selected borough and application state

Fallback

If GeoJSON cannot be loaded, the map container remains mounted and displays a localized status.

---

# AI Panel

Purpose

Guide users through selection, interpretation and follow-up.

The AI Panel is sticky at the top of the viewport on desktop.

It uses one consistent visual shell across all states.

## State 1 — Idle

Display

- UrbanInsight AI identity
- Product subtitle
- Friendly Urban introduction
- Product capabilities
- Prompt to click a borough

## State 2 — Hover

Display

```text
Looking at Camden...
Click to analyze.
```

The selected borough, if one exists, takes precedence over hover state.

## State 3 — Selected

Display the selected borough and the beginning of the workflow.

The state is brief because the AI request starts immediately.

## State 4 — Analyzing

Display five localized progress items:

1. Loading regional indicators
2. Reading Analysis Engine results
3. Building structured context
4. Interpreting results
5. Generating recommendations

The progress list is representational.

The backend operation itself is one non-streaming request.

## State 5 — Completed

Display:

- Borough name
- Overall score
- Regional rank
- Follow-up guidance or localized AI error

The frontend moves to completed after the AI request settles, including the error path.

The Analysis Workspace then appears.

## Follow-up Conversation

Available after completion.

Behavior

- User submits a question
- Current selected borough ID is sent
- Up to 12 previous messages may be sent
- New messages use the currently selected locale
- Existing messages keep their original language

## Borough Comparison

Available after completion.

Behavior

- Comparison list excludes the selected borough
- User selects one comparison borough
- Comparison response is added to the same conversation
- The Analysis Engine remains the source of all scores and rankings

---

# Analysis Workspace

Purpose

Display detailed stored analysis and AI interpretation.

Default State

Hidden.

It mounts after the application reaches `completed`.

The page scrolls smoothly toward the workspace shortly after completion.

## Section 1 — Heading

Display:

- Analysis badge
- Borough analysis title
- Introductory copy
- Generate Report button

## Section 2 — Overview

Display:

- Overall score
- Regional rank
- Rank context across 33 boroughs
- Statistical or AI summary

## Section 3 — Dimension Cards

Display three cards:

- Economic
- Social
- Ecological

Each card contains:

- Score
- Progress bar
- Localized dimension description

## Section 4 — Radar Chart

Visualize the three dimension scores.

## Section 5 — Contribution Analysis

Visualize the stored dimension contribution percentages with horizontal bars.

## Section 6 — Key Indicators

Display all 12 Version 1 indicators.

Labels and descriptions are localized from stable indicator IDs.

Values remain unchanged.

## Section 7 — Main Drivers

Display:

- AI indicator interpretation
- Two to four main driver items

This section appears only when structured AI insights are available.

## Section 8 — Strengths

Display two to four AI-generated strength items.

## Section 9 — Weaknesses

Display two to four AI-generated weakness items.

## Section 10 — Recommendations

Display two to four recommendations.

Each recommendation has:

- Title
- Detail
- `High` or `Medium` priority

Priority display labels are localized.

## Section 11 — AI Unavailable

If structured AI insights are missing:

- Keep statistical results visible
- Replace interpretation cards with an unavailable message
- Do not hide the workspace

## Section 12 — Generate Report

The report action appears at the top and bottom of the workspace.

Both locations reuse one export implementation and one loading state.

Primary action:

- Download a bilingual, A4 PDF report from `POST /reports/pdf`
- Include the score, rank, PCA/TOPSIS method, dimension and contribution charts,
  indicators, interpretation, recommendations and disclaimer
- Use the metadata and structured insights frozen when the current analysis completed
- Never trigger a new AI request during PDF generation

Secondary action:

- Export Markdown from `POST /ai/report`

Markdown filenames use:

```text
urbaninsight-{borough}-report.md
```

or:

```text
urbaninsight-{borough}-分析报告.md
```

PDF filenames distinguish basic and AI-applied analysis and use a `.pdf` extension.

---

# Language Behavior

Supported languages

- English
- Simplified Chinese

The active locale affects:

- Fixed interface text
- Indicator display labels
- New AI analysis requests
- New follow-up responses
- New comparison responses
- Generated reports
- Download filename

Official borough names remain in English.

Existing AI responses are not regenerated after a language switch.

---

# Error Behavior

Borough loading failure

- Log details in development
- Keep the page mounted
- Search has no borough results

Indicator or analysis fetch failure

- Use empty indicators or preview analysis data
- Do not crash the page

AI request failure

- Show localized generic error
- Keep provider details hidden
- Move to completed so statistical data remains available

Report failure

- Show localized report error near the report action

---

# User Journey

Open website

↓

Search or browse the London map

↓

Hover borough

↓

AI Panel previews borough

↓

Click or search-select borough

↓

Retrieve indicators and stored analysis

↓

Generate AI interpretation

↓

Analysis Workspace appears

↓

Explore charts and recommendations

↓

Ask, compare or generate report

---

# Design Principles

The map owns exploration.

Search owns discovery.

The AI Panel owns guidance and conversation.

The Analysis Workspace owns detailed results.

The Analysis Engine owns mathematics.

The AI Agent owns interpretation.
