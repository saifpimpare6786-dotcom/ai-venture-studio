# GEMINI.md
Antigravity-specific operating instructions. Highest priority — overrides AGENTS.md only where the two conflict.

## Autonomy mode by task type
- **Agent-driven (autopilot):** boilerplate, CRUD endpoints, UI scaffolding, standard React components, document upload handlers
- **Review-driven (approve each step):** LangGraph pipeline logic, Business Rules Engine, Analytics & Scoring Engine, Supabase schema migrations, Research Agent query construction — a silent logic error here corrupts report quality without an obvious symptom
- **Plan mode first:** any task touching the agent-pipeline files or the database schema — generate the Plan Artifact before executing

## Verification
- Use the Browser Subagent to actually exercise every frontend flow you build (Business Idea Wizard, AI Boardroom View, Analytics Dashboard, Reports view) before marking a task done. Screenshots/walkthrough artifacts required, not just "should work."
- Run the backend locally and hit the endpoint before deploying to Render.

## Model routing (the product's own LLM calls — not your model)
- Specialized Business Agents (Strategy, Finance, Marketing, Legal/Compliance, Risk, Sustainability, Investment Analysis) → NVIDIA NIM
- Critic Agent + Reviewer Agent → Gemini API (spreads load off the NIM 40 RPM ceiling)
- Research Agent → Tavily API (separate quota entirely — 1000 credits/month free tier, does not touch NIM or Gemini budget)
- If NIM returns 429 repeatedly, fail over the affected call to Gemini rather than blocking the pipeline
- If Tavily quota is exhausted mid-run, fall back gracefully to knowledge_base + uploaded documents only — never block the pipeline waiting on research

## Parallel agent dispatch (Manager surface)
When running multiple Antigravity agents at once, keep strict domain boundaries:
- Agent A: backend (`/backend`)
- Agent B: frontend (`/frontend`)
- Agent C: agent-pipeline (`/backend/pipeline`)
- Agent D: RAG/document processing + web research (`/backend/rag`, `/backend/research`)
Never let two agents edit the same file concurrently. Merge via review, not auto-merge.

## Git discipline
Commit after every accepted task. Small, frequent commits are the intended revert safety net for this project — do not batch multiple tasks into one commit.

## Precedence
System rules (immutable) → GEMINI.md (this file) → AGENTS.md → `.agents/rules/*.md` → built-in defaults.
