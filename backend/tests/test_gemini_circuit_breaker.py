import os
import sys
import unittest
from unittest.mock import patch

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from services.llm import (
    call_llm,
    reset_gemini_circuit_breaker,
    is_gemini_marked_down,
)


class TestGeminiCircuitBreaker(unittest.TestCase):
    """
    Unit test suite verifying the per-run Gemini circuit breaker.
    """

    def setUp(self):
        reset_gemini_circuit_breaker()

    def tearDown(self):
        reset_gemini_circuit_breaker()

    @patch("services.llm.call_gemini")
    @patch("services.llm.call_nvidia_nim")
    def test_circuit_breaker_threshold_and_bypass(self, mock_nim, mock_gemini):
        # Configure mock return values
        mock_gemini.side_effect = RuntimeError("Gemini 429 quota exhausted")
        mock_nim.return_value = "NVIDIA NIM response content"

        self.assertFalse(is_gemini_marked_down(), "Gemini should start operational.")

        # --- Call 1: Preferred provider Gemini (Fails) ---
        res1 = call_llm("Prompt 1", preferred_provider="gemini", agent_name="Reviewer Agent")
        self.assertEqual(res1, "NVIDIA NIM response content")
        self.assertEqual(mock_gemini.call_count, 1)
        self.assertEqual(mock_nim.call_count, 1)
        self.assertFalse(is_gemini_marked_down(), "1 failure should not mark Gemini DOWN yet.")

        # --- Call 2: Preferred provider Gemini (Fails 2nd time -> Trips Breaker) ---
        res2 = call_llm("Prompt 2", preferred_provider="gemini", agent_name="Critic Agent")
        self.assertEqual(res2, "NVIDIA NIM response content")
        self.assertEqual(mock_gemini.call_count, 2)
        self.assertEqual(mock_nim.call_count, 2)
        self.assertTrue(is_gemini_marked_down(), "2 consecutive failures MUST mark Gemini DOWN.")

        # --- Call 3: Preferred provider Gemini (Breaker active -> Bypasses Gemini attempt entirely) ---
        res3 = call_llm("Prompt 3", preferred_provider="gemini", agent_name="Executive Summary")
        self.assertEqual(res3, "NVIDIA NIM response content")
        # mock_gemini should STILL be 2 because call_gemini was bypassed!
        self.assertEqual(mock_gemini.call_count, 2, "Gemini call count must NOT increment when marked DOWN.")
        self.assertEqual(mock_nim.call_count, 3)

        # --- Reset for Next Run ---
        reset_gemini_circuit_breaker()
        self.assertFalse(is_gemini_marked_down(), "reset_gemini_circuit_breaker must clear DOWN state.")

        # --- Call 4: Next run should attempt Gemini primary again ---
        res4 = call_llm("Prompt 4", preferred_provider="gemini", agent_name="Reviewer Agent")
        self.assertEqual(res4, "NVIDIA NIM response content")
        self.assertEqual(mock_gemini.call_count, 3, "After reset, Gemini primary attempt must resume.")


if __name__ == "__main__":
    unittest.main()
