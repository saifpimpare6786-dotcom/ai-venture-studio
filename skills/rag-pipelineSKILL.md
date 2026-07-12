---
name: rag-pipeline
description: Use when building or modifying retrieval-augmented generation — connecting ChromaDB-stored document chunks (from uploads AND web research) to the AI agents so their reasoning is grounded in project-specific evidence rather than the LLM's raw knowledge alone.
---

# Skill: RAG Pipeline

## Objective
Give every AI agent in the pipeline document-aware, evidence-based context instead of relying on the LLM's raw knowledge alone. Reduces hallucination and personalizes output to the user's actual startup.

## Pipeline
```
documents (uploaded OR web-researched) → chunking → embeddings → vector database → retriever → relevant context → AI agents
```

## Components
- Vector database: ChromaDB, self-hosted, one collection per project (`project_{id}`)
- Embeddings model: Sentence Transformers, local (do NOT use the NVIDIA embeddings API — it burns NIM rate-limit budget needed for actual agent reasoning calls)
- Retriever: top-k semantic similarity search (start with k=5), filterable by document category metadata (now includes a `source_type` field: `upload` or `web_research`)

## Context sources feeding this pipeline (three total)
1. **User-uploaded documents** — see `skills/document-processing/SKILL.md`
2. **Research Agent web results** (Tavily) — see `skills/web-research/SKILL.md`. Treated identically to uploads once chunked/embedded — same collection, tagged `source_type: web_research`
3. **Static knowledge base** — government policies, MSME schemes, business frameworks (below)

## Knowledge base contents (in addition to user-uploaded documents and web research)
Government Startup Policies, MSME Schemes, Business Templates, Startup Methodologies, Industry Reports, Financial Benchmarks, Business Model Canvas Templates, SWOT Framework, PESTLE Framework, Porter's Five Forces, Lean Startup Principles, Design Thinking, Blue Ocean Strategy. These are static reference documents — embed them once at setup time into a shared `knowledge_base` collection separate from per-project collections.

## Retrieval flow at agent-call time
1. Agent receives a task from the Orchestrator (e.g. "assess financial viability")
2. Retriever queries the project's document collection (uploads + web research merged) AND the shared knowledge_base collection
3. Top-k chunks from each are merged, deduplicated, and injected into the agent's prompt as context
4. Agent reasons using this context plus its own domain expertise, and should reference which source (uploaded document, web research, or framework) informed its output where relevant

## Benefits (why this matters, keep in mind when tuning)
Reduced hallucinations, document-aware reasoning, personalized outputs, evidence-based recommendations.

## Common failure modes to guard against
- Empty retrieval (project has no uploaded documents AND Research Agent found nothing or quota was exhausted) — fall back gracefully to knowledge_base only, don't error
- Chunk bloat — cap total injected context per agent call to avoid blowing the model's context window and to control token cost against the rate limit
- Source imbalance — if web research returns far more chunks than a thin document upload, don't let it drown out the user's own uploaded evidence in the top-k merge; weight or cap per-source contribution
