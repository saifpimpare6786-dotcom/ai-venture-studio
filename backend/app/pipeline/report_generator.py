"""
Report Generator Node -- follows the registry pattern defined in skills/report-generation/SKILL.md.

Pattern for each report type:
  1. Pydantic schema         -> app/schemas/report.py
  2. Focused prompt template -> REPORT_REGISTRY[type]["system_prompt"]
  3. Registry entry          -> REPORT_REGISTRY dict (no if/else per type)
  4. Export mapping          -> REPORT_REGISTRY[type]["export_mapping"]

Adding a new report type = add a schema + one registry entry. Zero new node logic.
"""
import json
import re
from typing import Dict, Any, List, Optional
from app.database.supabase import get_supabase_client
from services.llm import call_llm
from app.pipeline.state import AgentState
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
    EsgSustainabilitySchema,
    PitchSummaryDeckSchema,
)


def extract_json_block(text: str) -> str:
    """Extracts raw JSON content from markdown code fences if present."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def safe_parse_json(raw_text: str) -> dict:
    """
    Parses raw LLM string into a JSON dictionary with sanitization and fallbacks.
    - Strips markdown code fences (```json ... ```).
    - First attempts standard json.loads(cleaned).
    - Second attempts json.loads(cleaned, strict=False) to tolerate unescaped control
      characters like literal newlines/tabs inside string literals (fixes "Invalid control character").
    - Third attempts non-printable control character stripping (ASCII 0x00-0x1F except \n, \r, \t) + strict=False.
    Raises json.JSONDecodeError if all parse attempts fail.
    """
    if isinstance(raw_text, dict):
        return raw_text
    cleaned = extract_json_block(str(raw_text))

    # 1. Standard json.loads
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # 2. Strict=False (handles unescaped literal control chars inside strings)
    try:
        return json.loads(cleaned, strict=False)
    except Exception:
        pass

    # 3. Strip non-printable ASCII control characters 0x00-0x08, 0x0B, 0x0C, 0x0E-0x1F
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', cleaned)
    try:
        return json.loads(sanitized, strict=False)
    except Exception:
        pass

    # Final attempt: let json.loads raise JSONDecodeError so caller gets exact line error
    return json.loads(sanitized, strict=False)


# ---------------------------------------------------------------------------
# Token estimation utilities (diagnostic -- no external dependency)
# ---------------------------------------------------------------------------

def _estimate_tokens(text: str) -> int:
    """Rough token estimate: 1 token approx 4 characters (industry standard heuristic)."""
    return max(1, len(text) // 4)


def _log_prompt_token_estimates(context: dict) -> None:
    """
    Prints estimated input token counts for each report type to stdout.
    Called once per pipeline run before generation starts -- surfaces the
    root cause of overlong prompts without requiring a tokenizer dependency.

    Estimates are intentionally conservative (chars/4); real counts will be
    slightly lower with BPE tokenizers but this is a reliable upper bound.
    """
    idea         = context.get("idea", "")
    strategy     = context.get("strategy", "")
    finance      = context.get("finance", "")
    marketing    = context.get("marketing", "")
    risk         = context.get("risk", "")
    council_str  = context.get("council_str", "")
    reviewer     = context.get("reviewer", "")
    critic       = context.get("critic", "")
    rules_json   = context.get("rules_json", "")
    scores_json  = context.get("scores_json", "")

    # Business Plan & Tier 2 reports use capped versions -- reflect that in estimates
    bp_ctx = (
        idea + strategy[:2500] + finance[:2500] + marketing[:2000]
        + risk[:1500] + council_str[:1500] + reviewer[:1000] + critic[:1000]
    )
    exec_ctx    = idea + strategy + finance + marketing + risk + council_str + reviewer + critic + scores_json
    swot_ctx    = idea + strategy + risk + council_str + critic + marketing
    fin_ctx     = idea + finance + strategy + marketing + rules_json + scores_json
    inv_ctx     = idea + scores_json + critic + reviewer + council_str + rules_json + strategy[:1500] + finance[:1500]
    bmc_ctx     = idea + strategy[:2000] + finance[:2500] + marketing[:2000] + risk[:1500] + council_str[:1500]
    pestle_ctx  = idea + strategy[:2000] + risk[:2500] + council_str[:1500] + reviewer[:1000] + critic[:1000]
    porters_ctx = idea + strategy[:2500] + finance[:1500] + risk[:1500] + council_str[:1500] + critic[:1000]
    comp_ctx    = idea + strategy[:2500] + marketing[:2000] + critic[:1000]
    mktgtm_ctx  = idea + marketing + strategy[:2000] + finance[:2000] + council_str[:1500]
    riskmat_ctx = idea + risk + critic + rules_json + council_str[:1500]
    esg_ctx     = idea + risk[:2500] + strategy[:2000] + rules_json
    pitch_ctx   = idea + strategy[:2500] + finance[:2500] + marketing[:2000] + scores_json

    print(
        "[Report Generator] Estimated input token counts per report type:\n"
        f"  Executive Summary                : ~{_estimate_tokens(exec_ctx):,} tokens\n"
        f"  SWOT Analysis                    : ~{_estimate_tokens(swot_ctx):,} tokens\n"
        f"  Financial Projection             : ~{_estimate_tokens(fin_ctx):,} tokens\n"
        f"  Investment Readiness             : ~{_estimate_tokens(inv_ctx):,} tokens\n"
        f"  Business Model Canvas            : ~{_estimate_tokens(bmc_ctx):,} tokens\n"
        f"  PESTLE Analysis                  : ~{_estimate_tokens(pestle_ctx):,} tokens\n"
        f"  Porter's Five Forces             : ~{_estimate_tokens(porters_ctx):,} tokens\n"
        f"  Competitor Analysis              : ~{_estimate_tokens(comp_ctx):,} tokens\n"
        f"  Marketing Plan & Go-To-Market    : ~{_estimate_tokens(mktgtm_ctx):,} tokens\n"
        f"  Risk Assessment & Mitigation     : ~{_estimate_tokens(riskmat_ctx):,} tokens\n"
        f"  ESG & Sustainability             : ~{_estimate_tokens(esg_ctx):,} tokens\n"
        f"  Pitch Summary & Investor Deck    : ~{_estimate_tokens(pitch_ctx):,} tokens\n"
        f"  Business Plan (capped)           : ~{_estimate_tokens(bp_ctx):,} tokens  "
        f"[raw uncapped: ~{_estimate_tokens(idea + strategy + finance + marketing + risk + council_str + reviewer + critic):,}]"
    )


def _coerce_schema_fields(report_content: dict, schema_class) -> dict:
    """
    Pre-validate/coerce schema fields before Pydantic validation.
    - Outer key unwrapping: unwrap single outer object keys (e.g. {"PESTLE Analysis": {...}}).
    - Case-insensitive key normalization & alias mapping: match LLM key variations to canonical fields.
    - str fields: convert nested dicts/lists to human-readable strings.
    - List[str] fields: convert dicts or list-of-dicts substructures to clean string lists.
    """
    #  0. Unwrap Single Top-Level Key (e.g. {"PESTLE Analysis": {...}} or {"pestle": {...}}) 
    while isinstance(report_content, dict) and len(report_content) == 1:
        single_key = next(iter(report_content))
        inner_val = report_content[single_key]
        if isinstance(inner_val, dict) and inner_val:
            print(f"[Report Generator] Auto-unwrapping outer key '{single_key}' -> inner dict")
            report_content = inner_val
        else:
            break

    if not isinstance(report_content, dict):
        return report_content

    schema_fields = schema_class.model_fields
    for canonical_field in schema_fields.keys():
        if canonical_field not in report_content or not report_content[canonical_field]:
            matched_key = None
            # 1. Exact case-insensitive match
            for key_in_dict in list(report_content.keys()):
                if key_in_dict.lower() == canonical_field.lower() and report_content[key_in_dict]:
                    matched_key = key_in_dict
                    break

            # 2. Substring / suffix match (e.g. "Legal Factors" -> "legal")
            if not matched_key:
                for key_in_dict in list(report_content.keys()):
                    k_low = key_in_dict.lower()
                    c_low = canonical_field.lower()
                    if (c_low in k_low or k_low in c_low) and report_content[key_in_dict]:
                        matched_key = key_in_dict
                        break

            if matched_key:
                print(f"[Report Generator] Normalizing key '{matched_key}' -> '{canonical_field}'")
                report_content[canonical_field] = report_content.pop(matched_key)

    #  Key Alias Mapping 
    field_aliases = {
        "marketing_sales_strategy": [
            "marketing_strategy", "marketing_and_sales_strategy", "go_to_market_strategy",
            "sales_strategy", "gtm_strategy", "marketing_sales", "marketing_and_sales"
        ],
        "company_description": ["company_overview", "company_description_and_mission", "company_details"],
        "market_analysis": ["market_overview", "market_and_industry_analysis", "industry_analysis"],
        "operational_plan": ["operations_plan", "operational_roadmap", "operations_and_compliance"],
        "financial_plan": ["financial_projections", "financial_plan_and_pricing", "financials"],
        "risk_register": ["risks", "risk_register_and_mitigations", "risk_mitigation"],
        "direct_competitors": ["competitors", "direct_competition", "main_competitors"],
        "target_customer_profiles": ["icps", "customer_profiles", "ideal_customer_profiles", "target_customers"],
        "outreach_acquisition_channels": ["acquisition_channels", "marketing_channels", "outreach_channels"],
        "regulatory_compliance_risks": ["regulatory_risks", "compliance_risks", "legal_risks"],
        "operational_technical_risks": ["operational_risks", "technical_risks", "technology_risks"],
        "market_financial_risks": ["market_risks", "financial_risks"],
        "environmental_impact_metrics": ["environmental_metrics", "carbon_impact_metrics", "environmental_impact"],
        "social_governance_frameworks": ["social_governance", "esg_frameworks", "governance_frameworks"],
        "regulatory_esg_compliance": ["esg_compliance", "regulatory_compliance"],
        "elevator_pitch_summary": ["elevator_pitch", "pitch_summary", "executive_pitch"],
        "slide_deck_outline": ["deck_outline", "pitch_deck_outline", "slides_outline"],
        "key_investment_highlights": ["investment_highlights", "key_highlights", "investor_highlights"],
        "use_of_funds_breakdown": ["use_of_funds", "funds_breakdown", "capital_allocation"],
    }
    for canonical_field, aliases in field_aliases.items():
        if canonical_field not in report_content or not report_content[canonical_field]:
            for alias in aliases:
                alias_key = alias.lower()
                for key_in_dict in list(report_content.keys()):
                    if key_in_dict.lower() == alias_key and report_content[key_in_dict]:
                        print(f"[Report Generator] Coercing key alias '{key_in_dict}' -> '{canonical_field}'")
                        report_content[canonical_field] = report_content.pop(key_in_dict)
                        break
                if canonical_field in report_content:
                    break

    for field_name, field_info in schema_fields.items():
        if field_name not in report_content:
            continue
        val = report_content[field_name]
        annotation = field_info.annotation
        # Resolve Optional[X] -> X
        origin = getattr(annotation, "__origin__", None)
        args = getattr(annotation, "__args__", ())

        # Check if the field is List[str]
        is_list_str = (
            origin is list and args and args[0] is str
        )
        # Check if the field is str
        is_str = annotation is str

        if is_str and not isinstance(val, str):
            if isinstance(val, dict):
                report_content[field_name] = "\n".join(
                    f"- {k.replace('_', ' ').title()}: {v}" for k, v in val.items()
                )
            elif isinstance(val, list):
                report_content[field_name] = "\n".join(f"- {item}" for item in val)
            else:
                report_content[field_name] = str(val)

        elif is_list_str:
            if isinstance(val, dict):
                # Dict returned for List[str] field (e.g. {"factors": [...], "impact": "..."})
                extracted_list = []
                for k, v in val.items():
                    if isinstance(v, list):
                        extracted_list.extend(str(item) for item in v)
                    else:
                        extracted_list.append(f"{k.replace('_', ' ').title()}: {v}")
                report_content[field_name] = extracted_list if extracted_list else [str(val)]

            elif isinstance(val, list):
                # Ensure every element is a string; if an element is a dict, format it nicely
                normalized_list = []
                for item in val:
                    if isinstance(item, dict):
                        parts = [f"{k.replace('_', ' ').title()}: {v}" for k, v in item.items()]
                        normalized_list.append(", ".join(parts))
                    else:
                        normalized_list.append(str(item))
                report_content[field_name] = normalized_list

            elif isinstance(val, str):
                lines = [
                    line.lstrip("-* ").strip()
                    for line in val.splitlines()
                    if line.strip()
                ]
                report_content[field_name] = lines if lines else [val]
            else:
                report_content[field_name] = [str(val)]

    return report_content


# ---------------------------------------------------------------------------
# Report Type Registry
# Each entry defines the complete generation contract for one report type.
# Prompt templates reference placeholders filled from pipeline context.
# ---------------------------------------------------------------------------

def _build_registry(context: dict) -> dict:
    """
    Build the report registry with context already interpolated into prompt templates.
    `context` keys: idea, strategy, finance, marketing, risk, council_str,
                    reviewer, critic, rules_json, scores_json, overall_score.
    """
    idea           = context["idea"]
    strategy       = context["strategy"]
    finance        = context["finance"]
    marketing      = context["marketing"]
    risk           = context["risk"]
    council_str    = context["council_str"]
    reviewer       = context["reviewer"]
    critic         = context["critic"]
    rules_json     = context["rules_json"]
    scores_json    = context["scores_json"]
    overall_score  = context["overall_score"]

    # Each report type gets a focused prompt that foregrounds the data most
    # relevant to it, reducing token noise for the LLM.

    # Business Plan input caps -- applied before interpolation to bound the
    # total input token count to ~3500-4500 tokens (vs a potential 8000+ with
    # full agent outputs). Caps are generous enough to retain all key content
    # from typical agent outputs (800-1500 tokens each). The Investment
    # Readiness report already uses strategy[:1500] / finance[:1500] as the
    # established pattern -- Business Plan extends this to all 8 context fields.
    bp_strategy    = strategy[:2500]
    bp_finance     = finance[:2500]
    bp_marketing   = marketing[:2000]
    bp_risk        = risk[:1500]
    bp_council     = council_str[:1500]
    bp_reviewer    = reviewer[:1000]
    bp_critic      = critic[:1000]

    return {
        #  1. Executive Summary 
        "Executive Summary": {
            "schema": ExecutiveSummarySchema,
            "export_formats": ["docx", "pptx", "pdf"],
            "max_tokens": 8192,
            "export_mapping": {
                "concept":                    "Venture Concept & Value Proposition",
                "market_opportunity":         "Market Opportunity & Target Segment",
                "strategic_positioning":      "Strategic Positioning & Channels",
                "financial_projection_summary": "Financial Projections & Pricing Models",
                "risk_mitigation_summary":    "Risk Mitigation & Compliance",
                "overall_score":              "Viability Performance Score",
                "key_recommendations":        "Key Boardroom Recommendations",
            },
            "system_prompt": f"""You are the Report Generator for AI Venture Studio.
