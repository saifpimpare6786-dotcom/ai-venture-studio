import os
import sys
from pydantic import ValidationError

# Add backend directory to Python sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from app.pipeline.rules_engine import DomainAssessmentsData, business_rules_engine_node

def run_pydantic_rules_unit_tests():
    print("=== Running Business Rules Engine Pydantic Unit Tests ===")

    # Test Case 1: Ideal consistent pricing and matching currency
    print("\nTest Case 1: Consistent pricing ($99, $120, $110 basic tier) & USD currency for US country")
    valid_data = {
        "target_country": "United States of America",
        "finance_currency": "USD",
        "strategy_pricing": [{"tier_name": "Basic Plan", "price_val": 99.0}],
        "finance_pricing": [{"tier_name": "basic", "price_val": 120.0}],
        "marketing_pricing": [{"tier_name": "Starter / Basic", "price_val": 110.0}]
    }
    try:
        DomainAssessmentsData.model_validate(valid_data)
        print("SUCCESS: Valid data passed Pydantic rules engine correctly.")
    except Exception as e:
        print(f"FAILED: Valid data threw exception: {str(e)}")

    # Test Case 2: Pricing mismatch (>2x)
    print("\nTest Case 2: Inconsistent pricing ($99 Strategy vs. $250 Finance basic tier)")
    mismatch_pricing = {
        "target_country": "United States",
        "finance_currency": "USD",
        "strategy_pricing": [{"tier_name": "Basic Plan", "price_val": 99.0}],
        "finance_pricing": [{"tier_name": "basic", "price_val": 250.0}],
        "marketing_pricing": [{"tier_name": "Starter", "price_val": 110.0}]
    }
    try:
        DomainAssessmentsData.model_validate(mismatch_pricing)
        print("FAILED: Inconsistent pricing passed validations.")
    except ValidationError as val_err:
        errors = [err.get("msg") for err in val_err.errors()]
        print(f"SUCCESS: Mismatch pricing failed validation as expected. Errors: {errors}")
    except Exception as e:
        print(f"FAILED: Threw unexpected error: {str(e)}")

    # Test Case 3: Currency mismatch
    print("\nTest Case 3: Currency mismatch (UK country, but USD '$' currency used)")
    mismatch_currency = {
        "target_country": "United Kingdom (UK)",
        "finance_currency": "$",
        "strategy_pricing": [{"tier_name": "Basic", "price_val": 100.0}],
        "finance_pricing": [{"tier_name": "basic", "price_val": 120.0}],
        "marketing_pricing": [{"tier_name": "basic", "price_val": 110.0}]
    }
    try:
        DomainAssessmentsData.model_validate(mismatch_currency)
        print("FAILED: Currency mismatch passed validations.")
    except ValidationError as val_err:
        errors = [err.get("msg") for err in val_err.errors()]
        print(f"SUCCESS: Currency mismatch failed validation as expected. Errors: {errors}")
    # Test Case 4: INR currency for India venture
    print("\nTest Case 4: Consistent INR pricing (Rs. 499, Rs. 1,999, Rs. 9,999) & INR currency for India country")
    inr_data = {
        "target_country": "India",
        "finance_currency": "INR",
        "strategy_pricing": [{"tier_name": "Starter", "price_val": 499.0}, {"tier_name": "Growth", "price_val": 1999.0}, {"tier_name": "Enterprise", "price_val": 9999.0}],
        "finance_pricing": [{"tier_name": "Starter", "price_val": 499.0}, {"tier_name": "Growth", "price_val": 1999.0}, {"tier_name": "Enterprise", "price_val": 9999.0}],
        "marketing_pricing": [{"tier_name": "Starter", "price_val": 499.0}, {"tier_name": "Growth", "price_val": 1999.0}, {"tier_name": "Enterprise", "price_val": 9999.0}]
    }
    try:
        DomainAssessmentsData.model_validate(inr_data)
        print("SUCCESS: INR data passed Pydantic rules engine correctly.")
    except Exception as e:
        print(f"FAILED: INR data threw exception: {str(e)}")

def run_rules_node_integration_test():
    print("\n=== Running Rules Engine Node Integration Test ===")
    
    # Test Case A: UK GBP
    mock_state_uk = {
        "project_id": "00000000-0000-0000-0000-000000000000",
        "business_idea_input": "Launch automated waste recycling logistics in London, UK.",
        "specialized_outputs": {
            "strategy": "We plan a basic tier priced at GBP 150/month for micro businesses.",
            "finance": "Our pricing model lists a starter tier at £150 per month, plus £20 utility setup fees.",
            "marketing": "We will promote the starter recycling plan for £160 per month to local shops."
        }
    }
    
    print("Executing business_rules_engine_node with UK mock input...")
    node_result_uk = business_rules_engine_node(mock_state_uk)
    val_res_uk = node_result_uk.get("rules_validation_result", {})
    print(f"UK Integration Is Valid: {val_res_uk.get('is_valid')}")
    assert val_res_uk.get("is_valid") is True, f"UK validation failed: {val_res_uk.get('errors')}"

    # Test Case B: India INR
    mock_state_inr = {
        "project_id": "00000000-0000-0000-0000-000000000001",
        "business_idea_input": "B2B SaaS logistics platform in Bangalore, India.",
        "specialized_outputs": {
            "strategy": "Starter: ₹499/month, Growth: ₹1,999/month, Enterprise: starting at ₹9,999/month.",
            "finance": "Starter: ₹499/month, Growth: ₹1,999/month, Enterprise: from ₹9,999/month.",
            "marketing": "Starter: ₹499/month, Growth: ₹1,999/month, Enterprise: from ₹9,999/month."
        }
    }

    print("\nExecuting business_rules_engine_node with India INR mock input...")
    node_result_inr = business_rules_engine_node(mock_state_inr)
    val_res_inr = node_result_inr.get("rules_validation_result", {})
    print(f"India INR Integration Is Valid: {val_res_inr.get('is_valid')}")
    print(f"India INR Extracted Metrics: {val_res_inr.get('extracted_data')}")
    assert val_res_inr.get("is_valid") is True, f"India INR validation failed: {val_res_inr.get('errors')}"
    print("SUCCESS: Both UK GBP and India INR integration extractions and validations executed correctly.")

if __name__ == "__main__":
    run_pydantic_rules_unit_tests()
    run_rules_node_integration_test()

