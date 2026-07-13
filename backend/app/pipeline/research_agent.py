import os
import time
import uuid
import httpx
from typing import Dict, Any, List
from app.database.supabase import get_supabase_client
from app.core.config import settings
from services.llm import call_llm
from services.document_parser import chunk_text
from services.rag_retriever import ingest_chunks, get_chroma_client
from app.pipeline.state import AgentState

QUERY_EXTRACTOR_SYSTEM_PROMPT = """
You are an expert search query generator. 
Analyze the provided business analysis plan and extract the 2-3 most specific, high-relevance web search queries suggested in the 'Web Research Recommendations' section. 

Return them ONLY as a plain list, one query per line, without numbers, bullets, or quotes.
"""

def execute_tavily_search(query: str) -> Dict[str, Any]:
    """
    Executes a Tavily search query with exponential backoff on HTTP 429 rate limits.
    """
    api_key = settings.TAVILY_API_KEY
    if not api_key:
        print("Tavily API key is missing. Skipping search.")
        return {}
        
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "include_answer": True
    }
    
    max_retries = 3
    backoff = 1.0
    for attempt in range(max_retries):
        try:
            response = httpx.post("https://api.tavily.com/search", json=payload, timeout=20.0)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                print(f"Tavily 429 rate limit hit. Retrying in {backoff}s...")
                time.sleep(backoff)
                backoff *= 2.0
            else:
                print(f"Tavily error (Status {response.status_code}): {response.text}")
                return {}
        except Exception as e:
            print(f"Tavily request error: {str(e)}")
            if attempt == max_retries - 1:
                return {}
            time.sleep(backoff)
            backoff *= 2.0
            
    return {}

