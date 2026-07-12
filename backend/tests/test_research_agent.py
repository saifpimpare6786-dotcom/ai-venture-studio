import os
import sys
import uuid

# Add backend directory to Python sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from app.database.supabase import get_supabase_client
from app.pipeline.graph import execute_pipeline
from services.rag_retriever import get_chroma_client

def run_test():
    print("=== AI Venture Studio LangGraph Pipeline with Research Node Verification ===")
    
    supabase = get_supabase_client()
    project_id = None
    
    # 1. Try to find an existing project to use for valid UUID foreign keys
    try:
        res = supabase.table("projects").select("id").limit(1).execute()
        if res.data:
            project_id = res.data[0]["id"]
            print(f"Found existing database project ID: {project_id}")
        else:
            print("No projects found in database. Using fallback mock project UUID.")
            project_id = str(uuid.uuid4())
    except Exception as e:
        project_id = str(uuid.uuid4())
        print(f"Database lookup warning (using fallback mock project): {str(e)}")

    # 2. Setup initial state
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
        "final_report": ""
    }

    # 3. Run the LangGraph pipeline
    try:
        final_state = execute_pipeline(initial_state)
        
        print("\n=== PIPELINE RUN COMPLETE ===")
        print(f"Project ID: {final_state.get('project_id')}")
        
        print("\n[Research Agent Node Output - Research Results Summary]:")
        print(final_state.get("research_results"))
        
        # 4. Verify ChromaDB Ingestion and Metadata Tagging
        print("\n--- Verifying ChromaDB Ingestion ---")
        client = get_chroma_client()
        collection_name = f"project_{project_id.replace('-', '_')}"
        
        try:
            collection = client.get_collection(name=collection_name)
            # Query Chroma for chunks tagged with source_type: web_research
            web_results = collection.get(where={"source_type": "web_research"})
            documents = web_results.get("documents", [])
            metadatas = web_results.get("metadatas", [])
            
            print(f"ChromaDB Query for 'source_type: web_research' returned {len(documents)} chunks.")
            if documents:
                print("\nSample Ingested Web Research Chunks from ChromaDB:")
                for i in range(min(len(documents), 2)):
                    print(f"[{i + 1}] Text: {documents[i][:150]}...")
                    print(f"    Metadata: {metadatas[i]}")
                print("\nSUCCESS: Web Research chunks are correctly chunked, embedded, and tagged in ChromaDB!")
            else:
                print("WARNING: ChromaDB query returned 0 chunks. Ingestion might have failed or been skipped.")
                sys.exit(1)
                
        except Exception as chroma_err:
            print(f"Error querying ChromaDB collection: {str(chroma_err)}")
            sys.exit(1)
            
    except Exception as run_err:
        print(f"\nERROR running pipeline: {str(run_err)}")
        sys.exit(1)

if __name__ == "__main__":
    run_test()
