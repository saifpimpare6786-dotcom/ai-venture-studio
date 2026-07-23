"""
Report Generator Node — follows the registry pattern defined in skills/report-generation/SKILL.md.

Pattern for each report type:
  1. Pydantic schema         → app/schemas/report.py
  2. Focused prompt template → REPORT_REGISTRY[type]["system_prompt"]
  3. Registry entry          → REPORT_REGISTRY dict (no if/else per type)
  4. Export mapping          → REPORT_REGISTRY[type]["export_mapping"]

Adding a new report type = add a schema + one registry entry. Zero new node logic.
"""
import json
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


# ---------------------------------------------------------------------------
# Token estimation utilities (diagnostic — no external dependency)
# ---------------------------------------------------------------------------

def _estimate_tokens(text: str) -> int:
    """Rough token estimate: 1 token ≈ 4 characters (industry standard heuristic)."""
    return max(1, len(text) // 4)


def _log_prompt_token_estimates(context: dict) -> None:
    """
    Prints estimated input token counts for each report type to stdout.
    Called once per pipeline run before generation starts — surfaces the
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

    # Business Plan uses capped versions — reflect that in the estimate
    bp_ctx = (
        idea + strategy[:2500] + finance[:2500] + marketing[:2000]
        + risk[:1500] + council_str[:1500] + reviewer[:1000] + critic[:1000]
    )
    exec_ctx  = idea + strategy + finance + marketing + risk + council_str + reviewer + critic + scores_json
    swot_ctx  = idea + strategy + risk + council_str + critic + marketing
    fin_ctx   = idea + finance + strategy + marketing + rules_json + scores_json
    inv_ctx   = idea + scores_json + critic + reviewer + council_str + rules_json + strategy[:1500] + finance[:1500]

    print(
        "[Report Generator] Estimated input token counts per report type:\n"
        f"  Executive Summary    : ~{_estimate_tokens(exec_ctx):,} tokens\n"
        f"  SWOT Analysis        : ~{_estimate_tokens(swot_ctx):,} tokens\n"
        f"  Financial Projection : ~{_estimate_tokens(fin_ctx):,} tokens\n"
        f"  Investment Readiness : ~{_estimate_tokens(inv_ctx):,} tokens\n"
        f"  Business Plan (capped): ~{_estimate_tokens(bp_ctx):,} tokens  "
        f"[raw uncapped: ~{_estimate_tokens(idea + strategy + finance + marketing + risk + council_str + reviewer + critic):,}]"
    )


def _coerce_schema_fields(report_content: dict, schema_class) -> dict:
    """
    Pre-validate/coerce schema fields before Pydantic validation.
    - Key alias mapping: rename common LLM key variations to canonical schema fields.
    - str fields: convert nested dicts/lists to human-readable strings.
    - List[str] fields: ensure the value is a list of strings.
    """
    # ── Key Alias Mapping ─────────────────────────────────────────────────
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
    }
    for canonical_field, aliases in field_aliases.items():
        if canonical_field not in report_content or not report_content[canonical_field]:
            for alias in aliases:
                if alias in report_content and report_content[alias]:
                    print(f"[Report Generator] Coercing key alias '{alias}' -> '{canonical_field}'")
                    report_content[canonical_field] = report_content.pop(alias)
                    break

    schema_fields = schema_class.model_fields
    for field_name, field_info in schema_fields.items():
        if field_name not in report_content:
            continue
        val = report_content[field_name]
        annotation = field_info.annotation
        # Resolve Optional[X] → X
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

        elif is_list_str and not isinstance(val, list):
            # LLM returned a string instead of an array
            if isinstance(val, str):
                # Split on newlines/bullets as a best-effort recovery
                lines = [
                    line.lstrip("•-* ").strip()
                    for line in val.splitlines()
                    if line.strip()
                ]
                report_content[field_name] = lines if lines else [val]
            else:
                report_content[field_name] = [str(val)]

        elif is_list_str and isinstance(val, list):
            # Ensure every element is a string
            report_content[field_name] = [str(item) for item in val]

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

    # Business Plan input caps — applied before interpolation to bound the
    # total input token count to ~3500–4500 tokens (vs a potential 8000+ with
    # full agent outputs). Caps are generous enough to retain all key content
    # from typical agent outputs (800–1500 tokens each). The Investment
    # Readiness report already uses strategy[:1500] / finance[:1500] as the
    # established pattern — Business Plan extends this to all 8 context fields.
    bp_strategy    = strategy[:2500]
    bp_finance     = finance[:2500]
    bp_marketing   = marketing[:2000]
    bp_risk        = risk[:1500]
    bp_council     = council_str[:1500]
    bp_reviewer    = reviewer[:1000]
    bp_critic      = critic[:1000]

    return {
        # ── 1. Executive Summary ────────────────────────────────────────────
        "Executive Summary": {
            "schema": ExecutiveSummarySchema,
            "export_formats": ["docx", "pptx", "pdf"],
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

Target JSON Format — return ONLY this block wrapped in ```json ... ```:
{{
  "concept": "Detailed venture overview: problem being solved, primary value proposition, and business model summary...",
  "market_opportunity": "ICP analysis, market sizing, competitive landscape, and research evidence supporting demand...",
  "strategic_positioning": "USPs, competitive moat, key marketing channels, and branding vectors...",
  "financial_projection_summary": "Revenue model with named tiers and EXACT numeric prices (e.g. Starter: $49/month), seed capital estimate, and funding overview...",
  "risk_mitigation_summary": "Top 3–4 compliance/regulatory/competitive risks with specific mitigation steps...",
  "overall_score": {overall_score},
  "key_recommendations": [
    "Recommendation 1 drawn from Council or Reviewer...",
    "Recommendation 2 addressing a Critic concern...",
    "Recommendation 3 on go-to-market or compliance..."
  ]
}}
""",
        },

        # ── 2. SWOT Analysis ────────────────────────────────────────────────
        "SWOT Analysis": {
            "schema": SwotAnalysisSchema,
            "export_formats": ["docx", "pptx", "pdf"],
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

Target JSON Format — return ONLY this block wrapped in ```json ... ```:
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

        # ── 3. Financial Projection ─────────────────────────────────────────
        "Financial Projection": {
            "schema": FinancialProjectionSchema,
            "export_formats": ["docx", "pdf"],
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

Target JSON Format — return ONLY this block wrapped in ```json ... ```:
{{
  "revenue_model_details": "Named pricing tiers with EXACT numeric values (e.g. Starter: $49/month, Growth: $199/month, Enterprise: from $499/month). Breakdown of all revenue streams...",
  "pricing_sanity_check": "Assessment of competitive margin adequacy, customer WTP alignment, and any pricing consistency issues flagged by the Business Rules Engine...",
  "capital_requirements": "Seed/working capital estimates, developer headcount and salary budgets, infrastructure costs, and monthly burn rate...",
  "break_even_analysis": "Estimated months to break-even, MRR target, or customer volume milestone. State key assumptions explicitly...",
  "scoring_context": "Financial Soundness score from the Scoring Engine with its rationale, contextualising the projection's overall credibility..."
}}
""",
        },

        # ── 4. Investment Readiness Report ──────────────────────────────────
        "Investment Readiness Report": {
            "schema": InvestmentReadinessSchema,
            "export_formats": ["docx", "pptx", "pdf"],
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

Target JSON Format — return ONLY this block wrapped in ```json ... ```:
{{
  "investment_thesis": "Compelling thesis on why this venture is investable: market size, differentiation, timing, and team-market fit argument...",
  "scoring_breakdown": "Viability score X/100 (rationale), Market Fit score Y/100 (rationale), Financial Soundness score Z/100 (rationale). Weighted overall: {overall_score}/100...",
  "critic_concerns": "Top 3–4 adversarial concerns the Critic raised, including assumptions challenged and strategic questions founders must answer convincingly...",
  "milestones_funding": "Phase 1/2/3 milestone targets, preferred funding instrument (pre-seed/seed/Series A), and capital allocation priorities by phase...",
  "rules_validation_summary": "Business Rules Engine outcome: [PASSED/FAILED]. Key findings: pricing consistency status, currency verification, any errors flagged..."
}}
""",
        },

        # ── 5. Business Plan (last — heaviest report, 2-call split architecture) ──
        # Positioned last so the 4 lighter reports always complete first even
        # if Business Plan requires retry overhead. Input fields are capped
        # (bp_* variables above) to keep input token count ≤ ~4500 tokens.
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

Target JSON Format — return ONLY this block wrapped in ```json ... ```:
{{
  "company_description": "Strategic vision, mission statement, problem-solution alignment, and venture model details...",
  "market_analysis": "Industry landscape, direct/indirect competitor matrix, supplier/buyer power, TAM/SAM/SOM estimates...",
  "marketing_sales_strategy": "ICP persona definitions, customer acquisition pipeline, go-to-market channels, branding taglines...",
  "operational_plan": "Execution milestones, critical partnerships, tech/security/privacy compliance checklist, legal requirements...",
  "financial_plan": "Revenue channels, EXACT pricing tier names and numeric values, break-even assumptions, capital burn rate...",
  "risk_register": [
    "Risk 1: [Risk description] — Mitigation: [specific action]",
    "Risk 2: [Risk description] — Mitigation: [specific action]",
    "Risk 3: [Risk description] — Mitigation: [specific action]"
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
    }


# ---------------------------------------------------------------------------
# JSON generation helper with repair retry
# ---------------------------------------------------------------------------

JSON_REPAIR_PROMPT = """
The following JSON is malformed or truncated (it may have been cut off mid-string).
Return the COMPLETE, VALID JSON object below, fixing any truncation or unescaped characters.
Do NOT add new fields or change existing values — only fix structural JSON errors.
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
      Call A — Company & Market  : company_description + market_analysis
      Call B — Ops & Finance     : marketing_sales_strategy + operational_plan
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
        own repair retry — caller must handle.
    """
    idea        = bp_ctx["idea"]
    strategy    = bp_ctx["strategy"]
    finance     = bp_ctx["finance"]
    marketing   = bp_ctx["marketing"]
    risk        = bp_ctx["risk"]
    council_str = bp_ctx["council_str"]
    reviewer    = bp_ctx["reviewer"]
    critic      = bp_ctx["critic"]

    # ── Call A: Company Description + Market Analysis ─────────────────────
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

Target JSON Format — return ONLY this block wrapped in ```json ... ```:
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
        part_a = json.loads(cleaned_a)
    except json.JSONDecodeError as err_a:
        print(f"[Business Plan Split] Part A JSON error: {err_a}. Attempting repair...")
        repair_a = call_llm(
            prompt=JSON_REPAIR_PROMPT.format(malformed=cleaned_a[:6000]),
            system_prompt="You are a JSON repair assistant. Return only valid JSON wrapped in ```json ... ``` fences.",
            preferred_provider=preferred,
            project_id=project_id,
            agent_name=f"Business Plan Generator [Part A Repair]{label_suffix}",
            max_tokens=max_tokens,
        )
        if isinstance(repair_a, dict) and repair_a.get("status") == "failed":
            raise ValueError(f"Business Plan Part A repair call failed: {repair_a['error']}")
        part_a = json.loads(extract_json_block(repair_a))

    # ── Call B: Marketing, Ops, Finance & Risk ───────────────────────────
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

Target JSON Format — return ONLY this block wrapped in ```json ... ```:
{{
  "marketing_sales_strategy": "ICP persona definitions, customer acquisition pipeline, go-to-market channels, branding taglines...",
  "operational_plan": "Execution milestones, critical partnerships, tech/security/privacy compliance checklist, legal requirements...",
  "financial_plan": "Revenue channels, EXACT pricing tier names and numeric values, break-even assumptions, capital burn rate...",
  "risk_register": [
    "Risk 1: [Risk description] — Mitigation: [specific action]",
    "Risk 2: [Risk description] — Mitigation: [specific action]",
    "Risk 3: [Risk description] — Mitigation: [specific action]"
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
        part_b = json.loads(cleaned_b)
    except json.JSONDecodeError as err_b:
        print(f"[Business Plan Split] Part B JSON error: {err_b}. Attempting repair...")
        repair_b = call_llm(
            prompt=JSON_REPAIR_PROMPT.format(malformed=cleaned_b[:6000]),
            system_prompt="You are a JSON repair assistant. Return only valid JSON wrapped in ```json ... ``` fences.",
            preferred_provider=preferred,
            project_id=project_id,
            agent_name=f"Business Plan Generator [Part B Repair]{label_suffix}",
            max_tokens=max_tokens,
        )
        if isinstance(repair_b, dict) and repair_b.get("status") == "failed":
            raise ValueError(f"Business Plan Part B repair call failed: {repair_b['error']}")
        part_b = json.loads(extract_json_block(repair_b))

    # ── Merge A + B into full Business Plan dict ──────────────────────────
    part_a_clean = {k: v for k, v in part_a.items() if not k.startswith("_")}
    part_b_clean = {k: v for k, v in part_b.items() if not k.startswith("_")}
    
    # Key union of both calls
    merged = {**part_a_clean, **part_b_clean}
    # Attach raw parts for diagnostic checkpoint logging if validation fails downstream
    merged["_raw_part_a"] = part_a_clean
    merged["_raw_part_b"] = part_b_clean
    return merged


# ---------------------------------------------------------------------------
# JSON generation helper — routes Business Plan through split-call path
# ---------------------------------------------------------------------------

def _generate_report_json(
    report_type: str,
    config: dict,
    project_id: str,
) -> dict:
    """
    Calls the LLM to generate one report's JSON.

    For Business Plan specifically, this uses a 2-call split architecture
    (_generate_business_plan_split) instead of a single large call:
      - Reduces both input and output token pressure per call.
      - Each sub-call has its own JSON repair retry.
      - On total failure of the split path, retries once with summarized
        (800-char) context before giving up — the "retry-with-repair" path
        described in the task spec.

    For all other report types:
      1. First call uses the full system_prompt with the report's max_tokens.
      2. On JSONDecodeError, re-prompts with the malformed output and a repair
         instruction — one repair retry only.
      3. On second failure, raises so the caller's per-report try/except captures it.

    Args:
        config: Registry entry dict (must contain system_prompt; optionally
                max_tokens, preferred_provider, _bp_context).
    Returns:
        Parsed report_content dict ready for schema coercion and Pydantic validation.
    Raises:
        ValueError / json.JSONDecodeError: on total failure.
    """
    max_tokens = config.get("max_tokens", 1024)
    preferred   = config.get("preferred_provider", "gemini")

    # ── Business Plan: split-call path ───────────────────────────────────
    if report_type == "Business Plan":
        bp_ctx = config.get("_bp_context")
        if not bp_ctx:
            # Defensive fallback: should never happen if registry is correct
            raise ValueError(
                "Business Plan registry entry missing '_bp_context'. "
                "This is a configuration error in _build_registry()."
            )

        # ── Split-call attempt ────────────────────────────────────────────
        try:
            print("[Report Generator] 'Business Plan' — using 2-call split architecture.")
            return _generate_business_plan_split(
                bp_ctx=bp_ctx,
                project_id=project_id,
                max_tokens=max_tokens // 2,  # Each call gets half the budget
                preferred=preferred,
            )
        except Exception as split_err:
            print(
                f"[Report Generator] 'Business Plan' — split-call path failed: {split_err}. "
                f"Retrying with summarized (800-char) context..."
            )

        # ── Context-reduced fallback retry ────────────────────────────────
        # Truncate every field to 800 chars — worst-case the report will be
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
        print("[Report Generator] 'Business Plan' — reduced-context retry: "
              f"~{_estimate_tokens(''.join(reduced_ctx.values())):,} input tokens.")
        # Each sub-call on reduced context gets 2048 tokens — plenty for
        # shorter input → shorter expected output.
        return _generate_business_plan_split(
            bp_ctx=reduced_ctx,
            project_id=project_id,
            max_tokens=2048,
            preferred=preferred,
            label_suffix=" [Reduced]",
        )
        # If this also raises, it propagates to the caller's except clause.

    # ── All other report types: standard single-call path ─────────────────

    # ── Attempt 1: normal generation ─────────────────────────────────────
    raw_text = call_llm(
        prompt="Generate the report as instructed.",
        system_prompt=config["system_prompt"],
        preferred_provider=preferred,
        project_id=project_id,
        agent_name=f"{report_type} Generator",
        max_tokens=max_tokens,
    )

    if isinstance(raw_text, dict) and raw_text.get("status") == "failed":
        raise ValueError(raw_text["error"])

    cleaned = extract_json_block(raw_text)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as first_err:
        print(
            f"[Report Generator] '{report_type}' — JSON parse error on attempt 1: {first_err}. "
            f"Attempting JSON repair retry..."
        )

    # ── Attempt 2: repair retry ───────────────────────────────────────────
    repair_prompt = JSON_REPAIR_PROMPT.format(malformed=cleaned[:6000])
    repaired_text = call_llm(
        prompt=repair_prompt,
        system_prompt="You are a JSON repair assistant. Return only valid JSON wrapped in ```json ... ``` fences.",
        preferred_provider=preferred,
        project_id=project_id,
        agent_name=f"{report_type} Generator [JSON Repair]",
        max_tokens=max_tokens,
    )

    if isinstance(repaired_text, dict) and repaired_text.get("status") == "failed":
        raise ValueError(f"JSON repair LLM call failed: {repaired_text['error']}")

    repaired_cleaned = extract_json_block(repaired_text)
    # Let JSONDecodeError propagate — caller's except clause will catch it
    return json.loads(repaired_cleaned)



def report_generator_node(state: AgentState) -> Dict[str, Any]:
    """
    Report Generator Node — SKILL.md registry pattern.

    Generates 5 priority report types (Executive Summary, Business Plan, SWOT,
    Financial Projection, Investment Readiness) from validated pipeline output.

    Contract:
    - Only runs after Business Rules Engine has validated the pipeline output.
    - If pipeline_aborted is True, skips all generation and records failure status.
    - Each report type is fully specified by its registry entry (schema + prompt + mapping).
    - Per-report success/failure is tracked independently — one failure does not block others.
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

    # ── Early-exit: pipeline aborted upstream ─────────────────────────────
    if state.get("pipeline_aborted"):
        abort_reason = state.get("abort_reason", "Upstream pipeline failure.")
        print(f"[Report Generator] Skipping — pipeline aborted: {abort_reason}")
        _record_pipeline_abort(supabase, project_id, abort_reason, scores)
        return {"final_report": f"# Report Generation Skipped\n\nPipeline aborted: {abort_reason}"}

    # ── Assemble shared context values ────────────────────────────────────
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

    # ── Build the registry with interpolated prompts ───────────────────────
    registry = _build_registry(context)

    # ── Log estimated input token counts (diagnostic) ─────────────────────
    _log_prompt_token_estimates(context)

    generated_reports: Dict[str, dict] = {}
    success_count = 0
    failure_count = 0

    # ── Check Business Rules Engine validation status ────────────────────
    rules_valid = rules_validation.get("is_valid", True)
    validation_warning_msg = None
    if not rules_valid:
        errors_list = rules_validation.get("errors", ["Validation found inconsistencies"])
        validation_warning_msg = f"Pricing Data Inconsistency — Financial figures may be unaligned ({', '.join(errors_list)})"
        print(f"[Report Generator] WARNING: {validation_warning_msg}. Proceeding with report generation and attaching warning banner.")

    # ── Generate each report type via the registry ────────────────────────
    for report_type, config in registry.items():
        print(f"[Report Generator] Generating: '{report_type}'...")

        try:
            # Generate JSON via helper (includes JSON repair retry on truncation)
            report_content = _generate_report_json(report_type, config, project_id)

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
            print(f"[Report Generator] '{report_type}' — OK")

        except Exception as err:
            failure_count += 1
            error_msg = str(err)
            print(f"[Report Generator] '{report_type}' — FAILED: {error_msg}")
            fallback_content = {"error": f"Report generation failed: {error_msg}"}
            generated_reports[report_type] = fallback_content
            _upsert_report(supabase, project_id, report_type, fallback_content, scores, "Failed")

    # ── Build final_report text summary ───────────────────────────────────
    final_report_str = _build_final_report_text(project_id, generated_reports, registry)

    # ── Log execution to agent_logs ───────────────────────────────────────
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
        f"--- [Report Generator Node] Finished — "
        f"{success_count}/{success_count + failure_count} reports generated ---"
    )
    return {"final_report": final_report_str}


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
    ]
    for report_type in registry_keys:
        _upsert_report(
            supabase,
            project_id,
            report_type,
            {"error": f"Pipeline aborted upstream — {abort_reason}"},
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
