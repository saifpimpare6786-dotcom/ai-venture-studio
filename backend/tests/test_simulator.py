import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.simulator_engine import SimulatorEngine

class TestSimulator(unittest.TestCase):
    def test_simulator_math_calculation(self):
        """Verify 36-month projections and unit economics math."""
        res = SimulatorEngine.calculate_scenario(
            starter_price=299.0,
            growth_price=799.0,
            enterprise_price=1999.0,
            cac=150.0,
            monthly_growth_rate_pct=15.0,
            monthly_churn_rate_pct=2.5,
            gross_margin_pct=80.0,
            headcount=4,
            avg_monthly_salary=4500.0,
            initial_capital=100000.0,
            months=36
        )

        summary = res["summary"]
        monthly = res["monthly_projections"]

        self.assertEqual(len(monthly), 36)
        self.assertGreater(summary["arpu"], 0)
        self.assertGreater(summary["ltv"], 0)
        self.assertGreaterEqual(summary["ltv_cac_ratio"], 3.0)
        self.assertGreater(summary["cac_payback_months"], 0)
        self.assertGreater(monthly[0]["mrr"], 0)
        self.assertGreater(monthly[-1]["mrr"], monthly[0]["mrr"]) # Growth over 36 months

    def test_scenario_matrix(self):
        """Verify Base, Bull, and Bear case scenario generation."""
        params = {
            "starter_price": 299.0,
            "growth_price": 799.0,
            "enterprise_price": 1999.0,
            "cac": 150.0,
            "monthly_growth_rate_pct": 15.0,
            "monthly_churn_rate_pct": 2.5,
            "gross_margin_pct": 80.0,
            "headcount": 4,
            "avg_monthly_salary": 4500.0,
            "initial_capital": 100000.0,
            "months": 36
        }
        scenarios = SimulatorEngine.generate_scenarios(params)

        self.assertIn("base_case", scenarios)
        self.assertIn("bull_case", scenarios)
        self.assertIn("bear_case", scenarios)
        # Bull case month 36 MRR should exceed base case
        self.assertGreater(scenarios["bull_case"]["summary"]["month_36_mrr"], scenarios["base_case"]["summary"]["month_36_mrr"])
        # Bear case month 36 MRR should be lower than base case
        self.assertLess(scenarios["bear_case"]["summary"]["month_36_mrr"], scenarios["base_case"]["summary"]["month_36_mrr"])

if __name__ == "__main__":
    unittest.main()
