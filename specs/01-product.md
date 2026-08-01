# UrbanInsight AI

## Overview

UrbanInsight AI is an AI-powered urban decision assistant for London.

It transforms multi-dimensional borough indicators and deterministic statistical results into interactive visual analysis and contextual explanations.

Users explore the city through a map, inspect persisted PCA-weighted TOPSIS results and ask an AI urban analyst to explain what those results mean.

The product focuses on making urban analytics intuitive, guided and decision-ready.

---

## Target Users

Urban planners

Researchers

Students

Government analysts

Business analysts

---

## Core Concept

The map is the center of the experience.

The AI accompanies the user throughout the exploration process.

The Analysis Engine is the only source of mathematical computation.

The AI explains stored results rather than creating rankings independently.

The AI should feel like an intelligent research assistant rather than a generic chatbot.

---

## Product Goals

Help users understand regional differences.

Explain why boroughs rank differently.

Identify strengths and weaknesses.

Interpret economic, social and ecological indicators.

Generate practical development suggestions.

Support contextual follow-up questions.

Compare boroughs using the same authoritative data.

Generate decision-ready PDF and Markdown analysis reports.

Preserve completed AI conversations as PDF without regenerating their content.

Present structured, scannable chat and comparison answers with clear waiting and recovery states.

Support English and Simplified Chinese workflows.

Allow UI development without LLM cost through Mock AI mode.

---

## Current Product Scope

Version 1 covers all 33 London boroughs.

The platform includes:

- Searchable borough selection
- MapLibre borough exploration
- Stored indicator and analysis retrieval
- PCA-weighted TOPSIS visualization
- Context-aware AI analysis
- Follow-up conversation
- Borough comparison
- Structured chat and comparison cards
- AI thinking feedback and request retry
- Conversation PDF export
- Markdown report export
- Charted analysis PDF export
- English and Simplified Chinese interface
- Mock and live AI modes
- OpenAI, Qwen and DeepSeek support

The platform does not currently include:

- User accounts
- Saved sessions
- User-uploaded datasets
- Multi-city datasets
- Streaming AI responses
- Runtime execution of the Analysis Engine from the browser

---

## User Journey

Open website

↓

Search or explore the London map

↓

Hover a borough

↓

AI Panel previews the region

↓

Click or select a borough

↓

Frontend retrieves indicators and stored analysis

↓

AI generates a contextual interpretation

↓

Analysis Workspace appears

↓

Explore scores, charts, indicators and insights

↓

Ask a follow-up question or compare another borough

↓

Retry a failed request if necessary

↓

Export the conversation or generate an analysis PDF/Markdown report

---

## Product Boundaries

The AI must not:

- Calculate PCA
- Calculate TOPSIS
- Generate independent rankings
- Modify stored scores
- Invent missing indicators

The frontend must not:

- Read the CSV directly
- Read SQLite directly
- Perform statistical analysis
- Know which live AI provider is active

These boundaries are core product requirements.
