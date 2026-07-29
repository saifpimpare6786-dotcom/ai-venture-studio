import os
import sys
import unittest
from io import StringIO
from unittest.mock import patch

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from services.llm import NIM_MODEL_ROUTING, ENABLE_DEEPSEEK_THINKING_MODE, print_nim_model_dispatch_table, call_nvidia_nim


class TestDispatchRouting(unittest.TestCase):
    """
    Verifies that all 13 agents route to meta/llama-3.1-70b-instruct,
    DeepSeek thinking mode is disabled by default, and the dispatch table prints properly.
    """

    def test_all_agents_route_to_llama70b(self):
        agents = [
            "Planning Agent",
            "Orchestrator Agent",
            "Research Agent",
            "Finance Agent",
            "Strategy Agent",
            "Marketing Agent",
            "Risk Agent",
            "Council Agent",
            "Reviewer Agent",
            "Critic Agent",
            "Business Rules Engine",
            "Analytics & Scoring",
            "Report Generator",
        ]
        self.assertEqual(len(agents), 13, "Pipeline must contain exactly 13 agents/nodes.")
        
        for agent in agents:
            resolved_model = NIM_MODEL_ROUTING.get(agent, NIM_MODEL_ROUTING["default"])
            self.assertEqual(
                resolved_model,
                "meta/llama-3.1-70b-instruct",
                f"Agent '{agent}' must route to 'meta/llama-3.1-70b-instruct'"
            )

    def test_deepseek_thinking_mode_disabled(self):
        self.assertFalse(
            ENABLE_DEEPSEEK_THINKING_MODE,
            "ENABLE_DEEPSEEK_THINKING_MODE must be False by default"
        )
        self.assertNotIn(
            "Finance Agent",
            NIM_MODEL_ROUTING,
            "Finance Agent direct key must be commented out in NIM_MODEL_ROUTING"
        )
        self.assertNotIn(
            "Risk Agent",
            NIM_MODEL_ROUTING,
            "Risk Agent direct key must be commented out in NIM_MODEL_ROUTING"
        )

    def test_print_nim_model_dispatch_table(self):
        captured_output = StringIO()
        with patch("sys.stdout", new=captured_output):
            print_nim_model_dispatch_table()
        
        output_str = captured_output.getvalue()
        self.assertIn("NVIDIA NIM MODEL DISPATCH ROUTING TABLE", output_str)
        self.assertIn("Planning Agent", output_str)
        self.assertIn("Finance Agent", output_str)
        self.assertIn("Risk Agent", output_str)
        self.assertIn("meta/llama-3.1-70b-instruct", output_str)

    def test_call_nvidia_nim_payload_model(self):
        mock_response = patch("httpx.post")
        with patch("httpx.post") as mock_post:
            mock_resp_obj = unittest.mock.MagicMock()
            mock_resp_obj.status_code = 200
            mock_resp_obj.json.return_value = {
                "choices": [{"message": {"content": "Test output"}}]
            }
            mock_post.return_value = mock_resp_obj

            res_fin = call_nvidia_nim(prompt="Test prompt", agent_name="Finance Agent")
            self.assertEqual(res_fin, "Test output")
            payload_fin = mock_post.call_args_list[-1][1]["json"]
            self.assertEqual(payload_fin["model"], "meta/llama-3.1-70b-instruct")

            res_risk = call_nvidia_nim(prompt="Test prompt", agent_name="Risk Agent")
            self.assertEqual(res_risk, "Test output")
            payload_risk = mock_post.call_args_list[-1][1]["json"]
            self.assertEqual(payload_risk["model"], "meta/llama-3.1-70b-instruct")


if __name__ == "__main__":
    unittest.main()
