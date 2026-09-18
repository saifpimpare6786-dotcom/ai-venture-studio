import unittest
import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.pipeline.rules_engine import BusinessRulesEngine
from services.simulator_engine import SimulatorEngine
from services.content_cache import ContentHashCache

class TestVentureStudio(unittest.TestCase):
    def test_rules_validation_pass(self):
        state = {
            "project_data": {"target_country": "United Kingdom", "currency": "GBP"},
            "finance_assessment": {
                "pricing_tiers": {"starter": 299.0, "growth": 799.0, "enterprise": 1999.0},
                "currency_used": "GBP"
            },
            "strategy_assessment": {
                "pricing_tiers": {"starter": 299.0, "growth": 799.0, "enterprise": 1999.0}
            },
            "marketing_assessment": {
                "pricing_tiers": {"starter": 299.0, "growth": 799.0, "enterprise": 1999.0}
            }
        }
        res = BusinessRulesEngine.validate_rules(state)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["error_count"], 0)

    def test_rules_price_mismatch(self):
        state = {
            "project_data": {"target_country": "United States", "currency": "USD"},
            "finance_assessment": {
                "pricing_tiers": {"starter": 299.0, "growth": 799.0, "enterprise": 1999.0},
                "currency_used": "USD"
            },
            "strategy_assessment": {
                "pricing_tiers": {"starter": 49.0, "growth": 799.0, "enterprise": 1999.0} # Mismatch
            },
            "marketing_assessment": {
                "pricing_tiers": {"starter": 299.0, "growth": 799.0, "enterprise": 1999.0}
            }
        }
        res = BusinessRulesEngine.validate_rules(state)
        self.assertFalse(res["is_valid"])
        self.assertTrue(any("Rule B" in err for err in res["errors"]))

    def test_simulator_math(self):
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
        self.assertEqual(len(res["monthly_projections"]), 36)
        self.assertGreater(res["summary"]["arpu"], 0)
        self.assertGreater(res["summary"]["ltv"], 0)
        self.assertGreater(res["summary"]["ltv_cac_ratio"], 3.0)

    def test_scenarios_generation(self):
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
        self.assertGreater(
            scenarios["bull_case"]["summary"]["month_36_mrr"],
            scenarios["base_case"]["summary"]["month_36_mrr"]
        )

    def test_content_hash_cache(self):
        cache = ContentHashCache()
        project = {
            "name": "MediSetu",
            "industry": "HealthTech",
            "target_country": "India",
            "currency": "INR",
            "problem_statement": "Clinics on paper",
            "solution_description": "Cloud EHR",
            "target_customers": "Solo doctors",
            "revenue_model": "SaaS"
        }
        h1 = cache.compute_hash(project, "executive_summary")
        h2 = cache.compute_hash(project, "executive_summary")
        self.assertEqual(h1, h2, "SHA-256 hash must be deterministic")

        # Test set & get
        payload = {"executive_summary": "Institutional healthtech brief"}
        cache.set(h1, "proj_123", "executive_summary", payload)
        cached = cache.get(h1)
        self.assertIsNotNone(cached)
        self.assertEqual(cached["executive_summary"], "Institutional healthtech brief")

    def test_rules_market_sizing_hierarchy(self):
        # Valid hierarchy ($SOM <= $SAM <= $TAM)
        valid_state = {
            "project_data": {"target_country": "United States", "currency": "USD"},
            "finance_assessment": {"pricing_tiers": {"starter": 299.0, "growth": 799.0, "enterprise": 1999.0}, "currency_used": "USD"},
            "strategy_assessment": {
                "pricing_tiers": {"starter": 299.0, "growth": 799.0, "enterprise": 1999.0},
                "market_mapping": {"top_down_tam": "$14.2B", "sam": "$2.8B", "som": "$280M"}
            },
            "marketing_assessment": {"pricing_tiers": {"starter": 299.0, "growth": 799.0, "enterprise": 1999.0}}
        }
        res = BusinessRulesEngine.validate_rules(valid_state)
        self.assertTrue(res["is_valid"])

        # Invalid hierarchy (SAM > TAM)
        invalid_state = {
            "project_data": {"target_country": "United States", "currency": "USD"},
            "finance_assessment": {"pricing_tiers": {"starter": 299.0, "growth": 799.0, "enterprise": 1999.0}, "currency_used": "USD"},
            "strategy_assessment": {
                "pricing_tiers": {"starter": 299.0, "growth": 799.0, "enterprise": 1999.0},
                "market_mapping": {"top_down_tam": "$2B", "sam": "$10B", "som": "$100M"}
            },
            "marketing_assessment": {"pricing_tiers": {"starter": 299.0, "growth": 799.0, "enterprise": 1999.0}}
        }
        res_invalid = BusinessRulesEngine.validate_rules(invalid_state)
        self.assertFalse(res_invalid["is_valid"])
        self.assertTrue(any("Rule F" in err for err in res_invalid["errors"]))

if __name__ == "__main__":
    unittest.main()
