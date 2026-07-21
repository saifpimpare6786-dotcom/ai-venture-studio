from pydantic import BaseModel, Field
from typing import List, Dict, Any

class ExecutiveSummarySchema(BaseModel):
    concept: str = Field(description="Venture overview, problem statement, and primary value proposition.")
    market_opportunity: str = Field(description="Summary of target client segment (ICP), market fit, and research findings.")
    strategic_positioning: str = Field(description="Core competitive advantages, unique selling proposition (USP), and growth channels.")
    financial_projection_summary: str = Field(description="Overview of revenue model, pricing, and required seed funding.")
    risk_mitigation_summary: str = Field(description="Top regulatory, operational, or competitive risks and mitigation strategies.")
    overall_score: float = Field(description="The calculated overall score (0 to 100) computed by the Scoring Engine.")

class BusinessPlanSchema(BaseModel):
    company_description: str = Field(description="Comprehensive venture details, strategic goals, mission, and problem-solution fit.")
    market_analysis: str = Field(description="Industry analysis, competitor landscape, supplier/buyer power, and target market sizing.")
    marketing_sales_strategy: str = Field(description="Go-to-market strategies, customer acquisition pipelines, ICP definitions, and branding vectors.")
    operational_plan: str = Field(description="Key operations, partner requirements, security/privacy, and regulatory compliance roadmap.")
    financial_plan: str = Field(description="Revenue model analysis, exact pricing structures, break-even timelines, and capital expenditure needs.")

class SwotAnalysisSchema(BaseModel):
    strengths: List[str] = Field(description="Internal strengths, specialized expertise, and technology advantages.")
    weaknesses: List[str] = Field(description="Internal weaknesses, operational constraints, and critical reasoning vulnerabilities.")
    opportunities: List[str] = Field(description="External market opportunities, upcoming regulations, and customer niches.")
    threats: List[str] = Field(description="External regulatory hurdles, security threats, and direct competitor maneuvers.")

class FinancialProjectionSchema(BaseModel):
    revenue_model_details: str = Field(description="Detailed breakdown of revenue channels, monetization streams, and concrete pricing tiers.")
    pricing_sanity_check: str = Field(description="Evaluation of competitive margins, customer pricing sensitivity, and pricing consistency verification.")
    capital_requirements: str = Field(description="Direct estimates of seed/working capital, developer headcount budgets, and operational burn rates.")
    break_even_analysis: str = Field(description="Plausible timeline, unit sales targets, or customer volume needed to break even.")

class InvestmentReadinessSchema(BaseModel):
    investment_thesis: str = Field(description="Compelling argument on why this venture represents a viable, high-potential investment opportunity.")
    scoring_breakdown: str = Field(description="Breakdown of viability, market fit, and finance scores, detailing the scoring rubric logic.")
    critic_concerns: str = Field(description="Adversarial VC critiques, assumptions grilled, and strategic risks requiring founder answers.")
    milestones_funding: str = Field(description="Venture timeline milestones, preferred funding type, and capital allocation priorities.")
