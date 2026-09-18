from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# 1. Executive Summary
class ExecutiveSummarySchema(BaseModel):
    concept: str = Field(..., description="Core venture thesis and value proposition")
    market_opportunity: str = Field(..., description="Addressable market and growth tailwinds")
    strategic_positioning: str = Field(..., description="Competitive moats and USP")
    financial_projection_summary: str = Field(..., description="High-level revenue and margin trajectory")
    risk_mitigation_summary: str = Field(..., description="Key hazards and countermeasures")
    overall_score: float = Field(..., description="Venture readiness score 0-100")
    key_recommendations: List[str] = Field(..., description="Top actionable C-suite priorities")

# 2. Full-Length Business Plan
class BusinessPlanSchema(BaseModel):
    company_description: str
    market_analysis: str
    market_sizing_triangulation: Optional[str] = Field(None, description="Top-down and bottom-up TAM/SAM/SOM sizing breakdown")
    marketing_sales_strategy: str
    operational_plan: str
    financial_plan: str
    risk_register: List[str]

# 3. Business Model Canvas (9 Blocks)
class BusinessModelCanvasSchema(BaseModel):
    value_propositions: List[str]
    customer_segments: List[str]
    channels: List[str]
    customer_relationships: List[str]
    revenue_streams: List[str]
    key_resources: List[str]
    key_activities: List[str]
    key_partnerships: List[str]
    cost_structure: List[str]

# 4. SWOT Analysis
class SwotAnalysisSchema(BaseModel):
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    threats: List[str]

# 5. PESTLE Analysis
class PestleAnalysisSchema(BaseModel):
    political: List[str]
    economic: List[str]
    social: List[str]
    technological: List[str]
    legal: List[str]
    environmental: List[str]

# 6. Porter's Five Forces
class PortersFiveForcesSchema(BaseModel):
    threat_of_new_entrants: str
    bargaining_power_of_buyers: str
    bargaining_power_of_suppliers: str
    threat_of_substitutes: str
    competitive_rivalry: str

# 7. Competitor Analysis Matrix
class CompetitorAnalysisSchema(BaseModel):
    direct_competitors: List[str]
    indirect_competitors: List[str]
    competitive_advantages: List[str]
    market_positioning: str
    whitespace_opportunity: Optional[str] = Field(None, description="Target whitespace wedge identified from 2x2 positioning")
    positioning_axes: Optional[Dict[str, str]] = Field(None, description="X and Y axes for competitive landscape mapping")
    market_map_quadrants: Optional[List[Dict[str, Any]]] = Field(None, description="Competitor positions across market map quadrants")

# 8. Detailed Financial Projection
class FinancialProjectionSchema(BaseModel):
    revenue_model_details: str
    pricing_sanity_check: str
    capital_requirements: str
    break_even_analysis: str
    scoring_context: str

# 9. Marketing Plan & Go-To-Market (GTM)
class MarketingGtmSchema(BaseModel):
    target_customer_profiles: List[str]
    outreach_acquisition_channels: List[str]
    brand_positioning_messaging: str
    growth_campaign_roadmap: List[str]
    where_to_play_wedge: Optional[str] = Field(None, description="Initial target wedge into market")

# 10. Risk Assessment & Mitigation Matrix
class RiskAssessmentMatrixSchema(BaseModel):
    regulatory_compliance_risks: List[str]
    operational_technical_risks: List[str]
    market_financial_risks: List[str]
    critic_adversarial_vulnerabilities: List[str]

# 11. Investment Readiness Report
class InvestmentReadinessSchema(BaseModel):
    investment_thesis: str
    scoring_breakdown: str
    critic_concerns: str
    milestones_funding: str
    rules_validation_summary: str

# 12. ESG & Sustainability Recommendations
class EsgSustainabilitySchema(BaseModel):
    environmental_impact_metrics: List[str]
    social_governance_frameworks: List[str]
    regulatory_esg_compliance: List[str]
    sustainability_roadmap: List[str]

# 13. Pitch Summary & Investor Deck Outline
class PitchSummaryDeckSchema(BaseModel):
    elevator_pitch_summary: str
    slide_deck_outline: List[Dict[str, Any]]
    key_investment_highlights: List[str]
    use_of_funds_breakdown: Dict[str, Any]
