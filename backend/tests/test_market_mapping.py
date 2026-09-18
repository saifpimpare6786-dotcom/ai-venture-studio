import unittest
import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.pipeline.rules_engine import BusinessRulesEngine
from app.pipeline.scoring_engine import ScoringEngine
from app.schemas.report import CompetitorAnalysisSchema, BusinessPlanSchema

class TestMarketMapping(unittest.TestCase):
    def test_market_sizing_hierarchy_pass(self):
        """Verify that a valid market sizing hierarchy ($SOM <= $SAM <= $TAM) passes Rule F."""
        state = {
            "project_data": {"target_country": "United States", "currency": "USD"},
            "finance_assessment": {
                "pricing_tiers": {"starter": 299.0, "growth": 799.0, "enterprise": 1999.0},
                "currency_used": "USD",
                "ltv_estimate": 12800.0,
                "cac_estimate": 150.0
            },
            "strategy_assessment": {
                "pricing_tiers": {"starter": 299.0, "growth": 799.0, "enterprise": 1999.0},
                "tam_sam_som": {"tam": "$14.2B Global", "sam": "$2.8B Regional", "som": "$280M Initial Target"},
                "market_mapping": {
                    "top_down_tam": "$14.2B Global",
                    "bottom_up_tam": "$11.8B",
                    "sam": "$2.8B Regional",
                    "som": "$280M Target",
                    "whitespace_quadrant": "High Specialization + Turnkey"
                }
            },
            "marketing_assessment": {
                "pricing_tiers": {"starter": 299.0, "growth": 799.0, "enterprise": 1999.0}
            }
        }
        res = BusinessRulesEngine.validate_rules(state)
        self.assertTrue(res["is_valid"])
        self.assertFalse(any("Rule F" in err for err in res["errors"]))

    def test_market_sizing_hierarchy_sam_exceeds_tam(self):
        """Verify that SAM exceeding TAM triggers Rule F validation error."""
        state = {
            "project_data": {"target_country": "United States", "currency": "USD"},
            "finance_assessment": {
                "pricing_tiers": {"starter": 299.0, "growth": 799.0, "enterprise": 1999.0},
                "currency_used": "USD"
            },
            "strategy_assessment": {
                "pricing_tiers": {"starter": 299.0, "growth": 799.0, "enterprise": 1999.0},
                "tam_sam_som": {"tam": "$2B", "sam": "$10B", "som": "$100M"}, # SAM > TAM
                "market_mapping": {
                    "top_down_tam": "$2B",
                    "sam": "$10B",
                    "som": "$100M"
                }
            },
            "marketing_assessment": {
                "pricing_tiers": {"starter": 299.0, "growth": 799.0, "enterprise": 1999.0}
            }
        }
        res = BusinessRulesEngine.validate_rules(state)
        self.assertFalse(res["is_valid"])
        self.assertTrue(any("Rule F" in err and "SAM" in err and "TAM" in err for err in res["errors"]))

    def test_market_sizing_hierarchy_som_exceeds_sam(self):
        """Verify that SOM exceeding SAM triggers Rule F validation error."""
        state = {
            "project_data": {"target_country": "United States", "currency": "USD"},
            "finance_assessment": {
                "pricing_tiers": {"starter": 299.0, "growth": 799.0, "enterprise": 1999.0},
                "currency_used": "USD"
            },
            "strategy_assessment": {
                "pricing_tiers": {"starter": 299.0, "growth": 799.0, "enterprise": 1999.0},
                "tam_sam_som": {"tam": "$20B", "sam": "$1B", "som": "$5B"}, # SOM > SAM
                "market_mapping": {
                    "top_down_tam": "$20B",
                    "sam": "$1B",
                    "som": "$5B"
                }
            },
            "marketing_assessment": {
                "pricing_tiers": {"starter": 299.0, "growth": 799.0, "enterprise": 1999.0}
            }
        }
        res = BusinessRulesEngine.validate_rules(state)
        self.assertFalse(res["is_valid"])
        self.assertTrue(any("Rule F" in err and "SOM" in err and "SAM" in err for err in res["errors"]))

    def test_scoring_with_market_mapping(self):
        """Verify that ScoringEngine factors market mapping validation into Market Fit."""
        state = {
            "rules_validation": {"is_valid": True, "errors": []},
            "council_debate": {"alignment_score": 90.0},
            "reviewer_assessment": {"coherence_score": 90.0},
            "finance_assessment": {
                "ltv_estimate": 15000.0,
                "cac_estimate": 150.0
            },
            "strategy_assessment": {
                "market_mapping": {
                    "whitespace_quadrant": "Turnkey Compliance"
                }
            }
        }
        scores = ScoringEngine.calculate_scores(state)
        self.assertTrue(scores["market_mapping_validated"])
        self.assertGreaterEqual(scores["market_fit_score"], 90.0)
        self.assertGreater(scores["overall_score"], 80.0)

    def test_competitor_analysis_schema_with_whitespace(self):
        """Verify CompetitorAnalysisSchema supports whitespace opportunity and 2x2 positioning."""
        data = {
            "direct_competitors": ["Incumbent X", "Player Y"],
            "indirect_competitors": ["Manual Spreadsheets"],
            "competitive_advantages": ["Real-time synchronization", "Domain-specific AI"],
            "market_positioning": "Category leader for automated compliance",
            "whitespace_opportunity": "Turnkey compliance for mid-market clinics",
            "positioning_axes": {
                "x_axis": "Deployment Speed",
                "y_axis": "Regulatory Rigor"
            },
            "market_map_quadrants": [
                {"name": "Incumbent X", "quadrant": "Slow Deployment / High Rigor"}
            ]
        }
        schema = CompetitorAnalysisSchema(**data)
        self.assertEqual(schema.whitespace_opportunity, "Turnkey compliance for mid-market clinics")
        self.assertIsNotNone(schema.positioning_axes)
        assert schema.positioning_axes is not None
        self.assertEqual(schema.positioning_axes["x_axis"], "Deployment Speed")

if __name__ == "__main__":
    unittest.main()
