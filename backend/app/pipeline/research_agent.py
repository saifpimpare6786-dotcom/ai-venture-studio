import os
import time
import uuid
import httpx
from typing import Dict, Any, List
from app.database.supabase import get_supabase_client
from app.core.config import settings
from services.llm import call_llm
from services.document_parser import chunk_text
from services.rag_retriever import ingest_chunks, get_chroma_client, retrieve_context
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
    Extracts queries from the plan, conducts web searches (Tavily API),
    falls back to local RAG (ChromaDB) if Tavily quota/API fails,
    chunks and embeds fresh web results into ChromaDB, and logs execution path.
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
                    "research_results": research_summary,
                    "research_summary": research_summary
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
    execution_paths = []
    tavily_failures = 0
    degraded_queries = []
    
    # 2. Execute Tavily search queries with local RAG fallback on quota/API failure
    for idx, query in enumerate(queries):
        print(f"Executing search {idx + 1}/{len(queries)}: '{query}'")
        search_data = execute_tavily_search(query)
        
        has_tavily_results = bool(
            search_data and (search_data.get("answer") or search_data.get("results"))
        )
        
        if has_tavily_results:
            print(f"[Research Agent] Path used: Live Tavily Search for query '{query}'")
            execution_paths.append({"query": query, "path": "live_tavily_search"})
            all_raw_results[query] = search_data
            
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
            if raw_text.strip():
                chunks = chunk_text(raw_text, chunk_size=300, overlap=30)
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
                
                aggregated_summaries.append(f"Query: '{query}' [Live Tavily Search]\nAnswer: {answer or 'No summary answer available.'}")
        else:
            # ── Tavily API Failed / Quota Exhausted: Fall back to Local RAG ──────
            tavily_failures += 1
            print(f"[Research Agent] Path used: Local RAG Fallback (ChromaDB) for query '{query}' (Tavily search failed/exhausted)")
            
            rag_chunks = []
            try:
                rag_chunks = retrieve_context(project_id, query, top_k=5)
            except Exception as rag_err:
                print(f"[Research Agent] Error querying local RAG for query '{query}': {rag_err}")
                
            if rag_chunks:
                print(f"[Research Agent] Local RAG Fallback retrieved {len(rag_chunks)} relevant chunks for query '{query}'")
                execution_paths.append({"query": query, "path": "local_rag_fallback", "chunks_retrieved": len(rag_chunks)})
                rag_text = "\n".join(f"- {c[:300]}" for c in rag_chunks[:3])
                aggregated_summaries.append(
                    f"Query: '{query}' [Local RAG Fallback]\nSummary Context:\n{rag_text}"
                )
            else:
                # ── Local RAG also has no relevant chunks: Log explicit warning ──
                print(f"[Research Agent] WARNING: Local RAG knowledge base returned no relevant chunks for query '{query}'. Proceeding with degraded/empty context for this query.")
                degraded_queries.append(query)
                execution_paths.append({"query": query, "path": "degraded_empty_context"})
                aggregated_summaries.append(
                    f"Query: '{query}' [DEGRADED INPUT WARNING]: Tavily search failed and local RAG knowledge base contained no relevant chunks for this topic."
                )

    # 3. Assemble research summary & attach status warning headers if degraded
    if aggregated_summaries:
        research_body = "\n\n---\n\n".join(aggregated_summaries)
        if tavily_failures > 0:
            status_header = f"[RESEARCH STATUS WARNING: Local RAG Fallback Active | Tavily Failures: {tavily_failures}/{len(queries)} | Degraded Queries: {len(degraded_queries)}]"
            research_summary = f"{status_header}\n\n{research_body}"
        else:
            research_summary = research_body
    else:
        research_summary = "[RESEARCH STATUS WARNING: Degraded Input - Tavily quota/API failed and local RAG contained no research context.]"

    # 4. Log transaction to Supabase agent_logs
    try:
        supabase = get_supabase_client()
        status_str = "completed (with_local_rag_fallback)" if tavily_failures > 0 else "completed"
        supabase.table("agent_logs").insert({
            "project_id": project_id,
            "agent_name": "Research Agent",
            "status": status_str,
            "input_data": {
                "extracted_queries": queries,
                "force_refresh": force_refresh
            },
            "output_data": {
                "research_results": research_summary,
                "research_summary": research_summary,
                "execution_paths": execution_paths,
                "tavily_failures": tavily_failures,
                "degraded_queries": degraded_queries,
                "fallback_used": tavily_failures > 0,
                "raw_results_keys": list(all_raw_results.keys())
            }
        }).execute()
        print(f"Logged Research Agent execution ({status_str}) to Supabase.")
    except Exception as db_err:
        print(f"Supabase Agent Log Sync Warning (continuing): {str(db_err)}")
        
    print(f"--- [Research Agent Node] Finished execution ---")
    return {
        "research_results": research_summary
    }

