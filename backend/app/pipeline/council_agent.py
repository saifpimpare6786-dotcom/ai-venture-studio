import os
import concurrent.futures
from typing import Dict, Any, List
from app.database.supabase import get_supabase_client
from services.llm import call_llm
from app.pipeline.state import AgentState

STRATEGY_COUNCIL_SYSTEM_PROMPT = """
You are the Strategy Agent acting as a member of the LLM Council.
Your task is to review the Marketing Plan.
Assess whether the target client profile, branding vectors, and outreach channels align with the overall strategic positioning and competitive barriers of the venture.
Provide a clear, brief, constructive critique of the Marketing Plan.
"""

FINANCE_COUNCIL_SYSTEM_PROMPT = """
You are the Finance Agent acting as a member of the LLM Council.
Your task is to review the Strategy and Marketing Plans.
Assess whether their growth expectations, pricing suggestions, and outreach budgets align realistically with the capital requirements and unit economics.
Flag any pricing strategy inconsistencies or financial gaps.
"""

MARKETING_COUNCIL_SYSTEM_PROMPT = """
You are the Marketing Agent acting as a member of the LLM Council.
Your task is to review the Finance Agent's pricing models and capital requirements.
Assess whether the proposed pricing tiers and monetisation strategies are attractive and practical for the target buyer persona's willingness to pay.
Provide feedback on buyer segmentation and messaging alignment.
"""

RISK_COUNCIL_SYSTEM_PROMPT = """
You are the Risk Agent acting as a member of the LLM Council.
Your task is to review the Strategy and Finance assessments.
Identify regulatory compliance gaps, operational loopholes, data security vulnerabilities, or pricing risks in their proposals.
Offer mitigation recommendations.
"""

def execute_review(system_prompt: str, user_prompt: str) -> str:
    """Helper function to execute a council call using Llama-3.1-70b-instruct via NVIDIA NIM."""
    try:
        return call_llm(prompt=user_prompt, system_prompt=system_prompt, preferred_provider="nvidia")
    except Exception as e:
        return f"Council review failed: {str(e)}"

def llm_council_node(state: AgentState) -> Dict[str, Any]:
    """
    LLM Council Node.
    Executes collaborative cross-reviews where specialized agents critique each other's outputs concurrently.
    Saves feedback list to the state and logs execution status to Supabase.
    """
    project_id = state.get("project_id")
    outputs = state.get("specialized_outputs", {})
    
    print(f"--- [LLM Council Node] Starting execution for Project {project_id} ---")
    
    # 1. Fetch domain assessment texts from the state
    strat_text = outputs.get("strategy", "No strategy assessment available.")
    fin_text = outputs.get("finance", "No finance assessment available.")
    mkt_text = outputs.get("marketing", "No marketing plan available.")
    risk_text = outputs.get("risk", "No risk assessment available.")
    
    # 2. Setup parallel execution calls
    reviews_setup = [
        {
            "role": "Strategy Agent's review of Marketing Plan",
            "system": STRATEGY_COUNCIL_SYSTEM_PROMPT,
            "prompt": f"Marketing Plan:\n{mkt_text}"
        },
        {
            "role": "Finance Agent's review of Strategy & Marketing",
            "system": FINANCE_COUNCIL_SYSTEM_PROMPT,
            "prompt": f"Strategy Assessment:\n{strat_text}\n\nMarketing Plan:\n{mkt_text}"
        },
        {
            "role": "Marketing Agent's review of Finance Proposals",
            "system": MARKETING_COUNCIL_SYSTEM_PROMPT,
            "prompt": f"Finance Proposals:\n{fin_text}"
        },
        {
            "role": "Risk Agent's review of Strategy & Finance",
            "system": RISK_COUNCIL_SYSTEM_PROMPT,
            "prompt": f"Strategy Assessment:\n{strat_text}\n\nFinance Proposals:\n{fin_text}"
        }
    ]
    
    feedback_list = []
    
    # Run the reviews concurrently using a ThreadPoolExecutor
    print("Executing Council debate reviews concurrently via ThreadPoolExecutor...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_to_role = {
            executor.submit(execute_review, review["system"], review["prompt"]): review["role"]
            for review in reviews_setup
        }
        for future in concurrent.futures.as_completed(future_to_role):
            role = future_to_role[future]
            try:
                result = future.result()
                feedback_list.append(f"### {role}\n{result}")
            except Exception as exc:
                feedback_list.append(f"### {role}\nReview threw an exception: {exc}")
                
    print(f"Concurrently completed {len(feedback_list)} council reviews.")
    
    # 3. Log results to Supabase agent_logs
    try:
        supabase = get_supabase_client()
        supabase.table("agent_logs").insert({
            "project_id": project_id,
            "agent_name": "Council Agent",
            "status": "completed",
            "input_data": {
                "specialized_outputs_keys": list(outputs.keys())
            },
            "output_data": {
                "feedback_count": len(feedback_list),
                "feedback_preview": "\n\n".join(feedback_list)[:1000]
            }
        }).execute()
        print("Logged Council Agent execution to Supabase.")
    except Exception as db_err:
        print(f"Supabase Agent Log Sync Warning for Council Agent (continuing): {str(db_err)}")
        
    print(f"--- [LLM Council Node] Finished execution ---")
    return {
        "council_feedback": feedback_list
    }
