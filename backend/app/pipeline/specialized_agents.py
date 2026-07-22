import os
from typing import Dict, Any, List
from app.database.supabase import get_supabase_client
from services.llm import call_llm
from services.rag_retriever import retrieve_context
from app.pipeline.state import AgentState

# System prompts for specialized business agents
STRATEGY_SYSTEM_PROMPT = """
You are the expert Strategy Agent for AI Venture Studio. 
Your role is to conduct a strategic analysis of the target startup business idea.
Analyze the provided business idea input, orchestrator directives, and RAG document context.

Deliver an expert assessment covering:
1. Market Fit Assessment: The validity of the problem-solution fit.
2. Competitive Landscape: Identification of key direct and indirect competitors or categories.
3. Strategic Position: Unique selling propositions (USPs) and strategic recommendations. If you discuss pricing structures, you MUST list at least two or three concrete pricing tiers with specific names and exact numeric values (e.g., Starter: $50/month, Growth: $200/month). Do not describe pricing generically without numeric values.

Ground your answers in retrieved RAG document/research evidence. Maintain a professional, executive tone.
"""

FINANCE_SYSTEM_PROMPT = """
You are the expert Finance Agent for AI Venture Studio.
Your role is to formulate financial pricing strategies and financial planning assumptions.
Analyze the provided business idea input, orchestrator directives, and RAG document context.

Deliver an expert assessment covering:
1. Revenue & Pricing Model: Suggested pricing strategies and monetisation vectors. You MUST outline at least two or three concrete pricing tiers with specific names and exact numeric values (e.g., Basic: $50/month, Premium: $200/month). You must always include at least one concrete numeric price example per tier so extraction has real numbers to validate against (e.g., do not say "Subscription-based model" or "Custom pricing" generically without providing a specific numeric dollar value).
2. Pricing Strategy Sanity Check: An evaluation of competitiveness and profit margins.
3. Capital Requirements: Rough estimates of seed capital, operational costs, and development resources.

Ground your answers in retrieved RAG document/research evidence. Maintain a professional, executive tone.
"""

MARKETING_SYSTEM_PROMPT = """
You are the expert Marketing Agent for AI Venture Studio.
Your role is to outline marketing growth plans and target client definition.
Analyze the provided business idea input, orchestrator directives, and RAG document context.

Deliver an expert assessment covering:
1. Customer Outreach Channels: The most effective digital and offline acquisition methods.
2. Ideal Client Profile (ICP): Persona specifications based on size, industry, or demographics.
3. Branding & Value Proposition Vectors: Emphasize core values and positioning taglines.
   PRICING RULE — CRITICAL: The Finance Agent has already defined the authoritative pricing tiers
   for this venture. These tiers are provided to you verbatim in the section labelled
   "Finance Agent Pricing Tiers (Authoritative — Do Not Change)" in your user prompt.
   You MUST reference those exact tier names and numeric values whenever pricing is mentioned
   in your assessment. Do NOT invent, round, or substitute different price figures.
   Do NOT omit pricing from your assessment — reference the Finance tiers explicitly by name
   and value (e.g. Starter: $50/month, Growth: $200/month) in your branding and messaging copy.

Ground your answers in retrieved RAG document/research/framework evidence. Maintain a professional, executive tone.
"""

RISK_SYSTEM_PROMPT = """
You are the expert Risk Agent for AI Venture Studio.
Your role is to evaluate regulatory, security, operational, and competitive hazards.
Analyze the provided business idea input, orchestrator directives, and RAG document context.

Deliver an expert assessment covering:
1. Regulatory Hurdles & Compliance: Applicable laws, data privacy acts, and reporting requirements.
2. Competitive & Operational Risks: Vulnerabilities to incumbents and execution bottlenecks.
3. Compliance Recommendations: Steps to align operations with industry standards.

Ground your answers in retrieved RAG document/research evidence. Maintain a professional, executive tone.
"""

