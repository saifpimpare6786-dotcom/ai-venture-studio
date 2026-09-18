from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ProjectCreate(BaseModel):
    name: str = Field(..., description="Startup or venture name")
    industry: str = Field(..., description="Industry domain, e.g., B2B SaaS, HealthTech")
    target_country: str = Field("United States", description="Jurisdiction / country")
    currency: str = Field("USD", description="Currency symbol/code, e.g., USD, GBP, INR, EUR")
    stage: str = Field("idea", description="Current venture stage: idea, prototype, revenue")
    problem_statement: str = Field(..., description="The core pain point being solved")
    solution_description: str = Field(..., description="How the product/service solves the problem")
    target_customers: str = Field(..., description="Ideal target audience or enterprise persona")
    customer_segment: Optional[str] = Field("B2B", description="B2B, B2C, B2B2C, Marketplace")
    competitors: Optional[str] = Field("", description="Known direct and indirect competitors")
    revenue_model: str = Field(..., description="Subscription, Usage-based, Transaction fee, etc.")
    pricing_strategy: Optional[str] = Field("", description="Pricing ideas or desired tiering")
    budget: float = Field(0.0, description="Available starting capital / budget")
    preferred_funding: float = Field(0.0, description="Target funding ask from angels/VCs")
    team_size: int = Field(1, description="Founding team headcount")
    timeline: str = Field("12 months", description="Target execution timeline")
    goals: List[str] = Field(default_factory=list, description="Top strategic milestones")
    notes: Optional[str] = Field("", description="Additional context or constraints")

class ProjectResponse(ProjectCreate):
    id: str
    user_id: str
    status: str
    overall_score: Optional[float] = None
    viability_score: Optional[float] = None
    market_fit_score: Optional[float] = None
    financial_score: Optional[float] = None
    is_valid_rules: Optional[bool] = True
    rules_validation: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: str
