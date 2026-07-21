import os
import json
from typing import Dict, Any, List
from app.database.supabase import get_supabase_client
from services.llm import call_llm
from app.pipeline.state import AgentState
from app.schemas.report import (
    ExecutiveSummarySchema,
    BusinessPlanSchema,
    SwotAnalysisSchema,
    FinancialProjectionSchema,
    InvestmentReadinessSchema
)

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

def report_generator_node(state: AgentState) -> Dict[str, Any]:
    """
    Report Generator Node.
    Consumes outputs from the Scoring Engine, Specialized Agents, and Rules Engine.
    Sequentially builds the 5 priority report types using Gemini, validates them against
    Pydantic schemas, and inserts/updates them in the public.reports database table.
    """
    project_id = state.get("project_id")
    idea = state.get("business_idea_input", "")
    outputs = state.get("specialized_outputs", {})
    council = state.get("council_feedback", [])
    reviewer = state.get("reviewer_notes", "")
    critic = state.get("critic_notes", "")
    rules_validation = state.get("rules_validation_result", {})
    scores = state.get("scores", {})
    
    print(f"--- [Report Generator Node] Starting execution for Project {project_id} ---")
    
    # Format inputs for LLM prompt
    strategy_text = outputs.get("strategy", "No strategy assessment available.")
    finance_text = outputs.get("finance", "No finance assessment available.")
    marketing_text = outputs.get("marketing", "No marketing plan available.")
    risk_text = outputs.get("risk", "No risk assessment available.")
    council_str = "\n---\n".join(council) if council else "No council feedback."
    overall_score_val = scores.get("overall_score", 0.0)
    
    context_data = (
        f"BUSINESS IDEA:\n{idea}\n\n"
        f"STRATEGY ASSESSMENT:\n{strategy_text}\n\n"
        f"FINANCE ASSESSMENT:\n{finance_text}\n\n"
        f"MARKETING PLAN:\n{marketing_text}\n\n"
        f"RISK ASSESSMENT:\n{risk_text}\n\n"
        f"COUNCIL DEBATE NOTES:\n{council_str}\n\n"
        f"REVIEWER EXECUTIVE BRIEFING:\n{reviewer}\n\n"
        f"CRITIC ADVERSARIAL NOTES:\n{critic}\n\n"
        f"BUSINESS RULES VALIDATION RESULT:\n{json.dumps(rules_validation, indent=2)}\n\n"
        f"SCORES SUMMARY:\n{json.dumps(scores, indent=2)}"
    )

    # 1. Define configurations for each priority report
    report_configs = {
        "Executive Summary": {
            "schema": ExecutiveSummarySchema,
            "export_formats": ["docx", "pptx", "pdf"],
            "export_mapping": {
                "concept": "Venture Concept & Value Proposition",
                "market_opportunity": "Market Opportunity & Target Segment",
                "strategic_positioning": "Strategic Positioning & Channels",
                "financial_projection_summary": "Financial Projections & Pricing Models",
                "risk_mitigation_summary": "Risk Mitigation & Compliance",
                "overall_score": "Viability Performance Score"
            },
            "system_prompt": f"""
You are the Report Generator for AI Venture Studio. Your task is to compile a structured, premium Executive Summary JSON object matching the requested schema.
Ground your synthesis in the provided boardroom assessments, critiques, and scores.

Target JSON Format:
{{
  "concept": "Detailed venture overview and problem-solution description...",
  "market_opportunity": "ICP analysis, supplier/buyer power, and target market sizing...",
  "strategic_positioning": "USPs, marketing acquisition vectors, and branding vectors...",
  "financial_projection_summary": "Revenue streams, concrete pricing models/tiers, and funding overview...",
  "risk_mitigation_summary": "Top compliance/regulatory risks and suggested mitigation roadmap...",
  "overall_score": {overall_score_val}
}}

Return ONLY the valid JSON block wrapped in a markdown code fence. Do not include any pre-text or post-text.
"""
        },
        "Business Plan": {
            "schema": BusinessPlanSchema,
            "export_formats": ["docx", "pdf"],
            "export_mapping": {
                "company_description": "Company Description & Mission",
                "market_analysis": "Market Analysis & Landscape",
                "marketing_sales_strategy": "Marketing & Sales Strategy",
                "operational_plan": "Operational & Compliance Roadmap",
                "financial_plan": "Financial Plan & Pricing Structures"
            },
            "system_prompt": """
You are the Report Generator for AI Venture Studio. Your task is to compile a structured, comprehensive Business Plan JSON object matching the requested schema.
Target JSON Format:
{
  "company_description": "Detailed venture model, strategic vision, goals, and problem-solution alignment...",
  "market_analysis": "Industry analysis, direct/indirect competitor matrix, and supplier/buyer dynamics...",
  "marketing_sales_strategy": "ICP descriptions, customer acquisition pipeline, growth metrics, and branding taglines...",
  "operational_plan": "Execution milestones, critical partnerships, security/privacy compliance, and legal checklist...",
  "financial_plan": "Revenue channels, concrete pricing models, break-even timelines, and capital burn rate assumptions..."
}
Return ONLY the valid JSON block wrapped in a markdown code fence.
"""
        },
        "SWOT Analysis": {
            "schema": SwotAnalysisSchema,
            "export_formats": ["docx", "pptx", "pdf"],
            "export_mapping": {
                "strengths": "Venture Strengths",
                "weaknesses": "Venture Weaknesses",
                "opportunities": "Market Opportunities",
                "threats": "External Threats"
            },
            "system_prompt": """
You are the Report Generator for AI Venture Studio. Your task is to generate a structured SWOT Analysis JSON object containing string arrays for each quadrant.
Target JSON Format:
{
  "strengths": ["Strength 1...", "Strength 2..."],
  "weaknesses": ["Weakness 1...", "Weakness 2..."],
  "opportunities": ["Opportunity 1...", "Opportunity 2..."],
  "threats": ["Threat 1...", "Threat 2..."]
}
Return ONLY the valid JSON block wrapped in a markdown code fence.
"""
        },
        "Financial Projection": {
            "schema": FinancialProjectionSchema,
            "export_formats": ["docx", "pdf"],
            "export_mapping": {
                "revenue_model_details": "Monetization & Pricing Tiers",
                "pricing_sanity_check": "Sanity Check & Margins",
                "capital_requirements": "Capital Requirements & Budgets",
                "break_even_analysis": "Break-Even Analysis & Plausible Timeline"
            },
            "system_prompt": """
You are the Report Generator for AI Venture Studio. Your task is to generate a Financial Projection report JSON object.
Target JSON Format:
{
  "revenue_model_details": "Detailed breakdown of monetization streams and pricing tiers...",
  "pricing_sanity_check": "Competitiveness check, margins evaluation, and pricing consistency sanity test...",
  "capital_requirements": "Estimates of seed/working capital, development headcount budgets, and burn rates...",
  "break_even_analysis": "Estimated customer volume or months needed to achieve break-even..."
}
Return ONLY the valid JSON block wrapped in a markdown code fence.
"""
        },
        "Investment Readiness Report": {
            "schema": InvestmentReadinessSchema,
            "export_formats": ["docx", "pptx", "pdf"],
            "export_mapping": {
                "investment_thesis": "Investment Thesis",
                "scoring_breakdown": "Scoring Engine Rubric & Breakdown",
                "critic_concerns": "VC Critiques & Strategic Risks",
                "milestones_funding": "Milestones & Capital Allocation"
            },
            "system_prompt": """
You are the Report Generator for AI Venture Studio. Your task is to generate an Investment Readiness Report JSON object.
Target JSON Format:
{
  "investment_thesis": "Clear thesis on why this startup represents an attractive investment opportunity...",
  "scoring_breakdown": "Explanation of viability, market fit, and finance scores using the scoring engine's rationale...",
  "critic_concerns": "Main VC critiques, assumptions grilled, and strategic issues founders must address...",
  "milestones_funding": "Core milestones timeline, preferred funding type, and capital allocation priorities..."
}
Return ONLY the valid JSON block wrapped in a markdown code fence.
"""
        }
    }

    supabase = get_supabase_client()
    generated_reports = {}

    # 2. Iterate through configs and call Gemini to generate each report
    for report_type, config in report_configs.items():
        print(f"Generating report: '{report_type}'...")
        
        try:
            # Enforce that reports are generated ONLY from data that has passed Business Rules Engine validation
            if not rules_validation or not rules_validation.get("is_valid", False):
                validation_errors = ", ".join(rules_validation.get("errors", ["Validation has not run or was not successful"]))
                raise ValueError(f"Business Rules validation failed: {validation_errors}")
            raw_text = call_llm(
                prompt=context_data,
                system_prompt=config["system_prompt"],
                preferred_provider="gemini",
                project_id=project_id,
                agent_name=f"{report_type} Generator"
            )
            
            if isinstance(raw_text, dict) and raw_text.get("status") == "failed":
                raise ValueError(raw_text["error"])
                
            cleaned_json = extract_json_block(raw_text)
            report_content = json.loads(cleaned_json)
            
            # Pre-validate/clean schema fields: convert nested dicts/lists to strings if schema expects str
            schema_fields = config["schema"].model_fields
            for field_name, field_info in schema_fields.items():
                if field_name in report_content:
                    val = report_content[field_name]
                    if field_info.annotation == str and not isinstance(val, str):
                        if isinstance(val, dict):
                            report_content[field_name] = "\n".join(f"- {k.replace('_', ' ').title()}: {v}" for k, v in val.items())
                        elif isinstance(val, list):
                            report_content[field_name] = "\n".join(f"- {v}" for v in val)
                        else:
                            report_content[field_name] = str(val)
            
            # Validate output using Pydantic schema
            config["schema"].model_validate(report_content)
            
            # Save or Update report record in public.reports database
            # Check if this report type already exists for the project
            existing = supabase.table("reports").select("id").eq("project_id", project_id).eq("report_type", report_type).execute()
            
            report_record = {
                "project_id": project_id,
                "report_type": report_type,
                "content": report_content,
                "scores": scores,
                "status": "Completed"
            }
            
            if existing.data:
                report_id = existing.data[0]["id"]
                supabase.table("reports").update(report_record).eq("id", report_id).execute()
                print(f"Updated existing database record for '{report_type}'.")
            else:
                supabase.table("reports").insert(report_record).execute()
                print(f"Created new database record for '{report_type}'.")
                
            generated_reports[report_type] = report_content
            
        except Exception as err:
            print(f"Failed to generate report type '{report_type}': {str(err)}")
            fallback_content = {
                "error": f"Report generation failed: {str(err)}"
            }
            generated_reports[report_type] = fallback_content
            
            try:
                # Save failure fallback report to Supabase
                existing = supabase.table("reports").select("id").eq("project_id", project_id).eq("report_type", report_type).execute()
                
                report_record = {
                    "project_id": project_id,
                    "report_type": report_type,
                    "content": fallback_content,
                    "scores": scores,
                    "status": "Failed"
                }
                
                if existing.data:
                    report_id = existing.data[0]["id"]
                    supabase.table("reports").update(report_record).eq("id", report_id).execute()
                    print(f"Updated database failure fallback record for '{report_type}'.")
                else:
                    supabase.table("reports").insert(report_record).execute()
                    print(f"Created new database failure fallback record for '{report_type}'.")
            except Exception as db_err:
                print(f"Failed to insert database failure fallback record for '{report_type}': {str(db_err)}")

    # 3. Create a readable text summary of all reports for final_report state
    summary_lines = [f"# Reports Suite for Project: {project_id}\n"]
    for r_type, r_content in generated_reports.items():
        summary_lines.append(f"## {r_type}")
        if "error" in r_content:
            summary_lines.append(f"Error: {r_content['error']}\n")
        else:
            for section, text in r_content.items():
                summary_lines.append(f"### {section.replace('_', ' ').title()}")
                if isinstance(text, list):
                    for item in text:
                        summary_lines.append(f"- {item}")
                else:
                    summary_lines.append(str(text))
                summary_lines.append("")
    
    final_report_str = "\n".join(summary_lines)
    
    # 4. Log report generator execution to Supabase agent_logs
    try:
        supabase.table("agent_logs").insert({
            "project_id": project_id,
            "agent_name": "Report Generator",
            "status": "completed",
            "input_data": {
                "reports_requested": list(report_configs.keys())
            },
            "output_data": {
                "reports_generated_count": len(generated_reports)
            }
        }).execute()
        print("Logged Report Generator execution to Supabase.")
    except Exception as db_err:
        print(f"Supabase Agent Log Sync Warning for Report Generator (continuing): {str(db_err)}")
        
    print(f"--- [Report Generator Node] Finished execution ---")
    return {
        "final_report": final_report_str
    }
