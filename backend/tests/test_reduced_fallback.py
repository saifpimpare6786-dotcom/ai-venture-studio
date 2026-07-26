from unittest.mock import patch
from app.pipeline.report_generator import _generate_report_json

def test_reduced_context_fallback():
    mock_config = {"system_prompt": "FULL PROMPT"}
    mock_reduced = {"system_prompt": "REDUCED PROMPT"}
    calls = []

    def mock_call_llm(*args, **kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            # First attempt fails due to rate limit / provider exhaustion
            return {"status": "failed", "error": "Rate limit 429"}
        # Fallback attempt succeeds
        return '{"threat_of_new_entrants": "High", "bargaining_power_of_buyers": "Low", "bargaining_power_of_suppliers": "Medium", "threat_of_substitutes": "Low", "competitive_rivalry": "High"}'

    with patch('app.pipeline.report_generator.call_llm', side_effect=mock_call_llm):
        res = _generate_report_json("Porter's Five Forces", mock_config, 'proj123', reduced_config=mock_reduced)
        assert len(calls) == 2
        assert calls[1]["system_prompt"] == "REDUCED PROMPT"
        assert res["threat_of_new_entrants"] == "High"
        print("Reduced-context fallback unit test PASSED successfully!")

if __name__ == "__main__":
    test_reduced_context_fallback()
