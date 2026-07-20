import os
import json
from typing import Dict, Any, List
from app.database.supabase import get_supabase_client
from services.llm import call_llm
from app.pipeline.state import AgentState

SCORING_SYSTEM_PROMPT = """
You are the expert Analytics & Scoring Engine for AI Venture Studio.
Your role is to evaluate the startup's business plan across three core dimensions using a weighted rubric:
1. Viability (Weight: 35%): Assessment of strategy, operational risks, compliance, and hurdles.
2. Market Fit (Weight: 35%): Assessment of customer acquisition, ICP definition, and competitive positioning.
3. Financial Soundness (Weight: 30%): Assessment of revenue model, pricing consistency, and capital requirements.

Input data includes:
- General Business Idea
- Strategy Assessment
- Finance Assessment
- Marketing Plan
- Risk Assessment
- Business Rules Validation result

Your task:
- Assign a score from 0 to 100 for each of the three dimensions (Viability, Market Fit, Financial Soundness).
- Provide a concise executive rationale (1-3 sentences) explaining the score for each dimension.
- Provide a brief section of general feedback on how to improve the scores.
- IMPORTANT: If the Business Rules Validation result contains validation errors (i.e. is_valid = False), you MUST penalize the Viability and Financial Soundness scores accordingly, citing the validation failures in the rationale.

Target JSON Format:
{
  "viability": {
    "score": 85,
    "rationale": "Rationale explanation here..."
  },
  "market_fit": {
    "score": 75,
    "rationale": "Rationale explanation here..."
  },
  "financial_soundness": {
    "score": 80,
    "rationale": "Rationale explanation here..."
  },
  "feedback": "Overall constructive feedback here..."
}

Return ONLY the valid JSON block wrapped in a markdown code fence. Do not include any introductory or concluding text.
"""

def extract_json_block(text: str) -> str:
    """Extracts raw JSON content from markdown code fences if present."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def analytics_scoring_node(state: AgentState) -> Dict[str, Any]:
    """
    Analytics & Scoring Engine Node.
    Consumes outputs from all specialized agents and validation results from the Business Rules Engine.
    Evaluates the business plan across dimensions, computes a weighted overall score programmatically,
    and logs the transaction to Supabase agent_logs.
    """
    project_id = state.get("project_id")
    idea = state.get("business_idea_input", "")
    outputs = state.get("specialized_outputs", {})
    rules_validation = state.get("rules_validation_result", {})
    
    print(f"--- [Analytics & Scoring Engine Node] Starting execution for Project {project_id} ---")
    
    # 1. Format inputs for the LLM prompt
    strategy_text = outputs.get("strategy", "No strategy assessment available.")
    finance_text = outputs.get("finance", "No finance assessment available.")
    marketing_text = outputs.get("marketing", "No marketing plan available.")
    risk_text = outputs.get("risk", "No risk assessment available.")
    
    rules_valid = rules_validation.get("is_valid", True)
    rules_errors = rules_validation.get("errors", [])
    rules_data = rules_validation.get("extracted_data", {})
    
    rules_summary = {
        "is_valid": rules_valid,
        "errors": rules_errors,
        "extracted_data": rules_data
    }
    
    user_prompt = (
        f"BUSINESS IDEA:\n{idea}\n\n"
        f"STRATEGY ASSESSMENT:\n{strategy_text}\n\n"
        f"FINANCE ASSESSMENT:\n{finance_text}\n\n"
        f"MARKETING PLAN:\n{marketing_text}\n\n"
        f"RISK ASSESSMENT:\n{risk_text}\n\n"
        f"BUSINESS RULES VALIDATION RESULT:\n{json.dumps(rules_summary, indent=2)}"
    )
    
    # Define default fallback scores
    fallback_scores = {
        "viability": {
            "score": 0.0,
            "rationale": "Evaluation failed or was skipped due to parsing/LLM failure."
        },
        "market_fit": {
            "score": 0.0,
            "rationale": "Evaluation failed or was skipped due to parsing/LLM failure."
        },
        "financial_soundness": {
            "score": 0.0,
            "rationale": "Evaluation failed or was skipped due to parsing/LLM failure."
        },
        "overall_score": 0.0,
        "feedback": "An error occurred during scoring. Please check the logs.",
        "rubric_weights": {
            "viability": 0.35,
            "market_fit": 0.35,
            "financial_soundness": 0.30
        }
    }
    
    scores = fallback_scores.copy()
    extracted_dict = {}
    is_success = False
    
    # 2. Call Gemini API to calculate scores (conserve NIM rate limit ceiling)
    try:
        raw_json_str = call_llm(
            prompt=user_prompt,
            system_prompt=SCORING_SYSTEM_PROMPT,
            preferred_provider="gemini",
            project_id=project_id,
            agent_name="Analytics & Scoring Engine"
        )
        
        if isinstance(raw_json_str, dict) and raw_json_str.get("status") == "failed":
            raise ValueError(raw_json_str["error"])
            
        cleaned_json_str = extract_json_block(raw_json_str)
        extracted_dict = json.loads(cleaned_json_str)
        
        # 3. Extract and sanitize values, compute weighted overall score programmatically
        viability_score = float(extracted_dict.get("viability", {}).get("score", 0.0))
        market_fit_score = float(extracted_dict.get("market_fit", {}).get("score", 0.0))
        finance_score = float(extracted_dict.get("financial_soundness", {}).get("score", 0.0))
        
        overall_score = round(
            0.35 * viability_score + 
            0.35 * market_fit_score + 
            0.30 * finance_score,
            2
        )
        
        scores = {
            "viability": {
                "score": viability_score,
                "rationale": extracted_dict.get("viability", {}).get("rationale", "")
            },
            "market_fit": {
                "score": market_fit_score,
                "rationale": extracted_dict.get("market_fit", {}).get("rationale", "")
            },
            "financial_soundness": {
                "score": finance_score,
                "rationale": extracted_dict.get("financial_soundness", {}).get("rationale", "")
            },
            "overall_score": overall_score,
            "feedback": extracted_dict.get("feedback", ""),
            "rubric_weights": {
                "viability": 0.35,
                "market_fit": 0.35,
                "financial_soundness": 0.30
            }
        }
        is_success = True
        print(f"Analytics & Scoring Engine computed overall score: {overall_score}")
        
    except Exception as parse_err:
        print(f"Analytics & Scoring Engine parsing or execution error: {str(parse_err)}")
        
    # 4. Log results to Supabase agent_logs
    try:
        supabase = get_supabase_client()
        supabase.table("agent_logs").insert({
            "project_id": project_id,
            "agent_name": "Analytics & Scoring Engine",
            "status": "completed" if is_success else "failed",
            "input_data": {
                "specialized_outputs_keys": list(outputs.keys()),
                "rules_valid": rules_valid,
                "rules_errors_count": len(rules_errors)
            },
            "output_data": {
                "scores": scores
            }
        }).execute()
        print("Logged Analytics & Scoring Engine execution to Supabase.")
    except Exception as db_err:
        print(f"Supabase Agent Log Sync Warning for Analytics & Scoring Engine (continuing): {str(db_err)}")
        
    print(f"--- [Analytics & Scoring Engine Node] Finished execution ---")
    return {
        "scores": scores
    }
