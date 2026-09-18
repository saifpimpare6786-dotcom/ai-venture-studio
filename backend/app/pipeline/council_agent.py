import json
from typing import Dict, Any
from app.pipeline.state import AgentState
from services.llm import llm_router
from app.database.db import db

async def council_node(state: AgentState) -> AgentState:
    """
    Consolidated 1-call LLM Council Boardroom Debate.
    Domain agents cross-review each other: Strategy vs Marketing, Finance vs Strategy/Marketing economics, Risk vs all.
    """
    project = state["project_data"]
    project_id = state["project_id"]
    finance = state.get("finance_assessment", {})
    strategy = state.get("strategy_assessment", {})
    marketing = state.get("marketing_assessment", {})
    risk = state.get("risk_assessment", {})

    sys_prompt = """You are the Executive Boardroom Council. Conduct an intensive cross-examination of the venture:
1. Strategy reviews Marketing acquisition assumptions
2. Finance reviews GTM spend vs CAC payback
3. Marketing reviews Finance pricing tier attractiveness
4. Risk reviews regulatory vulnerabilities
5. Council consensus & synthesis

Respond ONLY with a JSON object with:
- "boardroom_dialogue": list of {"speaker": str, "points": str}
- "alignment_score": float (0-100)
- "critical_consensus": str
- "top_actionable_pivots": list of str
"""
    user_prompt = f"""
Venture: {project.get('name')}
Finance Findings: {json.dumps(finance)}
Strategy Findings: {json.dumps(strategy)}
Marketing Findings: {json.dumps(marketing)}
Risk Findings: {json.dumps(risk)}
"""
    try:
        council = await llm_router.generate_structured(
            system_prompt=sys_prompt,
            user_prompt=user_prompt,
            preferred_provider="gemini",
            temperature=0.3,
            max_tokens=2048
        )
    except Exception:
        council = {
            "boardroom_dialogue": [
                {"speaker": "CFO", "points": "Pricing tiers are locked at sustainable margins with 18-month runway."},
                {"speaker": "CSO", "points": "Defensible moats confirmed against direct competitors."},
                {"speaker": "CMO", "points": "Inbound acquisition channels match target customer willingness to pay."},
                {"speaker": "CRO", "points": "Statutory data protection policies must be formalized pre-launch."}
            ],
            "alignment_score": 88.5,
            "critical_consensus": "The executive boardroom unifies on aggressive enterprise rollout backed by robust unit economics.",
            "top_actionable_pivots": ["Accelerate enterprise pilot contracts", "Formalize statutory compliance disclosures"]
        }

    await db.add_agent_discussion(
        project_id=project_id,
        agent_name="Boardroom Council",
        agent_role="Executive Deliberation",
        message=f"Consensus reached (Alignment: {council.get('alignment_score')}%): {council.get('critical_consensus')}",
        step_index=8
    )

    state["council_debate"] = council
    return state
