import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add backend directory to Python sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from app.core.config import settings
from services.llm import _clean_ollama_qwen_response, call_ollama, call_llm


class TestOllamaFallback(unittest.TestCase):
    def test_clean_ollama_qwen_response_thinking_tags(self):
        raw = "<think>\nThinking about business models...\nCalculating risk...\n</think>\nHere is the business strategy overview."
        cleaned = _clean_ollama_qwen_response(raw, json_mode=False)
        self.assertEqual(cleaned, "Here is the business strategy overview.")

    def test_clean_ollama_qwen_response_json_trimming(self):
        raw = "<think>Generating JSON object...</think>\nIntro text before JSON: {\"status\": \"ok\", \"score\": 85} concluding notes."
        cleaned = _clean_ollama_qwen_response(raw, json_mode=True)
        self.assertEqual(cleaned, '{"status": "ok", "score": 85}')

    @patch("services.llm.httpx.post")
    def test_call_ollama_payload_and_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "<think>Monologue</think>{\"result\": \"success\"}"
        }
        mock_post.return_value = mock_response

        res = call_ollama("Test prompt", system_prompt="System instructions", json_mode=True)
        
        self.assertEqual(res, '{"result": "success"}')
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        payload = kwargs["json"]
        self.assertEqual(payload["model"], settings.OLLAMA_MODEL)
        self.assertEqual(payload["prompt"], "Test prompt")
        self.assertEqual(payload["system"], "System instructions")
        self.assertFalse(payload["stream"])
        self.assertFalse(payload["think"])
        self.assertEqual(payload["format"], "json")

    @patch("services.llm.call_nvidia_nim")
    @patch("services.llm.call_gemini")
    @patch("services.llm.call_ollama")
    def test_call_llm_falls_back_to_ollama(self, mock_ollama, mock_gemini, mock_nim):
        mock_nim.side_effect = RuntimeError("NVIDIA NIM Rate Limit 429")
        mock_gemini.side_effect = RuntimeError("Gemini Quota Exceeded 429")
        mock_ollama.return_value = "Ollama Local Response Content"

        result = call_llm("Test prompt", preferred_provider="nvidia")
        
        self.assertEqual(result, "Ollama Local Response Content")
        mock_nim.assert_called_once()
        mock_gemini.assert_called_once()
        mock_ollama.assert_called_once_with(
            "Test prompt", system_prompt=None, max_tokens=2048, json_mode=False
        )


if __name__ == "__main__":
    unittest.main()
