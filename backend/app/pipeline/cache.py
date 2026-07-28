from typing import Dict, Any, Optional

def fetch_cached_agent_outputs(supabase, project_id: str) -> Optional[Dict[str, Any]]:
    """
    Attempts to fetch the latest completed, fully valid output from Supabase agent_logs
    for all 12 prior nodes:
    1. Planning Agent
    2. Orchestrator Agent
    3. Research Agent
    4. Finance Agent
    5. Strategy Agent
    6. Marketing Agent
    7. Risk Agent
    8. Council Agent (or LLM Council)
    9. Reviewer Agent
    10. Critic Agent
    11. Business Rules Engine
    12. Analytics & Scoring Engine

    Guarantees determinism by ordering by timestamp DESC, id DESC and querying per node type
    to strictly filter out any partial, warning, failed, or incomplete log entries in favor
    of the most recent fully complete one.

    Returns a populated state dict if ALL 12 prior node outputs exist and pass validation,
    or None if any node output is missing or incomplete.
    """
    if not supabase or not project_id:
        return None

    try:
        # Fetch all log rows for project_id ordered deterministically by timestamp DESC, id DESC
        res = (
            supabase.table("agent_logs")
            .select("agent_name, status, input_data, output_data, timestamp, id")
            .eq("project_id", project_id)
            .order("timestamp", desc=True)
            .order("id", desc=True)
            .execute()
        )

        if not res.data:
            return None

        # Helper to find latest valid log entry for given agent name filter function
        def get_latest_valid_output(agent_name_matcher, validator_fn, min_timestamp: Optional[str] = None):
            for row in res.data:
                name = row.get("agent_name", "")
                if agent_name_matcher(name):
                    status = row.get("status", "")
                    ts = row.get("timestamp", "unknown")
                    row_id = row.get("id", "unknown")

                    # Enforce timestamp cohesion: downstream nodes must be logged at or after min_timestamp
                    if min_timestamp and ts < min_timestamp:
                        print(f"[Cache Miss] Node '{name}' log ({ts}) predates latest Planning run ({min_timestamp}). Skipping stale entry.")
                        continue

                    out = row.get("output_data") or {}
                    val = validator_fn(status, out)
                    if val is not None:
                        print(f"[Cache Hit] Node: '{name}' | Log ID: {row_id} | Timestamp: {ts}")
                        return {"val": val, "timestamp": ts, "id": row_id}
            return None

        # 1. Planning Agent — establishes the min_timestamp baseline for all downstream nodes
        def val_planning(status, out):
            if status == "completed":
                plan = out.get("plan", "")
                if isinstance(plan, str) and len(plan.strip()) >= 200 and not plan.startswith("Execution failed:") and plan != "__FAILED__":
                    return plan
            return None

        plan_entry = get_latest_valid_output(lambda name: name == "Planning Agent", val_planning)
        if not plan_entry:
            return None
        plan = plan_entry["val"]
        min_ts = plan_entry["timestamp"]

        # 2. Orchestrator Agent
        def val_orch(status, out):
            if status == "completed":
                directives = out.get("directives") or out.get("orchestration", "")
                if isinstance(directives, str) and len(directives.strip()) >= 200 and not directives.startswith("Execution failed:") and directives != "__FAILED__":
                    return directives
            return None

        orch_entry = get_latest_valid_output(lambda name: name == "Orchestrator Agent", val_orch, min_timestamp=min_ts)
        if not orch_entry:
            return None
        directives = orch_entry["val"]

        # 3. Research Agent
        def val_research(status, out):
            if status in ("completed", "completed (cached)"):
                res_text = out.get("research_results") or out.get("research_summary", "")
                if isinstance(res_text, str) and len(res_text.strip()) >= 200 and not res_text.startswith("Execution failed:") and res_text != "__FAILED__":
                    return res_text
            return None

        res_entry = get_latest_valid_output(lambda name: name == "Research Agent", val_research, min_timestamp=min_ts)
        if not res_entry:
            return None
        research_results = res_entry["val"]

        # 4. Specialized Business Agents (Finance, Strategy, Marketing, Risk)
        specialized_outputs = {}
        for spec_agent, spec_key in [
            ("Finance Agent", "finance"),
            ("Strategy Agent", "strategy"),
            ("Marketing Agent", "marketing"),
            ("Risk Agent", "risk"),
        ]:
            def make_val_spec(target_key):
                def val_spec(status, out):
                    if status == "completed":
                        text = out.get(target_key) or out.get("assessment", "")
                        if isinstance(text, str) and len(text.strip()) >= 200 and not text.startswith("Execution failed:") and text != "__FAILED__":
                            return text
                    return None
                return val_spec

            spec_entry = get_latest_valid_output(lambda name, sa=spec_agent: name == sa, make_val_spec(spec_key), min_timestamp=min_ts)
            if not spec_entry:
                return None
            specialized_outputs[spec_key] = spec_entry["val"]

        # 5. Council Agent (MUST be status="completed", failure_count == 0, and exactly 4 complete valid reviews)
        def val_council(status, out):
            if status == "completed":
                failure_count = out.get("failure_count", 0)
                feedback_list = out.get("council_feedback") or out.get("feedback_list") or []
                if failure_count == 0 and isinstance(feedback_list, list) and len(feedback_list) == 4:
                    valid_feedback = [
                        fb for fb in feedback_list
                        if isinstance(fb, str)
                        and len(fb.strip()) >= 20
                        and not fb.startswith("Council review failed")
                        and "Review threw an exception" not in fb
                        and not fb.startswith("Execution failed:")
                    ]
                    if len(valid_feedback) == 4:
                        return valid_feedback
            return None

        council_entry = get_latest_valid_output(
            lambda name: name in ("Council Agent", "LLM Council"), val_council, min_timestamp=min_ts
        )
        if not council_entry:
            return None
        council_feedback = council_entry["val"]

        # 6. Reviewer Agent
        def val_reviewer(status, out):
            if status == "completed":
                rev = out.get("reviewer_notes", "")
                if isinstance(rev, str) and len(rev.strip()) >= 200 and not rev.startswith("Execution failed:") and rev != "__FAILED__":
                    return rev
            return None

        reviewer_entry = get_latest_valid_output(lambda name: name == "Reviewer Agent", val_reviewer, min_timestamp=min_ts)
        if not reviewer_entry:
            return None
        reviewer_notes = reviewer_entry["val"]

        # 7. Critic Agent
        def val_critic(status, out):
            if status == "completed":
                critic = out.get("critic_notes", "")
                if isinstance(critic, str) and len(critic.strip()) >= 200 and not critic.startswith("Execution failed:") and critic != "__FAILED__":
                    return critic
            return None

        critic_entry = get_latest_valid_output(lambda name: name == "Critic Agent", val_critic, min_timestamp=min_ts)
        if not critic_entry:
            return None
        critic_notes = critic_entry["val"]

        # 8. Business Rules Engine — MUST be status="completed" and is_valid MUST be True
        def val_rules(status, out):
            if status == "completed":
                rules_res = out.get("rules_validation_result") or out.get("validation_result", {})
                if isinstance(rules_res, dict) and rules_res.get("is_valid") is True and "extracted_data" in rules_res:
                    return rules_res
            return None

        rules_entry = get_latest_valid_output(lambda name: name == "Business Rules Engine", val_rules, min_timestamp=min_ts)
        if not rules_entry:
            return None
        rules_validation_result = rules_entry["val"]

        # 9. Analytics & Scoring Engine
        def val_scoring(status, out):
            if status == "completed":
                scores = out.get("scores", {})
                if isinstance(scores, dict) and "overall_score" in scores and scores.get("overall_score", 0) > 0:
                    return scores
            return None

        scoring_entry = get_latest_valid_output(lambda name: name == "Analytics & Scoring Engine", val_scoring, min_timestamp=min_ts)
        if not scoring_entry:
            return None
        scores = scoring_entry["val"]

        return {
            "plan": plan,
            "directives": directives,
            "research_results": research_results,
            "specialized_outputs": specialized_outputs,
            "council_feedback": council_feedback,
            "reviewer_notes": reviewer_notes,
            "critic_notes": critic_notes,
            "rules_validation_result": rules_validation_result,
            "scores": scores,
        }

    except Exception as e:
        print(f"[Cache Lookup Warning] Error querying agent_logs: {e}")
        return None