Generate a structured Executive Summary JSON for this venture. Pull insight from ALL agent
outputs, Council debate, Reviewer briefing, Critic concerns, and the Scoring Engine result.

Primary inputs:
BUSINESS IDEA:
{idea}

STRATEGY ASSESSMENT:
{strategy}

FINANCE ASSESSMENT:
{finance}

MARKETING PLAN:
{marketing}

RISK ASSESSMENT:
{risk}

COUNCIL DEBATE NOTES:
{council_str}

REVIEWER EXECUTIVE BRIEFING:
{reviewer}

CRITIC ADVERSARIAL NOTES:
{critic}

SCORES:
{scores_json}

Target JSON Format -- return ONLY this block wrapped in ```json ... ```:
{{
  "concept": "Detailed venture overview: problem being solved, primary value proposition, and business model summary...",
  "market_opportunity": "ICP analysis, market sizing, competitive landscape, and research evidence supporting demand...",
  "strategic_positioning": "USPs, competitive moat, key marketing channels, and branding vectors...",
  "financial_projection_summary": "Revenue model with named tiers and EXACT numeric prices (e.g. Starter: $49/month), seed capital estimate, and funding overview...",
  "risk_mitigation_summary": "Top 3-4 compliance/regulatory/competitive risks with specific mitigation steps...",
  "overall_score": {overall_score},
  "key_recommendations": [
    "Recommendation 1 drawn from Council or Reviewer...",
    "Recommendation 2 addressing a Critic concern...",
    "Recommendation 3 on go-to-market or compliance..."
  ]
}}
""",
        },

        #  2. SWOT Analysis 
        "SWOT Analysis": {
            "schema": SwotAnalysisSchema,
            "export_formats": ["docx", "pptx", "pdf"],
            "max_tokens": 8192,
            "export_mapping": {
                "strengths":    "Venture Strengths",
                "weaknesses":   "Venture Weaknesses",
                "opportunities": "Market Opportunities",
                "threats":      "External Threats",
            },
            "system_prompt": f"""You are the Report Generator for AI Venture Studio.
Generate a SWOT Analysis JSON. Derive each point directly from the agent assessments below.
Minimum 3 items per quadrant. Each item must be a complete, specific statement.

BUSINESS IDEA:
{idea}

