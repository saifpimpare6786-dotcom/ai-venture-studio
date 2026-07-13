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

def clean_project_collection(project_id: str):
    client = get_chroma_client()
    collection_name = f"project_{project_id.replace('-', '_')}"
    try:
        client.delete_collection(name=collection_name)
        print(f"Cleaned project collection: {collection_name}")
    except Exception:
        pass

def run_test():
    print("=== AI Venture Studio Parallel Specialized Agents Verification ===")
    
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

    # Clean collection to start fresh
    clean_project_collection(project_id)

    # Initial state definition
    initial_state = {
        "project_id": project_id,
        "business_idea_input": (
            "EcoSphere is an automated carbon tracking dashboard for small and medium enterprises. "
            "It connects directly to utility provider API meters, reads transport fuel logs, "
            "and automatically calculates carbon emissions reporting metrics."
        ),
        "rag_context": [
            "MSME green credit schemes in 2026 subsidize compliance tracking audits by up to 30%."
        ],
        "plan": "",
        "directives": "",
        "research_results": "",
        "specialized_outputs": {},
        "council_feedback": [],
        "reviewer_notes": "",
        "critic_notes": "",
        "rules_validation_result": {},
        "scores": {},
        "final_report": "",
        "force_refresh": True  # Force new search & ingestion
    }

    print("\n--- Executing Full Graph Pipeline ---")
    start_time = time.time()
    final_state = execute_pipeline(initial_state)
    elapsed = time.time() - start_time
    print(f"\nPipeline execution finished in {elapsed:.2f}s.")

    # 1. Verify parallel agent outputs in state
    outputs = final_state.get("specialized_outputs", {})
    print("\n--- Verifying Specialized Business Agent Outputs ---")
    print(f"Output keys: {list(outputs.keys())}")
    
    expected_keys = ["strategy", "finance", "marketing", "risk"]
    missing = [k for k in expected_keys if k not in outputs]
    
    if missing:
        print(f"ERROR: Missing specialized outputs: {missing}. Overwrite conflict or node error occurred.")
        sys.exit(1)
        
    print("SUCCESS: All four specialized agent outputs exist without conflicts!")
    
    for agent_key in expected_keys:
        content = outputs[agent_key]
        print(f"\n[{agent_key.upper()} AGENT ASSESSMENT PREVIEW] ({len(content)} chars):")
        print(content[:300] + "...")

    # 2. Verify agent logging in Supabase agent_logs
    print("\n--- Verifying Supabase Database Logs ---")
    try:
        res = supabase.table("agent_logs").select("agent_name, status").eq("project_id", project_id).execute()
        logs = res.data
        print(f"Logged executions found: {len(logs)}")
        for log in logs:
            print(f"- {log['agent_name']}: {log['status']}")
            
        logged_agents = [log["agent_name"] for log in logs]
        expected_log_names = ["Planning Agent", "Orchestrator Agent", "Research Agent", "Strategy Agent", "Finance Agent", "Marketing Agent", "Risk Agent"]
        missing_logs = [name for name in expected_log_names if name not in logged_agents]
        
        if missing_logs:
            print(f"Warning: Expected log entries missing: {missing_logs}")
        else:
            print("SUCCESS: All pipeline agent nodes successfully logged to Supabase agent_logs!")
    except Exception as e:
        print(f"Database logging verification warning: {str(e)}")

    print("\n=== PIPELINE AGENT VERIFICATION COMPLETE ===")

if __name__ == "__main__":
    run_test()
