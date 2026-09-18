from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict, total=False):
    project_id: str
    project_data: Dict[str, Any]
    
    # 1. Planning & Research
    plan: Dict[str, Any]
    research_results: List[Dict[str, Any]]
    rag_context: str
    
    # 2. Specialized Domains
    finance_assessment: Dict[str, Any] # Authoritative pricing anchor
    strategy_assessment: Dict[str, Any]
    marketing_assessment: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    
    # 3. Deliberation & Evaluation
    council_debate: Dict[str, Any]
    reviewer_assessment: Dict[str, Any]
    critic_assessment: Dict[str, Any]
    
    # 4. Deterministic Validation & Scoring
    rules_validation: Dict[str, Any]
    scores: Dict[str, Any]
    
    # 5. Output Reports & Telemetry
    reports: Dict[str, Any]
    discussion_logs: List[Dict[str, Any]]
    error_gate_status: Dict[str, Any]
    status: str
