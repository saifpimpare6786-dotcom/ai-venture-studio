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
  "target_country": "The target country or region stated in the business idea (e.g. 'UK', 'US', 'Europe', 'India'). Read the BUSINESS IDEA carefully: if it mentions 'UK', 'United Kingdom', 'London', output 'UK'. If 'US' or 'United States', output 'US'. If 'India', 'Indian', 'Bangalore', 'Mumbai', 'Delhi', output 'India'. If not specified, output 'Global'.",
  "finance_currency": "The currency code or symbol used in the Finance assessment (e.g. 'GBP', '£', 'USD', '$', 'EUR', '€', 'INR', '₹', 'Rs.'). If not specified, output 'USD'.",
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

Rules for tier_name:
- tier_name MUST ALWAYS be a non-empty, non-null string describing the pricing tier (e.g. 'Starter', 'Growth', 'Enterprise'). NEVER return null or empty string for tier_name.

Rules for price_val:
- MUST ALWAYS extract the MONTHLY recurring price figure for every tier across all three assessments (Strategy, Finance, Marketing).
- If an assessment states both monthly and annual prices (e.g. '₹499/month or ₹4,999/year', '$49/mo or $490/year', '£299/mo or £2,990/year'), ALWAYS extract the MONTHLY figure (499.0, 49.0, 299.0). NEVER extract annual figures, total contract values, or one-time setup fees as price_val.
- Use the exact numeric price value (as a float) regardless of currency symbol (£, $, €, ₹, INR, Rs.). Examples: 'from $500/month' → 500.0, 'Enterprise: starting at £1000' → 1000.0, 'Starter: ₹499/month' → 499.0, 'Growth: ₹1,999/mo' → 1999.0, 'Rs. 9,999' → 9999.0. Always strip commas from formatted numbers like '1,999' or '9,999' or '1,00,000' and extract the pure float figure matching the monthly rate.
- Use -1.0 ONLY if the tier is explicitly described WITHOUT ANY numeric figures (e.g., 'contact us for pricing', 'custom quote on request' where no numeric figure exists).
- Use null ONLY if the tier name is mentioned but no price or pricing intent can be determined from the text (i.e. the data is simply absent).

