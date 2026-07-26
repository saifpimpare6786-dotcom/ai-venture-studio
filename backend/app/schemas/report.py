from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


# ---------------------------------------------------------------------------
# Report schema base — every report schema inherits from this to carry the
# export_formats class variable that the Report Generator registry reads.
# ---------------------------------------------------------------------------

class ReportSchemaBase(BaseModel):
    """Base class for all report schemas. Subclasses declare export_formats."""
    # Subclasses override this at the class level, e.g.:
    #   export_formats: ClassVar[List[str]] = ["docx", "pdf"]
    pass


# ---------------------------------------------------------------------------
# Priority Tier 1 — the 5 prototype reports
# ---------------------------------------------------------------------------

class ExecutiveSummarySchema(ReportSchemaBase):
    """
    High-level boardroom briefing for founders and investors.
    Export formats: DOCX, PPTX, PDF
    """
    concept: str = Field(
        description="Venture overview, problem statement, and primary value proposition."
    )
    market_opportunity: str = Field(
        description=(
            "Summary of target client segment (ICP), market fit, competitive landscape, "
            "and key research findings."
        )
    )
    strategic_positioning: str = Field(
        description=(
            "Core competitive advantages, unique selling proposition (USP), growth channels, "
            "and branding vectors."
        )
    )
    financial_projection_summary: str = Field(
        description=(
            "Overview of revenue model, concrete pricing tiers with numeric values, "
            "and required seed funding estimate."
        )
    )
    risk_mitigation_summary: str = Field(
        description=(
            "Top regulatory, operational, or competitive risks identified by the Risk Agent "
            "and Critic, with a mitigation roadmap."
        )
    )
    overall_score: float = Field(
        description="The weighted overall score (0–100) computed by the Analytics & Scoring Engine.",
        ge=0.0,
        le=100.0
    )
    key_recommendations: List[str] = Field(
        description=(
            "3–5 prioritised actionable recommendations drawn from Council debate, "
            "Reviewer synthesis, and Critic adversarial notes."
        ),
        min_length=1
    )


class BusinessPlanSchema(ReportSchemaBase):
    """
    Full-length business plan suitable for bank/investor submission.
    Export formats: DOCX, PDF
    """
    company_description: str = Field(
        description=(
            "Comprehensive venture details, strategic vision and mission, team composition "
            "assumptions, and problem-solution alignment."
        )
    )
    market_analysis: str = Field(
        description=(
            "Industry analysis, direct and indirect competitor matrix, supplier/buyer power, "
            "TAM/SAM/SOM estimates, and target market sizing."
        )
    )
    marketing_sales_strategy: str = Field(
        description=(
            "Go-to-market approach, customer acquisition pipelines, ICP persona definitions, "
            "branding taglines, and channel mix."
        )
    )
    operational_plan: str = Field(
        description=(
            "Key operations, critical partnerships, tech stack summary, security/privacy "
            "compliance checklist, and execution milestone roadmap."
        )
    )
    financial_plan: str = Field(
        description=(
            "Revenue model analysis, exact pricing tier structures with numeric values, "
            "break-even timeline, capital expenditure, and burn rate assumptions."
        )
    )
    risk_register: List[str] = Field(
        description=(
            "Prioritised list of top risks (regulatory, operational, competitive, financial) "
            "with proposed mitigations for each."
        ),
        min_length=1
    )


class SwotAnalysisSchema(ReportSchemaBase):
    """
    Four-quadrant SWOT matrix.
    Export formats: DOCX, PPTX, PDF
    """
    strengths: List[str] = Field(
        description=(
            "Internal strengths: specialised expertise, technology advantages, early traction, "
            "unique IP, or cost structure advantages."
        ),
        min_length=2
    )
    weaknesses: List[str] = Field(
        description=(
            "Internal weaknesses: operational constraints, resource gaps, critical reasoning "
            "vulnerabilities identified by Critic Agent."
        ),
        min_length=2
    )
    opportunities: List[str] = Field(
        description=(
            "External market opportunities: emerging regulations, underserved niches, "
            "strategic partnership potential, technology tailwinds."
        ),
        min_length=2
    )
    threats: List[str] = Field(
        description=(
            "External threats: incumbent competitor moves, regulatory risk, macro headwinds, "
            "talent scarcity, cybersecurity exposure."
        ),
        min_length=2
    )


class FinancialProjectionSchema(ReportSchemaBase):
    """
    Detailed financial model narrative for CFO/investor review.
    Export formats: DOCX, PDF
    """
    revenue_model_details: str = Field(
        description=(
            "Detailed breakdown of revenue channels, monetisation streams, and concrete "
            "pricing tiers. Every tier must name the price in numeric form."
        )
    )
    pricing_sanity_check: str = Field(
        description=(
            "Evaluation of competitive margins, customer pricing sensitivity, consistency "
            "across Strategy/Finance/Marketing agents, and any Business Rules Engine "
            "validation findings."
        )
    )
    capital_requirements: str = Field(
        description=(
            "Direct estimates of seed/working capital needs, developer headcount and salary "
            "budgets, infrastructure costs, and projected burn rates."
        )
    )
    break_even_analysis: str = Field(
        description=(
            "Plausible timeline (months), customer volume, or MRR target needed to reach "
            "break-even, with key assumptions stated."
        )
    )
    scoring_context: str = Field(
        description=(
            "Financial Soundness score and rationale from the Scoring Engine, used to "
            "contextualise the projection's credibility."
        )
    )


