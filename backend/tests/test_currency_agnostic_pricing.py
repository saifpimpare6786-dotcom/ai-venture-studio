import os
import sys
import unittest

# Add backend directory to Python sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from app.pipeline.rules_engine import (
    fallback_extract_pricing,
    business_rules_engine_node,
    DomainAssessmentsData,
)


class TestCurrencyAgnosticPricing(unittest.TestCase):
    def test_fallback_extract_pricing_inr_formatting(self):
        # 1. Rupee symbol ₹ with Indian comma grouping
        text_symbol = (
            "1. Starter Tier: ₹499/month\n"
            "2. Growth Tier: ₹1,999/month\n"
            "3. Enterprise Tier: ₹9,999/month"
        )
        tiers_symbol = fallback_extract_pricing(text_symbol)
        self.assertEqual(len(tiers_symbol), 3)
        self.assertEqual(tiers_symbol[0]["price_val"], 499.0)
        self.assertEqual(tiers_symbol[1]["price_val"], 1999.0)
        self.assertEqual(tiers_symbol[2]["price_val"], 9999.0)

        # 2. Rs. / Rs abbreviation
        text_rs = (
            "Starter: Rs. 499 per month\n"
            "Growth: Rs 1,999 / mo\n"
            "Enterprise: RS 9,999/month"
        )
        tiers_rs = fallback_extract_pricing(text_rs)
        self.assertEqual(len(tiers_rs), 3)
        self.assertEqual(tiers_rs[0]["price_val"], 499.0)
        self.assertEqual(tiers_rs[1]["price_val"], 1999.0)
        self.assertEqual(tiers_rs[2]["price_val"], 9999.0)

        # 3. INR code & rupees word
        text_inr = (
            "Starter Tier (499 INR/month)\n"
            "Growth Tier (1,999 rupees/month)\n"
            "Enterprise Tier (9,999 INR per month)"
        )
        tiers_inr = fallback_extract_pricing(text_inr)
        self.assertEqual(len(tiers_inr), 3)
        self.assertEqual(tiers_inr[0]["price_val"], 499.0)
        self.assertEqual(tiers_inr[1]["price_val"], 1999.0)
        self.assertEqual(tiers_inr[2]["price_val"], 9999.0)

    def test_inr_venture_passes_bre(self):
        mock_state_inr = {
            "project_id": "11111111-1111-1111-1111-111111111111",
            "business_idea_input": "B2B SaaS logistics startup in Bengaluru, India.",
            "specialized_outputs": {
                "strategy": "We offer Starter: ₹499/month, Growth: ₹1,999/month, Enterprise: ₹9,999/month.",
                "finance": "Authoritative pricing tiers for India: Starter: ₹499/month, Growth: ₹1,999/month, Enterprise: ₹9,999/month.",
                "marketing": "Target tier messaging: Starter: ₹499/month, Growth: ₹1,999/month, Enterprise: ₹9,999/month."
            }
        }
        res = business_rules_engine_node(mock_state_inr)
        rules_res = res.get("rules_validation_result", {})
        self.assertTrue(rules_res.get("is_valid"), f"INR Validation failed: {rules_res.get('errors')}")
        extracted = rules_res.get("extracted_data", {})
        self.assertEqual(extracted.get("target_country"), "India")
        self.assertEqual(extracted.get("finance_currency"), "INR")

    def test_ecosphere_gbp_venture_still_works_unchanged(self):
        mock_state_gbp = {
            "project_id": "22222222-2222-2222-2222-222222222222",
            "business_idea_input": "EcoSphere: Carbon tracking dashboard for UK SMEs in London.",
            "specialized_outputs": {
                "strategy": "Starter: £299/month, Growth: £499/month, Enterprise: £1,499/month.",
                "finance": "Authoritative UK pricing: Starter: £299/month, Growth: £499/month, Enterprise: £1,499/month.",
                "marketing": "Tier messaging: Starter: £299/month, Growth: £499/month, Enterprise: £1,499/month."
            }
        }
        res = business_rules_engine_node(mock_state_gbp)
        rules_res = res.get("rules_validation_result", {})
        self.assertTrue(rules_res.get("is_valid"), f"GBP Validation failed: {rules_res.get('errors')}")
        extracted = rules_res.get("extracted_data", {})
        self.assertEqual(extracted.get("target_country"), "UK")
        self.assertEqual(extracted.get("finance_currency"), "GBP")


if __name__ == "__main__":
    unittest.main()
