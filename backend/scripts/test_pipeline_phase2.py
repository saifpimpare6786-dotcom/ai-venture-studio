import os
import sys

# Add backend directory to Python sys.path so we can import services and app modules
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# Load env variables from root .env file
from dotenv import load_dotenv
load_dotenv(os.path.join(backend_dir, "..", ".env"))

# Prevent Supabase errors from failing the script by supplying mock credentials if missing
if not os.environ.get("SUPABASE_URL"):
    os.environ["SUPABASE_URL"] = "https://mockproject.supabase.co"
if not os.environ.get("SUPABASE_SERVICE_ROLE_KEY"):
    os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "mockservicekey"

from app.pipeline.planning_agent import planning_agent_node
from app.pipeline.orchestrator_agent import orchestrator_agent_node

def run_standalone_agent_test():
    print("=== Standalone Planning & Orchestrator Node Verification ===")
    
    # 1. Initialize a fixed mock business idea state
    mock_state = {
        "project_id": "00000000-0000-0000-0000-000000000000",  # Default system UUID
        "business_idea_input": (
            "EcoSphere is an automated SaaS platform for carbon compliance auditing. "
            "It target SMEs by connecting directly to utility providers to read usage details "
            "and calculate emission metrics, saving significant operational reporting overhead."
        ),
        "rag_context": [
            "National carbon emission accounting policies in 2026 enforce stricter reporting deadlines for SMEs.",
            "Utility connection APIs offer reliable hourly data feeds for power and water usage analytics."
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
    
    print("\n--- Initial State ---")
    print(f"Business Idea: {mock_state['business_idea_input']}")
    print(f"RAG Context items count: {len(mock_state['rag_context'])}")

    # 2. Execute Planning Agent Node directly
    print("\n--- Running Planning Agent Node ---")
    plan_output = planning_agent_node(mock_state)
    mock_state["plan"] = plan_output.get("plan", "")
    
    print("\n[Planning Agent Output (Plan)]:")
    print(mock_state["plan"])

    # 3. Execute Orchestrator Agent Node directly
    print("\n--- Running Orchestrator Agent Node ---")
    orch_output = orchestrator_agent_node(mock_state)
    mock_state["research_results"] = orch_output.get("research_results", "")
    
    print("\n[Orchestrator Agent Output (Research Results Preview)]:")
    print(mock_state["research_results"])
    
    print("\n=== Standalone Test Completed Successfully ===")

if __name__ == "__main__":
    run_standalone_agent_test()