STRATEGY ASSESSMENT:
{strategy}

RISK ASSESSMENT:
{risk}

COUNCIL DEBATE NOTES:
{council_str}

CRITIC ADVERSARIAL NOTES:
{critic}

MARKETING PLAN:
{marketing}

Target JSON Format -- return ONLY this block wrapped in ```json ... ```:
{{
  "strengths": [
    "Specific internal strength 1 grounded in strategy/research...",
    "Specific internal strength 2...",
    "Specific internal strength 3..."
  ],
  "weaknesses": [
    "Specific internal weakness 1 raised by Critic or Risk Agent...",
    "Specific internal weakness 2...",
    "Specific internal weakness 3..."
  ],
  "opportunities": [
    "External opportunity 1 from market/research context...",
    "External opportunity 2...",
    "External opportunity 3..."
  ],
  "threats": [
    "External threat 1 from Risk Agent or Critic...",
    "External threat 2...",
    "External threat 3..."
  ]
}}
""",
        },

        #  3. Financial Projection 
        "Financial Projection": {
            "schema": FinancialProjectionSchema,
            "export_formats": ["docx", "pdf"],
            "max_tokens": 8192,
            "export_mapping": {
                "revenue_model_details": "Monetization & Pricing Tiers",
                "pricing_sanity_check":  "Sanity Check & Margins",
                "capital_requirements":  "Capital Requirements & Budgets",
                "break_even_analysis":   "Break-Even Analysis & Timeline",
                "scoring_context":       "Scoring Engine Financial Assessment",
            },
            "system_prompt": f"""You are the Report Generator for AI Venture Studio.
Generate a Financial Projection JSON grounded primarily in the Finance Agent assessment
and the Business Rules Engine validation result. Reference the Scoring Engine's Financial
Soundness score to calibrate credibility commentary.

BUSINESS IDEA:
{idea}

FINANCE ASSESSMENT (primary source):
{finance}

STRATEGY ASSESSMENT (for pricing cross-reference):
{strategy}

MARKETING PLAN (for pricing cross-reference):
{marketing}

BUSINESS RULES VALIDATION RESULT:
{rules_json}

SCORES (focus on financial_soundness):
{scores_json}

Target JSON Format -- return ONLY this block wrapped in ```json ... ```:
{{
  "revenue_model_details": "Named pricing tiers with EXACT numeric values (e.g. Starter: $49/month, Growth: $199/month, Enterprise: from $499/month). Breakdown of all revenue streams...",
  "pricing_sanity_check": "Assessment of competitive margin adequacy, customer WTP alignment, and any pricing consistency issues flagged by the Business Rules Engine...",
  "capital_requirements": "Seed/working capital estimates, developer headcount and salary budgets, infrastructure costs, and monthly burn rate...",
  "break_even_analysis": "Estimated months to break-even, MRR target, or customer volume milestone. State key assumptions explicitly...",
  "scoring_context": "Financial Soundness score from the Scoring Engine with its rationale, contextualising the projection's overall credibility..."
}}
""",
        },

        #  4. Investment Readiness Report 
        "Investment Readiness Report": {
            "schema": InvestmentReadinessSchema,
            "export_formats": ["docx", "pptx", "pdf"],
            "max_tokens": 8192,
            "export_mapping": {
                "investment_thesis":      "Investment Thesis",
                "scoring_breakdown":      "Scoring Engine Rubric & Breakdown",
                "critic_concerns":        "VC Critiques & Strategic Risks",
                "milestones_funding":     "Milestones & Capital Allocation",
                "rules_validation_summary": "Business Rules Validation Summary",
            },
            "system_prompt": f"""You are the Report Generator for AI Venture Studio.
Generate an Investment Readiness Report JSON written for a VC or angel investor audience.
Draw primarily on the Scoring Engine output, Critic Agent adversarial notes, and Business
Rules Engine validation to form an honest investability assessment.

BUSINESS IDEA:
{idea}

SCORES (primary source):
{scores_json}

CRITIC ADVERSARIAL NOTES (primary source):
{critic}

REVIEWER EXECUTIVE BRIEFING:
{reviewer}

COUNCIL DEBATE NOTES:
{council_str}

BUSINESS RULES VALIDATION RESULT:
{rules_json}

STRATEGY + FINANCE SUMMARY (for thesis grounding):
Strategy: {strategy[:1500]}
Finance: {finance[:1500]}

Target JSON Format -- return ONLY this block wrapped in ```json ... ```:
{{
  "investment_thesis": "Compelling thesis on why this venture is investable: market size, differentiation, timing, and team-market fit argument...",
  "scoring_breakdown": "Viability score X/100 (rationale), Market Fit score Y/100 (rationale), Financial Soundness score Z/100 (rationale). Weighted overall: {overall_score}/100...",
  "critic_concerns": "Top 3-4 adversarial concerns the Critic raised, including assumptions challenged and strategic questions founders must answer convincingly...",
  "milestones_funding": "Phase 1/2/3 milestone targets, preferred funding instrument (pre-seed/seed/Series A), and capital allocation priorities by phase...",
  "rules_validation_summary": "Business Rules Engine outcome: [PASSED/FAILED]. Key findings: pricing consistency status, currency verification, any errors flagged..."
}}
""",
        },

        #  5. Business Plan (last -- heaviest report, 2-call split architecture) 
        # Positioned last so the 4 lighter reports always complete first even
        # if Business Plan requires retry overhead. Input fields are capped
        # (bp_* variables above) to keep input token count  ~4500 tokens.
        # max_tokens=8192 gives the 6-field output (5 prose + risk list)
        # genuine headroom; previously 4096 was marginal for this schema.
        # Generation is handled by _generate_business_plan_split() via the
        # special-case branch in _generate_report_json().
        "Business Plan": {
            "schema": BusinessPlanSchema,
            "export_formats": ["docx", "pdf"],
            "max_tokens": 8192,
            "export_mapping": {
                "company_description":    "Company Description & Mission",
                "market_analysis":        "Market Analysis & Landscape",
                "marketing_sales_strategy": "Marketing & Sales Strategy",
                "operational_plan":       "Operational & Compliance Roadmap",
                "financial_plan":         "Financial Plan & Pricing Structures",
                "risk_register":          "Risk Register & Mitigations",
            },
            # The system_prompt below is used as the FALLBACK single-call
            # path only (if _generate_business_plan_split somehow cannot be
            # called). Normal generation goes through the split-call helper.
            "system_prompt": f"""You are the Report Generator for AI Venture Studio.
Generate a comprehensive Business Plan JSON suitable for bank or investor submission.

BUSINESS IDEA:
{idea}

STRATEGY ASSESSMENT (excerpt):
{bp_strategy}

FINANCE ASSESSMENT (excerpt):
{bp_finance}

MARKETING PLAN (excerpt):
{bp_marketing}

RISK ASSESSMENT (excerpt):
{bp_risk}

COUNCIL DEBATE NOTES (excerpt):
{bp_council}

REVIEWER NOTES (excerpt):
{bp_reviewer}

CRITIC NOTES (excerpt):
{bp_critic}

Target JSON Format -- return ONLY this block wrapped in ```json ... ```:
{{
  "company_description": "Strategic vision, mission statement, problem-solution alignment, and venture model details...",
  "market_analysis": "Industry landscape, direct/indirect competitor matrix, supplier/buyer power, TAM/SAM/SOM estimates...",
  "marketing_sales_strategy": "ICP persona definitions, customer acquisition pipeline, go-to-market channels, branding taglines...",
  "operational_plan": "Execution milestones, critical partnerships, tech/security/privacy compliance checklist, legal requirements...",
  "financial_plan": "Revenue channels, EXACT pricing tier names and numeric values, break-even assumptions, capital burn rate...",
  "risk_register": [
    "Risk 1: [Risk description] -- Mitigation: [specific action]",
    "Risk 2: [Risk description] -- Mitigation: [specific action]",
    "Risk 3: [Risk description] -- Mitigation: [specific action]"
  ]
}}
""",
            # Store capped context in registry so split-call helper can read it
            # without re-interpolating the full context dict.
            "_bp_context": {
                "idea": idea,
                "strategy": bp_strategy,
                "finance": bp_finance,
                "marketing": bp_marketing,
                "risk": bp_risk,
                "council_str": bp_council,
                "reviewer": bp_reviewer,
                "critic": bp_critic,
            },
        },

        #  6. Business Model Canvas 
        "Business Model Canvas": {
            "schema": BusinessModelCanvasSchema,
            "export_formats": ["docx", "pptx", "pdf"],
            "max_tokens": 8192,
            "export_mapping": {
                "value_propositions":     "Value Propositions",
                "customer_segments":      "Customer Segments",
                "channels":               "Channels & Distribution",
                "customer_relationships": "Customer Relationships",
                "revenue_streams":        "Revenue Streams & Pricing Tiers",
                "key_resources":           "Key Resources",
                "key_activities":          "Key Activities",
                "key_partnerships":        "Key Partnerships",
                "cost_structure":         "Cost Structure",
            },
            "system_prompt": f"""You are the Report Generator for AI Venture Studio.
