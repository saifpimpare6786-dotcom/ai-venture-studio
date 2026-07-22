import os
import json
from pydantic import BaseModel, Field, model_validator, ValidationError
from typing import Dict, Any, List, Optional
from app.database.supabase import get_supabase_client
from services.llm import call_llm
from app.pipeline.state import AgentState

EXTRACTION_SYSTEM_PROMPT = """
You are a precise data extraction agent. Your role is to read a business idea and domain assessments (Strategy, Finance, Marketing), and extract structured metrics into JSON format.

Target JSON Format:
{
  "target_country": "The target country or region stated in the business idea (e.g. 'UK', 'US', 'Europe', 'India'). If not specified, output 'Global'.",
  "finance_currency": "The currency code or symbol used in the Finance assessment (e.g. 'USD', '$', 'GBP', '£', 'EUR', '€'). If not specified, output 'USD'.",
  "strategy_pricing": [
    {"tier_name": "Tier name (e.g. Starter, Growth, Enterprise)", "price_val": 123.45}
  ],
  "finance_pricing": [
    {"tier_name": "Tier name", "price_val": 123.45}
  ],
  "marketing_pricing": [
    {"tier_name": "Tier name", "price_val": 123.45}
  ]
}

Rules for price_val:
- Use the exact numeric dollar/pound/euro value (as a float) if the assessment states a specific amount.
- Use -1.0 if the tier is explicitly described as "custom pricing", "contact us", "quote on request", or similar non-numeric pricing that is INTENTIONAL for that tier (e.g. an Enterprise tier that says "contact us for pricing").
- Use null ONLY if the tier name is mentioned but no price or pricing intent can be determined from the text (i.e. the data is simply absent).
- If a department's assessment mentions NO pricing tiers at all, output an empty list [] for that department.

Return ONLY the valid JSON block wrapped in a markdown code fence. Do not include any introductory or concluding text.
"""

# Sentinel value for intentional "custom / contact-us" pricing
_CUSTOM_PRICING_SENTINEL = -1.0


class BusinessAssessmentPricing(BaseModel):
    tier_name: str
    # price_val semantics:
    #   > 0       → concrete numeric price (included in mismatch check)
    #   -1.0      → intentional custom/contact-us pricing (skip mismatch)
    #   None      → price truly absent / could not be determined
    price_val: Optional[float] = None

    @property
    def is_custom(self) -> bool:
        return self.price_val is not None and self.price_val == _CUSTOM_PRICING_SENTINEL

    @property
    def is_missing(self) -> bool:
        return self.price_val is None

    @property
    def is_numeric(self) -> bool:
        return self.price_val is not None and self.price_val > 0


