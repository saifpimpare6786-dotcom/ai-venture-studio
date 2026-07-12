---
name: document-processing
description: Use when building or modifying the document processing pipeline that converts uploaded files (PDF, DOCX, PPTX, CSV, TXT, Excel, images) AND Research Agent web results into clean, chunked, embedded text for the RAG layer.
---

# Skill: Document Processing

## Objective
Convert uploaded startup documents — and, identically, Research Agent web results (see `skills/web-research/SKILL.md`) — into clean, chunked, embedded text stored in ChromaDB, without ever crashing the pipeline on a bad file or a bad web result.

## Supported input types
- Uploads: PDF, DOCX, PPTX, CSV, TXT, Excel, Image (OCR)
- Web research: Tavily API result text (routed through this same pipeline, tagged `source_type: web_research`)

## Document categories (what users actually upload)
Business Plan, Pitch Deck, Market Research, Competitor Analysis, Survey Results, Financial Statements, Business Canvas, Investor Notes, Customer Interviews.

## Libraries
- PDF: PyMuPDF
- DOCX: python-docx
- PPTX: python-pptx
- CSV/Excel: pandas
- Images: OCR (optional — use pytesseract or a hosted OCR call; only if time allows in the prototype)
- Web research text: no extraction library needed — Tavily already returns clean text/summaries, goes straight to chunking

## Processing steps (in order)
1. Extract text (skip for web research input — already text)
2. Extract tables (uploads only)
3. Extract metadata (filename or query, upload date, document category or `source_type: web_research`, project_id)
4. Detect headings (used for semantic chunk boundaries)
5. Split into semantic chunks (target ~300-500 tokens per chunk, respect heading boundaries)
6. Clean text (strip boilerplate, normalize whitespace, remove headers/footers)
7. Generate embeddings via Sentence Transformers (local model, e.g. `all-MiniLM-L6-v2`)
8. Store in ChromaDB, one collection per project, metadata tagged with document category (or `source_type: web_research`) and source filename/query

## Mandatory error handling
Wrap each file's (or each web result's) processing in its own try/except. One malformed upload or failed web fetch must never take down processing for other files/users. Log the failure to `agent_logs` with the filename/query and error, and surface a clear "this item couldn't be processed" state to the frontend — don't fail silently and don't crash the request.

## Output
Chunks stored in ChromaDB become retrievable by the RAG retriever (see `skills/rag-pipeline/SKILL.md`) and are what the AI agents cite as document-aware evidence, regardless of whether the original source was an upload or a web search.
