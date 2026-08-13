import os
import sys
import unittest

# Add backend directory to Python sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from app.core.config import settings
from services.llm import (
    call_nvidia_nim,
    call_gemini,
    call_llm,
    reset_llm_key_rotation,
    reset_gemini_circuit_breaker
)

class TestMultiApiKeyRotation(unittest.TestCase):

    def setUp(self):
        self.orig_nim_key = settings.NVIDIA_NIM_API_KEY
        self.orig_nim_keys = settings.NVIDIA_API_KEYS
        self.orig_gemini_key = settings.GEMINI_API_KEY
        self.orig_gemini_keys = settings.GEMINI_API_KEYS
        reset_gemini_circuit_breaker()

    def tearDown(self):
        settings.NVIDIA_NIM_API_KEY = self.orig_nim_key
        settings.NVIDIA_API_KEYS = self.orig_nim_keys
        settings.GEMINI_API_KEY = self.orig_gemini_key
        settings.GEMINI_API_KEYS = self.orig_gemini_keys
        reset_gemini_circuit_breaker()

    def test_key_parsing_backward_compatibility(self):
        settings.NVIDIA_NIM_API_KEY = "single_nvidia_key"
        settings.NVIDIA_API_KEYS = None
        settings.GEMINI_API_KEY = "single_gemini_key"
        settings.GEMINI_API_KEYS = None

        self.assertEqual(settings.get_nvidia_keys(), ["single_nvidia_key"])
        self.assertEqual(settings.get_gemini_keys(), ["single_gemini_key"])

        settings.NVIDIA_API_KEYS = "key1, key2 , key3 "
        settings.GEMINI_API_KEYS = "gkey1, gkey2"

        self.assertEqual(settings.get_nvidia_keys(), ["key1", "key2", "key3"])
        self.assertEqual(settings.get_gemini_keys(), ["gkey1", "gkey2"])

    def test_nvidia_key_rotation_on_auth_quota_failure(self):
        settings.NVIDIA_API_KEYS = "invalid_nim_key_1, invalid_nim_key_2"
        reset_llm_key_rotation()

        with self.assertRaises(RuntimeError) as ctx:
            call_nvidia_nim("Test ping", agent_name="Unit Test")
        
        self.assertIn("exhausted", str(ctx.exception).lower())

    def test_gemini_key_rotation_on_auth_quota_failure(self):
        settings.GEMINI_API_KEYS = "invalid_gemini_key_1, invalid_gemini_key_2"
        reset_llm_key_rotation()

        with self.assertRaises(RuntimeError) as ctx:
            call_gemini("Test ping")
        
        self.assertIn("exhausted", str(ctx.exception).lower())

    def test_nvidia_key_rotation_first_invalid_second_valid(self):
        real_nvidia_keys = settings.get_nvidia_keys()
        if not real_nvidia_keys:
            self.skipTest("No valid NVIDIA key available for live test.")
        
        valid_key = real_nvidia_keys[0]
        # First key is bogus, second key is valid
        settings.NVIDIA_API_KEYS = f"invalid_nim_key_bogus_123, {valid_key}"
        reset_llm_key_rotation()

        # Call should rotate past key 1 and succeed with key 2
        result = call_nvidia_nim("Test ping", agent_name="Rotation Test")
        self.assertTrue(isinstance(result, str) and len(result) > 0)

if __name__ == "__main__":
    unittest.main()
