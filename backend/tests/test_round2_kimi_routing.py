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

from app.pipeline.orchestrator_agent import orchestrator_agent_node
from app.pipeline.specialized_agents import strategy_agent_node
from services.llm import NIM_MODEL_ROUTING, reset_gemini_circuit_breaker


class TestRound2KimiRouting(unittest.TestCase):
    """
    Round 2 Verification: Confirms Strategy Agent and Orchestrator Agent routing
    to moonshotai/kimi-k2.6 across 3 consecutive runs.
    """

    def setUp(self):
        reset_gemini_circuit_breaker()

    def test_round2_kimi_routing_3_runs(self):
        print("\n" + "=" * 75)
        print("=== ROUND 2: STRATEGY & ORCHESTRATOR ROUTING VERIFICATION (3 RUNS) ===")
        print(f"Strategy Agent Model    : {NIM_MODEL_ROUTING.get('Strategy Agent')}")
        print(f"Orchestrator Agent Model: {NIM_MODEL_ROUTING.get('Orchestrator Agent')}")
        print("=" * 75)

        self.assertEqual(NIM_MODEL_ROUTING.get("Strategy Agent"), "moonshotai/kimi-k2.6")
        self.assertEqual(NIM_MODEL_ROUTING.get("Orchestrator Agent"), "moonshotai/kimi-k2.6")
        self.assertEqual(NIM_MODEL_ROUTING.get("Marketing Agent"), "deepseek-ai/deepseek-v4-flash")

        mock_state = {
            "project_id": str(uuid.uuid4()),
            "business_idea_input": (
                "EcoSphere is an automated carbon tracking dashboard for small and medium enterprises. "
                "It connects directly to utility provider API meters, reads transport fuel logs, "
                "and automatically calculates carbon emissions reporting metrics."
            ),
            "plan": (
                "1. Core Venture Summary: EcoSphere carbon compliance platform for SMEs.\n"
                "2. Sector Classification: Climate Tech / SaaS.\n"
                "3. Objectives: Formulate B2B pricing model and evaluate Scope 1-3 audit compliance."
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
            print(f"\n--- [Run {run_idx}/3] Executing Orchestrator Agent Node ---")
            t0 = time.time()
            try:
                orch_res = orchestrator_agent_node(mock_state)
                orch_time = round(time.time() - t0, 2)
                directives = orch_res.get("directives", "")
                orch_status = "SUCCESS" if directives and not directives.startswith("Execution failed:") else "FAILED"
                orch_chars = len(directives) if isinstance(directives, str) else 0
                results.append({
                    "run": run_idx,
                    "agent": "Orchestrator Agent",
                    "model": "moonshotai/kimi-k2.6",
                    "status": orch_status,
                    "latency_sec": orch_time,
                    "char_count": orch_chars
                })
                print(f"[Run {run_idx}/3] Orchestrator: {orch_status} in {orch_time}s | Chars: {orch_chars}")
            except Exception as e:
                results.append({
                    "run": run_idx,
                    "agent": "Orchestrator Agent",
                    "model": "moonshotai/kimi-k2.6",
                    "status": "ERROR",
                    "latency_sec": round(time.time() - t0, 2),
                    "char_count": 0
                })
                print(f"[Run {run_idx}/3] Orchestrator Exception: {e}")

            time.sleep(1.5)

            print(f"--- [Run {run_idx}/3] Executing Strategy Agent Node ---")
            t0 = time.time()
            try:
                strat_res = strategy_agent_node(mock_state)
                strat_time = round(time.time() - t0, 2)
                strat_out = strat_res.get("specialized_outputs", {}).get("strategy", "")
                strat_status = "SUCCESS" if strat_out and strat_out != "__FAILED__" else "FAILED"
                strat_chars = len(strat_out) if isinstance(strat_out, str) else 0
                results.append({
                    "run": run_idx,
                    "agent": "Strategy Agent",
                    "model": "moonshotai/kimi-k2.6",
                    "status": strat_status,
                    "latency_sec": strat_time,
                    "char_count": strat_chars
                })
                print(f"[Run {run_idx}/3] Strategy: {strat_status} in {strat_time}s | Chars: {strat_chars}")
            except Exception as e:
                results.append({
                    "run": run_idx,
                    "agent": "Strategy Agent",
                    "model": "moonshotai/kimi-k2.6",
                    "status": "ERROR",
                    "latency_sec": round(time.time() - t0, 2),
                    "char_count": 0
                })
                print(f"[Run {run_idx}/3] Strategy Exception: {e}")

            time.sleep(2.0)

        print("\n" + "=" * 80)
        print("=== ROUND 2 EXECUTION SUMMARY (3 RUNS) ===")
        print("Run | Agent              | Model                | Status  | Latency (s) | Chars")
        print("-" * 80)
        for r in results:
            print(f" {r['run']}  | {r['agent']:<18} | {r['model']:<20} | {r['status']:<7} | {r['latency_sec']:<11} | {r['char_count']}")
        print("=" * 80)

        # Assertions
        successful_runs = [r for r in results if r["status"] == "SUCCESS"]
        self.assertEqual(
            len(successful_runs), 6,
            f"All 6 executions (3 Orchestrator + 3 Strategy) must succeed. Successful count: {len(successful_runs)}/6"
        )


if __name__ == "__main__":
    unittest.main()