Return ONLY the valid JSON block wrapped in a markdown code fence. Do not include any introductory or concluding text.
"""

# Sentinel value for intentional "custom / contact-us" pricing
_CUSTOM_PRICING_SENTINEL = -1.0


class BusinessAssessmentPricing(BaseModel):
    tier_name: str = Field(default="General Tier")
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

        # ── Rule A: ALL THREE sources must have pricing data ────────────────────
        source_map = {
            "strategy":  self.strategy_pricing,
            "finance":   self.finance_pricing,
            "marketing": self.marketing_pricing,
        }
        empty_sources = [name for name, lst in source_map.items() if len(lst) == 0]
        if empty_sources:
            errors.append(
                f"Missing pricing data: {', '.join(empty_sources)} returned no pricing "
                f"tiers — cannot perform cross-source mismatch validation."
            )
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
            numeric_sources  = [src for src, item in source_items.items() if item.is_numeric]
            custom_sources   = [src for src, item in source_items.items() if item.is_custom]
            missing_sources  = [src for src, item in source_items.items() if item.is_missing]

            if missing_sources and numeric_sources:
                errors.append(
                    f"Tier '{normalized_tier}': null price_val in "
                    f"{', '.join(missing_sources)} while "
                    f"{', '.join(numeric_sources)} provide numeric prices — "
                    f"possible upstream agent failure or extraction gap."
                )

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

            if not custom_sources:
                numeric_prices = {
                    src: item.price_val
                    for src, item in source_items.items()
                    if item.is_numeric
                }
                if len(numeric_prices) >= 2:
                    min_price = min(numeric_prices.values())
                    max_price = max(numeric_prices.values())

                    # Check if one source extracted annual pricing (~10x to 12x of monthly)
                    normalized_prices = {}
                    for src, p in numeric_prices.items():
                        if p > 0 and min_price > 0 and (p / min_price >= 8.5) and (p / min_price <= 13.5):
                            # Normalize annual price to monthly rate for fair spread check
                            normalized_p = round(p / 10.0) if abs((p / 10.0) - min_price) < abs((p / 12.0) - min_price) else round(p / 12.0)
                            normalized_prices[src] = float(normalized_p)
                        else:
                            normalized_prices[src] = p
                    
                    norm_min = min(normalized_prices.values())
                    norm_max = max(normalized_prices.values())

                    if norm_max > 2.0 * norm_min:
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
            "india": ["INR", "₹", "RS", "RS.", "RUPEES", "RUPEE"],
            "global": ["USD", "$", "EUR", "€", "GBP", "£", "INR", "₹", "RS", "RS.", "RUPEES", "RUPEE"]
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

def fallback_extract_pricing(text: str) -> List[Dict[str, Any]]:
    """Deterministic fallback pricing tier extractor for text assessments across any currency (₹, INR, Rs., rupees, £, GBP, $, USD, €, EUR)."""
    import re
    if not text or text == "__FAILED__":
        return []
    
    results = []
    curr_pattern = r'(?:[₹$£€]|INR|GBP|USD|EUR|Rs\.?|RS\.?|Rupees?|rupees?)'
    num_pattern = r'(?<![0-9])([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]+)?)'

    # 1. First pass: look specifically for monthly pricing patterns (prefix currency)
    monthly_pattern = re.compile(
        rf'(?:([A-Za-z0-9\s\-\/\&\(\)]{{2,30}}))?\s*[:\-\=\@\(]?\s*(?:from|starting\s+at|approx\.?)?\s*{curr_pattern}\s*{num_pattern}\s*(?:(?:\/\s*|per\s+)(?:month|mo|m|monthly))\b',
        re.IGNORECASE
    )
    
    # 1b. Monthly pattern (suffix currency)
    monthly_suffix_pattern = re.compile(
        rf'(?:([A-Za-z0-9\s\-\/\&\(\)]{{2,30}}))?\s*[:\-\=\@\(]?\s*(?:from|starting\s+at|approx\.?)?\s*{num_pattern}\s*{curr_pattern}\s*(?:(?:\/\s*|per\s+)(?:month|mo|m|monthly))\b',
        re.IGNORECASE
    )

    # 2. General pass: look for general tier pricing (prefix currency)
    general_pattern = re.compile(
        rf'(?:([A-Za-z0-9\s\-\/\&\(\)]{{2,30}}))?\s*[:\-\=\@\(]?\s*(?:from|starting\s+at|approx\.?)?\s*{curr_pattern}\s*{num_pattern}',
        re.IGNORECASE
    )

    # 2b. General pass (suffix currency)
    general_suffix_pattern = re.compile(
        rf'(?:([A-Za-z0-9\s\-\/\&\(\)]{{2,30}}))?\s*[:\-\=\@\(]?\s*(?:from|starting\s+at|approx\.?)?\s*{num_pattern}\s*{curr_pattern}',
        re.IGNORECASE
    )

    seen_tiers = set()
    
    def process_matches(pattern, is_monthly=False, num_group_idx=2, tier_group_idx=1):
        for match in pattern.finditer(text):
            groups = match.groups()
            tier_raw = groups[tier_group_idx - 1] if len(groups) >= tier_group_idx else None
            price_str = groups[num_group_idx - 1] if len(groups) >= num_group_idx else None
            
            if not price_str:
                continue

            tier_name = tier_raw.strip() if tier_raw and tier_raw.strip() else "General Tier"
            tier_name = re.sub(r'^[0-9\.\-\*\#\s\(\)]+', '', tier_name).strip()
            tier_name = re.sub(r'[\(\)]+$', '', tier_name).strip()
            if not tier_name or len(tier_name) < 2:
                tier_name = "General Tier"
                
            if not is_monthly:
                if "annual" in tier_name.lower() or "year" in tier_name.lower():
                    continue
                match_start = max(0, match.start() - 20)
                match_end = min(len(text), match.end() + 20)
                context = text[match_start:match_end].lower()
                if "per year" in context or "/year" in context or "/yr" in context or "annual" in context or "annum" in context:
                    continue
                
            clean_price = price_str.replace(',', '')
            try:
                val = float(clean_price)
                if val > 0:
                    norm_key = tier_name.lower()
                    if norm_key not in seen_tiers:
                        seen_tiers.add(norm_key)
                        results.append({"tier_name": tier_name, "price_val": val})
            except ValueError:
                pass

    process_matches(monthly_pattern, is_monthly=True, num_group_idx=2, tier_group_idx=1)
    if not results:
        process_matches(monthly_suffix_pattern, is_monthly=True, num_group_idx=2, tier_group_idx=1)
    if not results:
        process_matches(general_pattern, is_monthly=False, num_group_idx=2, tier_group_idx=1)
    if not results:
        process_matches(general_suffix_pattern, is_monthly=False, num_group_idx=2, tier_group_idx=1)
        
    return results

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

    # 1b. Deterministic target country & currency normalization
    if isinstance(extracted_dict, dict):
        idea_lower = idea.lower()
        extracted_country = str(extracted_dict.get("target_country", "")).lower()
        if any(term in idea_lower for term in ["uk", "uk-based", "united kingdom", "london", "britain", "england", "scotland", "wales"]) and extracted_country in ("global", "", "none", "unknown"):
            extracted_dict["target_country"] = "UK"
        elif any(term in idea_lower for term in ["india", "indian", "mumbai", "delhi", "bengaluru", "bangalore", "hyderabad", "pune", "chennai", "kolkata", "noida", "gurugram", "gurgaon"]) and extracted_country in ("global", "", "none", "unknown"):
            extracted_dict["target_country"] = "India"

        combined_text = f"{idea} {finance_text} {strategy_text} {marketing_text}".lower()
        if any(sym in combined_text for sym in ["₹", "inr", "rs.", "rs ", "rupees", "rupee"]):
            extracted_dict["finance_currency"] = "INR"
        elif any(sym in combined_text for sym in ["£", "gbp"]):
            extracted_dict["finance_currency"] = "GBP"
        elif any(sym in combined_text for sym in ["€", "eur"]):
            extracted_dict["finance_currency"] = "EUR"
        elif any(sym in combined_text for sym in ["$", "usd"]):
            extracted_dict["finance_currency"] = "USD"

        # Canonicalize raw currency string
        raw_curr = str(extracted_dict.get("finance_currency", "")).strip()
        raw_curr_upper = raw_curr.upper()
        if raw_curr in ["₹", "Rs.", "Rs", "RS", "RS."] or "INR" in raw_curr_upper or "RUPEE" in raw_curr_upper:
            extracted_dict["finance_currency"] = "INR"
        elif raw_curr == "£" or "GBP" in raw_curr_upper:
            extracted_dict["finance_currency"] = "GBP"
        elif raw_curr == "€" or "EUR" in raw_curr_upper:
            extracted_dict["finance_currency"] = "EUR"
        elif raw_curr == "$" or "USD" in raw_curr_upper:
            extracted_dict["finance_currency"] = "USD"

        # Ensure pricing lists are non-empty using fallback extractor if LLM returned empty list
        source_texts = {
            "strategy_pricing": strategy_text,
            "finance_pricing": finance_text,
            "marketing_pricing": marketing_text
        }
        for key, text_content in source_texts.items():
            pricing_list = extracted_dict.get(key)
            if not isinstance(pricing_list, list) or len(pricing_list) == 0:
                fallback_tiers = fallback_extract_pricing(text_content)
                if fallback_tiers:
                    print(f"[Business Rules Engine] Used fallback pricing regex extractor for {key}: {fallback_tiers}")
                    extracted_dict[key] = fallback_tiers

        # Sanitize pricing tier names to prevent null/None validation failures
        for key in ["strategy_pricing", "finance_pricing", "marketing_pricing"]:
            pricing_list = extracted_dict.get(key)
            if isinstance(pricing_list, list):
                for item in pricing_list:
                    if isinstance(item, dict):
                        tier_name = item.get("tier_name")
                        if tier_name is None or not isinstance(tier_name, str) or not tier_name.strip():
                            item["tier_name"] = "General Tier"
        
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
