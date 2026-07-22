import os
from typing import Dict, Any
from app.database.supabase import get_supabase_client
from services.llm import call_llm
from app.pipeline.state import AgentState

REVIEWER_SYSTEM_PROMPT = """
You are the expert Reviewer Agent for the AI Venture Studio.
Your role is to check the completeness, coherence, and executive readiness of the specialized business assessments and boardroom council debates.

Evaluate and deliver an assessment covering:
1. Coherence & Alignment: Ensure Strategy, Finance, Marketing, and Risk assessments align without contradictions.
2. Completeness Check: Ensure all assigned orchestrator guidelines have been evaluated.
3. Executive Summary: Compile key recommendations and boardroom debate comments into a clear, unified executive report.

Route this reasoning via Gemini. Maintain a professional, executive boardroom tone.
"""

CRITIC_SYSTEM_PROMPT = """
You are the adversarial Critic Agent for the AI Venture Studio.
Your role is to act as a rigorous Venture Capitalist (VC), actively identifying weak reasoning, unsupported assumptions, execution bottlenecks, or compliance holes in the business proposals.

Deliver an adversarial critique covering:
1. Strategic Flaws: Overstated market demand, low entry barriers, or weak competitive positioning.
2. Financial & Unit Economics Risks: Unrealistic pricing, underestimated operational/development costs, or long paths to profitability.
3. Operational & Risk Hazards: Regulatory hurdles, data protection compliance (GDPR/security), or user acquisition friction.

Route this reasoning via Gemini. Be direct, critical, and constructive.
"""

def reviewer_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Reviewer Agent Node logic.
    Synthesizes assessments and debates to check completeness, coherence, and compile executive recommendations.
    Uses Gemini model to distribute LLM rate-limit overhead.
    """
    project_id = state.get("project_id")
    idea = state.get("business_idea_input", "")
    outputs = state.get("specialized_outputs", {})
    council = state.get("council_feedback", [])
    
    print(f"--- [Reviewer Agent Node] Starting execution for Project {project_id} ---")
    
    # 1. Format inputs
    outputs_str = ""
    for k, v in outputs.items():
        outputs_str += f"## {k.upper()} AGENT ASSESSMENT:\n{v}\n\n"
    council_str = "\n---\n".join(council) if council else "No council feedback provided."
    
    user_prompt = (
        f"Business Idea:\n{idea}\n\n"
        f"Specialized Agent Assessments:\n{outputs_str}\n"
        f"Council Debate Feedback:\n{council_str}"
    )
    
    # 2. Call Gemini API to spread load off NIM ceiling
    review = call_llm(
        prompt=user_prompt,
        system_prompt=REVIEWER_SYSTEM_PROMPT,
        preferred_provider="gemini",
        project_id=project_id,
        agent_name="Reviewer Agent"
    )
    
    # Check if LLM call failed completely — halt pipeline rather than propagating error text
    if isinstance(review, dict) and review.get("status") == "failed":
        error_msg = review["error"]
        print(f"[Reviewer Agent Node] FATAL: All LLM fallbacks exhausted — {error_msg}")
        try:
            supabase = get_supabase_client()
            supabase.table("agent_logs").insert({
                "project_id": project_id,
                "agent_name": "Reviewer Agent",
                "status": "failed",
                "input_data": {"specialized_outputs_keys": list(outputs.keys())},
                "output_data": {"error": error_msg}
            }).execute()
        except Exception as db_err:
            print(f"Supabase failure-log warning for Reviewer Agent: {str(db_err)}")
        return {
            "failed_agents": ["reviewer"],
            "reviewer_notes": "__FAILED__"
        }
    
    # 3. Log transaction to Supabase agent_logs
    try:
        supabase = get_supabase_client()
        supabase.table("agent_logs").insert({
            "project_id": project_id,
            "agent_name": "Reviewer Agent",
            "status": "completed",
            "input_data": {
                "specialized_outputs_keys": list(outputs.keys()),
                "has_council_feedback": len(council) > 0
            },
            "output_data": {
                "reviewer_notes": review[:1000]
            }
        }).execute()
        print("Logged Reviewer Agent execution to Supabase.")
    except Exception as db_err:
        print(f"Supabase Agent Log Sync Warning for Reviewer Agent (continuing): {str(db_err)}")
        
    print(f"--- [Reviewer Agent Node] Finished execution ---")
    return {
        "reviewer_notes": review
    }

def critic_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Critic Agent Node logic.
    Acts as an adversarial VC to constructively grill assumptions, pricing margins, and regulatory hazards.
    Uses Gemini model to distribute LLM rate-limit overhead.
    """
    project_id = state.get("project_id")
    idea = state.get("business_idea_input", "")
    outputs = state.get("specialized_outputs", {})
    council = state.get("council_feedback", [])
    reviewer_notes = state.get("reviewer_notes", "")
    
    print(f"--- [Critic Agent Node] Starting execution for Project {project_id} ---")
    
    # 1. Format inputs
    outputs_str = ""
    for k, v in outputs.items():
        outputs_str += f"## {k.upper()} AGENT ASSESSMENT:\n{v}\n\n"
    council_str = "\n---\n".join(council) if council else "No council feedback provided."
    
    user_prompt = (
        f"Business Idea:\n{idea}\n\n"
        f"Specialized Agent Assessments:\n{outputs_str}\n"
        f"Council Debate Feedback:\n{council_str}\n\n"
        f"Reviewer Executive Assessment:\n{reviewer_notes}"
    )
    
    # 2. Call Gemini API to spread load off NIM ceiling
    critique = call_llm(
        prompt=user_prompt,
        system_prompt=CRITIC_SYSTEM_PROMPT,
        preferred_provider="gemini",
        project_id=project_id,
        agent_name="Critic Agent"
    )
    
    # Check if LLM call failed completely — halt pipeline rather than propagating error text
    if isinstance(critique, dict) and critique.get("status") == "failed":
        error_msg = critique["error"]
        print(f"[Critic Agent Node] FATAL: All LLM fallbacks exhausted — {error_msg}")
        try:
            supabase = get_supabase_client()
            supabase.table("agent_logs").insert({
                "project_id": project_id,
                "agent_name": "Critic Agent",
                "status": "failed",
                "input_data": {"has_reviewer_notes": len(reviewer_notes) > 0},
                "output_data": {"error": error_msg}
            }).execute()
        except Exception as db_err:
            print(f"Supabase failure-log warning for Critic Agent: {str(db_err)}")
        return {
            "failed_agents": ["critic"],
            "critic_notes": "__FAILED__"
        }
    
    # 3. Log transaction to Supabase agent_logs
    try:
        supabase = get_supabase_client()
        supabase.table("agent_logs").insert({
            "project_id": project_id,
            "agent_name": "Critic Agent",
            "status": "completed",
            "input_data": {
                "has_reviewer_notes": len(reviewer_notes) > 0
            },
            "output_data": {
                "critic_notes": critique[:1000]
            }
        }).execute()
        print("Logged Critic Agent execution to Supabase.")
    except Exception as db_err:
        print(f"Supabase Agent Log Sync Warning for Critic Agent (continuing): {str(db_err)}")
        
    print(f"--- [Critic Agent Node] Finished execution ---")
    return {
        "critic_notes": critique
    }
