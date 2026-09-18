import math
import json
from typing import Dict, Any, List
from services.llm import llm_router

class SimulatorEngine:
    @staticmethod
    def calculate_scenario(
        starter_price: float = 49.0,
        growth_price: float = 149.0,
        enterprise_price: float = 499.0,
        starter_share_pct: float = 60.0,
        growth_share_pct: float = 30.0,
        enterprise_share_pct: float = 10.0,
        cac: float = 150.0,
        monthly_growth_rate_pct: float = 15.0,
        monthly_churn_rate_pct: float = 2.5,
        gross_margin_pct: float = 80.0,
        headcount: int = 4,
        avg_monthly_salary: float = 4500.0,
        fixed_monthly_opex: float = 2500.0,
        initial_capital: float = 100000.0,
        months: int = 36
    ) -> Dict[str, Any]:
        """
        Calculates month-by-month financial trajectories over 12-36 months.
        """
        # Normalise shares
        total_share = starter_share_pct + growth_share_pct + enterprise_share_pct
        s_share = (starter_share_pct / total_share)
        g_share = (growth_share_pct / total_share)
        e_share = (enterprise_share_pct / total_share)
        
        arpu = (starter_price * s_share) + (growth_price * g_share) + (enterprise_price * e_share)
        
        # Unit economics
        churn_decimal = max(monthly_churn_rate_pct / 100.0, 0.001)
        ltv = (arpu * (gross_margin_pct / 100.0)) / churn_decimal
        ltv_cac_ratio = round(ltv / max(cac, 1.0), 2)
        cac_payback_months = round(cac / max(arpu * (gross_margin_pct / 100.0), 1.0), 1)
        
        # Monthly state tracking
        active_customers = 10.0  # Month 1 starting baseline
        cash_balance = initial_capital
        total_revenue_burned = 0.0
        break_even_month = None
        cash_exhausted_month = None
        
        monthly_data = []
        
        for m in range(1, months + 1):
            # Growth & Churn
            new_customers = active_customers * (monthly_growth_rate_pct / 100.0)
            churned_customers = active_customers * churn_decimal
            active_customers = max(active_customers + new_customers - churned_customers, 0)
            
            # Revenue
            mrr = active_customers * arpu
            arr = mrr * 12.0
            gross_profit = mrr * (gross_margin_pct / 100.0)
            
            # Expenses (Payroll scales slowly with customer milestones)
            current_headcount = headcount + int(m / 10)
            payroll_cost = current_headcount * avg_monthly_salary
            marketing_cost = new_customers * cac
            total_opex = payroll_cost + fixed_monthly_opex + marketing_cost
            
            # Net Cash Flow
            net_profit = gross_profit - total_opex
            cash_balance += net_profit
            
            if net_profit > 0 and break_even_month is None:
                break_even_month = m
                
            if cash_balance < 0 and cash_exhausted_month is None:
                cash_exhausted_month = m
                
            if net_profit < 0:
                total_revenue_burned += abs(net_profit)
                
            monthly_data.append({
                "month": m,
                "active_customers": round(active_customers),
                "mrr": round(mrr, 2),
                "arr": round(arr, 2),
                "gross_profit": round(gross_profit, 2),
                "total_opex": round(total_opex, 2),
                "net_profit": round(net_profit, 2),
                "cash_balance": round(cash_balance, 2)
            })

        # Runway calculation
        latest_monthly_burn = max(-monthly_data[0]["net_profit"], 1.0)
        runway_months = round(initial_capital / latest_monthly_burn, 1) if break_even_month is None or break_even_month > 1 else 999.0

        # Health indicator
        health_status = "GREEN" if ltv_cac_ratio >= 4.0 and (break_even_month and break_even_month <= 18) else ("YELLOW" if ltv_cac_ratio >= 2.5 else "RED")

        return {
            "summary": {
                "arpu": round(arpu, 2),
                "ltv": round(ltv, 2),
                "ltv_cac_ratio": ltv_cac_ratio,
                "cac_payback_months": cac_payback_months,
                "break_even_month": break_even_month or "36+ Months",
                "runway_months": runway_months if runway_months < 999 else "Profitable / Self-Sustaining",
                "health_status": health_status,
                "total_capital_burned": round(total_revenue_burned, 2),
                "month_12_mrr": monthly_data[11]["mrr"] if len(monthly_data) >= 12 else 0,
                "month_24_mrr": monthly_data[23]["mrr"] if len(monthly_data) >= 24 else 0,
                "month_36_mrr": monthly_data[35]["mrr"] if len(monthly_data) >= 36 else 0
            },
            "monthly_projections": monthly_data
        }

    @classmethod
    def generate_scenarios(cls, base_params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Base Case, Bull Case (+30% growth, -20% churn), and Bear Case (-40% growth, +50% CAC)."""
        # Base Case
        base_result = cls.calculate_scenario(**base_params)
        
        # Bull Case
        bull_params = dict(base_params)
        bull_params["monthly_growth_rate_pct"] = base_params.get("monthly_growth_rate_pct", 15.0) * 1.3
        bull_params["monthly_churn_rate_pct"] = max(base_params.get("monthly_churn_rate_pct", 2.5) * 0.8, 0.5)
        bull_params["cac"] = base_params.get("cac", 150.0) * 0.85
        bull_result = cls.calculate_scenario(**bull_params)

        # Bear Case
        bear_params = dict(base_params)
        bear_params["monthly_growth_rate_pct"] = max(base_params.get("monthly_growth_rate_pct", 15.0) * 0.6, 2.0)
        bear_params["monthly_churn_rate_pct"] = base_params.get("monthly_churn_rate_pct", 2.5) * 1.5
        bear_params["cac"] = base_params.get("cac", 150.0) * 1.5
        bear_result = cls.calculate_scenario(**bear_params)

        return {
            "base_case": base_result,
            "bull_case": bull_result,
            "bear_case": bear_result
        }

    @staticmethod
    async def get_ai_sensitivity_commentary(project_name: str, params: Dict[str, Any], summary: Dict[str, Any]) -> str:
        """AI financial advisor commentary on the founder's simulated assumptions."""
        sys_prompt = "You are an institutional venture CFO analyzing sensitivity simulator outputs for a startup. Provide a concise, highly actionable 2-3 paragraph analysis highlighting leverage points, capital vulnerabilities, and strategic recommendations."
        user_prompt = f"""
Startup: {project_name}
Simulated Parameters:
{json.dumps(params, indent=2)}

Calculated Financial Summary:
{json.dumps(summary, indent=2)}

Provide your strategic CFO commentary and sensitivity risk breakdown.
"""
        try:
            res = await llm_router.generate_structured(
                system_prompt=sys_prompt,
                user_prompt=user_prompt,
                preferred_provider="nvidia",
                temperature=0.3,
                max_tokens=1024
            )
            return res.get("commentary") or res.get("analysis") or str(res)
        except Exception as e:
            return f"Sensitivity Analysis: LTV/CAC ratio of {summary.get('ltv_cac_ratio')}x and break-even at Month {summary.get('break_even_month')}. Maintain CAC below target thresholds to preserve initial runway."

simulator_engine = SimulatorEngine()