class InvestmentReadinessSchema(ReportSchemaBase):
    """
    VC-ready investment memo summarising investability, risks, and milestones.
    Export formats: DOCX, PPTX, PDF
    """
    investment_thesis: str = Field(
        description=(
            "Compelling argument for why this venture represents a viable, high-potential "
            "investment opportunity, referencing market size, differentiation, and team fit."
        )
    )
    scoring_breakdown: str = Field(
        description=(
            "Breakdown of Viability, Market Fit, and Financial Soundness scores with the "
            "Scoring Engine rationale for each dimension and the weighted overall score."
        )
    )
    critic_concerns: str = Field(
        description=(
            "Top adversarial VC critiques from Critic Agent, including assumptions challenged, "
            "strategic gaps, and questions founders must be able to answer."
        )
    )
    milestones_funding: str = Field(
        description=(
            "Core venture milestones timeline, preferred funding instrument (seed/pre-seed/"
            "Series A), and capital allocation priorities by phase."
        )
    )
    rules_validation_summary: str = Field(
        description=(
            "Summary of Business Rules Engine validation outcome: whether pricing consistency "
            "and currency checks passed, and any flagged errors."
        )
    )


# ---------------------------------------------------------------------------
# Priority Tier 2 — Additional Business Intelligence Reports
# ---------------------------------------------------------------------------

class BusinessModelCanvasSchema(ReportSchemaBase):
    """
    Nine-building-block framework for mapping venture business model mechanics.
    Export formats: DOCX, PPTX, PDF
    """
    value_propositions: List[str] = Field(
        description="Core bundles of products/services that create value for target customer segments.",
        min_length=1
    )
    customer_segments: List[str] = Field(
        description="Target user groups, buyer personas, or organizations served.",
        min_length=1
    )
    channels: List[str] = Field(
        description="Communication, distribution, and sales channels used to reach customers.",
        min_length=1
    )
    customer_relationships: List[str] = Field(
        description="Types of relationships established with customer segments (e.g. automated, personal, self-service).",
        min_length=1
    )
    revenue_streams: List[str] = Field(
        description="Monetisation mechanisms, concrete pricing tier structures with numeric figures, and income vectors.",
        min_length=1
    )
    key_resources: List[str] = Field(
        description="Essential physical, intellectual, human, or financial assets required.",
        min_length=1
    )
    key_activities: List[str] = Field(
        description="Critical operational actions necessary to deliver value, manage channels, and earn revenue.",
        min_length=1
    )
    key_partnerships: List[str] = Field(
        description="Network of suppliers, technology providers, and strategic partners required.",
        min_length=1
    )
    cost_structure: List[str] = Field(
        description="Major cost drivers, fixed vs variable operational costs, and capital requirements.",
        min_length=1
    )


class PestleAnalysisSchema(ReportSchemaBase):
    """
    Macro-environmental analysis across six key dimensions.
    Export formats: DOCX, PPTX, PDF
    """
    political: List[str] = Field(
        description="Government policies, tax laws, trade regulations, and political stability factors.",
        min_length=1
    )
    economic: List[str] = Field(
        description="Economic growth, interest rates, inflation, macro spend trends, and capital availability.",
        min_length=1
    )
    social: List[str] = Field(
        description="Demographic trends, cultural shifts, consumer behavior patterns, and workplace attitudes.",
        min_length=1
    )
    technological: List[str] = Field(
        description="Tech innovations, API ecosystem readiness, automation, R&D activity, and security standards.",
        min_length=1
    )
    legal: List[str] = Field(
        description="Industry compliance rules, GDPR/data protection, consumer privacy, and employment law.",
        min_length=1
    )
    environmental: List[str] = Field(
        description="Sustainability mandates, carbon reporting policies, ESG standards, and eco-friendly requirements.",
        min_length=1
    )


class PortersFiveForcesSchema(ReportSchemaBase):
    """
    Competitive intensity and industry attractiveness evaluation across five forces.
    Export formats: DOCX, PPTX, PDF
    """
    threat_of_new_entrants: str = Field(
        description="Evaluation of barriers to entry, capital requirements, network effects, and incumbent advantages."
    )
    bargaining_power_of_buyers: str = Field(
        description="Evaluation of buyer price sensitivity, switching costs, buyer concentration, and substitute availability."
    )
    bargaining_power_of_suppliers: str = Field(
        description="Evaluation of supplier concentration, uniqueness of inputs/APIs, and vendor switching costs."
    )
    threat_of_substitutes: str = Field(
        description="Evaluation of alternative manual or software solutions, performance trade-offs, and relative pricing."
    )
    competitive_rivalry: str = Field(
        description="Evaluation of industry growth rate, number/strength of direct competitors, and market saturation."
    )


