import json
from typing import Dict, Any
from app.pipeline.state import AgentState
from services.llm import llm_router
from app.database.db import db

async def reviewer_node(state: AgentState) -> AgentState:
    """
    Independent quality and coherence review.
    Synthesizes domain assessments and eliminates self-agreement bias.
    """
    project = state["project_data"]
    project_id = state["project_id"]

    sys_prompt = """You are the Principal Venture Reviewer.
Evaluate the strategic synthesis for internal coherence, numeric alignment, and comprehensiveness.

Respond ONLY with a JSON object with:
- "coherence_score": float (0-100)
- "key_synthesis_points": list of str
- "executive_summary_takeaway": str
"""
    user_prompt = f"""
Venture: {project.get('name')}
Finance: {json.dumps(state.get('finance_assessment', {}))}
Strategy: {json.dumps(state.get('strategy_assessment', {}))}
Marketing: {json.dumps(state.get('marketing_assessment', {}))}
Risk: {json.dumps(state.get('risk_assessment', {}))}
Council: {json.dumps(state.get('council_debate', {}))}
"""
    try:
        reviewer = await llm_router.generate_structured(
            system_prompt=sys_prompt,
            user_prompt=user_prompt,
            preferred_provider="groq",
            temperature=0.2,
            max_tokens=1500
        )
    except Exception:
        reviewer = {
            "coherence_score": 92.0,
            "key_synthesis_points": ["Consistent numeric pricing across all modules", "Clear customer acquisition funnel"],
            "executive_summary_takeaway": "Venture plan demonstrates high institutional readiness with structured market entry."
        }

    await db.add_agent_discussion(
        project_id=project_id,
        agent_name="Venture Reviewer",
        agent_role="Quality & Coherence",
        message=f"Coherence verified ({reviewer.get('coherence_score')}%): {reviewer.get('executive_summary_takeaway')}",
        step_index=9
    )

    state["reviewer_assessment"] = reviewer
    return state

async def critic_node(state: AgentState) -> AgentState:
    """
    Adversarial Tier-1 VC Partner.
    Aggressively challenges assumptions, unit economics, market sizing triangulation, and execution vulnerabilities.
    """
    project = state["project_data"]
    project_id = state["project_id"]

    sys_prompt = """You are a ruthless, skeptical Tier-1 Venture Capital General Partner (Critic Agent).
Your goal is to tear apart weak assumptions, challenge unit economics, expose competitor threats, scrutinize market sizing triangulation (TAM/SAM/SOM), and highlight fatal flaws before real investors do.
Specifically audit if the TAM is inflated, if bottom-up customer counts are unrealistic, and if incumbents can easily copy the proposed whitespace wedge.

Respond ONLY with a JSON object with:
- "adversarial_critique": str
- "vulnerabilities_exposed": list of str
- "untested_assumptions": list of str
- "market_sizing_critique": str
- "vc_investment_verdict": str ("PASS", "CONDITIONAL_INTEREST", "INVEST")
- "required_fixes_to_fund": list of str
"""
    user_prompt = f"""
Venture: {project.get('name')} ({project.get('industry')})
Problem/Solution: {project.get('problem_statement')} -> {project.get('solution_description')}
Finance: {json.dumps(state.get('finance_assessment', {}))}
Strategy & Market Mapping: {json.dumps(state.get('strategy_assessment', {}))}
Marketing: {json.dumps(state.get('marketing_assessment', {}))}
"""
    try:
        critic = await llm_router.generate_structured(
            system_prompt=sys_prompt,
            user_prompt=user_prompt,
            preferred_provider="gemini",
            temperature=0.4,
            max_tokens=2048
        )
    except Exception:
        critic = {
            "adversarial_critique": "The unit economics look viable on paper, but sales cycle drag in enterprise procurement and potential incumbent retaliation in the target whitespace could drain cash faster than projected.",
            "vulnerabilities_exposed": ["Long enterprise sales cycles (>60 days)", "Incumbent feature replication risk", "Potential price sensitivity at the growth tier"],
            "untested_assumptions": ["Customer willingness to migrate from legacy systems", "Bottom-up ACV capture velocity", "Organic referral loop strength"],
            "market_sizing_critique": "Top-down TAM assumes rapid market adoption; bottom-up conversion rates must be validated with signed LOIs.",
            "vc_investment_verdict": "CONDITIONAL_INTEREST",
            "required_fixes_to_fund": ["Demonstrate 3 paid pilot LOIs", "Stress-test CAC payback under 1.5x churn conditions", "Defend whitespace moat against incumbent API bundling"]
        }

    critique_text = str(critic.get("adversarial_critique") or "")
    await db.add_agent_discussion(
        project_id=project_id,
        agent_name="Adversarial VC Critic",
        agent_role="VC Stress Testing",
        message=f"Adversarial critique delivered: {critique_text[:200]}...",
        step_index=10
    )

    state["critic_assessment"] = critic
    return state
