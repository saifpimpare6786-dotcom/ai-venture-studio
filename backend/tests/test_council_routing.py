import os
import sys
from unittest.mock import patch, MagicMock

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from services.llm import call_nvidia_nim, call_llm
from app.pipeline.council_agent import llm_council_node

def test_llm_nim_routing_and_tokens():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Test output"}}]
    }

    with patch("httpx.post", return_value=mock_response) as mock_post:
        # Standard agent call -> default 2048 max_tokens & default llama-3.1-70b-instruct
        res1 = call_nvidia_nim(prompt="Test prompt", agent_name="Strategy Agent")
        assert res1 == "Test output"
        payload1 = mock_post.call_args_list[-1][1]["json"]
        assert payload1["max_tokens"] == 2048
        assert payload1["model"] == "meta/llama-3.1-70b-instruct"

        # Marketing Agent call -> meta/llama-3.1-70b-instruct
        res_mkt = call_nvidia_nim(prompt="Test prompt", agent_name="Marketing Agent")
        assert res_mkt == "Test output"
        payload_mkt = mock_post.call_args_list[-1][1]["json"]
        assert payload_mkt["model"] == "meta/llama-3.1-70b-instruct"

        # Report call -> auto-bumped to 8192 max_tokens
        res2 = call_nvidia_nim(prompt="Test prompt", agent_name="Report Generator (Executive Summary)")
        assert res2 == "Test output"
        payload2 = mock_post.call_args_list[-1][1]["json"]
        assert payload2["max_tokens"] == 8192

        # Council call -> auto-bumped to 8192 max_tokens
        res3 = call_nvidia_nim(prompt="Test prompt", agent_name="Council Agent")
        assert res3 == "Test output"
        payload3 = mock_post.call_args_list[-1][1]["json"]
        assert payload3["max_tokens"] == 8192

    print("[Test 1] NIM Routing & Token Budget Scaling PASSED!")


def test_council_node_consolidated_path():
    mock_state = {
        "project_id": "test-proj-council-1call",
        "specialized_outputs": {
            "strategy": "Strategy details...",
            "finance": "Finance details...",
            "marketing": "Marketing details...",
            "risk": "Risk details..."
        }
    }

    mock_json = """{
        "strategy_review": "Marketing plan aligns well.",
        "finance_review": "Unit economics need adjustment.",
        "marketing_review": "Pricing tiers look attractive.",
        "risk_review": "GDPR compliance risk identified.",
        "consensus_summary": "Overall good alignment with minor pricing and regulatory adjustments."
    }"""

    with patch("app.pipeline.council_agent.call_llm", return_value=mock_json), \
         patch("app.pipeline.council_agent.get_supabase_client", side_effect=Exception("DB skip")):
        
        res = llm_council_node(mock_state)
        feedback = res.get("council_feedback", [])
        assert len(feedback) == 5
        assert "### Strategy Agent's review" in feedback[0]
        assert "### Council Consensus Summary" in feedback[4]
        print("[Test 2] Consolidated 1-Call Council Review path PASSED!")


def test_council_node_fallback_path():
    mock_state = {
        "project_id": "test-proj-council-fallback",
        "specialized_outputs": {
            "strategy": "Strategy details...",
            "finance": "Finance details...",
            "marketing": "Marketing details...",
            "risk": "Risk details..."
        }
    }

    # Consolidated call & repair both return non-JSON string
    with patch("app.pipeline.council_agent.call_llm", return_value="Malformed non-JSON output"), \
         patch("app.pipeline.council_agent.get_supabase_client", side_effect=Exception("DB skip")):
        
        res = llm_council_node(mock_state)
        feedback = res.get("council_feedback", [])
        assert len(feedback) == 4
        assert any("### Strategy Agent's review of Marketing Plan" in item for item in feedback)
        print("[Test 3] Fallback 4-Call Concurrent Review path PASSED!")


if __name__ == "__main__":
    test_llm_nim_routing_and_tokens()
    test_council_node_consolidated_path()
    test_council_node_fallback_path()
    print("\nALL HYBRID ROUTING & COUNCIL DEBATE TESTS PASSED SUCCESSFULLY!")
