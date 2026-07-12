---
name: agent-orchestration
description: Use when building or modifying the core multi-agent LangGraph pipeline — Planning Agent, Orchestrator Agent, Research Agent, Specialized Business Agents, LLM Council, Reviewer Agent, Critic Agent, Business Rules Engine, Analytics & Scoring Engine, Report Generator. This is the core innovation of the product.
---

# Skill: Multi-Agent Orchestration

## Objective
Implement the Multi-Agent Deliberation Framework: specialized agents reason independently, debate via an LLM Council, undergo review and critique, and are validated against structured business rules before producing executive-ready outputs.

## Pipeline (LangGraph graph, nodes in order)
1. **Planning Agent** — breaks the business idea input + RAG context into a research/analysis plan (which specialized agents need to run, what each should focus on, whether web research is needed)
2. **Orchestrator Agent** — routes tasks to specialized agents per the plan, manages shared pipeline state, tracks completion
3. **Research Agent** — runs live web search (Tavily API) for market/competitor/industry data when documents are absent or thin; results are chunked/embedded into ChromaDB before any other agent consumes them — see `skills/web-research/SKILL.md`
4. **Specialized Business Agents** — run in parallel where possible:
   - Strategy
   - Finance
   - Marketing
   - Legal/Compliance
   - Risk Management
   - Sustainability
   - Investment Analysis
   (Prototype priority: start with Strategy, Finance, Marketing, Risk — add the rest once the pipeline is proven)
5. **LLM Council** — specialized agents' outputs are cross-reviewed by other agents in the council (each agent sees at least one other agent's output and comments on it)
6. **Reviewer Agent** — checks completeness and coherence of council output
7. **Critic Agent** — adversarially critiques the output, actively looks for weak reasoning or unsupported claims
8. **Business Rules Engine** — validates against structured business rules (start as pydantic validators — e.g. financial projections must have positive revenue in year 1 assumptions, required fields present, no contradictions between sections)
9. **Analytics & Scoring Engine** — scores the business plan across dimensions (e.g. viability, market fit, financial soundness) using a weighted rubric
10. **Report Generator** — assembles final output per report type (see `skills/report-generation/SKILL.md`)

## State schema (LangGraph state object — minimum required fields)
`project_id`, `business_idea_input`, `rag_context`, `plan`, `research_results`, `specialized_outputs` (dict keyed by agent name), `council_feedback`, `reviewer_notes`, `critic_notes`, `rules_validation_result`, `scores`, `final_report`.

## Model/API routing (mandatory — see AGENTS.md rate-limit rule)
- Planning Agent, Orchestrator Agent, Specialized Business Agents → NVIDIA NIM
- Reviewer Agent, Critic Agent → Gemini API (spreads load off NIM's ~40 RPM ceiling)
- Research Agent → Tavily API (separate quota entirely, does not touch NIM/Gemini budget — see `skills/web-research/SKILL.md`)
- Every NIM/Gemini call wrapped in exponential backoff + retry on HTTP 429, with failover to the other provider if one is exhausted
- Every Tavily call wrapped in its own backoff/retry; on exhaustion or failure, pipeline continues without web research rather than blocking

## Logging (mandatory — powers the AI Boardroom View)
Every node writes its input and output to the Supabase `agent_logs` table, tagged with `project_id`, `agent_name`, `timestamp`. The frontend AI Boardroom View reads this table to show the deliberation as it happens (poll or Supabase Realtime subscription).

## Testing approach
For each node, write a small test with a fixed mock business idea input and assert the node produces a well-formed output matching its expected schema before wiring it into the full graph. For the Research Agent specifically, test both the happy path (Tavily returns results) and the fallback path (Tavily fails/exhausted) to confirm the pipeline degrades gracefully rather than erroring.
