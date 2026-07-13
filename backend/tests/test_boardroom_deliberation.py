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
    print("=== AI Venture Studio Boardroom Deliberation Pipeline Verification ===")
    
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

    print("\n--- Executing Full Graph Pipeline (Boardroom Deliberation) ---")
    start_time = time.time()
    final_state = execute_pipeline(initial_state)
    elapsed = time.time() - start_time
    print(f"\nFull Pipeline execution finished in {elapsed:.2f}s.")

    # 1. Verify specialized outputs
    outputs = final_state.get("specialized_outputs", {})
    print("\n--- Verifying Specialized Business Agent Outputs ---")
    print(f"Output keys: {list(outputs.keys())}")
    for k in ["strategy", "finance", "marketing", "risk"]:
        if k not in outputs:
            print(f"ERROR: Missing assessment for agent '{k}'")
            sys.exit(1)
    print("SUCCESS: Parallel business agent outputs merged correctly!")

    # 2. Verify LLM Council feedback list
    council = final_state.get("council_feedback", [])
    print(f"\n--- Verifying LLM Council Feedback (Count: {len(council)}) ---")
    if not council:
        print("ERROR: LLM Council feedback list is empty!")
        sys.exit(1)
    for idx, feedback in enumerate(council):
        print(f"\nFeedback [{idx + 1}] Preview:")
        print(feedback[:250] + "...")
    print("SUCCESS: Council debate feedback recorded correctly!")

    # 3. Verify Reviewer Agent notes (Gemini)
    reviewer_notes = final_state.get("reviewer_notes", "")
    print(f"\n--- Verifying Reviewer Notes (Length: {len(reviewer_notes)}) ---")
    if not reviewer_notes:
        print("ERROR: Reviewer Notes are empty!")
        sys.exit(1)
    print(reviewer_notes[:500] + "...")
    print("SUCCESS: Reviewer notes generated and recorded!")

    # 4. Verify Critic Agent notes (Gemini)
    critic_notes = final_state.get("critic_notes", "")
    print(f"\n--- Verifying Critic Notes (Length: {len(critic_notes)}) ---")
    if not critic_notes:
        print("ERROR: Critic Notes are empty!")
        sys.exit(1)
    print(critic_notes[:500] + "...")
    print("SUCCESS: Critic notes generated and recorded!")

    # 5. Verify database logging to agent_logs
    print("\n--- Verifying Database Logs ---")
    try:
        res = supabase.table("agent_logs").select("agent_name, status").eq("project_id", project_id).execute()
        logs = res.data
        print(f"Logs recorded: {len(logs)}")
        logged_agents = [log["agent_name"] for log in logs]
        
        expected_agents = [
            "Planning Agent", "Orchestrator Agent", "Research Agent", 
            "Strategy Agent", "Finance Agent", "Marketing Agent", "Risk Agent",
            "Council Agent", "Reviewer Agent", "Critic Agent"
        ]
        missing_logs = [name for name in expected_agents if name not in logged_agents]
        
        if missing_logs:
            print(f"Warning: Expected log entries missing in database: {missing_logs}")
        else:
            print("SUCCESS: All nodes (including Council, Reviewer, and Critic) logged to Supabase agent_logs!")
    except Exception as e:
        print(f"Database verification check warning: {str(e)}")

    print("\n=== BOARDROOM DELIBERATION PIPELINE VERIFICATION COMPLETE ===")

if __name__ == "__main__":
    run_test()