class DomainAssessmentsData(BaseModel):
    target_country: str = Field(default="Global")
    finance_currency: str = Field(default="USD")
    strategy_pricing: List[BusinessAssessmentPricing] = Field(default=[])
    finance_pricing: List[BusinessAssessmentPricing] = Field(default=[])
    marketing_pricing: List[BusinessAssessmentPricing] = Field(default=[])

    @model_validator(mode="after")
    def validate_pricing_consistency(self) -> 'DomainAssessmentsData':
        errors = []

        # ── Rule A: Empty pricing list = missing data, not a pass ──────────
        source_map = {
            "strategy": self.strategy_pricing,
            "finance": self.finance_pricing,
            "marketing": self.marketing_pricing,
        }
        empty_sources = [name for name, lst in source_map.items() if len(lst) == 0]
        if empty_sources:
            errors.append(
                f"Missing pricing data: {', '.join(empty_sources)} returned no pricing "
                f"tiers — cannot perform cross-source mismatch validation."
            )
            # Raise immediately; no point running per-tier checks with incomplete data
            raise ValueError("; ".join(errors))

        # ── Rule B: Per-tier cross-source mismatch check ────────────────────
        def normalise_tier(name: str) -> str:
            name = name.lower().strip()
            if "start" in name or "basic" in name:
                return "basic"
            if "grow" in name or "pro" in name or "mid" in name:
                return "growth"
            if "enter" in name or "premium" in name or "large" in name:
                return "enterprise"
            return name

        all_tiers: Dict[str, Dict[str, BusinessAssessmentPricing]] = {}
        for item in self.strategy_pricing:
            all_tiers.setdefault(normalise_tier(item.tier_name), {})["strategy"] = item
        for item in self.finance_pricing:
            all_tiers.setdefault(normalise_tier(item.tier_name), {})["finance"] = item
        for item in self.marketing_pricing:
            all_tiers.setdefault(normalise_tier(item.tier_name), {})["marketing"] = item

        for normalized_tier, source_items in all_tiers.items():
            # Classify each source's contribution to this tier
            numeric_sources  = [src for src, item in source_items.items() if item.is_numeric]
            custom_sources   = [src for src, item in source_items.items() if item.is_custom]
            missing_sources  = [src for src, item in source_items.items() if item.is_missing]

            # ── Rule B1: null price alongside any concrete numeric ───────────
            # A None alongside a real number means extraction failure or agent gap.
            if missing_sources and numeric_sources:
                errors.append(
                    f"Tier '{normalized_tier}': null price_val in "
                    f"{', '.join(missing_sources)} while "
                    f"{', '.join(numeric_sources)} provide numeric prices — "
                    f"possible upstream agent failure or extraction gap."
                )

            # ── Rule B3: mixed numeric + custom-sentinel = inconsistency ─────
            # If at least one source gave a concrete number AND at least one gave
            # the non-numeric sentinel (-1.0), the sources disagree on whether
            # this tier is priced or unpriced — that is a real validation error.
            # The sentinel-vs-sentinel case (all sources agree tier is custom) is
            # the ONLY case where we skip the numeric mismatch check.
            if numeric_sources and custom_sources:
                breakdown = ", ".join(
                    [
                        f"{src}: {source_items[src].price_val}"
                        for src in sorted(source_items)
                    ]
                )
                errors.append(
                    f"Tier '{normalized_tier}' data inconsistency: "
                    f"{', '.join(numeric_sources)} gave concrete pricing while "
                    f"{', '.join(custom_sources)} declared it non-numeric/custom — "
                    f"agents must agree on whether this tier is priced or unpriced "
                    f"({breakdown})."
                )

            # ── Rule B2: numeric-only spread check (>2x) ────────────────────
            # Only runs when B3 didn't fire (i.e. all active sources are numeric).
            # Custom-sentinel sources are excluded here because B3 already caught
            # any numeric+custom inconsistency above.
            if not custom_sources:
                numeric_prices = {
                    src: item.price_val
                    for src, item in source_items.items()
                    if item.is_numeric
                }
                if len(numeric_prices) >= 2:
                    min_price = min(numeric_prices.values())
                    max_price = max(numeric_prices.values())
                    if max_price > 2.0 * min_price:
                        breakdown = ", ".join(
                            [f"{k}: {v}" for k, v in numeric_prices.items()]
                        )
                        errors.append(
                            f"Pricing mismatch for tier '{normalized_tier}': prices differ "
                            f"by more than 2x ({breakdown})"
                        )

        if errors:
            raise ValueError("; ".join(errors))
        return self

    @model_validator(mode="after")
    def validate_currency_matches_country(self) -> 'DomainAssessmentsData':
        country = self.target_country.lower().strip()
        currency = self.finance_currency.upper().strip()
        
        country_currency_map = {
            "uk": ["GBP", "£"],
            "united kingdom": ["GBP", "£"],
            "great britain": ["GBP", "£"],
            "london": ["GBP", "£"],
            "us": ["USD", "$"],
            "united states": ["USD", "$"],
            "america": ["USD", "$"],
            "europe": ["EUR", "€"],
            "eu": ["EUR", "€"],
            "germany": ["EUR", "€"],
            "france": ["EUR", "€"],
            "india": ["INR", "₹"],
            "global": ["USD", "$", "EUR", "€", "GBP", "£"]
        }
        
        matched_keys = [k for k in country_currency_map.keys() if k in country]
        if matched_keys:
            best_key = max(matched_keys, key=len)
            allowed = country_currency_map[best_key]
            
            matches = False
            for symbol in allowed:
                if symbol in currency or currency in symbol:
                    matches = True
                    break
            
            if not matches:
                raise ValueError(
                    f"Currency symbol '{self.finance_currency}' in Finance output does not match "
                    f"stated target country/region '{self.target_country}' (expected currency options: {allowed})"
                )
        return self

