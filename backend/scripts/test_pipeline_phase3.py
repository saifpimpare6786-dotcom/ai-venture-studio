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


import argparse


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


from app.pipeline.cache import fetch_cached_agent_outputs



# ---------------------------------------------------------------------------
# Main test runner
# ---------------------------------------------------------------------------
def run_phase3_test():
    parser = argparse.ArgumentParser(description="AI Venture Studio — Pipeline Phase 3 Test (incl. Report Generator)")
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Bypass cached node outputs in Supabase and re-run all pipeline steps clean",
    )
    parser.add_argument(
        "--project-id",
        type=str,
        default=None,
        help="Specific database project ID to test",
    )
    parser.add_argument(
        "--test-consistency",
        action="store_true",
        help="Run 3 consecutive cached pipeline runs on the same project_id and verify identical outputs",
    )
    args, _ = parser.parse_known_args()

    section("AI Venture Studio — Pipeline Phase 3 Test (incl. Report Generator)")

    # ── Resolve a live project ID from Supabase (or fall back to mock UUID) ──
    project_id = args.project_id or "00000000-0000-0000-0000-000000000000"
    supabase = None
    try:
        supabase = get_supabase_client()
        if not args.project_id:
            res = supabase.table("projects").select("id").limit(1).execute()
            if res.data:
                project_id = res.data[0]["id"]
                safe_print(f"Dynamically resolved database project ID: {project_id}")
        else:
            safe_print(f"Using CLI specified project ID: {project_id}")
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
        "force_refresh": args.force_refresh,
    }

    safe_print(f"\nBusiness Idea: {mock_state['business_idea_input']}")
    safe_print(f"RAG Context items: {len(mock_state['rag_context'])}")
    safe_print(f"Force Refresh: {args.force_refresh}")

    # ── 3x Consistency Test Mode ─────────────────────────────────────────────
    if args.test_consistency:
        section("3x Cache Consistency Test Mode")
        safe_print("Executing 3 consecutive cache-hit lookups on Supabase agent_logs...")
        runs = []
        for i in range(1, 4):
            safe_print(f"\n--- Cache Consistency Run [{i}/3] ---")
            c_state = fetch_cached_agent_outputs(supabase, project_id)
            if not c_state:
                safe_print(f"[FAIL] Run {i}: Cache lookup returned None. Run with --force-refresh to seed complete logs first.")
                sys.exit(1)

            # Calculate total context length and estimated input tokens for Report Generator
            council_str = "\n\n".join(c_state["council_feedback"])
            total_context_chars = (
                len(c_state["plan"])
                + len(c_state["directives"])
                + len(c_state["research_results"])
                + len(c_state["specialized_outputs"].get("finance", ""))
                + len(c_state["specialized_outputs"].get("strategy", ""))
                + len(c_state["specialized_outputs"].get("marketing", ""))
                + len(c_state["specialized_outputs"].get("risk", ""))
                + len(council_str)
                + len(c_state["reviewer_notes"])
                + len(c_state["critic_notes"])
            )
            est_rpt_tokens = total_context_chars // 4

            sig = {
                "council_feedback_count": len(c_state["council_feedback"]),
                "council_feedback_hash": [hash(fb) for fb in c_state["council_feedback"]],
                "plan_len": len(c_state["plan"]),
                "directives_len": len(c_state["directives"]),
                "research_results_len": len(c_state["research_results"]),
                "finance_len": len(c_state["specialized_outputs"].get("finance", "")),
                "strategy_len": len(c_state["specialized_outputs"].get("strategy", "")),
                "marketing_len": len(c_state["specialized_outputs"].get("marketing", "")),
                "risk_len": len(c_state["specialized_outputs"].get("risk", "")),
                "reviewer_notes_len": len(c_state["reviewer_notes"]),
                "critic_notes_len": len(c_state["critic_notes"]),
                "rules_valid": c_state["rules_validation_result"].get("is_valid"),
                "overall_score": c_state["scores"].get("overall_score"),
                "est_report_gen_input_tokens": est_rpt_tokens,
            }
            runs.append(sig)
            safe_print(f"Run {i} State Signature:")
            safe_print(json.dumps({k: v for k, v in sig.items() if k != "council_feedback_hash"}, indent=2))

        # Assert all 3 runs produced identical signatures
        r1, r2, r3 = runs[0], runs[1], runs[2]
        match12 = (r1 == r2)
        match23 = (r2 == r3)

        section("3x Cache Consistency Verification Summary")
        safe_print(f"  Run 1 == Run 2: {match12}")
        safe_print(f"  Run 2 == Run 3: {match23}")
        safe_print(f"  Council Feedback Count across runs: [{r1['council_feedback_count']}, {r2['council_feedback_count']}, {r3['council_feedback_count']}]")
        safe_print(f"  Report Generator Input Tokens across runs: [{r1['est_report_gen_input_tokens']}, {r2['est_report_gen_input_tokens']}, {r3['est_report_gen_input_tokens']}]")

        if match12 and match23 and r1["council_feedback_count"] == 4:
            safe_print("\n  RESULT: PASSED — All 3 consecutive cache-hit runs returned 100% IDENTICAL complete state & token counts!")
        else:
            safe_print("\n  RESULT: FAILED — Output differed between runs or Council feedback count != 4.")
            sys.exit(1)
        return

    # ─────────────────────────────────────────────────────────────────────────
    # Steps 1–12: Check Supabase agent_logs cache before running LLMs
    # ─────────────────────────────────────────────────────────────────────────
    cached_state = None
    if not args.force_refresh and supabase:
        safe_print("\nChecking Supabase agent_logs for cached prior node outputs...")
        cached_state = fetch_cached_agent_outputs(supabase, project_id)

    if cached_state and not args.force_refresh:
        section("CACHE HIT — Reusing Logged Node Outputs from Supabase (Steps 1–12)")
        mock_state.update(cached_state)

        subsection("Step 1 — Planning Agent (Cached)")
        safe_print("[Plan preview]:")
        safe_print(mock_state["plan"][:600] + ("..." if len(mock_state["plan"]) > 600 else ""))

        subsection("Step 2 — Orchestrator Agent (Cached)")
        safe_print("[Directives preview]:")
        safe_print(mock_state["directives"][:600] + ("..." if len(mock_state["directives"]) > 600 else ""))

        subsection("Step 3 — Research Agent (Cached)")
        safe_print("[Research results preview]:")
        safe_print(mock_state["research_results"][:600] + ("..." if len(mock_state["research_results"]) > 600 else ""))

        subsection("Step 4 — Finance Agent (Cached)")
        safe_print("[Finance Agent preview]:")
        safe_print(mock_state["specialized_outputs"].get("finance", "")[:600] + "...")

        subsection("Step 5 — Strategy Agent (Cached)")
        safe_print("[Strategy Agent preview]:")
        safe_print(mock_state["specialized_outputs"].get("strategy", "")[:600] + "...")

        subsection("Step 6 — Marketing Agent (Cached)")
        safe_print("[Marketing Agent preview]:")
        safe_print(mock_state["specialized_outputs"].get("marketing", "")[:600] + "...")

        subsection("Step 7 — Risk Agent (Cached)")
        safe_print("[Risk Agent preview]:")
        safe_print(mock_state["specialized_outputs"].get("risk", "")[:600] + "...")

        subsection("Step 8 — LLM Council (Cached)")
        safe_print(f"[Council feedback count: {len(mock_state['council_feedback'])}]")
        for i, fb in enumerate(mock_state["council_feedback"], 1):
            safe_print(f"  Feedback [{i}] preview: {str(fb)[:300]}...")

        subsection("Step 9 — Reviewer Agent (Cached)")
        safe_print("[Reviewer notes preview]:")
        safe_print(mock_state["reviewer_notes"][:800] + "...")

        subsection("Step 10 — Critic Agent (Cached)")
        safe_print("[Critic notes preview]:")
        safe_print(mock_state["critic_notes"][:800] + "...")

        subsection("Step 11 — Business Rules Engine (Cached)")
        is_valid = mock_state["rules_validation_result"].get("is_valid", False)
        errors   = mock_state["rules_validation_result"].get("errors", [])
        extracted = mock_state["rules_validation_result"].get("extracted_data", {})
        safe_print(f"  is_valid  : {is_valid}")
        safe_print(f"  errors    : {errors}")
        safe_print(f"  extracted : {json.dumps(extracted, indent=4)}")

        subsection("Step 12 — Analytics & Scoring Engine (Cached)")
        safe_print("[Scores]:")
        safe_print(json.dumps(mock_state["scores"], indent=2))

    else:
        if args.force_refresh:
            safe_print("\n[FORCE REFRESH ACTIVE] Bypassing cache — executing all steps 1–12 fresh.")
        else:
            safe_print("\n[CACHE MISS] Running steps 1–12 fresh and logging to Supabase...")

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

        # Step 4 — Finance Agent (must run before Strategy AND Marketing)
        subsection("Step 4 — Finance Agent")
        fin_out = finance_agent_node(mock_state)
        mock_state["specialized_outputs"].update(fin_out.get("specialized_outputs", {}))
        if fin_out.get("failed_agents"):
            mock_state["failed_agents"].extend(fin_out["failed_agents"])
        safe_print("[Finance Agent preview]:")
        safe_print(mock_state["specialized_outputs"].get("finance", "")[:600] + "...")

        # Step 5 — Strategy Agent  [reads Finance pricing from state — matches graph topology]
        subsection("Step 5 — Strategy Agent  [reads Finance pricing from state]")
        strat_out = strategy_agent_node(mock_state)
        mock_state["specialized_outputs"].update(strat_out.get("specialized_outputs", {}))
        if strat_out.get("failed_agents"):
            mock_state["failed_agents"].extend(strat_out["failed_agents"])
        safe_print("[Strategy Agent preview]:")
        safe_print(mock_state["specialized_outputs"].get("strategy", "")[:600] + "...")

        # Step 6 — Marketing Agent  [reads Finance pricing from state, parallel with Strategy in graph]
        subsection("Step 6 — Marketing Agent  [reads Finance pricing from state]")
        mkt_out = marketing_agent_node(mock_state)
        mock_state["specialized_outputs"].update(mkt_out.get("specialized_outputs", {}))
        if mkt_out.get("failed_agents"):
            mock_state["failed_agents"].extend(mkt_out["failed_agents"])
        safe_print("[Marketing Agent preview]:")
        safe_print(mock_state["specialized_outputs"].get("marketing", "")[:600] + "...")

        # Step 7 — Risk Agent  [runs in parallel with Finance in the graph; sequential here for simplicity]
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

    # Capture the raw Executive Summary JSON produced during Step 13's actual execution
    # directly from report_generator_node outputs (or database fallback).
    import json as _json

    generated_reports = rpt_out.get("generated_reports", {})
    report_content = generated_reports.get("Executive Summary", {})

    if not report_content and supabase:
        try:
            db_res = supabase.table("reports").select("content").eq("project_id", project_id).eq("report_type", "Executive Summary").execute()
            if db_res.data:
                report_content = db_res.data[0].get("content") or {}
        except Exception:
            pass

    validation_passed = False
    validation_errors = []

    if not report_content or "error" in report_content:
        safe_print(f"\n[VALIDATION] Executive Summary content missing or failed: {report_content.get('error', 'No content')}")
    else:
        try:
            safe_print("\n[Raw JSON captured from Step 13 Executive Summary output]:")
            safe_print(_json.dumps(report_content, indent=2, ensure_ascii=False))

            # Coerce types before Pydantic validation
            report_content = _coerce_schema_fields(report_content, ExecutiveSummarySchema)

            # Validate against schema
            validated = ExecutiveSummarySchema.model_validate(report_content)
            validation_passed = True

        except ValidationError as ve:
            for err in ve.errors():
                msg = err.get("msg", "Unknown error")
                loc = " -> ".join(str(l) for l in err.get("loc", []))
                validation_errors.append(f"{loc}: {msg}")
        except Exception as ex:
            validation_errors.append(f"Validation error: {ex}")


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
    section("Full Report Suite (8 Reports) Test Complete")
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
