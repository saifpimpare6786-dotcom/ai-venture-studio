import os
import sys
import uuid

# Add backend directory to Python sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# Load env variables from root or backend .env file
from dotenv import load_dotenv
backend_env = os.path.join(backend_dir, ".env")
if os.path.exists(backend_env):
    load_dotenv(backend_env)
else:
    load_dotenv(os.path.join(backend_dir, "..", ".env"))

from app.database.supabase import get_supabase_client
from app.pipeline.graph import execute_pipeline

def safe_print(text):
    if text is None:
        print(None)
    elif isinstance(text, str):
        # Handle encoding for Windows CP1252 terminal safely
        encoding = sys.stdout.encoding or "utf-8"
        print(text.encode(encoding, errors="replace").decode(encoding))
    else:
        print(text)

def run_test():
    print("=== AI Venture Studio LangGraph Agent Pipeline Test ===")
    
    supabase = get_supabase_client()
    project_id = None
    created_temp_project = False
    temp_user_id = None
    
    # 1. Try to find an existing project to use for valid UUID foreign keys
    try:
        res = supabase.table("projects").select("id, user_id").limit(1).execute()
        if res.data:
            project_id = res.data[0]["id"]
            print(f"Found existing project ID in database: {project_id}")
        else:
            print("No projects found in database. Creating a temporary test profile & project...")
            
            # Generate UUIDs
            temp_user_id = str(uuid.uuid4())
            project_id = str(uuid.uuid4())
            
            # Insert profile (auth.users id bypass via service role)
            # To bypass auth.users foreign key constraint, we can insert directly if possible.
            # Wait, public.profiles REFERENCES auth.users(id). If we insert a random user_id, 
            # foreign key constraint will fail because the user doesn't exist in auth.users!
            # Let's see if we can query auth users or find any profile first.
            profiles_res = supabase.table("profiles").select("id").limit(1).execute()
            if profiles_res.data:
                temp_user_id = profiles_res.data[0]["id"]
                print(f"Using existing profile ID: {temp_user_id}")
            else:
                # If no profiles exist, we might have to bypass log insertion or write a fallback.
                # Let's hope at least one profile exists. If not, we'll log a warning.
                pass
                
            if temp_user_id:
                # Insert project
                proj_res = supabase.table("projects").insert({
                    "id": project_id,
                    "user_id": temp_user_id,
                    "name": "EcoSphere Sustainable Tech",
                    "industry": "CleanTech & Sustainability",
                    "idea_input": "Carbon tracking dashboard for SMEs to simplify utilities reporting."
                }).execute()
                if proj_res.data:
                    created_temp_project = True
                    print(f"Successfully created temporary project: {project_id}")
    except Exception as e:
        print(f"Database lookup/setup warning: {str(e)}")
        
    if not project_id:
        # Fallback to a mock UUID so pipeline runs, even if database logs fail
        project_id = str(uuid.uuid4())
        print(f"Falling back to mock project UUID: {project_id}")

    # 2. Setup initial state
    initial_state = {
        "project_id": project_id,
        "business_idea_input": (
            "EcoSphere Ventures is an automated carbon tracking dashboard for small and medium enterprises. "
            "It connects to utility API logs, reads delivery truck transport mileage, and generates instant reports."
        ),
        "rag_context": [
            "MSME green credit schemes in 2026 subsidize up to 30% of sustainability software licensing fees.",
            "Average SME spends 80-120 hours annually aggregating utility invoices for carbon compliance audits."
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
        
        print("\n[Planning Agent Node Output - Plan]:")
        safe_print(final_state.get("plan"))
        
        print("\n[Orchestrator Agent Node Output - Research Results preview]:")
        safe_print(final_state.get("research_results"))
        
        print("\n[Business Rules Engine Output (Rules Validation Result)]:")
        safe_print(final_state.get("rules_validation_result"))
        
        print("\n[Analytics & Scoring Engine Output - Scores]:")
        safe_print(final_state.get("scores"))
        
        # Verify scores structure
        scores = final_state.get("scores", {})
        assert "overall_score" in scores, "overall_score must be computed"
        assert "viability" in scores, "viability score must be present"
        assert "market_fit" in scores, "market_fit score must be present"
        assert "financial_soundness" in scores, "financial_soundness score must be present"
        
        # Verify reports structure and database sync
        final_report = final_state.get("final_report", "")
        assert final_report, "final_report must be generated"
        print(f"\n[Report Generator Output - Final Report preview]:\n{final_report[:600]}...")
        
        reports_res = supabase.table("reports").select("id, report_type").eq("project_id", project_id).execute()
        print(f"\nGenerated database reports count: {len(reports_res.data)}")
        for r in reports_res.data:
            print(f"- {r['report_type']} (ID: {r['id']})")
        assert len(reports_res.data) >= 5, "At least 5 reports should be generated in DB"
        
        print("\nSUCCESS: LangGraph workflow ran end-to-end through all nodes, including Analytics & Report Generator!")
        
    except Exception as run_err:
        print(f"\nERROR running pipeline: {str(run_err)}")
        sys.exit(1)
        
    finally:
        # 4. Clean up temporary project if created
        if created_temp_project and project_id:
            try:
                print(f"\nCleaning up temporary project '{project_id}'...")
                supabase.table("projects").delete().eq("id", project_id).execute()
                print("Cleanup complete.")
            except Exception as cleanup_err:
                print(f"Warning cleaning up test project: {str(cleanup_err)}")

if __name__ == "__main__":
    run_test()
