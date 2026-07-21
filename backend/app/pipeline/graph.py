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
workflow.add_node("council", llm_council_node)
workflow.add_node("reviewer", reviewer_agent_node)
workflow.add_node("critic", critic_agent_node)
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

# Fan-in to LLM Boardroom Council
workflow.add_edge("strategy", "council")
workflow.add_edge("finance", "council")
workflow.add_edge("marketing", "council")
workflow.add_edge("risk", "council")

# Sequence from Council to Reviewer, Critic, and Business Rules Engine
workflow.add_edge("council", "reviewer")
workflow.add_edge("reviewer", "critic")
workflow.add_edge("critic", "rules_engine")
workflow.add_edge("rules_engine", "scoring")
workflow.add_edge("scoring", "report_generator")
workflow.add_edge("report_generator", END)

# 4. Compile the orchestrator pipeline workflow
app = workflow.compile()

def execute_pipeline(initial_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes the compiled multi-agent LangGraph pipeline.
    Invokes nodes starting from planning, through to parallel business agents, council debate, review, critique, and rules validation.
    """
    # Invoke returns the final updated state dictionary
    return app.invoke(initial_state)
