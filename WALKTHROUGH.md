# WALKTHROUGH.md
Full product spec for AI Venture Studio. This is the source of truth for what is being built. Read this before starting any task.

## 1. Summary
AI Venture Studio is an enterprise-grade Agentic AI platform designed to assist entrepreneurs, startup founders, incubators, MBA students, investors, and business consultants in transforming an initial business idea into an investment-ready business plan.

## 2. What the platform does
Combines Generative AI, Agentic AI, Multi-Agent Deliberation, Retrieval-Augmented Generation (RAG), Business Rules Validation, Analytics, and Cloud Computing into one intelligent decision-support ecosystem. Users collaborate with a team of specialized AI agents that simulate an executive boardroom across strategy, finance, marketing, legal compliance, risk management, sustainability, and investment analysis.

## 3. Core innovation — Multi-Agent Deliberation Framework
Specialized agents reason independently, debate via an LLM Council, undergo review and critique, and are validated against structured business rules before producing executive-ready outputs.

## 4. Core agent pipeline (in order)
1. **Planning Agent** — breaks down the business idea into a research/analysis plan
2. **Orchestrator Agent** — routes tasks to the right specialized agents, manages pipeline state
3. **Research Agent** — gathers live market/competitor/industry data via web search (Tavily API), used alongside or instead of uploaded documents — see section 18
4. **Specialized Business Agents** — domain experts: Strategy, Finance, Marketing, Legal/Compliance, Risk Management, Sustainability, Investment Analysis
5. **LLM Council** — specialized agents debate/cross-review each other's outputs
6. **Reviewer Agent** — checks outputs for completeness and coherence
7. **Critic Agent** — adversarially critiques outputs to catch weak reasoning
8. **Business Rules Engine** — validates outputs against structured business rules before they proceed
9. **Analytics & Scoring Engine** — scores the business plan across dimensions
10. **Report Generator** — assembles the final executive-ready outputs

## 5. Report outputs (13 total)
1. Executive Summary
2. Business Plan
3. Business Model Canvas
4. SWOT Analysis
5. PESTLE Analysis
6. Porter's Five Forces
7. Competitor Analysis
8. Financial Projection
9. Marketing Plan
10. Risk Assessment
11. Investment Readiness Report
12. ESG Recommendations
13. Pitch Summary

(Prototype build order and priority tiering is in TASKS.md — build the pipeline deep on a subset first, then extend to the rest using the same pattern, per `skills/report-generation/SKILL.md`.)

## 6. Deployment architecture
- Frontend: Lovable/React on Vercel (prototype: React directly, no Lovable dependency — see AGENTS.md tech stack)
- Backend: FastAPI on Render
- Database/Storage: Supabase
- Vector database: ChromaDB
- LLM: NVIDIA NIM AI models (primary)
- Web research: Tavily API

## 7. End-to-end system flow
```
User → Authentication Layer → Project Workspace → Business Idea Input → Document Upload (optional)
→ Web Research (optional, Tavily) → Document Processing → Knowledge Extraction → Vector Database (RAG)
→ Planning Agent → Orchestrator Agent → Research Agent → Specialized Business Agents
→ LLM Council (Collaborative Deliberation) → Reviewer Agent → Critic Agent → Business Rules Engine
→ Analytics & Scoring Engine → Report Generator → Database & Storage → Interactive Dashboard
→ Export (PDF, DOCX, PPT)
```

## 8. Frontend layer
Modules: User Registration/Login, Dashboard, Startup Project Management, Business Idea Wizard, Document Upload, AI Boardroom View, AI Chat, Analytics Dashboard, Business Reports, Project History, User Settings.
Frontend handles interaction and visualization only — business logic stays in the backend.

## 9. Authentication layer
- Technology: Supabase Authentication
- Methods: Google Login, Email/Password Login
- Responsibilities: user authentication, session management, user profile, startup project ownership, secure API access

## 10. Startup workspace — fields per project
Startup Name, Industry, Business Idea, Business Description, Business Stage, Target Customers, Location, Investment Budget, Revenue Model, Expected Timeline, Current Team Size, Business Goals, Preferred Funding Type, Uploaded Documents, Generated Reports, Agent Discussions, Analytics, Version History.

