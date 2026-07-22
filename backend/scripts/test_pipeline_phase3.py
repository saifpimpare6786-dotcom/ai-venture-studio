# -*- coding: utf-8 -*-
"""
test_pipeline_phase3.py
=======================
End-to-end pipeline test extending phase 2 with the Report Generator step.

Execution order mirrors the LangGraph graph exactly:
  1.  Planning Agent
  2.  Orchestrator Agent
  3.  Research Agent
  4.  Finance Agent           ← sequential (Marketing depends on it)
  5.  Marketing Agent         ← reads Finance output from state
  6.  Strategy Agent          ← parallel with Finance/Risk in production; sequential here
  7.  Risk Agent
  8.  LLM Council
  9.  Reviewer Agent
  10. Critic Agent
  11. Business Rules Engine
  12. Analytics & Scoring Engine
  13. Report Generator         ← NEW (Phase 3)
      a) Generates Executive Summary report
      b) Validates output against ExecutiveSummarySchema
      c) Prints full report text and validation result

Run from the backend directory:
    python -X utf8 scripts/test_pipeline_phase3.py
"""

import os
import sys
import json

# ---------------------------------------------------------------------------
# Path + env setup (identical to phase 2)
# ---------------------------------------------------------------------------
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from dotenv import load_dotenv
backend_env = os.path.join(backend_dir, ".env")
if os.path.exists(backend_env):
    load_dotenv(backend_env)
else:
    load_dotenv(os.path.join(backend_dir, "..", ".env"))

# Supply mock credentials if Supabase vars are missing so the script runs offline
if not os.environ.get("SUPABASE_URL"):
    os.environ["SUPABASE_URL"] = "https://mockproject.supabase.co"
if not os.environ.get("SUPABASE_SERVICE_ROLE_KEY"):
    os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "mockservicekey"


# ---------------------------------------------------------------------------
# Imports (deferred until after env is set)
# ---------------------------------------------------------------------------
from app.database.supabase import get_supabase_client
from app.pipeline.planning_agent import planning_agent_node
from app.pipeline.orchestrator_agent import orchestrator_agent_node
from app.pipeline.research_agent import research_agent_node
from app.pipeline.specialized_agents import (
    strategy_agent_node,
    finance_agent_node,
    marketing_agent_node,
    risk_agent_node,
)
from app.pipeline.council_agent import llm_council_node
from app.pipeline.review_critic_agents import reviewer_agent_node, critic_agent_node
from app.pipeline.rules_engine import business_rules_engine_node
from app.pipeline.scoring_engine import analytics_scoring_node
from app.pipeline.report_generator import report_generator_node, _build_registry, _coerce_schema_fields
from app.schemas.report import ExecutiveSummarySchema
from pydantic import ValidationError


# ---------------------------------------------------------------------------
# Terminal-safe printer (handles Windows CP1252 stdout encoding)
# ---------------------------------------------------------------------------
def safe_print(text):
    if text is None:
        print(None)
        return
    if not isinstance(text, str):
        print(text)
        return
    enc = sys.stdout.encoding or "utf-8"
    print(text.encode(enc, errors="replace").decode(enc))


def section(title: str):
    """Prints a prominent section banner."""
    bar = "=" * 70
    safe_print(f"\n{bar}")
    safe_print(f"  {title}")
    safe_print(bar)


def subsection(title: str):
    safe_print(f"\n--- {title} ---")


