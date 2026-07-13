from typing import TypedDict, List, Dict, Any, NotRequired, Annotated

def merge_dict(left: Dict[str, Any], right: Dict[str, Any]) -> Dict[str, Any]:
    """Reducer that merges dict updates from parallel nodes instead of overwriting."""
    new_dict = left.copy() if left else {}
    if right:
        new_dict.update(right)
    return new_dict

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
    directives: NotRequired[str]
    research_results: str
    specialized_outputs: Annotated[Dict[str, str], merge_dict]
    council_feedback: List[str]
    reviewer_notes: str
    critic_notes: str
    rules_validation_result: Dict[str, Any]
    scores: Dict[str, Any]
    final_report: str
    force_refresh: NotRequired[bool]
