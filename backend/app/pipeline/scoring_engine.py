from typing import Dict, Any
from app.pipeline.state import AgentState
from app.database.db import db

class ScoringEngine:
    @staticmethod
    def calculate_scores(state: AgentState) -> Dict[str, Any]:
        """
        Evaluates weighted rubric:
        - Viability (35%)
        - Market Fit (35%)
        - Financial Soundness (30%)
        """
        rules = state.get("rules_validation", {"is_valid": True, "errors": []})
        council = state.get("council_debate", {})
        reviewer = state.get("reviewer_assessment", {})
        finance = state.get("finance_assessment", {})

        # Base scoring from agent evaluations
        alignment = float(council.get("alignment_score", 85.0))
        coherence = float(reviewer.get("coherence_score", 85.0))
        
        # Financial soundness baseline
        ltv = float(finance.get("ltv_estimate", 10000.0))
        cac = max(float(finance.get("cac_estimate", 150.0)), 1.0)
        ltv_cac = ltv / cac
        fin_base = 80.0 if ltv_cac >= 4.0 else (70.0 if ltv_cac >= 2.5 else 55.0)

        # Viability & Market Fit baselines
        strat_assess = state.get("strategy_assessment", {})
        has_market_mapping = bool(strat_assess.get("market_mapping", {}).get("whitespace_quadrant"))
        mkt_bonus = 3.0 if has_market_mapping else 0.0

        viability_score = min(max((alignment * 0.5) + (coherence * 0.5), 50.0), 98.0)
        market_fit_score = min(max((coherence * 0.7) + (alignment * 0.3) + mkt_bonus, 50.0), 96.0)
        financial_score = min(max(fin_base, 40.0), 95.0)

        # Penalties for deterministic rule violations
        if not rules.get("is_valid", True):
            errors = rules.get("errors", [])
            error_penalty = len(errors) * 5.0
            
            # Specific market rule penalty
            market_errors = sum(1 for e in errors if "Rule F" in e)
            if market_errors > 0:
                market_fit_score = max(market_fit_score - (market_errors * 7.5), 25.0)
            
            financial_score = max(financial_score - error_penalty, 25.0)
            viability_score = max(viability_score - (error_penalty * 0.5), 30.0)

        # Overall weighted composite
        overall_score = round(
            (0.35 * viability_score) + 
            (0.35 * market_fit_score) + 
            (0.30 * financial_score), 
            1
        )

        return {
            "overall_score": overall_score,
            "viability_score": round(viability_score, 1),
            "market_fit_score": round(market_fit_score, 1),
            "financial_score": round(financial_score, 1),
            "rules_penalty_applied": not rules.get("is_valid", True),
            "market_mapping_validated": has_market_mapping,
            "scoring_formula": "0.35 * Viability + 0.35 * MarketFit + 0.30 * FinancialSoundness"
        }

async def scoring_node(state: AgentState) -> AgentState:
    project_id = state["project_id"]
    scores = ScoringEngine.calculate_scores(state)
    state["scores"] = scores

    rules_val: Dict[str, Any] = state.get("rules_validation") if isinstance(state.get("rules_validation"), dict) else {}
    await db.update_project(project_id, {
        "overall_score": scores["overall_score"],
        "viability_score": scores["viability_score"],
        "market_fit_score": scores["market_fit_score"],
        "financial_score": scores["financial_score"],
        "is_valid_rules": bool(rules_val.get("is_valid", True)),
        "rules_validation": rules_val
    })

    await db.add_agent_discussion(
        project_id=project_id,
        agent_name="Analytics & Scoring Engine",
        agent_role="Scoring & Rubric",
        message=f"Scoring finalized: Overall {scores['overall_score']}/100 (Viability: {scores['viability_score']}, Market Fit: {scores['market_fit_score']}, Financials: {scores['financial_score']}).",
        step_index=12
    )
    return state
