from typing import TypedDict, List, Dict, Any, NotRequired, Annotated

def merge_dict(left: Dict[str, Any], right: Dict[str, Any]) -> Dict[str, Any]:
    """Reducer that merges dict updates from parallel nodes instead of overwriting."""
    new_dict = left.copy() if left else {}
    if right:
        new_dict.update(right)
    return new_dict

def list_append_reducer(left: List[str], right: List[str]) -> List[str]:
    """Reducer that appends new items to the existing list (used for failed_agents)."""
    result = list(left) if left else []
    if right:
        result.extend(right)
    return result

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
    # Failure tracking: accumulated across parallel branches via list_append_reducer
    failed_agents: NotRequired[Annotated[List[str], list_append_reducer]]
    pipeline_aborted: NotRequired[bool]
    abort_reason: NotRequired[str]
    council_feedback: List[str]
    reviewer_notes: str
    critic_notes: str
    rules_validation_result: Dict[str, Any]
    scores: Dict[str, Any]
    final_report: str
    force_refresh: NotRequired[bool]
