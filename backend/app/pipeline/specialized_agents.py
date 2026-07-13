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
3. Strategic Position: Unique selling propositions (USPs) and strategic recommendations.

Ground your answers in retrieved RAG document/research evidence. Maintain a professional, executive tone.
"""

FINANCE_SYSTEM_PROMPT = """
You are the expert Finance Agent for AI Venture Studio.
Your role is to formulate financial pricing strategies and financial planning assumptions.
Analyze the provided business idea input, orchestrator directives, and RAG document context.

Deliver an expert assessment covering:
1. Revenue & Pricing Model: Suggested pricing strategies and monetisation vectors.
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
    search_keyword: str
) -> Dict[str, Any]:
    """Helper function to execute specialized agent node reasoning, context retrieval, and database logging."""
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
    
    # 3. Call LLM (Meta Llama-3.1-70b-instruct via NVIDIA NIM)
    output = call_llm(prompt=user_prompt, system_prompt=system_prompt, preferred_provider="nvidia")
    
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
    return execute_agent_logic(
        state=state,
        agent_name="Marketing Agent",
        system_prompt=MARKETING_SYSTEM_PROMPT,
        search_keyword="marketing sales channels client profile branding vectors"
    )

def risk_agent_node(state: AgentState) -> Dict[str, Any]:
    return execute_agent_logic(
        state=state,
        agent_name="Risk Agent",
        system_prompt=RISK_SYSTEM_PROMPT,
        search_keyword="risk regulatory compliance hurdles security safety"
    )