Generate a structured Business Model Canvas JSON (9 building blocks) for this venture.
Pull insight from ALL agent outputs, Council debate, Reviewer briefing, and Critic notes.

BUSINESS IDEA:
{idea}

STRATEGY ASSESSMENT:
{strategy[:2000]}

FINANCE ASSESSMENT:
{finance[:2500]}

MARKETING PLAN:
{marketing[:2000]}

RISK ASSESSMENT:
{risk[:1500]}

COUNCIL DEBATE NOTES:
{council_str[:1500]}

Target JSON Format -- return ONLY this block wrapped in ```json ... ```:
{{
  "value_propositions": [
    "Core value proposition 1...",
    "Core value proposition 2..."
  ],
  "customer_segments": [
    "Target segment 1 (e.g. UK SMEs 20-500 employees)...",
    "Target segment 2..."
  ],
  "channels": [
    "Direct sales, digital marketing, utility provider integrations..."
  ],
  "customer_relationships": [
    "Self-service onboarding, dedicated customer success for enterprise..."
  ],
  "revenue_streams": [
    "Tiered subscription model (Starter, Growth, Enterprise with numeric pricing)..."
  ],
  "key_resources": [
    "Utility API connection framework, automated emissions calculation engine..."
  ],
  "key_activities": [
    "Platform engineering, compliance audit automation, utility integration management..."
  ],
  "key_partnerships": [
    "Utility providers, industry compliance bodies, sustainability auditors..."
  ],
  "cost_structure": [
    "R&D / engineering salaries, API infrastructure, customer acquisition..."
  ]
}}
""",
        },

        #  7. PESTLE Analysis 
        "PESTLE Analysis": {
            "schema": PestleAnalysisSchema,
            "export_formats": ["docx", "pptx", "pdf"],
            "max_tokens": 8192,
            "export_mapping": {
                "political":     "Political Factors",
                "economic":      "Economic Factors",
                "social":        "Social & Demographic Factors",
                "technological": "Technological Factors",
                "legal":         "Legal & Regulatory Factors",
                "environmental": "Environmental Factors",
            },
            "system_prompt": f"""You are the Report Generator for AI Venture Studio.
Generate a structured PESTLE Analysis JSON covering macro-environmental drivers for this venture.
Pull insight from Strategy, Risk, Rules Engine, and Critic assessments.

CRITICAL: Return a JSON object with exactly these six top-level keys: political, economic, social, technological, legal, environmental -- do not wrap the response in any outer object or key (such as "PESTLE Analysis" or "pestle"). Each of the six keys MUST contain a list of strings.

Target JSON Format -- return ONLY this block wrapped in ```json ... ```:
{{
  "political": [
    "UK Environment Act 2021 mandates and Net-Zero 2050 targets...",
    "Government subsidies and green tax incentives for SMEs..."
  ],
  "economic": [
    "Inflationary pressures impacting SME software budgets...",
    "Growth in capital allocation for sustainability compliance software..."
  ],
  "social": [
    "Corporate ESG consciousness and customer demand for green supply chains...",
    "Shift toward transparent corporate environmental disclosure..."
  ],
  "technological": [
    "Utility provider API infrastructure readiness for automated data ingestion...",
    "Data encryption and cloud security standards for sensitive customer feeds..."
  ],
  "legal": [
    "Streamlined Energy and Carbon Reporting (SECR) disclosure laws...",
    "UK GDPR and Data Protection Act compliance requirements..."
  ],
  "environmental": [
    "Transition toward mandatory Scope 1, Scope 2, and Scope 3 carbon reporting...",
    "Net-zero auditing and corporate ESG compliance frameworks..."
  ]
}}

BUSINESS IDEA:
{idea}

STRATEGY ASSESSMENT:
{strategy[:2000]}

RISK ASSESSMENT:
{risk[:2500]}

COUNCIL DEBATE NOTES:
{council_str[:1500]}

REVIEWER BRIEFING:
{reviewer[:1000]}

CRITIC ADVERSARIAL NOTES:
{critic[:1000]}
""",
        },

        #  8. Porter's Five Forces 
        "Porter's Five Forces": {
            "schema": PortersFiveForcesSchema,
            "export_formats": ["docx", "pptx", "pdf"],
            "max_tokens": 8192,
            "export_mapping": {
                "threat_of_new_entrants":        "Threat of New Entrants",
                "bargaining_power_of_buyers":    "Bargaining Power of Buyers",
                "bargaining_power_of_suppliers": "Bargaining Power of Suppliers",
                "threat_of_substitutes":        "Threat of Substitutes",
                "competitive_rivalry":          "Competitive Rivalry Among Existing Players",
            },
            "system_prompt": f"""You are the Report Generator for AI Venture Studio.
Generate a structured Porter's Five Forces analysis JSON evaluating industry competitive dynamics.
Pull insight from Strategy, Finance, Risk, Council, and Critic assessments.

BUSINESS IDEA:
{idea}

STRATEGY ASSESSMENT:
{strategy[:2500]}

FINANCE ASSESSMENT:
{finance[:1500]}

RISK ASSESSMENT:
{risk[:1500]}

COUNCIL DEBATE NOTES:
{council_str[:1500]}

CRITIC ADVERSARIAL NOTES:
{critic[:1000]}

Target JSON Format -- return ONLY this block wrapped in ```json ... ```:
{{
  "threat_of_new_entrants": "Evaluation of barriers to entry, API complexity, capital needs, and brand moats...",
  "bargaining_power_of_buyers": "Evaluation of buyer price sensitivity, switching costs, and alternative options...",
  "bargaining_power_of_suppliers": "Evaluation of utility API supplier lock-in, data access costs, and provider dependencies...",
  "threat_of_substitutes": "Evaluation of manual spreadsheets, traditional consulting, and legacy software substitutes...",
  "competitive_rivalry": "Evaluation of incumbent competitor count, market growth rate, and rivalry intensity..."
}}
""",
        },

        # ── 9. Competitor Analysis ──────────────────────────────────────────
        "Competitor Analysis": {
            "schema": CompetitorAnalysisSchema,
            "export_formats": ["docx", "pptx", "pdf"],
            "max_tokens": 8192,
            "export_mapping": {
                "direct_competitors":      "Direct Competitors & Strengths/Weaknesses",
                "indirect_competitors":    "Indirect Substitutes & Legacy Alternatives",
                "competitive_advantages":  "Core Competitive Advantages & Moat",
                "market_positioning":      "Strategic Market Positioning & Defense",
            },
            "system_prompt": f"""You are the Report Generator for AI Venture Studio.
Generate a structured Competitor Analysis JSON evaluating the competitive landscape for this venture.
Pull insight from Strategy, Research, Marketing, and Critic assessments.

CRITICAL: Return a JSON object with exactly these four top-level keys: direct_competitors, indirect_competitors, competitive_advantages, market_positioning -- do not wrap the response in any outer object or key.

Target JSON Format -- return ONLY this block wrapped in ```json ... ```:
{{
  "direct_competitors": [
    "Direct competitor 1: key offerings, market share, strengths and weaknesses...",
    "Direct competitor 2: pricing model and customer segment overlap..."
  ],
  "indirect_competitors": [
    "Indirect substitute 1: manual Excel spreadsheets and internal compliance teams...",
    "Indirect substitute 2: boutique sustainability consulting firms..."
  ],
  "competitive_advantages": [
    "Proprietary API automation for direct utility data ingestion...",
    "Tiered SME pricing model with significantly lower TCO..."
  ],
  "market_positioning": "Strategic positioning statement defining how the venture occupies the mid-market SME carbon compliance niche..."
}}

BUSINESS IDEA:
{idea}

STRATEGY ASSESSMENT:
{strategy[:2500]}

MARKETING PLAN:
{marketing[:2000]}

CRITIC ADVERSARIAL NOTES:
{critic[:1000]}
""",
        },

        #  10. Marketing Plan & Go-To-Market 
        "Marketing Plan & Go-To-Market": {
            "schema": MarketingGtmSchema,
            "export_formats": ["docx", "pptx", "pdf"],
            "max_tokens": 8192,
            "export_mapping": {
                "target_customer_profiles":      "Ideal Customer Profiles (ICPs)",
                "outreach_acquisition_channels": "Customer Acquisition & Outreach Channels",
                "brand_positioning_messaging":   "Brand Messaging & Value Proposition",
                "growth_campaign_roadmap":       "Go-To-Market Growth Roadmap & Milestones",
            },
            "system_prompt": f"""You are the Report Generator for AI Venture Studio.
