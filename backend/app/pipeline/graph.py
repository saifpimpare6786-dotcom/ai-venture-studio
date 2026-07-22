from langgraph.graph import StateGraph, END
from app.pipeline.state import AgentState
from app.pipeline.planning_agent import planning_agent_node
from app.pipeline.orchestrator_agent import orchestrator_agent_node
from app.pipeline.research_agent import research_agent_node
from app.pipeline.specialized_agents import (
    strategy_agent_node,
    finance_agent_node,
    marketing_agent_node,
    risk_agent_node
)
from app.pipeline.council_agent import llm_council_node
from app.pipeline.review_critic_agents import (
    reviewer_agent_node,
    critic_agent_node
)
from app.pipeline.rules_engine import business_rules_engine_node
from app.pipeline.scoring_engine import analytics_scoring_node
from app.pipeline.report_generator import report_generator_node
from typing import Dict, Any

# ---------------------------------------------------------------------------
# Pipeline Gate Nodes
# ---------------------------------------------------------------------------

def pipeline_gate_node(state: AgentState) -> Dict[str, Any]:
    """
    Gate 1: runs after all four specialized agents fan in.
    If any agent wrote its key into failed_agents, marks the pipeline as
    aborted so the conditional edge can route to END instead of Council.
    """
    failed = state.get("failed_agents") or []
    if failed:
        abort_reason = (
            f"Pipeline halted: specialized agent(s) exhausted all LLM fallbacks — "
            f"failed nodes: {', '.join(failed)}"
        )
        print(f"[Pipeline Gate] {abort_reason}")
        return {"pipeline_aborted": True, "abort_reason": abort_reason}
    print("[Pipeline Gate] All specialized agents succeeded — routing to Council.")
    return {}


def post_critic_gate_node(state: AgentState) -> Dict[str, Any]:
    """
    Gate 2: runs after Critic (before Rules Engine).
    If Reviewer or Critic wrote their key into failed_agents, aborts the
    pipeline rather than feeding __FAILED__ into the Rules Engine and Scoring.
    """
    failed = state.get("failed_agents") or []
    # Only care about reviewer/critic failures here; specialized-agent failures
    # would already have been caught by Gate 1 above.
    post_council_failed = [f for f in failed if f in ("reviewer", "critic")]
    if post_council_failed:
        abort_reason = (
            f"Pipeline halted: post-council agent(s) exhausted all LLM fallbacks — "
            f"failed nodes: {', '.join(post_council_failed)}"
        )
        print(f"[Post-Critic Gate] {abort_reason}")
        return {"pipeline_aborted": True, "abort_reason": abort_reason}
    # Also respect an abort that Gate 1 may have already set
    if state.get("pipeline_aborted"):
        return {}
    print("[Post-Critic Gate] Reviewer and Critic succeeded — routing to Rules Engine.")
    return {}


# ---------------------------------------------------------------------------
# Conditional routing functions
# ---------------------------------------------------------------------------

def route_after_gate(state: AgentState) -> str:
    """Routes to 'council' if pipeline is healthy, else to END."""
    if state.get("pipeline_aborted"):
        return END
    return "council"


def route_after_post_critic_gate(state: AgentState) -> str:
    """Routes to 'rules_engine' if pipeline is healthy, else to END."""
    if state.get("pipeline_aborted"):
        return END
    return "rules_engine"


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

# 1. Initialize StateGraph with the custom AgentState TypedDict schema
workflow = StateGraph(AgentState)

# 2. Register the nodes
workflow.add_node("planning", planning_agent_node)
workflow.add_node("orchestrator", orchestrator_agent_node)
workflow.add_node("research", research_agent_node)
workflow.add_node("strategy", strategy_agent_node)
workflow.add_node("finance", finance_agent_node)
workflow.add_node("marketing", marketing_agent_node)
workflow.add_node("risk", risk_agent_node)
workflow.add_node("pipeline_gate", pipeline_gate_node)
workflow.add_node("council", llm_council_node)
workflow.add_node("reviewer", reviewer_agent_node)
workflow.add_node("critic", critic_agent_node)
workflow.add_node("post_critic_gate", post_critic_gate_node)
workflow.add_node("rules_engine", business_rules_engine_node)
workflow.add_node("scoring", analytics_scoring_node)
workflow.add_node("report_generator", report_generator_node)

# 3. Configure execution routing
workflow.set_entry_point("planning")
workflow.add_edge("planning", "orchestrator")
workflow.add_edge("orchestrator", "research")

# Fan-out to specialized agents in parallel
workflow.add_edge("research", "strategy")
workflow.add_edge("research", "finance")
workflow.add_edge("research", "marketing")
workflow.add_edge("research", "risk")

# Fan-in through Gate 1 before Council
workflow.add_edge("strategy", "pipeline_gate")
workflow.add_edge("finance", "pipeline_gate")
workflow.add_edge("marketing", "pipeline_gate")
workflow.add_edge("risk", "pipeline_gate")

# Gate 1 conditional: healthy → Council, aborted → END
workflow.add_conditional_edges("pipeline_gate", route_after_gate)

# Sequence from Council through Reviewer → Critic → Gate 2
workflow.add_edge("council", "reviewer")
workflow.add_edge("reviewer", "critic")
workflow.add_edge("critic", "post_critic_gate")

# Gate 2 conditional: healthy → Rules Engine, aborted → END
workflow.add_conditional_edges("post_critic_gate", route_after_post_critic_gate)

workflow.add_edge("rules_engine", "scoring")
workflow.add_edge("scoring", "report_generator")
workflow.add_edge("report_generator", END)

# 4. Compile the orchestrator pipeline workflow
app = workflow.compile()

def execute_pipeline(initial_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes the compiled multi-agent LangGraph pipeline.
    Invokes nodes starting from planning, through to parallel business agents,
    council debate, review, critique, and rules validation.

    Returns the final state dictionary. Callers should check:
        result.get("pipeline_aborted") — True if a hard-gate fired.
        result.get("abort_reason")     — Human-readable explanation.
    """
    return app.invoke(initial_state)
