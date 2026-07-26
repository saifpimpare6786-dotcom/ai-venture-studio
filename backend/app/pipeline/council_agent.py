import os
import json
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

CONSOLIDATED_COUNCIL_SYSTEM_PROMPT = """
You are the LLM Council representing the Strategy, Finance, Marketing, and Risk Agents.
Your task is to conduct a comprehensive collaborative cross-review of the venture's specialized domain assessments.

Analyze all four domain assessments (Strategy, Finance, Marketing, Risk) and provide detailed, constructive feedback for each perspective, followed by a consensus summary.

You MUST return a JSON object with EXACTLY these five top-level keys:
- "strategy_review": Strategy Agent's review of the Marketing Plan (assessing alignment of client profile, branding, and outreach channels with strategic positioning).
- "finance_review": Finance Agent's review of Strategy & Marketing (assessing growth expectations, pricing suggestions, unit economics, and capital requirements).
- "marketing_review": Marketing Agent's review of Finance proposals (assessing attractiveness of pricing tiers, monetization strategies, buyer persona willingness to pay, and messaging alignment).
- "risk_review": Risk Agent's review of Finance & Strategy proposals (identifying regulatory compliance gaps, operational loopholes, data security vulnerabilities, or pricing risks, with mitigations).
- "consensus_summary": Boardroom consensus summary synthesizing key alignment points and critical action items across all four reviews.

Do not wrap the JSON response in any outer key.
"""

def execute_review(system_prompt: str, user_prompt: str, project_id: str = None, role: str = None) -> str:
    """Helper function to execute a council call using Llama-3.1-70b-instruct via NVIDIA NIM."""
    try:
        res = call_llm(
            prompt=user_prompt,
            system_prompt=system_prompt,
            preferred_provider="nvidia",
            project_id=project_id,
            agent_name=role
        )
        if isinstance(res, dict) and res.get("status") == "failed":
            return f"Council review failed: {res['error']}"
        return res
    except Exception as e:
        return f"Council review failed: {str(e)}"

def execute_fallback_4_calls(outputs: Dict[str, Any], project_id: str) -> List[str]:
    """Fallback execution method: 4 separate concurrent LLM calls via ThreadPoolExecutor."""
    strat_text = outputs.get("strategy", "No strategy assessment available.")
    fin_text = outputs.get("finance", "No finance assessment available.")
    mkt_text = outputs.get("marketing", "No marketing plan available.")
    risk_text = outputs.get("risk", "No risk assessment available.")
    
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
    print("Executing Council debate reviews concurrently via ThreadPoolExecutor (4-call fallback)...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_to_role = {
            executor.submit(
                execute_review,
                review["system"],
                review["prompt"],
                project_id,
                review["role"]
            ): review["role"]
            for review in reviews_setup
        }
        for future in concurrent.futures.as_completed(future_to_role):
            role = future_to_role[future]
            try:
                result = future.result()
                feedback_list.append(f"### {role}\n{result}")
            except Exception as exc:
                feedback_list.append(f"### {role}\nReview threw an exception: {exc}")

    return feedback_list

