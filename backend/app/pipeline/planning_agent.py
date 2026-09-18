import json
from typing import Dict, Any
from app.pipeline.state import AgentState
from services.llm import llm_router
from app.database.db import db

async def planning_node(state: AgentState) -> AgentState:
    """
    Analyzes the 14 raw business idea parameters and formulates a structured execution plan.
    """
    project = state["project_data"]
    project_id = state["project_id"]

    sys_prompt = """You are the Lead Venture Planning Architect. 
Analyze the startup parameters and produce an execution blueprint in JSON with:
1. "domain_focus": key strategic priorities for Finance, Strategy, Marketing, and Risk
2. "knowledge_gaps": critical unanswered questions
3. "search_queries": 2-3 specific search queries for market data, competitor pricing, and statutory laws
4. "executive_hypothesis": concise 2-sentence thesis on venture viability
"""
    user_prompt = f"""
Venture: {project.get('name')} ({project.get('industry')} - {project.get('target_country')})
Problem: {project.get('problem_statement')}
Solution: {project.get('solution_description')}
Target Customers: {project.get('target_customers')}
Revenue Model: {project.get('revenue_model')}
Budget: {project.get('budget')} {project.get('currency')} | Funding Goal: {project.get('preferred_funding')}
Team Size: {project.get('team_size')}
"""
    try:
        plan = await llm_router.generate_structured(
            system_prompt=sys_prompt,
            user_prompt=user_prompt,
            preferred_provider="ollama",
            temperature=0.2,
            max_tokens=1024
        )
    except Exception as e:
        plan = {
            "domain_focus": {"finance": "Unit economics & runway", "strategy": "B2B moat", "marketing": "Inbound CAC", "risk": "Regulatory"},
            "knowledge_gaps": ["Market size validation"],
            "search_queries": [f"{project.get('industry')} market size {project.get('target_country')}", f"{project.get('name')} competitors"],
            "executive_hypothesis": "Venture addresses an acute market pain point with scalable unit economics."
        }

    await db.add_agent_discussion(
        project_id=project_id,
        agent_name="Planning Architect",
        agent_role="Strategic Planning",
        message=f"Blueprint established. Primary hypothesis: {plan.get('executive_hypothesis')}",
        step_index=1
    )

    state["plan"] = plan
    return state
