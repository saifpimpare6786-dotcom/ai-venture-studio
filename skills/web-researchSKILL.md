---
name: web-research
description: Use when building or modifying the Research Agent — live web search for market, industry, and competitor data via the Tavily API, used as an alternative or supplement to manual document upload.
---

# Skill: Web Research (Research Agent)

## Objective
Give the pipeline live market/competitor/industry evidence without requiring the user to upload documents. Feeds the same RAG pipeline as uploaded files — never treated as a separate context source.

## Provider: Tavily API
- Built specifically for LLM agent search — returns clean, summarized results, not raw HTML
- Free tier: 1000 credits/month, no card required
- Basic search = 1 credit/call (links + snippets)
- Advanced search = 2 credits/call (includes content extraction — use for competitor/market queries where extraction quality matters, not for simple lookups)
- Separate quota entirely from NVIDIA NIM and Gemini — does not compete with the agent-reasoning rate limit, but must not be treated as unlimited either

## When this runs
Triggered after the Orchestrator Agent step, before or in parallel with Specialized Business Agents. Runs whether or not the user uploaded documents — if documents exist, web research supplements them; if not, it substitutes for them.

## Query construction
Build queries from Business Idea Collection Module fields (see WALKTHROUGH.md section 11): Industry, Target Audience, Location/Country, Business Name/competitors if named. Example query patterns:
- `"{industry} market size {country} {year}"`
- `"{industry} competitors {target audience}"`
- `"{industry} industry trends {country}"`

Keep queries specific — broad one-word queries return low-quality results and waste credits on a re-query.

## Processing flow
```
Business idea fields → query construction → Tavily API call → raw results
→ chunk → embed (Sentence Transformers) → store in ChromaDB (project's collection)
→ retrievable by Specialized Business Agents via the standard RAG retriever
```
Never pass raw Tavily output directly into an agent prompt. It must go through `skills/document-processing/SKILL.md`'s chunk/clean/embed steps first, exactly like an uploaded file, so citation and rate-limit-aware retrieval behave consistently across all context sources.

## Mandatory error handling
- Wrap every Tavily call in its own try/except with exponential backoff on rate-limit or timeout errors
- If Tavily quota is exhausted for the month, or the call fails after retries, log it and continue the pipeline using uploaded documents + static knowledge base only — this is a soft dependency, never a hard blocker
- Cap the number of Tavily calls per pipeline run (recommend 2-3 max: one industry overview, one competitor lookup, one market-data lookup) to conserve monthly quota across all users

## Cost control tips
- Use Basic search by default; upgrade to Advanced only for the competitor-analysis query where extracted content materially improves output quality
- Cache research results per project — don't re-run the same queries if the user re-generates a report for the same business idea
- At prototype scale (~166 full research runs/month at 6 credits/run), the free tier comfortably covers development and demo use; monitor usage if load testing with many repeated runs
