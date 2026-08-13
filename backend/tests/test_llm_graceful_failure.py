import os
import sys

# Add backend directory to Python sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from app.core.config import settings
from services.llm import call_llm
from app.pipeline.planning_agent import planning_agent_node
from app.pipeline.review_critic_agents import reviewer_agent_node

def run_graceful_failure_tests():
    print("=== Running LLM Graceful Failure Robustness Tests ===")

    # 1. Back up original API keys and endpoints
    original_nim_key = settings.NVIDIA_NIM_API_KEY
    original_gemini_key = settings.GEMINI_API_KEY
    original_ollama_url = settings.OLLAMA_BASE_URL

    try:
        # Mock API keys and Ollama URL to force failures across all 3 providers
        print("\nMocking API keys and Ollama URL to invalid values...")
        settings.NVIDIA_NIM_API_KEY = "invalid_nim_key_to_force_failure"
        settings.GEMINI_API_KEY = "invalid_gemini_key_to_force_failure"
        settings.OLLAMA_BASE_URL = "http://localhost:99999"

        # 2. Verify wrapper returns error dict rather than raising exceptions
        print("Calling call_llm wrapper with invalid keys...")
        result = call_llm("Verify failover", preferred_provider="nvidia")
        
        print(f"Wrapper result type: {type(result)}")
        
        if not isinstance(result, dict) or result.get("status") != "failed":
            print("ERROR: call_llm wrapper did not return the expected failure dictionary!")
            sys.exit(1)
            
        print("SUCCESS: call_llm handled triple-provider failure and returned a dictionary safely!")

        # 3. Verify Planning Node handles failure dict gracefully
        print("\nTesting Planning Node graceful fallback...")
        mock_state = {
            "project_id": "00000000-0000-0000-0000-000000000000",
            "business_idea_input": "Test green energy startup",
            "rag_context": []
        }
        node_res = planning_agent_node(mock_state)
        print("Planning Node returned state keys:", list(node_res.keys()))
        
        if "Execution failed" not in node_res.get("plan", ""):
            print("ERROR: Planning Node did not capture the LLM error state!")
            sys.exit(1)
            
        print("SUCCESS: Planning Node handled LLM failure and continued executing!")

        # 4. Verify Reviewer Node handles failure dict gracefully
        print("\nTesting Reviewer Node graceful fallback...")
        mock_state_rev = {
            "project_id": "00000000-0000-0000-0000-000000000000",
            "business_idea_input": "Test green energy startup",
            "specialized_outputs": {"strategy": "Strategy test assessments"},
            "council_feedback": []
        }
        reviewer_res = reviewer_agent_node(mock_state_rev)
        print("Reviewer Node returned keys:", list(reviewer_res.keys()))
        
        if "Execution failed" not in reviewer_res.get("reviewer_notes", ""):
            print("ERROR: Reviewer Node did not capture the LLM error state!")
            sys.exit(1)
            
        print("SUCCESS: Reviewer Node handled LLM failure and continued executing!")

    finally:
        # Restore original API keys and endpoints
        print("\nRestoring original API keys and configuration...")
        settings.NVIDIA_NIM_API_KEY = original_nim_key
        settings.GEMINI_API_KEY = original_gemini_key
        settings.OLLAMA_BASE_URL = original_ollama_url

    print("\n=== ALL LLM GRACEFUL FAILURE TESTS COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    run_graceful_failure_tests()
