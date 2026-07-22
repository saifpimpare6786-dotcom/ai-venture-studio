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
