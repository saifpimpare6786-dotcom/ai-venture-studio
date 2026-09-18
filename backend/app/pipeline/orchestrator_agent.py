import json
from typing import Dict, Any
from app.pipeline.state import AgentState
from app.database.db import db
from services.rag_retriever import rag_retriever

async def orchestrator_node(state: AgentState) -> AgentState:
    """
    Directs the pipeline context and retrieves relevant static SME and project RAG context.
    """
    project = state["project_data"]
    project_id = state["project_id"]
    plan = state.get("plan", {})

    # Retrieve relevant RAG context from ChromaDB
    query = f"{project.get('industry')} {project.get('target_country')} {project.get('revenue_model')} benchmarks regulations"
    rag_context = rag_retriever.retrieve_context(project_id, query, top_k=4)
    state["rag_context"] = rag_context

    await db.add_agent_discussion(
        project_id=project_id,
        agent_name="Pipeline Orchestrator",
        agent_role="Context Director",
        message="Context assembly complete. Dispatching to Research and Finance Anchor.",
        step_index=2
    )
    return state

async def research_node(state: AgentState) -> AgentState:
    """
    Executes live web search via Tavily API with SHA-256 caching and vector indexing.
    """
    project = state["project_data"]
    project_id = state["project_id"]
    plan = state.get("plan", {})
    queries = plan.get("search_queries", [f"{project.get('industry')} market size {project.get('target_country')}"])

    search_results = []
    for q in queries[:2]:
        res = await rag_retriever.execute_web_search(q)
        if res:
            search_results.extend(res)

    state["research_results"] = search_results

    await db.add_agent_discussion(
        project_id=project_id,
        agent_name="Market Intelligence Agent",
        agent_role="Web Research",
        message=f"Retrieved and verified {len(search_results)} live market sources and statutory indicators.",
        step_index=3
    )
    return state