Generate a structured Marketing Plan & Go-To-Market JSON outlining customer acquisition strategy.
Pull insight from Marketing, Strategy, Finance, and Council debate notes.

CRITICAL: Return a JSON object with exactly these four top-level keys: target_customer_profiles, outreach_acquisition_channels, brand_positioning_messaging, growth_campaign_roadmap -- do not wrap the response in any outer object or key.

Target JSON Format -- return ONLY this block wrapped in ```json ... ```:
{{
  "target_customer_profiles": [
    "ICP 1: UK-based SMEs (20-500 employees) subject to SECR/Environment Act reporting...",
    "ICP 2: Sustainability officers and operations managers at mid-sized firms..."
  ],
  "outreach_acquisition_channels": [
    "Digital inbound marketing: targeted LinkedIn and Google Ads campaigns...",
    "Channel partnerships: utility providers and industry trade associations..."
  ],
  "brand_positioning_messaging": "Core brand positioning narrative establishing the venture as the most effortless, automated compliance partner for UK SMEs...",
  "growth_campaign_roadmap": [
    "Phase 1 (Months 1-6): Launch beta pilot with 50 UK SMEs, refine utility API integrations...",
    "Phase 2 (Months 7-12): Scale inbound marketing and initiate trade body partnerships...",
    "Phase 3 (Months 13-24): Expand enterprise tier and cross-border UK/EU compliance features..."
  ]
}}

BUSINESS IDEA:
{idea}

MARKETING PLAN (primary source):
{marketing}

STRATEGY ASSESSMENT:
{strategy[:2000]}

FINANCE ASSESSMENT (pricing context):
{finance[:2000]}

COUNCIL DEBATE NOTES:
{council_str[:1500]}
""",
        },

        #  11. Risk Assessment & Mitigation Matrix 
        "Risk Assessment & Mitigation Matrix": {
            "schema": RiskAssessmentMatrixSchema,
            "export_formats": ["docx", "pdf"],
            "max_tokens": 8192,
            "export_mapping": {
                "regulatory_compliance_risks":     "Regulatory & Legal Compliance Risks",
                "operational_technical_risks":     "Operational & Technological Risks",
                "market_financial_risks":         "Market & Financial Risks",
                "critic_adversarial_vulnerabilities": "Critic Adversarial Vulnerabilities & Action Items",
            },
            "system_prompt": f"""You are the Report Generator for AI Venture Studio.
Generate a structured Risk Assessment & Mitigation Matrix JSON detailing risks and mitigations.
Pull insight from Risk Agent, Critic Agent, Business Rules Engine, and Council debate notes.

CRITICAL: Return a JSON object with exactly these four top-level keys: regulatory_compliance_risks, operational_technical_risks, market_financial_risks, critic_adversarial_vulnerabilities -- do not wrap the response in any outer object or key.

Target JSON Format -- return ONLY this block wrapped in ```json ... ```:
{{
  "regulatory_compliance_risks": [
    "Risk: Evolving UK SECR / Environment Act standards. Mitigation: Maintain continuous legal monitoring and modular compliance engine updates...",
    "Risk: GDPR / Data Privacy exposure. Mitigation: Implement zero-trust architecture and automated PII anonymization..."
  ],
  "operational_technical_risks": [
    "Risk: Utility provider API rate-limits or feed downtime. Mitigation: Asynchronous batch queueing and fallback manual upload processing...",
    "Risk: Cloud infrastructure scaling bottlenecks. Mitigation: Serverless microservices architecture with auto-scaling database read-replicas..."
  ],
  "market_financial_risks": [
    "Risk: SME budget contraction during macro inflation. Mitigation: Low-friction starter pricing tier (GBP 299/mo) with immediate ROI demonstration...",
    "Risk: Incumbent software platform competitive response. Mitigation: Focus on specialized utility API integrations that generalist CRMs lack..."
  ],
  "critic_adversarial_vulnerabilities": [
    "Vulnerability: Over-reliance on voluntary SME compliance adoption. Action Item: Target industries with mandatory SECR audit duties first...",
    "Vulnerability: Customer acquisition cost (CAC) inflation. Action Item: Leverage utility partner co-marketing to reduce direct ad spend..."
  ]
}}

BUSINESS IDEA:
{idea}

RISK ASSESSMENT (primary source):
{risk}

CRITIC ADVERSARIAL NOTES (primary source):
{critic}

BUSINESS RULES VALIDATION RESULT:
{rules_json}

COUNCIL DEBATE NOTES:
{council_str[:1500]}
""",
        },

        # ── 12. ESG & Sustainability Recommendations ───────────────────────
        "ESG & Sustainability Recommendations": {
            "schema": EsgSustainabilitySchema,
            "export_formats": ["docx", "pptx", "pdf"],
            "max_tokens": 8192,
            "export_mapping": {
                "environmental_impact_metrics": "Environmental & Carbon Emission Impact",
                "social_governance_frameworks": "Social Impact & Governance Frameworks",
                "regulatory_esg_compliance":    "Regulatory ESG Compliance & Audit Readiness",
                "sustainability_roadmap":       "Sustainability Implementation Roadmap",
            },
            "system_prompt": f"""You are the Report Generator for AI Venture Studio.
Generate a structured ESG & Sustainability Recommendations JSON detailing environmental targets and compliance frameworks.
Pull insight from Risk Agent, Strategy Agent, Business Rules Engine, and Council notes.

CRITICAL: Return a JSON object with exactly these four top-level keys: environmental_impact_metrics, social_governance_frameworks, regulatory_esg_compliance, sustainability_roadmap -- do not wrap the response in any outer object or key.

Target JSON Format -- return ONLY this block wrapped in ```json ... ```:
{{
  "environmental_impact_metrics": [
    "Scope 1 & Scope 2 direct emission reduction via automated utility data tracking...",
    "Scope 3 supply chain carbon accounting automation for UK SMEs..."
  ],
  "social_governance_frameworks": [
    "Ethical supply chain data governance and zero-trust customer data privacy...",
    "Board-level ESG oversight committee and transparent stakeholder reporting..."
  ],
  "regulatory_esg_compliance": [
    "UK Environment Act 2021 compliance disclosure readiness for firms >250 employees...",
    "Streamlined Energy and Carbon Reporting (SECR) alignment and audit trail generation..."
  ],
  "sustainability_roadmap": [
    "Phase 1 (Months 1-6): Launch automated Scope 1/2 utility data ingestion...",
    "Phase 2 (Months 7-12): Implement Scope 3 supplier carbon footprint calculations...",
    "Phase 3 (Months 13-24): Achieve ISO 14064 carbon verification certification for platform outputs..."
  ]
}}

BUSINESS IDEA:
{idea}

RISK ASSESSMENT (primary source):
{risk[:2500]}

STRATEGY ASSESSMENT:
{strategy[:2000]}

BUSINESS RULES VALIDATION RESULT:
{rules_json}
""",
        },

        # ── 13. Pitch Summary & Investor Deck Outline ─────────────────────
        "Pitch Summary & Investor Deck Outline": {
            "schema": PitchSummaryDeckSchema,
            "export_formats": ["docx", "pptx", "pdf"],
            "max_tokens": 8192,
            "export_mapping": {
                "elevator_pitch_summary":     "Elevator Pitch Summary",
                "slide_deck_outline":         "10-Slide Investor Deck Structure",
                "key_investment_highlights": "Core Investment Highlights & Moat",
                "use_of_funds_breakdown":     "Capital Allocation & Use of Funds",
            },
            "system_prompt": f"""You are the Report Generator for AI Venture Studio.
Generate a structured Pitch Summary & Investor Deck Outline JSON defining investor presentation strategy.
Pull insight from Strategy, Finance, Marketing, and Analytics Scores.

CRITICAL: Return a JSON object with exactly these four top-level keys: elevator_pitch_summary, slide_deck_outline, key_investment_highlights, use_of_funds_breakdown -- do not wrap the response in any outer object or key.

