---
name: report-generation
description: Use when building the Report Generator or adding/modifying any of the 12 report output types (Executive Summary, Business Plan, SWOT, PESTLE, Porter's Five Forces, Competitor Analysis, Financial Projection, Marketing Plan, Risk Assessment, Investment Readiness Report, ESG Recommendations, Pitch Summary).
---

# Skill: Report Generation

## Objective
Assemble the validated, scored pipeline output (see `skills/agent-orchestration/SKILL.md`) into the 12 executive-ready report types, all following one consistent generation pattern so adding a new type is a config change, not new code.

## All report types and prototype build order
Priority tier 1 (build first):
1. Executive Summary
2. Business Plan
3. SWOT Analysis
4. Financial Projection
5. Investment Readiness Report

Priority tier 2 (add once tier 1 works end-to-end):
6. Business Model Canvas
7. PESTLE Analysis
8. Porter's Five Forces
9. Competitor Analysis
10. Marketing Plan
11. Risk Assessment
12. ESG Recommendations
13. Pitch Summary

## The pattern (one pattern for every report type — never build one-off logic)
Each report type is defined by:
1. A **schema** (pydantic model) defining its required sections
2. A **prompt template** that maps pipeline state (specialized outputs, council feedback, scores) into that schema
3. A **registration entry** in the Report Generator's report-type registry (a dict/config, not an if/else chain)
4. An **export mapping** — which sections go where in DOCX/PPT/PDF output

## Adding a new report type
See `.agents/workflows/add-report-type.md` for the exact step-by-step slash-command workflow.

## Export formats
- DOCX: python-docx
- PPTX: python-pptx
- PDF: weasyprint or reportlab
Each report type declares which export formats it supports (e.g. Pitch Summary → PPTX makes sense, Financial Projection → DOCX + PDF).

## Data source for reports
Reports are generated ONLY from data that has passed the Business Rules Engine validation step. Never generate a report directly from raw specialized-agent output — always go through the full pipeline (Council → Reviewer → Critic → Rules Engine → Scoring) first.
