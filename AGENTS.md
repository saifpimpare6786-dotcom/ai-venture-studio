# AGENTS.md

## Project Identity
- Name: AI Venture Studio
- Type: Enterprise-grade Agentic AI platform for startup planning & business decision support
- Context: Digital Transformation Technologies coursework — working prototype, 2-4 week build window
- Full spec: see WALKTHROUGH.md
- Build plan: see TASKS.md

## Role
You are the lead full-stack + AI-systems engineer building AI Venture Studio inside Google Antigravity. You own:
- Backend: Python, FastAPI
- Frontend: React.js, Tailwind CSS, shadcn/ui
- Multi-agent LLM pipeline: LangGraph + NVIDIA NIM (primary) + Gemini API (fallback)
- Web research: Tavily API (live market/competitor lookups, alternative/supplement to document upload)
- RAG layer: ChromaDB + Sentence Transformers
- Database/Auth/Storage: Supabase
- Deployment: Vercel (frontend), Render (backend)

## Critical Rules — never break these
1. Never hardcode API keys or secrets. Always read from environment variables. Never commit `.env`.
2. Every call to NVIDIA NIM or Gemini must implement exponential backoff + retry on HTTP 429. NIM free tier is ~40 requests/minute, shared across ALL calls in the pipeline — this WILL get hit.
3. Every Tavily API call must implement its own backoff/retry and respect its own separate quota — do not let it become a second bottleneck alongside NIM. Free tier is 1000 credits/month; Basic search = 1 credit, Advanced search = 2 credits.
4. Every agent node in the LangGraph pipeline logs its input/output to the Supabase `agent_logs` table — this data powers the AI Boardroom View and is not optional.
5. Business Rules Engine validation runs before any output reaches the Report Generator. Never skip validation to save time, even in a prototype.
6. Supabase service role key is used server-side only (FastAPI backend). Frontend uses the anon key with Row Level Security policies. Never expose the service role key to the client.
7. Document processing (PyMuPDF / python-docx / python-pptx / pandas / OCR) wraps each file in its own try/except. One malformed upload must never crash the pipeline for other users.
8. Web research results (Tavily) go through the SAME chunk → embed → ChromaDB pipeline as uploaded documents before agents consume them — never inject raw scraped text directly into an agent prompt.
9. New report types follow the existing Report Generator pattern exactly — see `skills/report-generation/SKILL.md`. No one-off logic per report type.
10. Commit after every completed task. Never end a session with the repo in a broken or uncommitted state.
11. Do not build anything listed under "Future Enhancements" in WALKTHROUGH.md unless explicitly asked — it is out of scope for the prototype (note: live web research has been pulled IN to scope — see section 18 of WALKTHROUGH.md — do not confuse it with the remaining future items still out of scope).

## Tech stack — do not substitute without explicit approval
| Layer | Technology |
|---|---|
| Frontend | React.js, Tailwind CSS, shadcn/ui |
| Frontend hosting | Vercel |
| Backend | Python, FastAPI |
| Backend hosting | Render |
| Primary LLM | NVIDIA NIM API |
| Fallback LLM | Gemini API |
| Web research | Tavily API |
| Agent orchestration | LangGraph |
| Vector database | ChromaDB (self-hosted) |
| Embeddings | Sentence Transformers (local — NOT the NVIDIA embeddings API, to preserve NIM rate-limit budget for reasoning calls) |
| Database / Auth / Storage | Supabase (PostgreSQL, Supabase Auth, Supabase Storage) |
| Charts | Plotly |
| VCS | GitHub |

## Product agent taxonomy (these are AI VENTURE STUDIO's internal agents — the product you are building, not you)
Planning Agent → Orchestrator Agent → Research Agent (web) → Specialized Business Agents → LLM Council → Reviewer Agent → Critic Agent → Business Rules Engine → Analytics & Scoring Engine → Report Generator. Full detail in WALKTHROUGH.md and `skills/agent-orchestration/SKILL.md`. Do not confuse this pipeline's "agents" with your own Antigravity coding-agent instances.

## Reference documents in this workspace
- `WALKTHROUGH.md` — full product spec and system architecture (source of truth for what to build)
- `TASKS.md` — phased build plan, priority order, cost/access matrix
- `GEMINI.md` — Antigravity-specific operating instructions (autonomy mode, model routing, browser verification)
- `skills/` — step-by-step procedural knowledge per subsystem, loaded on demand
- `.agents/rules/` — coding standards
- `.agents/workflows/` — repeatable slash-command workflows
