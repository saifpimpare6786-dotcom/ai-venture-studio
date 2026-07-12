# TASKS.md
Build plan for the AI Venture Studio prototype. Timeline: 2-4 weeks (target 3 weeks + 1 buffer week). Full architecture, prioritized breadth-after-depth: get the whole pipeline working end-to-end first, then extend report-type coverage.

## Access / cost matrix
| Service | Status | Note |
|---|---|---|
| NVIDIA NIM | Free (already have key) | Free tier ~40 req/min shared across ALL calls — this is the biggest technical risk, see Risk section |
| Gemini API | Free tier | Fallback + load-split for Critic/Reviewer agents |
| Tavily API | Free tier | 1000 credits/month, no card required. Basic search = 1 credit, Advanced search = 2 credits. Separate quota from NIM/Gemini — see Risk section |
| Supabase | Free | 500MB DB, 1GB storage, 50K MAU. Auto-pauses after 7 days idle — resume manually before demo day |
| ChromaDB | Free, self-hosted | No cloud fee |
| Vercel | Free (Hobby) | Frontend deploy |
| Render | Free tier | Backend deploy. Cold start ~30-50s after idle — warm it up before any live demo |
| GitHub | Free | — |
| LangGraph | Free, open-source | Orchestration core |
| Sentence Transformers | Free, self-hosted | Used instead of NVIDIA embeddings API to save NIM rate-limit budget |
| Lovable | Paid (skipped) | Not used in prototype — React/Tailwind/shadcn built directly in Antigravity |

## Risk flag — read before building the agent pipeline
NIM free tier is ~40 requests/minute TOTAL. One report generation = Planning → Orchestrator → Research Agent → 3-7 Specialized Agents → LLM Council (cross-critique, more calls) → Reviewer → Critic = 10-15+ LLM calls per report. This throttles fast.
Mitigations (mandatory, not optional):
- Route Critic + Reviewer calls to Gemini free tier, keep NIM for Specialized Agent reasoning
- Route web research to Tavily (separate quota) — never let research calls compete with NIM/Gemini budget
- Exponential backoff + retry on every LLM call and every Tavily call, from day 1
- Cache RAG retrieval and agent outputs so re-runs don't re-burn rate limit or research quota

## Phase 1 — Foundation (Week 1)
- [ ] Init GitHub repo, commit immediately
- [ ] Supabase project: schema for `projects`, `users`, `documents`, `reports`, `agent_logs`, `agent_discussions`
- [ ] Supabase Auth: Google + email/password login
- [ ] FastAPI skeleton → deploy to Render
- [ ] React skeleton (Tailwind + shadcn/ui) → deploy to Vercel
- [ ] Document upload + processing pipeline: PyMuPDF/python-docx/python-pptx/pandas → chunk → Sentence Transformers embed → ChromaDB store
- [ ] Tavily API key setup, basic search call wired and tested standalone (before pipeline integration)
- [ ] Antigravity: dispatch 2 parallel agents via Manager surface — backend scaffold + frontend scaffold, Agent-driven mode

## Phase 2 — Agent pipeline core (Week 2)
- [ ] LangGraph graph: Planning Agent → Orchestrator → Research Agent → 4 Specialized Agents to start (Strategy, Finance, Marketing, Risk)
- [ ] Research Agent: query construction from Business Idea fields, Tavily call, results routed through document-processing pipeline into ChromaDB
- [ ] LLM Council step: cross-review between specialized agents + Critic agent
- [ ] Reviewer Agent + Critic Agent
- [ ] Business Rules Engine — start as Python/pydantic validators, not a full rules DSL
- [ ] Wire RAG retriever into agent context (now pulling from uploaded docs + web research + knowledge base)
- [ ] Antigravity: switch to Editor view + Plan mode (Review-driven) for this phase — logic correctness matters, don't run on autopilot

## Phase 3 — Reports, analytics, export, UI wiring (Week 3)
- [ ] Analytics & Scoring Engine: weighted rubric per section
- [ ] Report Generator — build these 5 first: Executive Summary, Business Plan, SWOT Analysis, Financial Projection, Investment Readiness Report
- [ ] Export: DOCX/PPT/PDF (python-docx, python-pptx, weasyprint/reportlab)
- [ ] Wire frontend: Business Idea Wizard, Document Upload (now optional, with "skip and use web research instead" path), AI Boardroom View (stream agent debate), Analytics Dashboard (Plotly), Reports view
- [ ] Antigravity Browser Subagent: verify every UI flow live

## Phase 4 — Buffer (Week 4, if available)
- [ ] Remaining report types: Business Model Canvas, PESTLE Analysis, Porter's Five Forces, Competitor Analysis, Marketing Plan, Risk Assessment, ESG Recommendations, Pitch Summary — same pattern as Phase 3, see `skills/report-generation/SKILL.md`
- [ ] Rate-limit hardening, error states, edge cases (including Tavily quota exhaustion fallback)
- [ ] Demo recording, deploy freeze, README

## Definition of done for the prototype
- Full pipeline runs end-to-end for at least one business idea input: idea → (documents and/or web research) → RAG → all agent stages → validated report → dashboard → export
- At minimum the 5 priority report types are generating correctly
- Deployed and reachable at public Vercel + Render URLs
- No hardcoded secrets in the repo