class CompetitorAnalysisSchema(ReportSchemaBase):
    """
    Detailed competitive matrix and market positioning evaluation.
    Export formats: DOCX, PPTX, PDF
    """
    direct_competitors: List[str] = Field(
        description="Main direct competitors, their core capabilities, market share, strengths, and weaknesses.",
        min_length=1
    )
    indirect_competitors: List[str] = Field(
        description="Indirect substitutes, legacy manual workarounds, and alternative product categories.",
        min_length=1
    )
    competitive_advantages: List[str] = Field(
        description="Core moat, unique selling propositions (USPs), proprietary tech, or pricing advantages.",
        min_length=1
    )
    market_positioning: str = Field(
        description="Strategic niche placement, target pricing tier justification, and defensive moat summary."
    )


class MarketingGtmSchema(ReportSchemaBase):
    """
    Go-to-market strategy, ideal customer profiles, and acquisition channel mix.
    Export formats: DOCX, PPTX, PDF
    """
    target_customer_profiles: List[str] = Field(
        description="Ideal Customer Profiles (ICPs), buyer personas, firmographic criteria, and pain points.",
        min_length=1
    )
    outreach_acquisition_channels: List[str] = Field(
        description="Primary customer acquisition pipelines, digital marketing channels, partner networks, and sales mix.",
        min_length=1
    )
    brand_positioning_messaging: str = Field(
        description="Core brand messaging hierarchy, tagline vectors, value proposition, and customer messaging strategy."
    )
    growth_campaign_roadmap: List[str] = Field(
        description="Phase 1, Phase 2, Phase 3 customer growth milestones, promotional campaigns, and expansion metrics.",
        min_length=1
    )


class RiskAssessmentMatrixSchema(ReportSchemaBase):
    """
    Comprehensive risk register covering regulatory, operational, market, and adversarial vulnerabilities.
    Export formats: DOCX, PDF
    """
    regulatory_compliance_risks: List[str] = Field(
        description="Regulatory hurdles, legal compliance, data privacy (GDPR), SECR laws, and mitigation plans.",
        min_length=1
    )
    operational_technical_risks: List[str] = Field(
        description="Operational bottlenecks, API integration dependencies, cloud security, and tech mitigations.",
        min_length=1
    )
    market_financial_risks: List[str] = Field(
        description="Market acceptance, buyer price sensitivity, capital runway constraints, and financial mitigations.",
        min_length=1
    )
    critic_adversarial_vulnerabilities: List[str] = Field(
        description="Core vulnerabilities identified by Critic Agent / Council debate and founder action items.",
        min_length=1
    )


class EsgSustainabilitySchema(ReportSchemaBase):
    """
    ESG framework, carbon auditing roadmap, and sustainability compliance guidelines.
    Export formats: DOCX, PPTX, PDF
    """
    environmental_impact_metrics: List[str] = Field(
        description="Scope 1, 2, and 3 carbon emission metrics, energy efficiency goals, and environmental targets.",
        min_length=1
    )
    social_governance_frameworks: List[str] = Field(
        description="Social impact initiatives, stakeholder engagement, ethical supply chain governance, and board oversight.",
        min_length=1
    )
    regulatory_esg_compliance: List[str] = Field(
        description="UK Environment Act 2021, SECR disclosures, EU CSRD standards, and ESG compliance audit readiness.",
        min_length=1
    )
    sustainability_roadmap: List[str] = Field(
        description="Phase 1, Phase 2, Phase 3 ESG implementation milestones, green certifications, and net-zero targets.",
        min_length=1
    )


class PitchSummaryDeckSchema(ReportSchemaBase):
    """
    Elevator pitch, slide deck structure, investment highlights, and capital allocation breakdown.
    Export formats: DOCX, PPTX, PDF
    """
    elevator_pitch_summary: str = Field(
        description="Concise 2-3 sentence elevator pitch summarizing thesis, problem, solution, TAM, and traction."
    )
    slide_deck_outline: List[str] = Field(
        description="Structured 10-12 slide pitch deck outline (Problem, Solution, Market, Product, Business Model, Traction, Competition, Financials, Team, Ask).",
        min_length=1
    )
    key_investment_highlights: List[str] = Field(
        description="Top 3-5 core reasons investors should back this venture (moat, unit economics, regulatory tailwinds).",
        min_length=1
    )
    use_of_funds_breakdown: List[str] = Field(
        description="Clear percentage capital allocation across Product R&D, Sales/GTM, Compliance/Legal, and Working Capital.",
        min_length=1
    )