Target JSON Format -- return ONLY this block wrapped in ```json ... ```:
{{
  "elevator_pitch_summary": "EcoSphere is an automated carbon compliance SaaS platform that connects directly to utility provider APIs, enabling UK SMEs to automate SECR disclosures with zero manual data entry overhead.",
  "slide_deck_outline": [
    "Slide 1: Title & Vision -- EcoSphere: Automated Carbon Compliance for SMEs",
    "Slide 2: Problem -- UK SMEs face mandatory carbon disclosure laws with expensive, manual reporting overhead",
    "Slide 3: Solution -- Direct-to-utility API data capture with automated Scope 1-3 audit reports",
    "Slide 4: Market Size -- TAM GBP 5B UK/EU SME carbon accounting software market",
    "Slide 5: Product & Tech -- Proprietary utility API connectors with zero-trust encryption",
    "Slide 6: Business Model -- SaaS subscription tiers (GBP 299/mo Starter, GBP 499/mo Growth)",
    "Slide 7: Go-To-Market -- Utility co-marketing partnerships and digital inbound campaigns",
    "Slide 8: Competition -- First-mover automated API capture vs manual Excel spreadsheets and generalist CRMs",
    "Slide 9: Financials -- 75% Gross Margin, break-even at Month 14, CAC GBP 500 / LTV GBP 5,000",
    "Slide 10: Team & The Ask -- Seeking GBP 500k seed funding for product engineering and GTM expansion"
  ],
  "key_investment_highlights": [
    "Regulatory Tailwinds: UK Environment Act 2021 mandates create mandatory SME customer demand",
    "Defensive Moat: Direct utility provider API integrations eliminate manual competitor workarounds",
    "High Margins: 75% gross profit margin with 10x LTV/CAC ratio"
  ],
  "use_of_funds_breakdown": [
    "40% Product & Engineering: Expand utility provider API integrations and Scope 3 LCA engine",
    "35% Sales & Marketing: Scale inbound digital campaigns and utility co-marketing partnerships",
    "15% Regulatory & Security: Achieve ISO 14064 verification and zero-trust security audit",
    "10% Working Capital & Reserve: Maintain 18-month operational runway"
  ]
}}

BUSINESS IDEA:
{idea}

STRATEGY ASSESSMENT:
{strategy[:2500]}

FINANCE ASSESSMENT:
{finance[:2500]}

MARKETING PLAN:
{marketing[:2000]}

ANALYTICAL SCORES:
{scores_json}
""",
        },
    }


# ---------------------------------------------------------------------------
# JSON generation helper with repair retry
# ---------------------------------------------------------------------------

JSON_REPAIR_PROMPT = """
The following JSON response was truncated or malformed (it may have been cut off mid-string or contain unescaped characters/syntax errors).
Return the COMPLETE, VALID JSON object below, fixing any truncation, missing brackets/quotes, or unescaped control characters.
Continue and complete any cut-off strings or fields. Do NOT truncate or drop required fields.
Wrap your output in ```json ... ``` fences.

Malformed input:
{malformed}
"""


# ---------------------------------------------------------------------------
# Business Plan: 2-call split-architecture generator
# ---------------------------------------------------------------------------

def _generate_business_plan_split(
    bp_ctx: dict,
    project_id: str,
    max_tokens: int = 4096,
    preferred: str = "gemini",
    label_suffix: str = "",
) -> dict:
    """
    Generates the Business Plan in two sequential LLM calls instead of one.

    Splitting the 6-field Business Plan schema into two focused calls:
      Call A -- Company & Market  : company_description + market_analysis
      Call B -- Ops & Finance     : marketing_sales_strategy + operational_plan
                                   + financial_plan + risk_register

    Each call uses at most half of the input context and targets 3 or fewer
    output fields, keeping both input and output token budgets well within
    the 4096-token limit per call.

    Args:
        bp_ctx: Capped context dict with keys: idea, strategy, finance,
                marketing, risk, council_str, reviewer, critic.
        project_id: Pipeline project ID (for agent_logs foreign key).
        max_tokens: Per-call output token budget (default 4096).
        preferred: Provider preference passed to call_llm.
        label_suffix: Appended to agent_name in logs (e.g. " [Reduced]").

    Returns:
        Merged dict with all 6 BusinessPlanSchema fields.

    Raises:
        ValueError / json.JSONDecodeError: if either call fails after its
        own repair retry -- caller must handle.
    """
    idea        = bp_ctx["idea"]
    strategy    = bp_ctx["strategy"]
    finance     = bp_ctx["finance"]
    marketing   = bp_ctx["marketing"]
    risk        = bp_ctx["risk"]
    council_str = bp_ctx["council_str"]
    reviewer    = bp_ctx["reviewer"]
    critic      = bp_ctx["critic"]

    #  Call A: Company Description + Market Analysis 
    prompt_a = f"""You are the Report Generator for AI Venture Studio.
Generate PART 1 of a Business Plan JSON covering company description and market analysis.
CRITICAL: Return ONLY a JSON block containing EXACTLY both of these two required fields:
"company_description" and "market_analysis".

BUSINESS IDEA:
{idea}

STRATEGY ASSESSMENT:
{strategy}

FINANCE ASSESSMENT (for context):
{finance[:1200]}

COUNCIL DEBATE NOTES:
{council_str}

Target JSON Format -- return ONLY this block wrapped in ```json ... ```:
{{
  "company_description": "Strategic vision, mission statement, problem-solution alignment, and venture model details...",
  "market_analysis": "Industry landscape, direct/indirect competitor matrix, supplier/buyer power, TAM/SAM/SOM estimates..."
}}
"""

    raw_a = call_llm(
        prompt="Generate Business Plan Part 1 (Company & Market) as instructed.",
        system_prompt=prompt_a,
        preferred_provider=preferred,
        project_id=project_id,
        agent_name=f"Business Plan Generator [Part A]{label_suffix}",
        max_tokens=max_tokens,
    )
    if isinstance(raw_a, dict) and raw_a.get("status") == "failed":
        raise ValueError(f"Business Plan Part A LLM call failed: {raw_a['error']}")

    cleaned_a = extract_json_block(raw_a)
    try:
        part_a = safe_parse_json(cleaned_a)
    except Exception as err_a:
        print(f"[Business Plan Split] Part A JSON error: {err_a}. Attempting repair...")
        repair_a = call_llm(
            prompt=JSON_REPAIR_PROMPT.format(malformed=cleaned_a[:6000]),
            system_prompt="You are a JSON repair assistant. Complete and repair truncated JSON. Return only valid JSON wrapped in ```json ... ``` fences.",
            preferred_provider=preferred,
            project_id=project_id,
            agent_name=f"Business Plan Generator [Part A Repair]{label_suffix}",
            max_tokens=max(max_tokens, 4096),
        )
        if isinstance(repair_a, dict) and repair_a.get("status") == "failed":
            raise ValueError(f"Business Plan Part A repair call failed: {repair_a['error']}")
        part_a = safe_parse_json(repair_a)

    #  Call B: Marketing, Ops, Finance & Risk 
    prompt_b = f"""You are the Report Generator for AI Venture Studio.
Generate PART 2 of a Business Plan JSON covering marketing/sales strategy,
operational plan, financial plan, and risk register.
CRITICAL: Return ONLY a JSON block containing EXACTLY all four of these required fields:
"marketing_sales_strategy", "operational_plan", "financial_plan", and "risk_register".

BUSINESS IDEA:
{idea}

FINANCE ASSESSMENT (primary source):
{finance}

MARKETING PLAN:
{marketing}

RISK ASSESSMENT:
{risk}

REVIEWER NOTES:
{reviewer}

CRITIC NOTES:
{critic}