## 11. Business idea collection module — fields collected
Business Name, Industry, Problem Statement, Solution, Target Audience, Customer Segment, Revenue Model, Pricing, Budget, Country, Business Goals, Funding Requirement, Growth Expectations, Optional Notes.
These fields double as the input to the Research Agent's query construction — see section 18.

## 12. Document upload module
- Supported file types: PDF, DOCX, PPTX, CSV, TXT, Excel, Image (OCR)
- Document categories users can upload: Business Plan, Pitch Deck, Market Research, Competitor Analysis, Survey Results, Financial Statements, Business Canvas, Investor Notes, Customer Interviews
- Document upload is now OPTIONAL — if a user uploads nothing, the Research Agent (section 18) can supply market/competitor context instead

## 13. Document processing layer
- Purpose: convert uploaded files into machine-readable knowledge
- Libraries: PyMuPDF, python-docx, python-pptx, pandas, OCR (optional)
- Steps: extract text → extract tables → extract metadata → detect headings → split into semantic chunks → clean text → generate embeddings → store in vector database
- This same pipeline (chunk → embed → store) also processes Research Agent output — see section 18

## 14. Knowledge base contents
Uploaded Documents, Government Startup Policies, MSME Schemes, Business Templates, Startup Methodologies, Industry Reports, Financial Benchmarks, Business Model Canvas Templates, SWOT Framework, PESTLE Framework, Porter's Five Forces, Lean Startup Principles, Design Thinking, Blue Ocean Strategy.

## 15. RAG layer
- Purpose: enable AI agents to answer using project-specific documents
- Pipeline: documents → chunking → embeddings → vector database → retriever → relevant context → AI agents
- Benefits: reduced hallucinations, document-aware reasoning, personalized outputs, evidence-based recommendations

## 16. Full technical skill list (per source spec)
Lovable (UI generation), React.js, Tailwind CSS, Shadcn UI, Python, FastAPI, NVIDIA NIM API (primary LLM), Gemini API (optional fallback), Tavily API (web research), LangGraph, ChromaDB, NVIDIA Embeddings or Sentence Transformers, Supabase (PostgreSQL), Supabase Auth, Supabase Storage, Plotly, Vercel (frontend), Render (backend), GitHub.

Prototype deviation: Lovable is skipped (paid, not required — Antigravity builds the React UI directly). Sentence Transformers is used instead of NVIDIA Embeddings to conserve NIM rate-limit budget. Tavily API added for live web research (pulled forward from Future Enhancements). See AGENTS.md for the finalized prototype stack.

## 17. Future enhancements — OUT OF SCOPE for this prototype
Patent search; Trademark verification; Government scheme recommendation engine; Domain availability checker; AI logo generator; AI pitch deck designer; Investor matchmaking; Competitor website analysis; Financial benchmarking; Startup valuation calculator; Voice-based AI advisor; Multi-language support; Team collaboration workspace; Calendar integration; Email notifications; API integrations with incubators and accelerators.

Note: "Live market data integration" has been moved OUT of this section and INTO scope — see section 18. Do not build any of the items still listed above unless explicitly instructed.

## 18. Web Research Module (Research Agent) — NEW, IN SCOPE
- Purpose: gather live market, industry, and competitor data directly from the web, as an alternative or supplement to manual document upload
- Provider: Tavily API — purpose-built for LLM agent search, free tier 1000 credits/month, no card required
- Trigger: runs automatically alongside/after the Orchestrator Agent step, using fields from the Business Idea Collection Module (industry, target audience, location, competitors) to build search queries
- Search depth: Basic search (1 credit) for simple lookups, Advanced search (2 credits, includes content extraction) for competitor/market queries where extraction quality matters — use Advanced sparingly to conserve quota
- Output handling: results are NEVER injected raw into an agent prompt — they go through the same chunk → embed (Sentence Transformers) → ChromaDB pipeline as uploaded documents (section 13), then get retrieved via the standard RAG retriever (section 15)
- Fallback: if Tavily quota is exhausted or a query fails, pipeline continues using uploaded documents + static knowledge base only — this is a soft dependency, not a hard blocker
- Cost impact: adds 1-3 extra calls per pipeline run, against a separate quota from NIM/Gemini — see `skills/web-research/SKILL.md` for implementation detail