def llm_council_node(state: AgentState) -> Dict[str, Any]:
    """
    LLM Council Node.
    Executes collaborative cross-reviews where specialized agents critique each other's outputs.
    Optimized: Uses 1 consolidated LLM call returning JSON with all four perspectives + consensus summary.
    Safeguard: Falls back to 4 concurrent calls if consolidated call fails or returns malformed JSON after 1 repair retry.
    Saves feedback list to state and logs execution status to Supabase agent_logs.
    """
    project_id = state.get("project_id")
    outputs = state.get("specialized_outputs", {})
    
    print(f"--- [LLM Council Node] Starting execution for Project {project_id} ---")
    
    strat_text = outputs.get("strategy", "No strategy assessment available.")
    fin_text = outputs.get("finance", "No finance assessment available.")
    mkt_text = outputs.get("marketing", "No marketing plan available.")
    risk_text = outputs.get("risk", "No risk assessment available.")
    
    consolidated_prompt = f"""
Domain Assessments for Review:

1. Strategy Assessment:
{strat_text}

2. Finance Assessment:
{fin_text}

3. Marketing Plan:
{mkt_text}

4. Risk Assessment:
{risk_text}
"""
    
    parsed_json = None
    path_used = "consolidated_1_call"
    
    # 1. Primary Attempt: Consolidated 1-Call Council Review
    print("Executing Consolidated Council Debate (1 LLM call)...")
    raw_res = call_llm(
        prompt=consolidated_prompt,
        system_prompt=CONSOLIDATED_COUNCIL_SYSTEM_PROMPT,
        preferred_provider="nvidia",
        project_id=project_id,
        agent_name="Council Agent",
        json_mode=True
    )
    
    if isinstance(raw_res, str):
        # Unwrap outer ```json ``` markdown code blocks if present
        clean_text = raw_res.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()
        
        try:
            parsed_json = json.loads(clean_text)
            # Unwrap if wrapped under an outer key
            if isinstance(parsed_json, dict) and len(parsed_json) == 1 and not all(k in parsed_json for k in ("strategy_review", "finance_review")):
                first_val = list(parsed_json.values())[0]
                if isinstance(first_val, dict):
                    parsed_json = first_val
        except Exception as json_err:
            print(f"[LLM Council Node] Initial JSON parsing failed: {json_err}. Attempting 1 repair retry...")
            repair_prompt = f"Fix the following string so it is a valid JSON object with keys strategy_review, finance_review, marketing_review, risk_review, consensus_summary:\n\n{raw_res[:3000]}"
            repair_res = call_llm(
                prompt=repair_prompt,
                system_prompt="Return ONLY a valid JSON object. No explanation, no markdown backticks.",
                preferred_provider="nvidia",
                project_id=project_id,
                agent_name="Council Agent Repair",
                json_mode=True
            )
            if isinstance(repair_res, str):
                clean_repair = repair_res.strip()
                if clean_repair.startswith("```json"):
                    clean_repair = clean_repair[7:]
                if clean_repair.startswith("```"):
                    clean_repair = clean_repair[3:]
                if clean_repair.endswith("```"):
                    clean_repair = clean_repair[:-3]
                clean_repair = clean_repair.strip()
                try:
                    parsed_json = json.loads(clean_repair)
                except Exception as repair_err:
                    print(f"[LLM Council Node] Repair JSON parsing failed: {repair_err}.")

    # Validate parsed JSON structure
    valid_consolidated = bool(
        isinstance(parsed_json, dict) and
        all(k in parsed_json for k in ("strategy_review", "finance_review", "marketing_review", "risk_review"))
    )

    feedback_list = []
    if valid_consolidated:
        print("[LLM Council Node] Path used: Consolidated 1-Call Council Review (SUCCESS)")
        feedback_list = [
            f"### Strategy Agent's review of Marketing Plan\n{parsed_json.get('strategy_review')}",
            f"### Finance Agent's review of Strategy & Marketing\n{parsed_json.get('finance_review')}",
            f"### Marketing Agent's review of Finance Proposals\n{parsed_json.get('marketing_review')}",
            f"### Risk Agent's review of Strategy & Finance\n{parsed_json.get('risk_review')}",
            f"### Council Consensus Summary\n{parsed_json.get('consensus_summary', 'Consensus achieved across all domain reviews.')}"
        ]
    else:
        # 2. Fallback Path: 4-Call Concurrent Execution
        path_used = "fallback_4_calls"
        print("[LLM Council Node] Path used: Fallback 4-Call Concurrent Review (Consolidated call failed/unparseable)")
        feedback_list = execute_fallback_4_calls(outputs, project_id)

    # 3. Log results to Supabase agent_logs
    try:
        supabase = get_supabase_client()
        supabase.table("agent_logs").insert({
            "project_id": project_id,
            "agent_name": "Council Agent",
            "status": "completed" if valid_consolidated else "warning (fallback_used)",
            "input_data": {
                "specialized_outputs_keys": list(outputs.keys()),
                "path_used": path_used
            },
            "output_data": {
                "feedback_count": len(feedback_list),
                "path_used": path_used,
                "valid_consolidated": valid_consolidated,
                "council_feedback": feedback_list,
                "feedback_preview": "\n\n".join(feedback_list)[:1000]
            }
        }).execute()
        print(f"Logged Council Agent execution ({path_used}) to Supabase.")
    except Exception as db_err:
        print(f"Supabase Agent Log Sync Warning for Council Agent (continuing): {str(db_err)}")
        
    print(f"--- [LLM Council Node] Finished execution ---")
    return {
        "council_feedback": feedback_list
    }

