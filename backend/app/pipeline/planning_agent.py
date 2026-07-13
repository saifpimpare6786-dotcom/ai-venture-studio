import os
from typing import Dict, Any
from app.database.supabase import get_supabase_client
from services.llm import call_llm
from app.pipeline.state import AgentState

PLANNING_SYSTEM_PROMPT = """
You are the lead Planning Agent for the AI Venture Studio. 
Your role is to analyze the entrepreneur's raw business idea input and any parsed RAG document context, and formulate a structured, exhaustive analysis plan.

Your output must define:
1. Core Venture Summary: A clear description of what the venture does.
2. Sector Classification: The specific startup industry category.
3. Analytical Objectives: Specific instructions for downstream specialized business agents:
   - Strategy Agent (competitor landscape, target market fit, strategic position)
   - Finance Agent (assumptions, pricing sanity check, capital requirements)
   - Marketing Agent (outreach channels, ideal client profile, branding vectors)
   - Risk Agent (regulatory hurdles, competitive risks, compliance vectors)
4. Web Research Recommendations: Specific query suggestions for the Research Agent.

Be professional, concise, and structured in your output.
"""

def planning_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Planning Agent Node logic.
    Formulates a structured roadmap from raw business idea inputs and RAG context.
    Logs transaction events to Supabase database.
    """
    project_id = state.get("project_id")
    idea_input = state.get("business_idea_input", "")
    rag_context = state.get("rag_context", [])
    
    print(f"--- [Planning Agent Node] Starting execution for Project {project_id} ---")
    
    # 1. Construct prompt
    context_str = "\n---\n".join(rag_context) if rag_context else "No document RAG context provided."
    user_prompt = f"Business Idea Input:\n{idea_input}\n\nDocument Context:\n{context_str}"
    
    # 2. Call NVIDIA NIM with Gemini fallback
    plan = call_llm(
        prompt=user_prompt,
        system_prompt=PLANNING_SYSTEM_PROMPT,
        preferred_provider="nvidia",
        project_id=project_id,
        agent_name="Planning Agent"
    )
    
    # Check if LLM call failed completely
    if isinstance(plan, dict) and plan.get("status") == "failed":
        print(f"Planning Agent node failed: {plan['error']}")
        return {
            "plan": f"Execution failed: {plan['error']}"
        }
    
    # 3. Log transaction to Supabase agent_logs
    try:
        supabase = get_supabase_client()
        supabase.table("agent_logs").insert({
            "project_id": project_id,
            "agent_name": "Planning Agent",
            "status": "completed",
            "input_data": {
                "business_idea_input": idea_input[:500] if idea_input else "",
                "has_rag_context": len(rag_context) > 0
            },
            "output_data": {
                "plan": plan[:1000]
            }
        }).execute()
        print("Logged Planning Agent execution to Supabase.")
    except Exception as db_err:
        print(f"Supabase Agent Log Sync Warning (continuing): {str(db_err)}")
        
    print(f"--- [Planning Agent Node] Finished execution ---")
    return {"plan": plan}
