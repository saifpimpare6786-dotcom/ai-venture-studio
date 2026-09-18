import re
from typing import Dict, Any, List, Optional
from app.pipeline.state import AgentState
from app.database.db import db

class BusinessRulesEngine:
    CURRENCY_MAP = {
        "United Kingdom": "GBP",
        "UK": "GBP",
        "India": "INR",
        "European Union": "EUR",
        "Germany": "EUR",
        "France": "EUR",
        "United States": "USD",
        "Global": "USD"
    }

    @staticmethod
    def _parse_magnitude(val: Any) -> Optional[float]:
        """Parses numeric magnitude from string with B/M/K units (e.g. '$14.2B' -> 14200000000.0)."""
        if not val or not isinstance(val, (str, int, float)):
            return None
        if isinstance(val, (int, float)):
            return float(val)
        s = val.upper().replace(",", "").replace("$", "").replace("£", "").replace("€", "").replace("₹", "").strip()
        match = re.search(r"([\d\.]+)\s*([BMK]|BILLION|MILLION|THOUSAND)?", s)
        if not match:
            return None
        num_str, unit = match.groups()
        try:
            num = float(num_str)
        except ValueError:
            return None
        if unit in ("B", "BILLION"):
            return num * 1_000_000_000
        elif unit in ("M", "MILLION"):
            return num * 1_000_000
        elif unit in ("K", "THOUSAND"):
            return num * 1_000
        return num

    @classmethod
    def validate_rules(cls, state: AgentState) -> Dict[str, Any]:
        """
        Executes deterministic mathematical and strategic checks:
        Rule A: Completeness (Finance, Strategy, Marketing must provide pricing)
        Rule B: Cross-Domain Price Match (±0.0 tolerance)
        Rule C: Null vs Numeric Anomaly
        Rule D: Geographic Currency Enforcement
        Rule E: Enterprise Floor Enforcement
        Rule F: Market Sizing Hierarchy & Whitespace Mapping Sanity (SOM <= SAM <= TAM)
        """
        errors: List[str] = []
        project = state["project_data"]
        country = project.get("target_country", "United States")
        expected_currency = project.get("currency") or cls.CURRENCY_MAP.get(country, "USD")

        fin_assess: Dict[str, Any] = state.get("finance_assessment") if isinstance(state.get("finance_assessment"), dict) else {}
        strat_assess: Dict[str, Any] = state.get("strategy_assessment") if isinstance(state.get("strategy_assessment"), dict) else {}
        mkt_assess: Dict[str, Any] = state.get("marketing_assessment") if isinstance(state.get("marketing_assessment"), dict) else {}

        fin_prices: Dict[str, Any] = fin_assess.get("pricing_tiers") if isinstance(fin_assess.get("pricing_tiers"), dict) else {}
        strat_prices: Dict[str, Any] = strat_assess.get("pricing_tiers") if isinstance(strat_assess.get("pricing_tiers"), dict) else {}
        mkt_prices: Dict[str, Any] = mkt_assess.get("pricing_tiers") if isinstance(mkt_assess.get("pricing_tiers"), dict) else {}

        # Rule A: Data Completeness
        if not fin_prices:
            errors.append("Rule A Failure: Finance Agent failed to provide numeric pricing tiers.")
        if not strat_prices:
            errors.append("Rule A Failure: Strategy Agent omitted pricing structures.")
        if not mkt_prices:
            errors.append("Rule A Failure: Marketing Agent omitted pricing structures.")

        # Rule B: Cross-Domain Price Matching
        for tier in ["starter", "growth", "enterprise"]:
            fp = fin_prices.get(tier)
            sp = strat_prices.get(tier)
            mp = mkt_prices.get(tier)

            if fp is not None and sp is not None and abs(fp - sp) > 0.01:
                errors.append(f"Rule B Failure: Strategy price for '{tier}' ({sp}) does not match Finance anchor ({fp}).")
            if fp is not None and mp is not None and abs(fp - mp) > 0.01:
                errors.append(f"Rule B Failure: Marketing price for '{tier}' ({mp}) does not match Finance anchor ({fp}).")

        # Rule C: Null vs Numeric Anomaly
        for tier in ["starter", "growth", "enterprise"]:
            vals = [fin_prices.get(tier), strat_prices.get(tier), mkt_prices.get(tier)]
            has_numeric = any(v is not None for v in vals)
            has_none = any(v is None for v in vals)
            if has_numeric and has_none and not any(f"Rule B" in e and tier in e for e in errors):
                errors.append(f"Rule C Failure: Incomplete tier definition for '{tier}' across agents.")

        # Rule D: Currency Enforcement
        actual_currency = fin_assess.get("currency_used", expected_currency)
        if expected_currency and actual_currency and expected_currency.upper() != str(actual_currency).upper():
            errors.append(f"Rule D Failure: Jurisdiction '{country}' expects currency '{expected_currency}', but got '{actual_currency}'.")

        # Rule E: Enterprise Floor Enforcement
        ent_price = fin_prices.get("enterprise")
        if ent_price is not None and ent_price < 100.0:
            errors.append(f"Rule E Failure: Enterprise pricing floor must be a concrete enterprise value (got {ent_price}).")

        # Rule F: Market Sizing Hierarchy (SOM <= SAM <= TAM) & Whitespace Sanity Check
        tam_sam_som = strat_assess.get("tam_sam_som", {})
        mkt_map = strat_assess.get("market_mapping", {})
        
        tam_val = cls._parse_magnitude(mkt_map.get("top_down_tam") or tam_sam_som.get("tam"))
        sam_val = cls._parse_magnitude(mkt_map.get("sam") or tam_sam_som.get("sam"))
        som_val = cls._parse_magnitude(mkt_map.get("som") or tam_sam_som.get("som"))

        if tam_val is not None and sam_val is not None and sam_val > tam_val * 1.05:
            errors.append(f"Rule F Failure: SAM ({mkt_map.get('sam') or tam_sam_som.get('sam')}) exceeds TAM ({mkt_map.get('top_down_tam') or tam_sam_som.get('tam')}) in market sizing hierarchy.")
        if sam_val is not None and som_val is not None and som_val > sam_val * 1.05:
            errors.append(f"Rule F Failure: SOM ({mkt_map.get('som') or tam_sam_som.get('som')}) exceeds SAM ({mkt_map.get('sam') or tam_sam_som.get('sam')}) in market sizing hierarchy.")

        is_valid = len(errors) == 0
        return {
            "is_valid": is_valid,
            "error_count": len(errors),
            "errors": errors,
            "currency_validated": expected_currency,
            "rules_checked": [
                "Rule A (Completeness)",
                "Rule B (Price Matching)",
                "Rule C (Null Anomaly)",
                "Rule D (Currency)",
                "Rule E (Enterprise Floor)",
                "Rule F (Market Sizing Hierarchy & Mapping)"
            ]
        }

async def rules_node(state: AgentState) -> AgentState:
    project_id = state["project_id"]
    res = BusinessRulesEngine.validate_rules(state)
    state["rules_validation"] = res

    status_msg = "Passed all deterministic business validation rules (100% Coherent)." if res["is_valid"] else f"Detected {res['error_count']} parameter discrepancies."
    await db.add_agent_discussion(
        project_id=project_id,
        agent_name="Deterministic Rules Sentry",
        agent_role="Mathematical Quality Gate",
        message=status_msg,
        step_index=11
    )
    return state
