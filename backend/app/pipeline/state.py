from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict):
    """
    State schema for the LangGraph orchestrator graph.
    Maintains variables accumulated across the planning, research, 
    council debate, critique, rules engine, and report assembly nodes.
    """
    project_id: str
    business_idea_input: str
    rag_context: List[str]
    plan: str
    research_results: str
    specialized_outputs: Dict[str, str]
    council_feedback: List[str]
    reviewer_notes: str
    critic_notes: str
    rules_validation_result: Dict[str, Any]
    scores: Dict[str, Any]
    final_report: str
