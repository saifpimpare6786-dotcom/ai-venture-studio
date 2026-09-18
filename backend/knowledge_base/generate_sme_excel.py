import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import os

def create_knowledge_base():
    wb = openpyxl.Workbook()
    
    # -------------------------------------------------------------
    # Sheet 1: SME Industry Knowledge Base (Main RAG Source)
    # -------------------------------------------------------------
    ws_main = wb.active
    if ws_main is None:
        ws_main = wb.create_sheet(title="SME_Industry_Insights")
    else:
        ws_main.title = "SME_Industry_Insights"
    assert ws_main is not None
    ws_main.views.sheetView[0].showGridLines = True

    columns = [
        ("Industry", 24),
        ("Sub_Sector", 26),
        ("Organisation_Name", 26),
        ("SME_Expert_Role", 26),
        ("Industry_Insights", 45),
        ("Core_Problem_Solved", 42),
        ("Strategic_Solution_Playbook", 48),
        ("Customer_Acquisition_Strategy", 42),
        ("Pricing_and_Monetization_Model", 38),
        ("Unit_Economics_Benchmarks", 38),
        ("Key_Risks_and_Compliance", 42),
        ("Competitive_Moat", 36),
        ("Failure_Modes_Warning", 40)
    ]

    # Setup Headers
    for col_idx, (header_name, col_width) in enumerate(columns, 1):
        cell = ws_main.cell(row=1, column=col_idx, value=header_name)
        cell.font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid") # Slate 800
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws_main.column_dimensions[get_column_letter(col_idx)].width = col_width
    ws_main.row_dimensions[1].height = 28

    # Comprehensive rows across the 5 required industries
    rows_data = [
        # --- 1. HealthTech / Digital Health ---
        [
            "HealthTech/Digital Health",
            "Remote Patient Monitoring (RPM)",
            "BioTelemetry / CareCloud RPM",
            "VP of Clinical Operations & Telehealth",
            "Shift from fee-for-service to value-based care is driving hospital adoption of continuous vitals monitoring, reducing 30-day readmission rates by 38%.",
            "Hospitals penalized under HRRP for unmanaged chronic congestive heart failure and COPD patient readmissions.",
            "Cellular-connected plug-and-play biometric hardware (no Wi-Fi setup needed) paired with 24/7 dedicated triage nurse dashboard and EHR integration.",
            "B2B enterprise provider sales targeting Chief Medical Officers and ACO directors via clinical pilot trials with 100-patient cohorts.",
            "Hardware lease ($45/mo/patient) + SaaS clinical triage seat fee ($250/physician/mo) with CPT codes 99453, 99454, 99457 billing support.",
            "Gross Margin: 72% | CAC Payback: 14 months | LTV/CAC: 5.2x | Churn: <0.5%/mo | ARPU: $1,400/provider/mo",
            "HIPAA compliance, FDA 510(k) clearance requirements for predictive diagnostics, and CMS reimbursement policy adjustments.",
            "Direct bidirectional Epic/Cerner FHIR API EHR integration and proprietary algorithmic arrhythmia detection with 99.2% sensitivity.",
            "Failing to tie into existing Medicare/insurance CPT billing codes, forcing clinics to treat the solution as an unreimbursed out-of-pocket overhead."
        ],
        [
            "HealthTech/Digital Health",
            "Digital Therapeutics & Behavioral Health",
            "Pear Therapeutics (Post-Mortem) / Lyra Health",
            "Chief Commercial Officer (Ex-Pharma Digital)",
            "Direct-to-consumer mental health suffers high churn (>65% at 90 days); enterprise B2B employer-sponsored or payer-reimbursed models achieve sustained retention.",
            "Workforce productivity loss due to unmanaged burnout, anxiety, and depression with 6-month waitlists for in-person therapists.",
            "Evidence-based cognitive behavioral therapy (CBT) modules combined with synchronous on-demand licensed tele-counselors and automated triage.",
            "Targeting Enterprise VP of People / HR Benefits Brokers through ROI calculators proving healthcare claims reduction and absenteeism drops.",
            "PEPM (Per Employee Per Month) subscription ($3.50 - $6.00 PEPM) paid by enterprise employer regardless of active utilization.",
            "Gross Margin: 68% | CAC Payback: 11 months | LTV/CAC: 4.8x | Annual Retention: 92% | PEPM: $4.50",
            "State-by-state medical licensing reciprocity, DPDPA / GDPR health record confidentiality, and clinical trial efficacy requirements.",
            "Proprietary clinical outcome dataset demonstrating measurable PHQ-9 and GAD-7 symptom reduction published in peer-reviewed journals.",
            "Relying solely on prescription digital therapeutics (PDT) insurance reimbursement pathways without employer B2B direct distribution."
        ],

        # --- 2. B2B SaaS / Enterprise ---
        [
            "B2B Saas/ Enterprise",
            "Developer Productivity & Observability",
            "Datadog / Postman",
            "Chief Technology Officer & SaaS Architect",
            "Microservice architectures generate massive log volumes; engineering teams spend 25% of sprint velocity debugging latency anomalies across fragmented clouds.",
            "Distributed tracing blindness causing customer-facing downtime and ballooning cloud data egress expenses.",
            "Unified single-agent telemetry daemon collecting metrics, traces, and logs with automated root-cause graph visualization and anomaly alerts.",
            "Bottom-up Product-Led Growth (PLG) targeting software architects via free developer tiers and OSS CLI, expanding to enterprise CIO procurement.",
            "Usage-based tiered ingestion ($0.10/GB log ingest, $15/host/mo) with guaranteed enterprise minimum commitments starting at $25k/year.",
            "Gross Margin: 81% | CAC Payback: 12 months | LTV/CAC: 6.4x | Net Revenue Retention (NRR): 130% | Logo Churn: 0.7%/mo",
            "SOC 2 Type II, ISO 27001, FedRAMP certification for enterprise procurement; vulnerability to data exfiltration breaches.",
            "Deep proprietary compiler and eBPF kernel instrumentation providing zero-code-modification deployment across Kubernetes clusters.",
            "Over-indexing on bottom-up developer usage without building enterprise security features (SSO, RBAC, audit logs) needed to close 6-figure ACVs."
        ],
        [
            "B2B Saas/ Enterprise",
            "Enterprise Procurement & Spend Automation",
            "Ramp / Coupa",
            "VP of Enterprise Sales & FinOps",
            "Mid-market enterprise companies lose 3-5% of EBITDA annually to shadow IT subscriptions, duplicate supplier contracts, and unmanaged procurement.",
            "Fragmented purchase orders and invoice approvals spread across email, Slack, and legacy ERPs with zero real-time spend visibility.",
            "Automated vendor contract extraction using LLMs, unified corporate card issuance with programmatic policy limits, and instant 3-way ERP matching.",
            "Top-down direct sales to CFOs and Controllers paired with automated ROI audits analyzing 90 days of corporate card statements.",
            "Hybrid SaaS platform fee ($500 - $2,500/mo) + Interchange fee share (1.2% - 1.8% on processed virtual card spend).",
            "Gross Margin: 78% | CAC Payback: 9 months | LTV/CAC: 7.1x | Dollar Retention: 125% | Payback: <10 months",
            "Credit default risk on non-reimbursed card floats, PCI-DSS Level 1 compliance, and complex legacy ERP connector maintenance (SAP/NetSuite).",
            "Proprietary OCR and document parsing LLM fine-tuned on millions of vendor invoices; exclusive banking partner BIN sponsorship.",
            "Targeting early-stage startups with low corporate spend instead of 50-500 FTE mid-market enterprises where vendor bloat is acute."
        ],

        # --- 3. Fintech / Payments ---
        [
            "Fintech/payments",
            "Cross-Border B2B Settlement & FX",
            "Wise Business / Airwallex",
            "Head of International Treasury & FX Solutions",
            "Global supply chains and remote teams face 3-5% hidden FX spreads and 3-5 business day settlement delays via legacy SWIFT correspondent banking.",
            "SME exporters and remote engineering firms suffer cash drag and opaque wire fees eating into thin export operating margins.",
            "Local clearing rails integration (ACH, SEPA, Faster Payments, UPI) with peer-to-peer domestic netting engines bypassing SWIFT correspondent loops.",
            "Strategic integration into global freelancing platforms, accounting tools (Xero/QuickBooks), and direct digital acquisition targeting importing SMEs.",
            "Transparent markup on mid-market FX spread (0.35% - 0.65%) + nominal flat payout fee ($1.50 per local clearing transaction).",
            "Gross Margin: 64% | CAC Payback: 10 months | LTV/CAC: 5.8x | Monthly Volume Retention: 95% | Burn Multiple: 1.1x",
            "AML/CFT regulatory licensing across 30+ jurisdictions, Anti-Financial Crime KYC screening, and intra-day foreign exchange liquidity shocks.",
            "Direct local payment rail memberships and algorithmic multi-currency netting pool balancing liquidity across 50+ currency pairs.",
            "Under-capitalizing treasury reserves leading to liquidity crunches during volatile FX swings or sudden regulatory freeze of correspondent accounts."
        ],
        [
            "Fintech/payments",
            "Embedded Lending & Invoice Factoring for SMEs",
            "Pipe / Kabbage / Rupifi",
            "Chief Risk Officer (Credit Risk & Underwriting)",
            "SMEs have 60-90 day invoice payment terms from enterprise buyers, creating working capital bottlenecks that prevent scaling inventory or hiring.",
            "Traditional commercial banks demand 3 years of audited financials and collateral, rejecting 70% of high-growth digital SME credit applications.",
            "Embedded SDK linking directly to merchant accounting (QuickBooks/Xero) and banking APIs (Plaid) to underwrite real-time cash flow and disburse in <2 hours.",
            "B2B2B partnership distribution through B2B marketplaces, wholesale supply platforms, and procurement software providers.",
            "Discount fee on factored invoices (1.5% - 3.0% per 30 days) or revenue-share origination fee with lending balance-sheet capital partners.",
            "Gross Margin: 70% (on software/servicing) | Default Rate: <1.8% | LTV/CAC: 4.5x | Return on Capital: 14.5% annual",
            "Non-performing loan (NPL) escalation during macro recessions, state lending licensing, and usury rate cap regulations.",
            "Machine-learning underwriting engine parsing real-time bank ledger transactions to predict default risk with 3x the accuracy of FICO scores.",
            "Lending off own balance sheet before establishing institutional debt facility warehouses, resulting in rapid equity dilution to fund loan book."
        ],

        # --- 4. Ecommerce / Consumer ---
        [
            "Ecommerce/consumer",
            "D2C Omnichannel Logistics & Returns Optimization",
            "Loop Returns / ShipBob",
            "VP of Supply Chain & E-Commerce Logistics",
            "E-commerce brands suffer 20-30% return rates in apparel and consumer goods, eroding 35% of net profit via reverse logistics and unsellable inventory.",
            "High shopper friction in return processes leading to customer churn; warehouse bottleneck processing returned SKU restocking.",
            "Self-serve return portal incentivizing exchanges and store credit over cash refunds (+30% retained revenue), bundled with localized 3PL return hubs.",
            "Shopify App Store ecosystem listing, co-marketing with direct-to-consumer digital agencies, and merchant ROI case studies.",
            "Tiered monthly SaaS subscription ($99 - $999/mo based on order volume) + $0.20 per return transaction processed.",
            "Gross Margin: 76% | CAC Payback: 7 months | LTV/CAC: 6.0x | Net Dollar Retention: 118% | Annual Churn: 8%",
            "Over-reliance on single platform app stores (e.g. Shopify policy changes), carrier rate inflation (FedEx/UPS surcharges), and warehouse labor strikes.",
            "Proprietary consumer exchange recommendation engine and deep API hooks into carrier manifests and merchant inventory ERPs.",
            "Failing to monetize exchange incentives, treating the software as a simple return label generator instead of a revenue-retention engine."
        ],
        [
            "Ecommerce/consumer",
            "Personalized Consumer Nutrition & Wellness D2C",
            "AG1 / Huel / Curology",
            "Head of Growth & Retention (Consumer D2C)",
            "Rising digital ad CAC (+60% post-iOS 14.5 ATT privacy updates) has made one-off consumer purchase models structurally unprofitable.",
            "High customer acquisition costs coupled with low repeat purchase rates leading to negative unit economics on transaction 1.",
            "Hyper-focused single-hero product subscription, aggressive influencer affiliate gifting flywheel, and automated retention SMS drip cycles.",
            "Creator-led podcast sponsorships, TikTok/Meta user-generated content (UGC), and unboxing referral mechanics with free starter kits.",
            "Monthly recurring subscription ($79/month) with free delivery and bundled welcome kit; 15% discount vs one-time purchase.",
            "Gross Margin: 74% | Payback on CAC: 3.2 months | LTV/CAC: 3.5x | 6-Month Cohort Retention: 48% | Blended CAC: $95",
            "FDA dietary supplement disclaimer standards, FTC guidelines for influencer endorsements, and raw ingredient supply-chain inflation.",
            "Direct proprietary formulation, bespoke taste-profile formulation, and closed-loop subscriber cohort analytics predicting churn triggers.",
            "Spending 80%+ of venture budget on Meta ads without building a high-retention subscription habit, leading to cash burnout when ad CPMS spike."
        ],

        # --- 5. AI & Automation ---
        [
            "AI & Automation",
            "Vertical Legal & Regulatory AI Agents",
            "Harvey AI / Robin AI",
            "Former Big Law Partner & Head of Legal AI",
            "Enterprise legal teams and law firms spend 40% of associate billable hours manually reviewing 200+ page NDAs, master service agreements, and compliance filings.",
            "Manual contract review is slow, prone to human fatigue oversight, and costs enterprises $800+/hour in external counsel billings.",
            "Specialized domain-tuned LLM agents with legal citation verification, clause deviation redlining against company playbooks, and vector precedent retrieval.",
            "High-touch enterprise pilots with AmLaw 100 firms and Fortune 500 General Counsels; SOC-2 Type II audit report delivered at first meeting.",
            "Annual enterprise license: $25,000 - $120,000/year (tiered by seats and document processing throughput).",
            "Gross Margin: 84% | CAC Payback: 10 months | LTV/CAC: 6.8x | Net Retention: 135% | Gross Margin: 82%",
            "Model hallucination liability, client attorney-client privilege breach concerns, and strict non-retention agreements for LLM inference training.",
            "Proprietary fine-tuned legal benchmark models, deterministic rule verification sentry (zero fabrication), and deep integrations with Microsoft Word/iManage.",
            "Selling generic LLM wrapper features without deterministic citation verification, leading to catastrophic lawyer hallucinations in court or contracts."
        ],
        [
            "AI & Automation",
            "Autonomous Customer Support & Voice AI Agents",
            "Sierra AI / Decagon / Bland AI",
            "VP of Customer Experience & Conversational AI",
            "Enterprise B2C contact centers suffer 45% annual agent turnover and spend $6 - $12 per tier-1 support ticket with 20-minute hold times.",
            "Legacy rule-based IVR chatbots have sub-20% resolution rates, frustrating consumers and escalating tickets to costly human agents.",
            "Multi-modal conversational agent with sub-400ms latency, dynamic API tool-calling (refunds, re-bookings, address updates), and graceful human escalation.",
            "Direct enterprise displacement of legacy Zendesk/Genesys tiers with 30-day proof-of-concept testing resolution rates on real historical ticket logs.",
            "Outcome-based pricing ($0.75 - $1.50 per successfully resolved ticket without human intervention) vs legacy per-seat pricing.",
            "Gross Margin: 76% | CAC Payback: 8 months | LTV/CAC: 7.5x | Ticket Resolution Rate: 72% | NRR: 140%",
            "Telephony regulatory compliance (TCPA, STIR/SHAKEN), audio latency spikes, and edge-case prompt injection attacks via customer voice/chat inputs.",
            "Proprietary low-latency voice synthesis pipeline, guardrailed sandboxed tool-execution engine, and bi-directional CRM state synchronization.",
            "Pricing per agent seat instead of per resolved ticket; charging flat seats causes customers to revert to legacy software when ticket volume dips."
        ]
    ]

    # Write Data
    thin_border = Border(
        left=Side(style='thin', color='E2E8F0'),
        right=Side(style='thin', color='E2E8F0'),
        top=Side(style='thin', color='E2E8F0'),
        bottom=Side(style='thin', color='E2E8F0')
    )

    for row_idx, row in enumerate(rows_data, 2):
        bg_color = "FFFFFF" if row_idx % 2 == 0 else "F8FAFC"
        fill = PatternFill(start_color=bg_color, end_color=bg_color, fill_type="solid")
        
        for col_idx, value in enumerate(row, 1):
            cell = ws_main.cell(row=row_idx, column=col_idx, value=value)
            cell.font = Font(name="Calibri", size=10, color="0F172A")
            cell.fill = fill
            cell.border = thin_border
            
            # Alignments
            if col_idx in [1, 2, 3, 4]:
                cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
            else:
                cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
                
        ws_main.row_dimensions[row_idx].height = 65

    # -------------------------------------------------------------
    # Sheet 2: Industry Financial Benchmarks & Levers (Simulator Anchor)
    # -------------------------------------------------------------
    ws_bench = wb.create_sheet(title="Industry_Ratios_Benchmarks")
    ws_bench.views.sheetView[0].showGridLines = True

    bench_headers = [
        ("Industry", 24),
        ("Target_Gross_Margin_Pct", 24),
        ("Target_CAC_Payback_Months", 26),
        ("Target_LTV_CAC_Ratio", 22),
        ("Target_Annual_Churn_Pct", 22),
        ("Seed_Monthly_Growth_Rate_Pct", 28),
        ("Typical_Starter_Price_USD", 25),
        ("Typical_Growth_Price_USD", 25),
        ("Typical_Enterprise_Floor_USD", 28),
        ("Recommended_Burn_Multiple", 26)
    ]

    for col_idx, (header, width) in enumerate(bench_headers, 1):
        cell = ws_bench.cell(row=1, column=col_idx, value=header)
        cell.font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="0F766E", end_color="0F766E", fill_type="solid") # Teal 700
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws_bench.column_dimensions[get_column_letter(col_idx)].width = width
    ws_bench.row_dimensions[1].height = 28

    bench_data = [
        ["HealthTech/Digital Health", 75.0, 16.0, 5.5, 4.0, 12.0, 599, 1499, 4999, 1.2],
        ["B2B Saas/ Enterprise", 82.0, 12.0, 4.5, 5.0, 15.0, 299, 799, 1999, 1.3],
        ["Fintech/payments", 65.0, 14.0, 5.0, 6.0, 18.0, 499, 1299, 3999, 1.4],
        ["Ecommerce/consumer", 70.0, 6.0, 3.2, 18.0, 20.0, 19, 49, 149, 1.5],
        ["AI & Automation", 80.0, 9.0, 6.0, 5.5, 22.0, 399, 1199, 3499, 1.3]
    ]

    for row_idx, row in enumerate(bench_data, 2):
        bg_color = "FFFFFF" if row_idx % 2 == 0 else "F0FDFA"
        fill = PatternFill(start_color=bg_color, end_color=bg_color, fill_type="solid")
        for col_idx, val in enumerate(row, 1):
            cell = ws_bench.cell(row=row_idx, column=col_idx, value=val)
            cell.font = Font(name="Calibri", size=10, color="0F172A")
            cell.fill = fill
            cell.border = thin_border
            if col_idx == 1:
                cell.alignment = Alignment(horizontal="left", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="right", vertical="center")
        ws_bench.row_dimensions[row_idx].height = 24

    # -------------------------------------------------------------
    # Sheet 3: Metadata & Contributor Guide (Consulting Comparison)
    # -------------------------------------------------------------
    ws_meta = wb.create_sheet(title="SME_Storyline_Architecture")
    ws_meta.views.sheetView[0].showGridLines = True

    meta_sections = [
        ("PROJECT STORYLINE & VALUE PROPOSITION", [
            ("Core Thesis", "Traditional Tier-1 consulting firms (McKinsey, BCG, Bain) guard proprietary historical client playbooks behind $500k+ fees, taking 8-16 weeks to deploy senior SME partner interviews."),
            ("AI Venture Studio Solution", "We democratize institutional venture strategy via an Open/SME-Curated Knowledge Spine. Practitioners from SME sectors deposit granular playbooks, unit economics, and failure modes into this structured intelligence grid."),
            ("RAG Ingestion Workflow", "When a founder inputs their venture (e.g. Industry = Fintech/payments), our multi-agent boardroom (Finance Anchor, Strategy, Marketing, Risk, Council, VC Critic) pulls exact benchmark ratios, compliance traps, and proven GTM motions to deliver personalized, verified deliverables in 2 minutes.")
        ]),
        ("DATASET SCHEMA SPECIFICATIONS", [
            ("1. Industry", "Top-level categorization matching the 5 target industry verticals."),
            ("2. Sub_Sector", "Granular functional domain (e.g. Remote Patient Monitoring, Cross-Border Settlement)."),
            ("3. Organisation_Name", "Leading benchmark company or SME organization case study."),
            ("4. SME_Expert_Role", "Credibility anchor (e.g. VP Clinical Ops, Chief Risk Officer, CTO)."),
            ("5. Industry_Insights", "High-level market dynamics, macroeconomic tailwinds, and macro shifts."),
            ("6. Core_Problem_Solved", "Real-world operational, structural, or technological bottleneck."),
            ("7. Strategic_Solution_Playbook", "Actionable architectural and operational methodology used to resolve problem."),
            ("8. Customer_Acquisition_Strategy", "Validated GTM channels, sales cycle, and CAC acceleration methods."),
            ("9. Pricing_and_Monetization_Model", "Exact pricing tiers, packaging strategies, and billing mechanics."),
            ("10. Unit_Economics_Benchmarks", "Gross Margins, CAC Payback, LTV:CAC, Churn, and Burn Multiples."),
            ("11. Key_Risks_and_Compliance", "Statutory mandates (HIPAA, DPDPA, GDPR, PCI-DSS, SECR, FCA)."),
            ("12. Competitive_Moat", "Defensive moats (Network effects, switching costs, proprietary datasets)."),
            ("13. Failure_Modes_Warning", "Post-mortem analysis of why 80% of founders fail in this specific niche.")
        ])
    ]

    curr_row = 1
    for title, items in meta_sections:
        c = ws_meta.cell(row=curr_row, column=1, value=title)
        c.font = Font(name="Calibri", size=12, bold=True, color="FFFFFF")
        c.fill = PatternFill(start_color="312E81", end_color="312E81", fill_type="solid") # Indigo 900
        ws_meta.merge_cells(start_row=curr_row, start_column=1, end_row=curr_row, end_column=3)
        curr_row += 1
        
        for key, val in items:
            k_cell = ws_meta.cell(row=curr_row, column=1, value=key)
            k_cell.font = Font(name="Calibri", size=10, bold=True, color="1E1B4B")
            k_cell.alignment = Alignment(horizontal="left", vertical="top")
            
            v_cell = ws_meta.cell(row=curr_row, column=2, value=val)
            v_cell.font = Font(name="Calibri", size=10, color="0F172A")
            v_cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
            ws_meta.merge_cells(start_row=curr_row, start_column=2, end_row=curr_row, end_column=3)
            ws_meta.row_dimensions[curr_row].height = 36
            curr_row += 1
        curr_row += 1

    ws_meta.column_dimensions["A"].width = 30
    ws_meta.column_dimensions["B"].width = 50
    ws_meta.column_dimensions["C"].width = 50

    output_path = os.path.join("d:\\ECC\\ECC\\AI Venture Studio\\backend\\knowledge_base", "industry_sme_knowledge_base.xlsx")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    wb.save(output_path)
    print(f"Successfully created: {output_path}")

if __name__ == "__main__":
    create_knowledge_base()
