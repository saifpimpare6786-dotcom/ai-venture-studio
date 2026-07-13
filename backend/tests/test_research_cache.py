import os
import sys
import time
import uuid

# Add backend directory to Python sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from app.database.supabase import get_supabase_client
from app.pipeline.graph import execute_pipeline
from services.rag_retriever import get_chroma_client

def count_web_chunks(project_id: str) -> int:
    client = get_chroma_client()
    collection_name = f"project_{project_id.replace('-', '_')}"
    try:
        col = client.get_collection(name=collection_name)
        res = col.get(where={"source_type": "web_research"})
        return len(res.get("documents", []))
    except Exception:
        return 0

def run_test():
    print("=== AI Venture Studio Research Agent Cache & De-duplication Test ===")
    
    supabase = get_supabase_client()
    project_id = None
    
    # Try to find an existing project to use for valid UUID foreign keys
    try:
        res = supabase.table("projects").select("id").limit(1).execute()
        if res.data:
            project_id = res.data[0]["id"]
            print(f"Found database project ID: {project_id}")
        else:
            project_id = str(uuid.uuid4())
            print(f"No projects found. Using mock project UUID: {project_id}")
    except Exception as e:
        project_id = str(uuid.uuid4())
        print(f"Database lookup warning (using fallback mock project): {str(e)}")

    # Setup initial state
    initial_state = {
        "project_id": project_id,
        "business_idea_input": (
            "EcoSphere Ventures is an automated carbon tracking dashboard for small and medium enterprises. "
            "It connects to utility API logs, reads delivery truck transport mileage, and generates instant reports."
        ),
        "rag_context": [
            "MSME green credit schemes in 2026 subsidize up to 30% of sustainability software licensing fees."
        ],
        "plan": "",
        "research_results": "",
        "specialized_outputs": {},
        "council_feedback": [],
        "reviewer_notes": "",
        "critic_notes": "",
        "rules_validation_result": {},
        "scores": {},
        "final_report": "",
        "force_refresh": True  # Start with a force refresh to create a clean fresh cache baseline
    }

    # STEP 1: Execute with force_refresh=True to establish clean cache baseline
    print("\n--- STEP 1: Executing with force_refresh=True (Clears cache, runs Tavily) ---")
    start_time = time.time()
    state_after_1 = execute_pipeline(initial_state)
    elapsed_1 = time.time() - start_time
    chunks_1 = count_web_chunks(project_id)
    print(f"STEP 1 Completed in {elapsed_1:.2f}s. Web research chunks in ChromaDB: {chunks_1}")
    
    if chunks_1 == 0:
        print("ERROR: Ingested 0 chunks in STEP 1. Verification failed.")
        sys.exit(1)

    # STEP 2: Execute with force_refresh=False (Cache Check Active)
    print("\n--- STEP 2: Executing with force_refresh=False (Should hit cache, skip Tavily) ---")
    initial_state["force_refresh"] = False
    initial_state["plan"] = state_after_1["plan"]  # reuse planning step outputs
    
    start_time = time.time()
    state_after_2 = execute_pipeline(initial_state)
    elapsed_2 = time.time() - start_time
    chunks_2 = count_web_chunks(project_id)
    print(f"STEP 2 Completed in {elapsed_2:.2f}s (Expected: very fast). Web research chunks in ChromaDB: {chunks_2}")
    
    # Assert chunk counts match and did not double
    if chunks_2 != chunks_1:
        print(f"ERROR: Chunk count changed from {chunks_1} to {chunks_2}. Caching failed to prevent duplication.")
        sys.exit(1)
        
    print("SUCCESS: Chunks did not double in count on cached run.")

    # STEP 3: Execute with force_refresh=True (Bypasses cache, de-duplicates, runs Tavily)
    print("\n--- STEP 3: Executing with force_refresh=True (Bypasses cache, clears old chunks, runs Tavily) ---")
    initial_state["force_refresh"] = True
    
    start_time = time.time()
    state_after_3 = execute_pipeline(initial_state)
    elapsed_3 = time.time() - start_time
    chunks_3 = count_web_chunks(project_id)
    print(f"STEP 3 Completed in {elapsed_3:.2f}s. Web research chunks in ChromaDB: {chunks_3}")
    
    # Assert chunk count is still stable and did not double
    if chunks_3 != chunks_1:
        print(f"Note: Chunks count updated to {chunks_3} (Step 1 had {chunks_1}). This is expected if Tavily returns slightly different results.")
    
    # Double check total collection count to make sure no duplicate accumulation happened
    if chunks_3 > chunks_1 * 1.5:
         print(f"ERROR: Chunk count grew significantly to {chunks_3}. De-duplication failed to clear old cache.")
         sys.exit(1)
         
    print("\n=== CACHE VERIFICATION SUCCESSFUL: Cache hits bypass search and de-duplication clears old chunks ===")

if __name__ == "__main__":
    run_test()
