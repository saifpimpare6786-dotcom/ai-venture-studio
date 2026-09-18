import unittest
import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.pipeline.rules_engine import BusinessRulesEngine

class TestRules(unittest.TestCase):
    def test_deterministic_rules_pass(self):
        """Verify that consistent pricing across agents passes validation."""
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

    def test_deterministic_rules_price_mismatch(self):
        """Verify that contradictory pricing between Strategy and Finance triggers Rule B failure."""
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

    def test_deterministic_rules_currency_mismatch(self):
        """Verify that wrong currency for country triggers Rule D failure."""
        state = {
            "project_data": {"target_country": "United Kingdom", "currency": "GBP"},
            "finance_assessment": {
                "pricing_tiers": {"starter": 299.0, "growth": 799.0, "enterprise": 1999.0},
                "currency_used": "USD" # Should be GBP
            },
            "strategy_assessment": {"pricing_tiers": {"starter": 299.0, "growth": 799.0, "enterprise": 1999.0}},
            "marketing_assessment": {"pricing_tiers": {"starter": 299.0, "growth": 799.0, "enterprise": 1999.0}}
        }
        res = BusinessRulesEngine.validate_rules(state)
        self.assertFalse(res["is_valid"])
        self.assertTrue(any("Rule D" in err for err in res["errors"]))

if __name__ == "__main__":
    unittest.main()