# ---------------------------------------------------------------------------
# Main test runner
# ---------------------------------------------------------------------------
def run_phase3_test():
    section("AI Venture Studio — Pipeline Phase 3 Test (incl. Report Generator)")

    # ── Resolve a live project ID from Supabase (or fall back to mock UUID) ──
    project_id = "00000000-0000-0000-0000-000000000000"
    try:
        supabase = get_supabase_client()
        res = supabase.table("projects").select("id").limit(1).execute()
        if res.data:
            project_id = res.data[0]["id"]
            safe_print(f"Dynamically resolved database project ID: {project_id}")
    except Exception as db_err:
        safe_print(f"Database lookup warning (using mock project ID): {db_err}")

    # ── Initial state — includes all fields required by the gate nodes ────────
    mock_state = {
        "project_id": project_id,
        "business_idea_input": (
            "EcoSphere is an automated SaaS platform for carbon compliance auditing. "
            "It targets SMEs by connecting directly to utility providers to read usage "
            "details and calculate emission metrics, saving significant operational "
            "reporting overhead. Target market: UK-based SMEs with 20–500 employees. "
            "Pricing model: tiered subscription."
        ),
        "rag_context": [
            "National carbon emission accounting policies in 2026 enforce stricter "
            "reporting deadlines for UK SMEs.",
            "Utility connection APIs offer reliable hourly data feeds for power and "
            "water usage analytics.",
            "UK Environment Act 2021 mandates carbon disclosures for companies above "
            "250 employees from 2025.",
        ],
        "plan": "",
        "directives": "",
        "research_results": "",
        "specialized_outputs": {},
        # Failure-tracking fields required by pipeline gate nodes
        "failed_agents": [],
        "pipeline_aborted": False,
        "abort_reason": "",
        "council_feedback": [],
        "reviewer_notes": "",
        "critic_notes": "",
        "rules_validation_result": {},
        "scores": {},
        "final_report": "",
        "force_refresh": True,
    }

    safe_print(f"\nBusiness Idea: {mock_state['business_idea_input']}")
    safe_print(f"RAG Context items: {len(mock_state['rag_context'])}")

    # ─────────────────────────────────────────────────────────────────────────
    # Steps 1–12: identical to phase 2 (reproduced here so this script is
    # fully self-contained and runnable without phase 2 being imported)
    # ─────────────────────────────────────────────────────────────────────────

    # Step 1 — Planning Agent
    subsection("Step 1 — Planning Agent")
    plan_out = planning_agent_node(mock_state)
    mock_state["plan"] = plan_out.get("plan", "")
    safe_print("[Plan preview]:")
    safe_print(mock_state["plan"][:600] + ("..." if len(mock_state["plan"]) > 600 else ""))

    # Step 2 — Orchestrator Agent
    subsection("Step 2 — Orchestrator Agent")
    orch_out = orchestrator_agent_node(mock_state)
    mock_state["directives"] = orch_out.get("directives", "")
    safe_print("[Directives preview]:")
    safe_print(mock_state["directives"][:600] + ("..." if len(mock_state["directives"]) > 600 else ""))

    # Step 3 — Research Agent
    subsection("Step 3 — Research Agent")
    research_out = research_agent_node(mock_state)
    mock_state["research_results"] = research_out.get("research_results", "")
    safe_print("[Research results preview]:")
    safe_print(mock_state["research_results"][:600] + ("..." if len(mock_state["research_results"]) > 600 else ""))

    # Step 4 — Finance Agent (must run before Marketing)
    subsection("Step 4 — Finance Agent")
    fin_out = finance_agent_node(mock_state)
    mock_state["specialized_outputs"].update(fin_out.get("specialized_outputs", {}))
    if fin_out.get("failed_agents"):
        mock_state["failed_agents"].extend(fin_out["failed_agents"])
    safe_print("[Finance Agent preview]:")
    safe_print(mock_state["specialized_outputs"].get("finance", "")[:600] + "...")

    # Step 5 — Marketing Agent (reads Finance output from state)
    subsection("Step 5 — Marketing Agent  [reads Finance pricing from state]")
    mkt_out = marketing_agent_node(mock_state)
    mock_state["specialized_outputs"].update(mkt_out.get("specialized_outputs", {}))
    if mkt_out.get("failed_agents"):
        mock_state["failed_agents"].extend(mkt_out["failed_agents"])
    safe_print("[Marketing Agent preview]:")
    safe_print(mock_state["specialized_outputs"].get("marketing", "")[:600] + "...")

    # Step 6 — Strategy Agent
    subsection("Step 6 — Strategy Agent")
    strat_out = strategy_agent_node(mock_state)
    mock_state["specialized_outputs"].update(strat_out.get("specialized_outputs", {}))
    if strat_out.get("failed_agents"):
        mock_state["failed_agents"].extend(strat_out["failed_agents"])
    safe_print("[Strategy Agent preview]:")
    safe_print(mock_state["specialized_outputs"].get("strategy", "")[:600] + "...")

    # Step 7 — Risk Agent
    subsection("Step 7 — Risk Agent")
    risk_out = risk_agent_node(mock_state)
    mock_state["specialized_outputs"].update(risk_out.get("specialized_outputs", {}))
    if risk_out.get("failed_agents"):
        mock_state["failed_agents"].extend(risk_out["failed_agents"])
    safe_print("[Risk Agent preview]:")
    safe_print(mock_state["specialized_outputs"].get("risk", "")[:600] + "...")

    # Check gate 1 — if any specialized agent failed, abort now
    if mock_state["failed_agents"]:
        safe_print(
            f"\n[GATE 1] Pipeline aborted — failed specialized agents: "
            f"{mock_state['failed_agents']}"
        )
        safe_print("Skipping remaining steps.")
        return

    # Step 8 — LLM Council
    subsection("Step 8 — LLM Council")
    council_out = llm_council_node(mock_state)
    mock_state["council_feedback"] = council_out.get("council_feedback", [])
    safe_print(f"[Council feedback count: {len(mock_state['council_feedback'])}]")
    for i, fb in enumerate(mock_state["council_feedback"], 1):
        safe_print(f"  Feedback [{i}] preview: {str(fb)[:300]}...")

    # Step 9 — Reviewer Agent
    subsection("Step 9 — Reviewer Agent")
    rev_out = reviewer_agent_node(mock_state)
    mock_state["reviewer_notes"] = rev_out.get("reviewer_notes", "")
    if rev_out.get("failed_agents"):
        mock_state["failed_agents"].extend(rev_out["failed_agents"])
    safe_print("[Reviewer notes preview]:")
    safe_print(mock_state["reviewer_notes"][:800] + "...")

    # Step 10 — Critic Agent
    subsection("Step 10 — Critic Agent")
    critic_out = critic_agent_node(mock_state)
    mock_state["critic_notes"] = critic_out.get("critic_notes", "")
    if critic_out.get("failed_agents"):
        mock_state["failed_agents"].extend(critic_out["failed_agents"])
    safe_print("[Critic notes preview]:")
    safe_print(mock_state["critic_notes"][:800] + "...")

    # Check gate 2 — Reviewer or Critic failures
    post_council_failures = [
        f for f in mock_state["failed_agents"] if f in ("reviewer", "critic")
    ]
    if post_council_failures:
        safe_print(
            f"\n[GATE 2] Pipeline aborted — failed post-council agents: "
            f"{post_council_failures}"
        )
        safe_print("Skipping Report Generator.")
        return

    # Step 11 — Business Rules Engine
    subsection("Step 11 — Business Rules Engine")
    rules_out = business_rules_engine_node(mock_state)
    mock_state["rules_validation_result"] = rules_out.get("rules_validation_result", {})
    is_valid = mock_state["rules_validation_result"].get("is_valid", False)
    errors   = mock_state["rules_validation_result"].get("errors", [])
    extracted = mock_state["rules_validation_result"].get("extracted_data", {})
    safe_print(f"  is_valid  : {is_valid}")
    safe_print(f"  errors    : {errors}")
    safe_print(f"  extracted : {json.dumps(extracted, indent=4)}")

    # Step 12 — Analytics & Scoring Engine
    subsection("Step 12 — Analytics & Scoring Engine")
    scoring_out = analytics_scoring_node(mock_state)
    mock_state["scores"] = scoring_out.get("scores", {})
    safe_print("[Scores]:")
    safe_print(json.dumps(mock_state["scores"], indent=2))

    # ─────────────────────────────────────────────────────────────────────────
    # Step 13 — Report Generator  [PHASE 3 ADDITION]
    # ─────────────────────────────────────────────────────────────────────────
    section("Step 13 — Report Generator  [Phase 3]")

    rpt_out = report_generator_node(mock_state)
    mock_state["final_report"] = rpt_out.get("final_report", "")

    # ── 13a. Print the full final_report text ─────────────────────────────
    subsection("13a — Full final_report text")
    safe_print(mock_state["final_report"])

    # ── 13b. Validate Executive Summary against Pydantic schema ───────────
    subsection("13b — Executive Summary Pydantic schema validation")

    # The node writes all reports to Supabase and returns a Markdown summary
    # string. For schema validation we reconstruct the Executive Summary JSON
    # from the registry using the same context the node used, then validate it.
    # This mirrors what the node does internally and lets us inspect the raw
    # structured object.

    safe_print("\nAttempting to extract Executive Summary JSON from report_generator output...")

    # Re-run just the Executive Summary LLM call and capture raw JSON
    import json as _json
    from services.llm import call_llm
    from app.pipeline.report_generator import extract_json_block

    context = {
        "idea":        mock_state["business_idea_input"],
        "strategy":    mock_state["specialized_outputs"].get("strategy", ""),
        "finance":     mock_state["specialized_outputs"].get("finance", ""),
        "marketing":   mock_state["specialized_outputs"].get("marketing", ""),
        "risk":        mock_state["specialized_outputs"].get("risk", ""),
        "council_str": "\n---\n".join(mock_state["council_feedback"])
                       if mock_state["council_feedback"] else "No council feedback.",
        "reviewer":    mock_state["reviewer_notes"],
        "critic":      mock_state["critic_notes"],
        "rules_json":  _json.dumps(mock_state["rules_validation_result"], indent=2),
        "scores_json": _json.dumps(mock_state["scores"], indent=2),
        "overall_score": mock_state["scores"].get("overall_score", 0.0),
    }

    registry = _build_registry(context)
    exec_config = registry["Executive Summary"]

    safe_print("\nCalling Gemini to generate Executive Summary for schema validation...")
    raw_text = call_llm(
        prompt="Generate the report as instructed.",
        system_prompt=exec_config["system_prompt"],
        preferred_provider="gemini",
        project_id=project_id,
        agent_name="Executive Summary Generator [Phase 3 Test]",
    )

    validation_passed = False
    validation_errors = []
    report_content    = {}

    if isinstance(raw_text, dict) and raw_text.get("status") == "failed":
        safe_print(f"\n[VALIDATION] LLM call failed: {raw_text.get('error')}")
    else:
        try:
            cleaned = extract_json_block(raw_text)
            report_content = _json.loads(cleaned)
            safe_print("\n[Raw JSON extracted from LLM response]:")
            safe_print(_json.dumps(report_content, indent=2, ensure_ascii=False))

            # Coerce types before Pydantic validation
            report_content = _coerce_schema_fields(report_content, ExecutiveSummarySchema)

            # Validate against schema
            validated = ExecutiveSummarySchema.model_validate(report_content)
            validation_passed = True

        except _json.JSONDecodeError as je:
            validation_errors.append(f"JSON parse error: {je}")
            safe_print(f"\n[RAW LLM output that failed JSON parse]:\n{raw_text}")
        except ValidationError as ve:
            for err in ve.errors():
                msg = err.get("msg", "Unknown error")
                loc = " -> ".join(str(l) for l in err.get("loc", []))
                validation_errors.append(f"{loc}: {msg}")

    # ── 13c. Print validation result ──────────────────────────────────────
    subsection("13c — Validation Result")

    if validation_passed:
        safe_print("\n  RESULT : PASSED")
        safe_print(f"  Overall Score in report: {report_content.get('overall_score')}")
        recs = report_content.get("key_recommendations", [])
        safe_print(f"  key_recommendations count: {len(recs)}")
        for i, rec in enumerate(recs, 1):
            safe_print(f"    [{i}] {rec}")
    else:
        safe_print("\n  RESULT : FAILED")
        safe_print(f"  Validation errors ({len(validation_errors)}):")
        for err in validation_errors:
            safe_print(f"    - {err}")

    # ── Final summary ─────────────────────────────────────────────────────
    section("Phase 3 Test Complete")
    rules_ok  = mock_state["rules_validation_result"].get("is_valid", False)
    score_val = mock_state["scores"].get("overall_score", "N/A")
    safe_print(f"  Business Rules validation : {'PASSED' if rules_ok else 'FAILED'}")
    safe_print(f"  Overall viability score   : {score_val}")
    safe_print(f"  Report generation         : {'COMPLETED' if mock_state['final_report'] else 'NO OUTPUT'}")
    safe_print(f"  Executive Summary schema  : {'PASSED' if validation_passed else 'FAILED'}")
    if validation_errors:
        safe_print(f"  Schema errors             : {validation_errors}")


if __name__ == "__main__":
    run_phase3_test()
