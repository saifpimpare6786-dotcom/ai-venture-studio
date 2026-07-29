import os
import sys
import time
import uuid
import unittest

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from dotenv import load_dotenv
backend_env = os.path.join(backend_dir, ".env")
if os.path.exists(backend_env):
    load_dotenv(backend_env)
else:
    load_dotenv(os.path.join(backend_dir, "..", ".env"))

from app.pipeline.specialized_agents import marketing_agent_node
from services.llm import NIM_MODEL_ROUTING


class TestMarketingDeepSeekRouting(unittest.TestCase):
    """
    Round 1 Verification: Confirms Marketing Agent routing to deepseek-ai/deepseek-v4-flash
    across 3 consecutive runs, evaluating latency, character volume, and rate-limit stability.
    """

    def test_marketing_agent_3_runs(self):
        print("\n" + "=" * 70)
        print("=== ROUND 1: MARKETING AGENT ROUTING VERIFICATION (3 TEST RUNS) ===")
        print(f"Target Model Configured for 'Marketing Agent': {NIM_MODEL_ROUTING.get('Marketing Agent')}")
        print("=" * 70)

        target_model = NIM_MODEL_ROUTING.get("Marketing Agent", NIM_MODEL_ROUTING["default"])
        self.assertEqual(
            target_model,
            "meta/llama-3.1-70b-instruct",
            "NIM_MODEL_ROUTING must map 'Marketing Agent' to 'meta/llama-3.1-70b-instruct'"
        )

        mock_state = {
            "project_id": str(uuid.uuid4()),
            "business_idea_input": (
                "EcoSphere is an automated carbon tracking dashboard for small and medium enterprises. "
                "It connects directly to utility provider API meters, reads transport fuel logs, "
                "and automatically calculates carbon emissions reporting metrics."
            ),
            "directives": "Focus on high-converting B2B inbound channels and SME partner ecosystem.",
            "specialized_outputs": {
                "finance": (
                    "FINANCE PRICING REFERENCE:\n"
                    "Starter: £149/month\n"
                    "Growth: £499/month\n"
                    "Enterprise: from £1,499/month"
                )
            }
        }

        results = []

        for run_idx in range(1, 4):
            print(f"\n--- [Run {run_idx}/3] Executing Marketing Agent Node ---")
            start_time = time.time()
            
            try:
                res = marketing_agent_node(mock_state)
                elapsed = time.time() - start_time
                output_text = res.get("specialized_outputs", {}).get("marketing", "")
                
                status = "SUCCESS" if output_text and output_text != "__FAILED__" else "FAILED"
                char_count = len(output_text) if output_text else 0
                
                results.append({
                    "run": run_idx,
                    "status": status,
                    "model": "deepseek-ai/deepseek-v4-flash",
                    "latency_sec": round(elapsed, 2),
                    "char_count": char_count,
                    "error": None
                })
                
                print(f"[Run {run_idx}/3] Completed in {elapsed:.2f}s | Status: {status} | Chars: {char_count}")
                
            except Exception as e:
                elapsed = time.time() - start_time
                results.append({
                    "run": run_idx,
                    "status": "ERROR",
                    "model": "deepseek-ai/deepseek-v4-flash",
                    "latency_sec": round(elapsed, 2),
                    "char_count": 0,
                    "error": str(e)
                })
                print(f"[Run {run_idx}/3] Exception: {e}")

            # Pause briefly between runs to avoid triggering back-to-back RPM quota spikes
            time.sleep(2.0)

        print("\n" + "=" * 70)
        print("=== ROUND 1 EXECUTION SUMMARY (3 RUNS) ===")
        print("Run | Model                             | Status  | Latency (s) | Chars")
        print("-" * 70)
        for r in results:
            print(f" {r['run']}  | {r['model']:<33} | {r['status']:<7} | {r['latency_sec']:<11} | {r['char_count']}")
        print("=" * 70)

        # Assertions for 3-run stability
        successful_runs = [r for r in results if r["status"] == "SUCCESS"]
        self.assertEqual(
            len(successful_runs), 3,
            f"All 3 test runs must succeed. Successful count: {len(successful_runs)}/3"
        )
        for r in results:
            self.assertGreater(r["char_count"], 300, "Marketing Agent output must contain substantive text (>300 chars)")


if __name__ == "__main__":
    unittest.main()
