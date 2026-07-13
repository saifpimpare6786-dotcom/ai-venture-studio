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
    except Exception as e:
        print(f"FAILED: Threw unexpected error: {str(e)}")

def run_rules_node_integration_test():
    print("\n=== Running Rules Engine Node Integration Test ===")
    
    # Setup a mock state with custom assessments to force extraction
    mock_state = {
        "project_id": "00000000-0000-0000-0000-000000000000",
        "business_idea_input": "Launch automated waste recycling logistics in London, UK.",
        "specialized_outputs": {
            "strategy": "We plan a basic tier priced at GBP 150/month for micro businesses.",
            "finance": "Our pricing model lists a starter tier at £150 per month, plus £20 utility setup fees.",
            "marketing": "We will promote the starter recycling plan for £160 per month to local shops."
        }
    }
    
    print("Executing business_rules_engine_node with mock input...")
    node_result = business_rules_engine_node(mock_state)
    val_res = node_result.get("rules_validation_result", {})
    
    print("\nRules Node Execution Result:")
    print(f"Is Valid: {val_res.get('is_valid')}")
    print(f"Errors Found: {val_res.get('errors')}")
    print(f"Extracted Metrics: {val_res.get('extracted_data')}")
    
    if val_res.get("is_valid") is not True:
        print("Warning: validation failed, check details above (e.g. extraction precision or threshold triggers).")
    else:
        print("SUCCESS: Integration extraction and validation executed correctly.")

if __name__ == "__main__":
    run_pydantic_rules_unit_tests()
    run_rules_node_integration_test()