Target JSON Format -- return ONLY this block wrapped in ```json ... ```:
{{
  "marketing_sales_strategy": "ICP persona definitions, customer acquisition pipeline, go-to-market channels, branding taglines...",
  "operational_plan": "Execution milestones, critical partnerships, tech/security/privacy compliance checklist, legal requirements...",
  "financial_plan": "Revenue channels, EXACT pricing tier names and numeric values, break-even assumptions, capital burn rate...",
  "risk_register": [
    "Risk 1: [Risk description] -- Mitigation: [specific action]",
    "Risk 2: [Risk description] -- Mitigation: [specific action]",
    "Risk 3: [Risk description] -- Mitigation: [specific action]"
  ]
}}
"""

    raw_b = call_llm(
        prompt="Generate Business Plan Part 2 (Marketing & Sales, Ops, Finance & Risk) as instructed.",
        system_prompt=prompt_b,
        preferred_provider=preferred,
        project_id=project_id,
        agent_name=f"Business Plan Generator [Part B]{label_suffix}",
        max_tokens=max_tokens,
    )
    if isinstance(raw_b, dict) and raw_b.get("status") == "failed":
        raise ValueError(f"Business Plan Part B LLM call failed: {raw_b['error']}")

    cleaned_b = extract_json_block(raw_b)
    try:
        part_b = safe_parse_json(cleaned_b)
    except Exception as err_b:
        print(f"[Business Plan Split] Part B JSON error: {err_b}. Attempting repair...")
        repair_b = call_llm(
            prompt=JSON_REPAIR_PROMPT.format(malformed=cleaned_b[:6000]),
            system_prompt="You are a JSON repair assistant. Complete and repair truncated JSON. Return only valid JSON wrapped in ```json ... ``` fences.",
            preferred_provider=preferred,
            project_id=project_id,
            agent_name=f"Business Plan Generator [Part B Repair]{label_suffix}",
            max_tokens=max(max_tokens, 4096),
        )
        if isinstance(repair_b, dict) and repair_b.get("status") == "failed":
            raise ValueError(f"Business Plan Part B repair call failed: {repair_b['error']}")
        part_b = safe_parse_json(repair_b)

    #  Merge A + B into full Business Plan dict 
    part_a_clean = {k: v for k, v in part_a.items() if not k.startswith("_")}
    part_b_clean = {k: v for k, v in part_b.items() if not k.startswith("_")}
    
    # Key union of both calls
    merged = {**part_a_clean, **part_b_clean}
    # Attach raw parts for diagnostic checkpoint logging if validation fails downstream
    merged["_raw_part_a"] = part_a_clean
    merged["_raw_part_b"] = part_b_clean
    return merged


# ---------------------------------------------------------------------------
# JSON generation helper -- routes Business Plan through split-call path
# ---------------------------------------------------------------------------

def _generate_report_json(
    report_type: str,
    config: dict,
    project_id: str,
    reduced_config: Optional[dict] = None,
) -> dict:
    """
    Calls the LLM to generate one report's JSON.

    For Business Plan specifically, this uses a 2-call split architecture
    (_generate_business_plan_split) instead of a single large call:
      - Reduces both input and output token pressure per call.
      - Each sub-call has its own JSON repair retry.
      - On total failure of the split path, retries once with summarized
        (800-char) context before giving up -- the "retry-with-repair" path
        described in the task spec.

    For all other report types:
      1. First call uses the full system_prompt with the report's max_tokens.
      2. On JSON error or LLM failure, attempts a JSON repair retry (if raw text exists).
      3. On total failure of Attempt 1 & 2, retries once with summarized (800-char) context
         (Attempt 3) as a final safety net for ALL report types before marking as failed.

    Args:
        config: Registry entry dict (must contain system_prompt; optionally
                max_tokens, preferred_provider, _bp_context).
        reduced_config: Pre-built registry entry using 800-char summarized context.
    Returns:
        Parsed report_content dict ready for schema coercion and Pydantic validation.
    Raises:
        ValueError / json.JSONDecodeError: on total failure.
    """
    max_tokens = config.get("max_tokens", 8192)
    preferred   = config.get("preferred_provider", "gemini")

    #  Business Plan: split-call path 
    if report_type == "Business Plan":
        bp_ctx = config.get("_bp_context")
        if not bp_ctx:
            # Defensive fallback: should never happen if registry is correct
            raise ValueError(
                "Business Plan registry entry missing '_bp_context'. "
                "This is a configuration error in _build_registry()."
            )

        #  Split-call attempt 
        try:
            print("[Report Generator] 'Business Plan' -- using 2-call split architecture.")
            return _generate_business_plan_split(
                bp_ctx=bp_ctx,
                project_id=project_id,
                max_tokens=max_tokens // 2,  # Each call gets half the budget
                preferred=preferred,
            )
        except Exception as split_err:
            print(
                f"[Report Generator] 'Business Plan' -- split-call path failed: {split_err}. "
                f"Retrying with summarized (800-char) context..."
            )

        #  Context-reduced fallback retry 
        # Truncate every field to 800 chars -- worst-case the report will be
        # less detailed, but it will complete rather than fail entirely.
        reduced_ctx = {
            "idea":        bp_ctx["idea"][:800],
            "strategy":    bp_ctx["strategy"][:800],
            "finance":     bp_ctx["finance"][:800],
            "marketing":   bp_ctx["marketing"][:800],
            "risk":        bp_ctx["risk"][:800],
            "council_str": bp_ctx["council_str"][:800],
            "reviewer":    bp_ctx["reviewer"][:400],
            "critic":      bp_ctx["critic"][:400],
        }
        print("[Report Generator] 'Business Plan' -- reduced-context retry: "
              f"~{_estimate_tokens(''.join(reduced_ctx.values())):,} input tokens.")
        # Each sub-call on reduced context gets 2048 tokens -- plenty for
        # shorter input -> shorter expected output.
        return _generate_business_plan_split(
            bp_ctx=reduced_ctx,
            project_id=project_id,
            max_tokens=2048,
            preferred=preferred,
            label_suffix=" [Reduced]",
        )
        # If this also raises, it propagates to the caller's except clause.

    #  All other report types: standard single-call path 

    # Extract JSON schema if schema class is declared in config
    response_schema = None
    if "schema" in config and hasattr(config["schema"], "model_json_schema"):
        try:
            response_schema = config["schema"].model_json_schema()
        except Exception:
            response_schema = None

    raw_text = None
    #  Attempt 1: normal generation 
    try:
        raw_response = call_llm(
            prompt="Generate the report as instructed.",
            system_prompt=config["system_prompt"],
            preferred_provider=preferred,
            project_id=project_id,
            agent_name=f"{report_type} Generator",
            max_tokens=max_tokens,
            response_schema=response_schema,
            json_mode=True,
        )

        if isinstance(raw_response, dict) and raw_response.get("status") == "failed":
            raise ValueError(raw_response["error"])

        raw_text = raw_response
        return safe_parse_json(raw_text)

    except Exception as first_err:
        print(
            f"[Report Generator] '{report_type}' -- Attempt 1 failed ({first_err})."
        )

    #  Attempt 2: JSON repair retry (if Attempt 1 produced raw text) 
    if raw_text and isinstance(raw_text, str) and raw_text.strip():
        print(f"[Report Generator] '{report_type}' -- Attempting Attempt 2: JSON repair retry...")
        try:
            cleaned = extract_json_block(raw_text)
            repair_prompt = JSON_REPAIR_PROMPT.format(malformed=cleaned[:6000])
            repair_max_tokens = max(max_tokens, 8192)

            repaired_text = call_llm(
                prompt=repair_prompt,
                system_prompt="You are a JSON repair assistant. Complete and repair truncated JSON. Return only valid JSON wrapped in ```json ... ``` fences.",
                preferred_provider=preferred,
                project_id=project_id,
                agent_name=f"{report_type} Generator [JSON Repair]",
                max_tokens=repair_max_tokens,
            )

            if not (isinstance(repaired_text, dict) and repaired_text.get("status") == "failed"):
                return safe_parse_json(repaired_text)
        except Exception as repair_err:
            print(f"[Report Generator] '{report_type}' -- Attempt 2 JSON repair failed: {repair_err}.")

    #  Attempt 3: Reduced-Context Fallback Retry (Final Safety Net) 
    # Triggered if Attempt 1 and 2 failed, OR if full LLM provider exhaustion occurred (e.g. rate-limit failure)
    reduced_sys_prompt = None
    if reduced_config and "system_prompt" in reduced_config:
        reduced_sys_prompt = reduced_config["system_prompt"]
    else:
        reduced_sys_prompt = config["system_prompt"] + "\n\nCRITICAL: Keep response concise and complete. Ensure all JSON keys are present and valid."

    print(
        f"[Report Generator] '{report_type}' -- primary/repair attempts failed. "
        f"Retrying with Attempt 3: reduced-context (800-char summarized context) fallback retry..."
    )

    reduced_response = call_llm(
        prompt="Generate a concise, complete JSON report as instructed. Ensure all JSON brackets and quotes are properly closed.",
        system_prompt=reduced_sys_prompt,
        preferred_provider=preferred,
        project_id=project_id,
        agent_name=f"{report_type} Generator [Reduced Fallback]",
        max_tokens=4096,
        response_schema=response_schema,
        json_mode=True,
    )

    if isinstance(reduced_response, dict) and reduced_response.get("status") == "failed":
        raise ValueError(f"Full LLM provider exhaustion on all attempts: {reduced_response['error']}")

    return safe_parse_json(reduced_response)


def report_generator_node(state: AgentState) -> Dict[str, Any]:
    """
    Report Generator Node -- SKILL.md registry pattern.

    Generates 5 priority report types (Executive Summary, Business Plan, SWOT,
    Financial Projection, Investment Readiness) from validated pipeline output.

    Contract:
    - Only runs after Business Rules Engine has validated the pipeline output.
    - If pipeline_aborted is True, skips all generation and records failure status.
    - Each report type is fully specified by its registry entry (schema + prompt + mapping).
    - Per-report success/failure is tracked independently -- one failure does not block others.
    - All results (success and failure) are upserted to public.reports in Supabase.
    """
    project_id       = state.get("project_id")
    idea             = state.get("business_idea_input", "")
    outputs          = state.get("specialized_outputs", {})
    council          = state.get("council_feedback", [])
    reviewer         = state.get("reviewer_notes", "")
    critic           = state.get("critic_notes", "")
    rules_validation = state.get("rules_validation_result", {})
    scores           = state.get("scores", {})

    print(f"--- [Report Generator Node] Starting execution for Project {project_id} ---")

    supabase = get_supabase_client()

    #  Early-exit: pipeline aborted upstream 
    if state.get("pipeline_aborted"):
        abort_reason = state.get("abort_reason", "Upstream pipeline failure.")
        print(f"[Report Generator] Skipping -- pipeline aborted: {abort_reason}")
        _record_pipeline_abort(supabase, project_id, abort_reason, scores)
        return {"final_report": f"# Report Generation Skipped\n\nPipeline aborted: {abort_reason}"}

    #  Assemble shared context values 
    strategy    = outputs.get("strategy", "No strategy assessment available.")
    finance     = outputs.get("finance", "No finance assessment available.")
    marketing   = outputs.get("marketing", "No marketing plan available.")
    risk        = outputs.get("risk", "No risk assessment available.")
    council_str = "\n---\n".join(council) if council else "No council feedback."
    overall_score = scores.get("overall_score", 0.0)

    context = {
        "idea": idea,
        "strategy": strategy,
        "finance": finance,
        "marketing": marketing,
        "risk": risk,
        "council_str": council_str,
        "reviewer": reviewer,
        "critic": critic,
        "rules_json": json.dumps(rules_validation, indent=2),
        "scores_json": json.dumps(scores, indent=2),
        "overall_score": overall_score,
    }

    # Reduced context (capped fields for Attempt 3 safety net)
    reduced_context = {
        "idea": idea[:800],
        "strategy": strategy[:800],
        "finance": finance[:800],
        "marketing": marketing[:800],
        "risk": risk[:800],
        "council_str": council_str[:800],
        "reviewer": reviewer[:400],
        "critic": critic[:400],
        "rules_json": json.dumps(rules_validation, indent=2),
        "scores_json": json.dumps(scores, indent=2),
        "overall_score": overall_score,
    }

    #  Build the registry with interpolated prompts 
    registry = _build_registry(context)
    reduced_registry = _build_registry(reduced_context)

    #  Log estimated input token counts (diagnostic) 
    _log_prompt_token_estimates(context)

    generated_reports: Dict[str, dict] = {}
    success_count = 0
    failure_count = 0

    #  Check Business Rules Engine validation status 
    rules_valid = rules_validation.get("is_valid", True)
    validation_warning_msg = None
    if not rules_valid:
        errors_list = rules_validation.get("errors", ["Validation found inconsistencies"])
        validation_warning_msg = f"Pricing Data Inconsistency -- Financial figures may be unaligned ({', '.join(errors_list)})"
        print(f"[Report Generator] WARNING: {validation_warning_msg}. Proceeding with report generation and attaching warning banner.")

    #  Generate each report type via the registry 
    for report_type, config in registry.items():
        print(f"[Report Generator] Generating: '{report_type}'...")
        reduced_config = reduced_registry.get(report_type)

        try:
            # Generate JSON via helper (includes JSON repair & reduced-context retry on failure)
            report_content = _generate_report_json(report_type, config, project_id, reduced_config=reduced_config)

            # Coerce field types and key aliases to match schema before Pydantic validation
            report_content = _coerce_schema_fields(report_content, config["schema"])

            # Validate against Pydantic schema with diagnostic checkpoint on failure
            try:
                config["schema"].model_validate(report_content)
            except Exception as val_err:
                print(f"\n[Report Generator] ERROR: Schema validation checkpoint failed for '{report_type}'!")
                if "_raw_part_a" in report_content or "_raw_part_b" in report_content:
                    print("=== DIAGNOSTIC CHECKPOINT: Raw Split Call Outputs (Before Merge) ===")
                    print(f"--- Part A Raw Keys: {list(report_content.get('_raw_part_a', {}).keys())} ---")
                    print(json.dumps(report_content.get("_raw_part_a", {}), indent=2))
                    print(f"--- Part B Raw Keys: {list(report_content.get('_raw_part_b', {}).keys())} ---")
                    print(json.dumps(report_content.get("_raw_part_b", {}), indent=2))
                    merged_keys = [k for k in report_content.keys() if not k.startswith("_")]
                    print(f"--- Merged Keys: {merged_keys} ---")
                else:
                    print(f"--- Raw Response Keys: {list(k for k in report_content.keys() if not k.startswith('_'))} ---")
                    print(json.dumps({k: v for k, v in report_content.items() if not k.startswith("_")}, indent=2))
                print("===================================================================\n")
                raise val_err

            # Clean up internal debug keys before DB upsert
            report_content_clean = {k: v for k, v in report_content.items() if not k.startswith("_")}
            if validation_warning_msg:
                report_content_clean["validation_warning"] = validation_warning_msg

            # Upsert to Supabase reports table
            _upsert_report(supabase, project_id, report_type, report_content_clean, scores, "Completed")

            generated_reports[report_type] = report_content_clean
            success_count += 1
            print(f"[Report Generator] '{report_type}' -- OK")

        except Exception as err:
            failure_count += 1
            error_msg = str(err)
            print(f"[Report Generator] '{report_type}' -- FAILED: {error_msg}")
            fallback_content = {"error": f"Report generation failed: {error_msg}"}
            generated_reports[report_type] = fallback_content
            _upsert_report(supabase, project_id, report_type, fallback_content, scores, "Failed")

    #  Build final_report text summary 
    final_report_str = _build_final_report_text(project_id, generated_reports, registry)

    #  Log execution to agent_logs 
    try:
        supabase.table("agent_logs").insert({
            "project_id": project_id,
            "agent_name": "Report Generator",
            "status": "completed" if failure_count == 0 else "warning",
            "input_data": {
                "reports_requested": list(registry.keys()),
            },
            "output_data": {
                "reports_generated": success_count,
                "reports_failed": failure_count,
                "report_types": list(generated_reports.keys()),
            },
        }).execute()
        print("Logged Report Generator execution to Supabase.")
    except Exception as db_err:
        print(f"Supabase Agent Log Sync Warning for Report Generator: {str(db_err)}")

    print(
        f"--- [Report Generator Node] Finished -- "
        f"{success_count}/{success_count + failure_count} reports generated ---"
    )
    return {"final_report": final_report_str, "generated_reports": generated_reports}



# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _upsert_report(
    supabase,
    project_id: str,
    report_type: str,
    content: dict,
    scores: dict,
    status: str,
) -> None:
    """Insert or update a report record in public.reports."""
    try:
        existing = (
            supabase.table("reports")
            .select("id")
            .eq("project_id", project_id)
            .eq("report_type", report_type)
            .execute()
        )
        record = {
            "project_id": project_id,
            "report_type": report_type,
            "content": content,
            "scores": scores,
            "status": status,
        }
        if existing.data:
            report_id = existing.data[0]["id"]
            supabase.table("reports").update(record).eq("id", report_id).execute()
            print(f"  >> Updated existing record for '{report_type}'.")
        else:
            supabase.table("reports").insert(record).execute()
            print(f"  >> Created new record for '{report_type}'.")
    except Exception as db_err:
        print(f"  >> Supabase write warning for '{report_type}': {str(db_err)}")


def _record_pipeline_abort(supabase, project_id: str, abort_reason: str, scores: dict) -> None:
    """Write Failed status for all report types when pipeline was aborted upstream."""
    registry_keys = [
        "Executive Summary",
        "Business Plan",
        "SWOT Analysis",
        "Financial Projection",
        "Investment Readiness Report",
        "Business Model Canvas",
        "PESTLE Analysis",
        "Porter's Five Forces",
    ]
    for report_type in registry_keys:
        _upsert_report(
            supabase,
            project_id,
            report_type,
            {"error": f"Pipeline aborted upstream -- {abort_reason}"},
            scores,
            "Failed",
        )


def _build_final_report_text(
    project_id: str,
    generated_reports: Dict[str, dict],
    registry: dict,
) -> str:
    """Builds a human-readable Markdown summary of all generated reports."""
    lines = [f"# AI Venture Studio - Reports Suite\n**Project:** {project_id}\n"]

    for report_type, content in generated_reports.items():
        lines.append(f"\n## {report_type}")

        if "error" in content:
            lines.append(f"> [FAILED] {content['error']}\n")
            continue

        if "validation_warning" in content:
            lines.append(f"> [WARNING] {content['validation_warning']}\n")

        # Use human-readable section labels from export_mapping where available
        export_mapping = registry.get(report_type, {}).get("export_mapping", {})

        for field_key, field_value in content.items():
            if field_key == "validation_warning":
                continue
            label = export_mapping.get(field_key, field_key.replace("_", " ").title())
            lines.append(f"\n### {label}")
            if isinstance(field_value, list):
                for item in field_value:
                    lines.append(f"- {item}")
            else:
                lines.append(str(field_value))

        lines.append("")

    return "\n".join(lines)
