from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class SimulatorParams(BaseModel):
    starter_price: float = Field(299.0, description="Starter monthly price")
    growth_price: float = Field(799.0, description="Growth monthly price")
    enterprise_price: float = Field(1999.0, description="Enterprise monthly price floor")
    starter_share_pct: float = Field(60.0, description="Starter customer share %")
    growth_share_pct: float = Field(30.0, description="Growth customer share %")
    enterprise_share_pct: float = Field(10.0, description="Enterprise customer share %")
    cac: float = Field(150.0, description="Customer Acquisition Cost")
    monthly_growth_rate_pct: float = Field(15.0, description="Monthly compounded growth rate %")
    monthly_churn_rate_pct: float = Field(2.5, description="Monthly churn rate %")
    gross_margin_pct: float = Field(80.0, description="Gross profit margin %")
    headcount: int = Field(4, description="Team headcount")
    avg_monthly_salary: float = Field(4500.0, description="Average salary per employee / month")
    fixed_monthly_opex: float = Field(2500.0, description="Fixed monthly operational expense")
    initial_capital: float = Field(100000.0, description="Starting cash / funding reserve")
    months: int = Field(36, description="Forecast timeline in months (12-36)")

class SimulatorMonthPoint(BaseModel):
    month: int
    active_customers: int
    mrr: float
    arr: float
    gross_profit: float
    total_opex: float
    net_profit: float
    cash_balance: float

class SimulatorSummary(BaseModel):
    arpu: float
    ltv: float
    ltv_cac_ratio: float
    cac_payback_months: float
    break_even_month: Any
    runway_months: Any
    health_status: str
    total_capital_burned: float
    month_12_mrr: float
    month_24_mrr: float
    month_36_mrr: float

class SimulatorResponse(BaseModel):
    summary: SimulatorSummary
    monthly_projections: List[SimulatorMonthPoint]
    ai_commentary: Optional[str] = None

class RedTeamRequest(BaseModel):
    scenario_type: str = Field("big_tech_enters", description="Shock scenario type")
    custom_shock: Optional[str] = Field("", description="Custom shock text if scenario_type is custom")

class RedTeamResponse(BaseModel):
    scenario_title: str
    viability_delta: int
    adjusted_score: float
    primary_impact: str
    agent_deliberations: Dict[str, str]
    defensive_pivot_actions: List[str]

class InterrogateRequest(BaseModel):
    agent_persona: str = Field("strategy", description="strategy | finance | marketing | risk | critic")
    question: str

class InterrogateResponse(BaseModel):
    agent_persona: str
    response: str
    data_sources_referenced: List[str]

class TermSheetRequest(BaseModel):
    term_sheet_text: str

class TermSheetResponse(BaseModel):
    summary: str
    overall_risk_rating: str
    clauses_analyzed: List[Dict[str, Any]]
    key_recommendations: List[str]