def extract_json_block(text: str) -> str:
    """Extracts raw JSON content from markdown code fences if present."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def business_rules_engine_node(state: AgentState) -> Dict[str, Any]:
    """
    Business Rules Engine Node.
    Consumes assessment details from Strategy, Finance, and Marketing.
    Applies Pydantic validations to enforce pricing consistency and currency verification.
    Records errors if any check fails, and saves output to rules_validation_result.

    Hard-exits immediately (is_valid=False) if the pipeline was already aborted upstream.
    """
    project_id = state.get("project_id")
    idea = state.get("business_idea_input", "")
    outputs = state.get("specialized_outputs", {})

    print(f"--- [Business Rules Engine Node] Starting execution for Project {project_id} ---")

    # ── Early-exit if an upstream gate already aborted the pipeline ─────────
    if state.get("pipeline_aborted"):
        abort_reason = state.get("abort_reason", "Upstream pipeline failure.")
        print(f"[Business Rules Engine] Skipping validation — pipeline already aborted: {abort_reason}")
        rules_result = {
            "is_valid": False,
            "errors": [f"Validation skipped — pipeline aborted upstream: {abort_reason}"],
            "extracted_data": {}
        }
        return {"rules_validation_result": rules_result}

    strategy_text = outputs.get("strategy", "")
    finance_text = outputs.get("finance", "")
    marketing_text = outputs.get("marketing", "")

    user_prompt = (
        f"BUSINESS IDEA:\n{idea}\n\n"
        f"STRATEGY ASSESSMENT:\n{strategy_text}\n\n"
        f"FINANCE ASSESSMENT:\n{finance_text}\n\n"
        f"MARKETING PLAN:\n{marketing_text}"
    )
    
    # 1. Structured data extraction via LLM
    extracted_dict = {}
    try:
        raw_json_str = call_llm(
            prompt=user_prompt,
            system_prompt=EXTRACTION_SYSTEM_PROMPT,
            preferred_provider="nvidia",
            project_id=project_id,
            agent_name="Business Rules Engine"
        )
        if isinstance(raw_json_str, dict) and raw_json_str.get("status") == "failed":
            raise ValueError(raw_json_str["error"])
        cleaned_json_str = extract_json_block(raw_json_str)
        extracted_dict = json.loads(cleaned_json_str)
    except Exception as parse_err:
        print(f"Rules engine extraction parser error: {str(parse_err)}")
        
    is_valid = True
    errors = []
    
    # 2. Pydantic validation enforcement
    if extracted_dict:
        try:
            DomainAssessmentsData.model_validate(extracted_dict)
            print("Business Rules Engine: Pydantic validations passed successfully!")
        except ValidationError as val_err:
            is_valid = False
            for err in val_err.errors():
                msg = err.get("msg", "Validation rule failure")
                if "Value error, " in msg:
                    msg = msg.replace("Value error, ", "")
                errors.append(msg)
            print(f"Business Rules Engine: Validation failures found: {errors}")
        except Exception as general_err:
            is_valid = False
            errors.append(str(general_err))
            print(f"Business Rules Engine error: {str(general_err)}")
    else:
        is_valid = False
        errors.append("Could not parse or extract structured data from text assessments.")
        
    rules_result = {
        "is_valid": is_valid,
        "errors": errors,
        "extracted_data": extracted_dict
    }
    
    # 3. Log results to agent_logs database table
    try:
        supabase = get_supabase_client()
        supabase.table("agent_logs").insert({
            "project_id": project_id,
            "agent_name": "Business Rules Engine",
            "status": "completed" if is_valid else "warning",
            "input_data": {
                "pricing_extracted": extracted_dict
            },
            "output_data": {
                "validation_result": rules_result
            }
        }).execute()
        print("Logged Business Rules Engine execution to Supabase.")
    except Exception as db_err:
        print(f"Supabase Agent Log Sync Warning for Business Rules Engine (continuing): {str(db_err)}")
        
    print(f"--- [Business Rules Engine Node] Finished execution ---")
    return {
        "rules_validation_result": rules_result
    }
