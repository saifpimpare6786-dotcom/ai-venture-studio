import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from app.core.config import settings
from services.llm import (
    call_groq,
    call_llm,
    reset_llm_key_rotation,
    reset_gemini_circuit_breaker
)


class TestGroqProvider(unittest.TestCase):

    def setUp(self):
        self.orig_groq_key = settings.GROQ_API_KEY
        self.orig_groq_keys = settings.GROQ_API_KEYS
        reset_gemini_circuit_breaker()
        reset_llm_key_rotation()

    def tearDown(self):
        settings.GROQ_API_KEY = self.orig_groq_key
        settings.GROQ_API_KEYS = self.orig_groq_keys
        reset_gemini_circuit_breaker()
        reset_llm_key_rotation()

    @patch("services.llm.httpx.post")
    def test_call_groq_payload_and_headers(self, mock_post):
        settings.GROQ_API_KEYS = "gsk_test_key_1,gsk_test_key_2"
        reset_llm_key_rotation()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Groq test output"}}]
        }
        mock_post.return_value = mock_resp

        res = call_groq("Test prompt", system_prompt="System prompt", agent_name="Strategy Agent")
        
        self.assertEqual(res, "Groq test output")
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        
        self.assertEqual(args[0], "https://api.groq.com/openai/v1/chat/completions")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer gsk_test_key_1")
        payload = kwargs["json"]
        self.assertEqual(payload["model"], "llama-3.3-70b-versatile")
        self.assertEqual(len(payload["messages"]), 2)
        self.assertEqual(payload["messages"][0], {"role": "system", "content": "System prompt"})
        self.assertEqual(payload["messages"][1], {"role": "user", "content": "Test prompt"})

    @patch("services.llm.call_groq")
    def test_call_llm_tries_groq_first(self, mock_groq):
        mock_groq.return_value = "Response from Groq"
        
        result = call_llm("Test prompt", agent_name="Finance Agent")
        
        self.assertEqual(result, "Response from Groq")
        mock_groq.assert_called_once()

    @patch("services.llm.call_nvidia_nim")
    @patch("services.llm.call_groq")
    def test_call_llm_falls_back_to_nvidia_when_groq_fails(self, mock_groq, mock_nim):
        mock_groq.side_effect = RuntimeError("All 2 Groq API key(s) exhausted for this run.")
        mock_nim.return_value = "Response from NVIDIA NIM"

        result = call_llm("Test prompt", agent_name="Finance Agent")

        self.assertEqual(result, "Response from NVIDIA NIM")
        mock_groq.assert_called_once()
        mock_nim.assert_called_once()


if __name__ == "__main__":
    unittest.main()
