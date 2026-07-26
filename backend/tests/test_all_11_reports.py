from app.schemas.report import (
    ExecutiveSummarySchema,
    BusinessPlanSchema,
    SwotAnalysisSchema,
    FinancialProjectionSchema,
    InvestmentReadinessSchema,
    BusinessModelCanvasSchema,
    PestleAnalysisSchema,
    PortersFiveForcesSchema,
    CompetitorAnalysisSchema,
    MarketingGtmSchema,
    RiskAssessmentMatrixSchema,
)
from app.pipeline.report_generator import _coerce_schema_fields

def test_all_11_report_schemas():
    schemas = [
        ("Executive Summary", ExecutiveSummarySchema, {
            "concept": "EcoSphere carbon audit SaaS",
            "market_opportunity": "UK SMEs under SECR",
            "strategic_positioning": "Automated utility APIs",
            "financial_projection_summary": "Tiered subscriptions",
            "risk_mitigation_summary": "GDPR compliance",
            "overall_score": 90.0,
            "key_recommendations": ["Scale digital sales", "Target UK SMEs"],
        }),
        ("Business Plan", BusinessPlanSchema, {
            "company_description": "EcoSphere SaaS venture",
            "market_analysis": "TAM $5B UK SME market",
            "marketing_sales_strategy": "Inbound LinkedIn ads",
            "operational_plan": "Utility API integration",
            "financial_plan": "Break even month 14",
            "risk_register": ["Risk 1: API downtime"],
        }),
        ("SWOT Analysis", SwotAnalysisSchema, {
            "strengths": ["Proprietary utility API connector", "First mover in SME carbon audit"],
            "weaknesses": ["Early-stage brand recognition", "Small initial engineering team"],
            "opportunities": ["UK Environment Act compliance mandates", "Expanding EU ESG disclosure rules"],
            "threats": ["Incumbent CRM software additions", "Macroeconomic SME spending slowdown"],
        }),
        ("Financial Projection", FinancialProjectionSchema, {
            "revenue_model_details": "Starter: £299/mo, Growth: £499/mo",
            "pricing_sanity_check": "Consistent across Strategy and Finance",
            "capital_requirements": "Seed capital requirement: £500k",
            "break_even_analysis": "Break even in 14 months",
            "scoring_context": "Financial Soundness score 88/100",
        }),
        ("Investment Readiness Report", InvestmentReadinessSchema, {
            "investment_thesis": "High growth potential in UK ESG SaaS",
            "scoring_breakdown": "Overall score 90.0",
            "critic_concerns": "Address SME churn",
            "milestones_funding": "Seed round £500k",
            "rules_validation_summary": "Passed pricing consistency checks",
        }),
        ("Business Model Canvas", BusinessModelCanvasSchema, {
            "value_propositions": ["Automated carbon auditing"],
            "customer_segments": ["UK SMEs"],
            "channels": ["Direct sales"],
            "customer_relationships": ["Automated SaaS"],
            "revenue_streams": ["Subscriptions"],
            "key_resources": ["Utility APIs"],
            "key_activities": ["Software engineering"],
            "key_partnerships": ["Utility providers"],
            "cost_structure": ["R&D and hosting"],
        }),
        ("PESTLE Analysis", PestleAnalysisSchema, {
            "political": ["Net Zero 2050 mandate"],
            "economic": ["SME budget trends"],
            "social": ["ESG awareness"],
            "technological": ["Utility API availability"],
            "legal": ["SECR compliance"],
            "environmental": ["Scope 1-3 reporting"],
        }),
        ("Porter's Five Forces", PortersFiveForcesSchema, {
            "threat_of_new_entrants": "Medium due to API complexity",
            "bargaining_power_of_buyers": "Low due to regulatory duty",
            "bargaining_power_of_suppliers": "Medium utility provider power",
            "threat_of_substitutes": "Low manual Excel workarounds",
            "competitive_rivalry": "Moderate in SME sustainability",
        }),
        ("Competitor Analysis", CompetitorAnalysisSchema, {
            "direct_competitors": ["GreenKPO: audit-ready carbon software", "EcoHedge: SME carbon calculator"],
            "indirect_competitors": ["Manual Excel spreadsheets", "Boutique sustainability consultancies"],
            "competitive_advantages": ["Automated utility API ingestion", "Low TCO SME pricing"],
            "market_positioning": "Leading automated compliance platform for UK mid-market SMEs",
        }),
        ("Marketing Plan & Go-To-Market", MarketingGtmSchema, {
            "target_customer_profiles": ["ICP 1: UK SMEs 20-500 employees", "ICP 2: Operations directors"],
            "outreach_acquisition_channels": ["LinkedIn Ads", "Utility provider co-marketing"],
            "brand_positioning_messaging": "Effortless automated carbon auditing for UK SMEs",
            "growth_campaign_roadmap": ["Phase 1: Pilot 50 SMEs", "Phase 2: Scale digital ads"],
        }),
        ("Risk Assessment & Mitigation Matrix", RiskAssessmentMatrixSchema, {
            "regulatory_compliance_risks": ["Risk: Evolving SECR rules. Mitigation: Continuous legal tracking"],
            "operational_technical_risks": ["Risk: API rate limits. Mitigation: Async batch queueing"],
            "market_financial_risks": ["Risk: Inflationary budget cuts. Mitigation: Low-cost starter tier"],
            "critic_adversarial_vulnerabilities": ["Vulnerability: SME churn. Action: Automated onboarding"],
        }),
    ]

    assert len(schemas) == 11, f"Expected 11 report schemas, got {len(schemas)}"

    for name, schema_cls, sample in schemas:
        coerced = _coerce_schema_fields(sample, schema_cls)
        val = schema_cls.model_validate(coerced)
        assert val is not None
        print(f"[{name}] Schema Validation & Coercing PASSED!")

    print("\nALL 11 REPORT SCHEMAS VALIDATED SUCCESSFULLY!")

if __name__ == "__main__":
    test_all_11_report_schemas()