def research_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Research Agent Node logic.
    Extracts queries from the plan, conducts web searches, 
    chunks and embeds the results into ChromaDB, and logs execution.
    """
    project_id = state.get("project_id")
    plan = state.get("plan", "")
    
    print(f"--- [Research Agent Node] Starting execution for Project {project_id} ---")
    
    if not plan:
        print("No plan available in state. Skipping research.")
        return {"research_results": "No research conducted. Plan was empty."}
        
    force_refresh = state.get("force_refresh", False)
    
    # Cache Check: Check if chunks already exist in ChromaDB for this project
    client = get_chroma_client()
    collection_name = f"project_{project_id.replace('-', '_')}"
    
    has_cache = False
    collection = None
    existing_chunks = []
    try:
        collection = client.get_collection(name=collection_name)
        existing = collection.get(where={"source_type": "web_research"})
        if existing and existing.get("documents"):
            existing_chunks = existing.get("documents", [])
            has_cache = True
            print(f"Cache check: Found {len(existing_chunks)} existing web research chunks in ChromaDB.")
    except Exception:
        # Collection might not exist yet
        pass
        
    if has_cache and not force_refresh:
        print("Cache Hit! Reusing existing web research chunks from ChromaDB cache. Skipping Tavily searches.")
        # Reconstruct summary from cached chunks
        deduped = []
        seen = set()
        for doc in existing_chunks:
            if doc not in seen:
                seen.add(doc)
                deduped.append(doc)
        research_summary = "\n\n---\n\n".join(deduped[:10])  # limit summary size if there are many chunks
        
        # Log cached execution to agent_logs
        try:
            supabase = get_supabase_client()
            supabase.table("agent_logs").insert({
                "project_id": project_id,
                "agent_name": "Research Agent",
                "status": "completed (cached)",
                "input_data": {
                    "force_refresh": force_refresh,
                    "cache_hit": True,
                    "cached_chunks_count": len(existing_chunks)
                },
                "output_data": {
                    "research_summary": research_summary[:1000]
                }
            }).execute()
            print("Logged cached Research Agent execution to Supabase.")
        except Exception as db_err:
            print(f"Supabase Agent Log Sync Warning (continuing): {str(db_err)}")
            
        print(f"--- [Research Agent Node] Finished execution (Cached) ---")
        return {
            "research_results": research_summary
        }
        
    # If force_refresh is True and we have existing cache, delete old chunks to prevent duplication
    if force_refresh and has_cache and collection:
        try:
            print("Force refresh is active. Deleting existing web research chunks in ChromaDB...")
            collection.delete(where={"source_type": "web_research"})
            print("Existing chunks deleted.")
        except Exception as delete_err:
            print(f"Warning deleting old chunks: {str(delete_err)}")
            
    # 1. Extract search queries using the LLM
    print("Extracting queries from plan...")
    queries_raw = call_llm(
        prompt=plan,
        system_prompt=QUERY_EXTRACTOR_SYSTEM_PROMPT,
        preferred_provider="nvidia",
        project_id=project_id,
        agent_name="Research Agent"
    )
    
    # Check if LLM call failed completely
    if isinstance(queries_raw, dict) and queries_raw.get("status") == "failed":
        print(f"Research Agent node failed to extract queries: {queries_raw['error']}")
        return {
            "research_results": f"Execution failed: {queries_raw['error']}"
        }
        
    queries = [q.strip() for q in queries_raw.split("\n") if q.strip()]
    
    # Cap queries at 3 to conserve quota
    queries = queries[:3]
    print(f"Extracted queries for search: {queries}")
    
    all_raw_results = {}
    aggregated_summaries = []
    
    # 2. Execute Tavily search queries
    for idx, query in enumerate(queries):
        print(f"Executing search {idx + 1}/{len(queries)}: '{query}'")
        search_data = execute_tavily_search(query)
        if not search_data:
            continue
            
        all_raw_results[query] = search_data
        
        # Accumulate clean text content for the database ingestion
        answer = search_data.get("answer", "")
        results = search_data.get("results", [])
        
        text_elements = []
        if answer:
            text_elements.append(f"Answer Summary: {answer}")
            
        for r_idx, r in enumerate(results):
            title = r.get("title", "No Title")
            url = r.get("url", "No URL")
            content = r.get("content", "")
            text_elements.append(f"Result [{r_idx + 1}] {title} ({url})\nContent: {content}")
            
        raw_text = "\n\n".join(text_elements)
        if not raw_text.strip():
            continue
            
        # 3. Route through document-processing pipeline
        # Chunk text
        chunks = chunk_text(raw_text, chunk_size=300, overlap=30)
        
        # Embed and ingest into ChromaDB
        query_slug = "".join(c if c.isalnum() else "_" for c in query.lower())
        document_id = f"web_research_{str(uuid.uuid4())[:8]}"
        filename = f"web_search_{query_slug}"
        
        print(f"Ingesting {len(chunks)} search chunks into ChromaDB...")
        ingest_chunks(
            project_id=project_id,
            document_id=document_id,
            filename=filename,
            category="Web Research",
            chunks=chunks,
            extra_metadata={"source_type": "web_research"}
        )
        
        # Collect summaries for state output
        aggregated_summaries.append(f"Query: '{query}'\nAnswer: {answer or 'No summary answer available.'}")
        
    research_summary = "\n\n---\n\n".join(aggregated_summaries) if aggregated_summaries else "Web research completed, but no results were returned."
    
    # 4. Log transaction to Supabase agent_logs
    try:
        supabase = get_supabase_client()
        supabase.table("agent_logs").insert({
            "project_id": project_id,
            "agent_name": "Research Agent",
            "status": "completed",
            "input_data": {
                "extracted_queries": queries
            },
            "output_data": {
                "research_summary": research_summary[:1000],
                "raw_results_keys": list(all_raw_results.keys())
            }
        }).execute()
        print("Logged Research Agent execution to Supabase.")
    except Exception as db_err:
        print(f"Supabase Agent Log Sync Warning (continuing): {str(db_err)}")
        
    print(f"--- [Research Agent Node] Finished execution ---")
    return {
        "research_results": research_summary
    }
