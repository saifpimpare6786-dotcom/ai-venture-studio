import os
import sys
import json

# Add backend directory to Python sys.path so we can import services and app modules
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

# Prevent Supabase errors from failing the script by supplying mock credentials if missing
if not os.environ.get("SUPABASE_URL"):
    os.environ["SUPABASE_URL"] = "https://mockproject.supabase.co"
if not os.environ.get("SUPABASE_SERVICE_ROLE_KEY"):
    os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "mockservicekey"

from app.database.supabase import get_supabase_client
from app.pipeline.planning_agent import planning_agent_node
from app.pipeline.orchestrator_agent import orchestrator_agent_node
from app.pipeline.research_agent import research_agent_node
from app.pipeline.specialized_agents import (
    strategy_agent_node,
    finance_agent_node,
    marketing_agent_node,
    risk_agent_node
)
from app.pipeline.council_agent import llm_council_node
from app.pipeline.review_critic_agents import (
    reviewer_agent_node,
    critic_agent_node
)
from app.pipeline.rules_engine import business_rules_engine_node
from app.pipeline.scoring_engine import analytics_scoring_node

def run_standalone_agent_test():
    print("=== Standalone Planning & Orchestrator Node Verification ===")
    
    # Dynamically resolve an existing project ID from the DB so logs insert successfully
    project_id = "00000000-0000-0000-0000-000000000000"
    try:
        supabase = get_supabase_client()
        res = supabase.table("projects").select("id").limit(1).execute()
        if res.data:
            project_id = res.data[0]["id"]
            print(f"Dynamically resolved database project ID: {project_id}")
    except Exception as db_err:
        print(f"Database lookup warning (using default mock project): {str(db_err)}")
        
    # 1. Initialize a fixed mock business idea state
    mock_state = {
        "project_id": project_id,
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
        "directives": "",
        "research_results": "",
        "specialized_outputs": {},
        "council_feedback": [],
        "reviewer_notes": "",
        "critic_notes": "",
        "rules_validation_result": {},
        "scores": {},
        "final_report": "",
        "force_refresh": True
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
    mock_state["directives"] = orch_output.get("directives", "")
    
    print("\n[Orchestrator Agent Output (Downstream Directives)]:")
    print(mock_state["directives"])
    
    # 4. Execute Research Agent Node directly
    print("\n--- Running Research Agent Node ---")
    research_output = research_agent_node(mock_state)
    mock_state["research_results"] = research_output.get("research_results", "")
    
    print("\n[Research Agent Output (Research Results Summary)]:")
    print(mock_state["research_results"])
    
    # 5. Execute Specialized Business Agent Nodes directly
    print("\n--- Running Specialized Business Agent Nodes ---")
    
    # Strategy Agent
    print("\nExecuting Strategy Agent...")
    strat_output = strategy_agent_node(mock_state)
    mock_state["specialized_outputs"].update(strat_output.get("specialized_outputs", {}))
    print("[Strategy Agent Output Assessment Preview]:")
    print(mock_state["specialized_outputs"].get("strategy", "")[:800] + "...\n")
    
    # Finance Agent
    print("\nExecuting Finance Agent...")
    fin_output = finance_agent_node(mock_state)
    mock_state["specialized_outputs"].update(fin_output.get("specialized_outputs", {}))
    print("[Finance Agent Output Assessment Preview]:")
    print(mock_state["specialized_outputs"].get("finance", "")[:800] + "...\n")
    
    # Marketing Agent
    print("\nExecuting Marketing Agent...")
    mkt_output = marketing_agent_node(mock_state)
    mock_state["specialized_outputs"].update(mkt_output.get("specialized_outputs", {}))
    print("[Marketing Agent Output Assessment Preview]:")
    print(mock_state["specialized_outputs"].get("marketing", "")[:800] + "...\n")
    
    # Risk Agent
    print("\nExecuting Risk Agent...")
    risk_output = risk_agent_node(mock_state)
    mock_state["specialized_outputs"].update(risk_output.get("specialized_outputs", {}))
    print("[Risk Agent Output Assessment Preview]:")
    print(mock_state["specialized_outputs"].get("risk", "")[:800] + "...\n")
    
    # 6. Execute LLM Council Node directly
    print("\n--- Running LLM Council Node ---")
    council_output = llm_council_node(mock_state)
    mock_state["council_feedback"] = council_output.get("council_feedback", [])
    
    print(f"\n[LLM Council Output (Feedback Count: {len(mock_state['council_feedback'])})]:")
    for idx, feedback in enumerate(mock_state["council_feedback"]):
        print(f"\nFeedback [{idx + 1}]:")
        print(feedback[:1000] + "...\n")
        
    # 7. Execute Reviewer Agent Node directly
    print("\n--- Running Reviewer Agent Node ---")
    rev_output = reviewer_agent_node(mock_state)
    mock_state["reviewer_notes"] = rev_output.get("reviewer_notes", "")
    
    print("\n[Reviewer Agent Output (Reviewer Notes)]:")
    print(mock_state["reviewer_notes"][:1500] + "...\n")
    
    # 8. Execute Critic Agent Node directly
    print("\n--- Running Critic Agent Node ---")
    critic_output = critic_agent_node(mock_state)
    mock_state["critic_notes"] = critic_output.get("critic_notes", "")
    
    print("\n[Critic Agent Output (Critic Notes)]:")
    print(mock_state["critic_notes"][:1500] + "...\n")
    
    # 9. Execute Business Rules Engine directly
    print("\n--- Running Business Rules Engine Node ---")
    rules_output = business_rules_engine_node(mock_state)
    mock_state["rules_validation_result"] = rules_output.get("rules_validation_result", {})
    
    print("\n[Business Rules Engine Output (Rules Validation Result)]:")
    print(f"Is Valid: {mock_state['rules_validation_result'].get('is_valid')}")
    print(f"Errors Found: {mock_state['rules_validation_result'].get('errors')}")
    print(f"Extracted Metrics: {mock_state['rules_validation_result'].get('extracted_data')}\n")
    
    # 10. Execute Analytics & Scoring Engine directly
    print("\n--- Running Analytics & Scoring Engine Node ---")
    scoring_output = analytics_scoring_node(mock_state)
    mock_state["scores"] = scoring_output.get("scores", {})
    
    print("\n[Analytics & Scoring Engine Output (Scores)]:")
    print(json.dumps(mock_state["scores"], indent=2))
    
    print("\n=== Standalone Test Completed Successfully ===")

if __name__ == "__main__":
    run_standalone_agent_test()
