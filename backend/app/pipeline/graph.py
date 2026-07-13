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

# 3. Configure execution routing
workflow.set_entry_point("planning")
workflow.add_edge("planning", "orchestrator")
workflow.add_edge("orchestrator", "research")

# Fan-out to specialized agents in parallel
workflow.add_edge("research", "strategy")
workflow.add_edge("research", "finance")
workflow.add_edge("research", "marketing")
workflow.add_edge("research", "risk")

# Fan-in back to END
workflow.add_edge("strategy", END)
workflow.add_edge("finance", END)
workflow.add_edge("marketing", END)
workflow.add_edge("risk", END)

# 4. Compile the orchestrator pipeline workflow
app = workflow.compile()

def execute_pipeline(initial_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes the compiled multi-agent LangGraph pipeline.
    Invokes nodes starting from the planning agent through to parallel specialized business agents.
    """
    # Invoke returns the final updated state dictionary
    return app.invoke(initial_state)