def execute_agent_logic(
    state: AgentState, 
    agent_name: str, 
    system_prompt: str, 
    search_keyword: str,
    extra_context: str = ""
) -> Dict[str, Any]:
    """Helper function to execute specialized agent node reasoning, context retrieval, and database logging.
    
    Args:
        extra_context: Optional additional context injected into the user prompt before the LLM call.
                       Used by Marketing Agent to receive Finance Agent pricing tiers.
    """
    project_id = state.get("project_id")
    idea = state.get("business_idea_input", "")
    directives = state.get("directives", "")
    
    print(f"--- [{agent_name} Node] Starting execution for Project {project_id} ---")
    
    # 1. Retrieve RAG context
    agent_query = f"{idea} {search_keyword}"
    context_chunks = retrieve_context(project_id, query=agent_query, top_k=5)
    context_str = "\n---\n".join(context_chunks) if context_chunks else "No RAG context retrieved."
    
    # 2. Construct user prompt
    user_prompt = (
        f"Business Idea Input:\n{idea}\n\n"
        f"Orchestrator Directives:\n{directives}\n\n"
        f"Retrieved Document/Research Context:\n{context_str}"
    )
    # Inject extra context (e.g. Finance pricing tiers for Marketing Agent) after base prompt
    if extra_context:
        user_prompt += f"\n\n{extra_context}"
    
    # 3. Call LLM (Meta Llama-3.1-70b-instruct via NVIDIA NIM)
    output = call_llm(
        prompt=user_prompt,
        system_prompt=system_prompt,
        preferred_provider="nvidia",
        project_id=project_id,
        agent_name=agent_name
    )
    
    # Check if LLM call failed completely
    if isinstance(output, dict) and output.get("status") == "failed":
        agent_key = agent_name.lower().replace(" agent", "")
        error_msg = output["error"]
        print(f"[{agent_name} Node] FATAL: All LLM fallbacks exhausted — {error_msg}")
        # Log the failure to Supabase so the Boardroom View shows it
        try:
            supabase = get_supabase_client()
            supabase.table("agent_logs").insert({
                "project_id": project_id,
                "agent_name": agent_name,
                "status": "failed",
                "input_data": {"search_query": agent_query[:200]},
                "output_data": {"error": error_msg}
            }).execute()
        except Exception as db_err:
            print(f"Supabase failure-log warning for {agent_name}: {str(db_err)}")
        # Write sentinel so downstream nodes can detect failure without parsing error text
        return {
            "failed_agents": [agent_key],
            "specialized_outputs": {agent_key: "__FAILED__"}
        }
    
    # 4. Log to Supabase agent_logs
    try:
        supabase = get_supabase_client()
        supabase.table("agent_logs").insert({
            "project_id": project_id,
            "agent_name": agent_name,
            "status": "completed",
            "input_data": {
                "search_query": agent_query[:200],
                "directives_preview": directives[:300] if directives else "",
                "has_rag_context": len(context_chunks) > 0
            },
            "output_data": {
                "assessment": output[:1000]
            }
        }).execute()
        print(f"Logged {agent_name} execution to Supabase.")
    except Exception as db_err:
        print(f"Supabase Agent Log Sync Warning for {agent_name} (continuing): {str(db_err)}")
        
    print(f"--- [{agent_name} Node] Finished execution ---")
    
    # Ensure parallel outputs are stored under the respective agent key in specialized_outputs
    agent_key = agent_name.lower().replace(" agent", "")
    return {
        "specialized_outputs": {
            agent_key: output
        }
    }

def strategy_agent_node(state: AgentState) -> Dict[str, Any]:
    return execute_agent_logic(
        state=state,
        agent_name="Strategy Agent",
        system_prompt=STRATEGY_SYSTEM_PROMPT,
        search_keyword="strategy competitive landscape market fit positioning"
    )

def finance_agent_node(state: AgentState) -> Dict[str, Any]:
    return execute_agent_logic(
        state=state,
        agent_name="Finance Agent",
        system_prompt=FINANCE_SYSTEM_PROMPT,
        search_keyword="pricing assumptions financial projections capital cost revenue"
    )

def marketing_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Marketing Agent Node.
    Runs AFTER Finance Agent completes (sequential dependency — see graph.py).
    Extracts Finance Agent's finalized pricing tiers from state and injects them
    as locked-in context so Marketing cannot hallucinate different price figures.
    """
    # Extract Finance pricing tiers from state to build the authoritative pricing block
    finance_output = state.get("specialized_outputs", {}).get("finance", "")
    
    finance_pricing_context = ""
    if finance_output and finance_output != "__FAILED__":
        finance_pricing_context = (
            "Finance Agent Pricing Tiers (Authoritative — Do Not Change):\n"
            "The following pricing tiers were defined by the Finance Agent for this venture. "
            "You MUST use these exact tier names and price values in any pricing references in "
            "your marketing assessment. Do not invent, round, or substitute different numbers.\n"
            f"{finance_output[:3000]}"  # cap to avoid prompt bloat — tiers appear near the top
        )
    else:
        finance_pricing_context = (
            "Finance Agent Pricing Tiers (Authoritative — Do Not Change):\n"
            "Finance Agent output is not yet available. Do not include any specific pricing "
            "figures in your marketing assessment; refer to pricing tiers generically instead."
        )
    
    return execute_agent_logic(
        state=state,
        agent_name="Marketing Agent",
        system_prompt=MARKETING_SYSTEM_PROMPT,
        search_keyword="marketing sales channels client profile branding vectors",
        extra_context=finance_pricing_context
    )

def risk_agent_node(state: AgentState) -> Dict[str, Any]:
    return execute_agent_logic(
        state=state,
        agent_name="Risk Agent",
        system_prompt=RISK_SYSTEM_PROMPT,
        search_keyword="risk regulatory compliance hurdles security safety"
    )
