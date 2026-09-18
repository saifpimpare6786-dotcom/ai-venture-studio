import React, { useState } from 'react';
import { 
  Building2, Globe, Target, DollarSign, FileSpreadsheet, 
  ArrowRight, ArrowLeft, Upload, CheckCircle2, Sparkles, 
  Users, Clock, Milestone, FileText, BookmarkCheck
} from 'lucide-react';
import { api } from '../lib/api';

const PRESET_BRIEFS = [
  {
    id: 'aiventurestudio',
    title: 'AI Venture Studio — Autonomous Incubation SaaS',
    tag: 'India • B2B SaaS • Enterprise',
    data: {
      name: 'AI Venture Studio',
      industry: 'B2B SaaS',
      target_country: 'India',
      currency: 'INR',
      stage: 'prototype',
      problem_statement: "India has one of the world's largest startup ecosystems with 1.5 lakh+ DPIIT-recognised startups, but early-stage founders — especially first-time and tier-2/3 city founders — lack affordable access to rigorous business validation. Professional feasibility studies, financial models, and investor-readiness assessments require costly consultants (often ₹ lakhs) or finance/strategy expertise founders don't have. Consequently, most ideas are launched under-validated or fail from avoidable, un-surfaced flaws. Simultaneously, startup incubators, university e-cells, and early-stage investors face a mirror bottleneck: no fast, objective, standardized way to screen large cohorts of applicants at scale.",
      solution_description: "AI Venture Studio turns a single structured business idea into a complete, investment-grade venture evaluation — 13 institutional reports (comprehensive Business Plan, Financial Projections, Unit Economics, SWOT, PESTLE, Porter's Five Forces, Competitor Intelligence, Risk & Moat Audit, Investor Deck Outline, Go-To-Market strategy) plus a quantified 0–100 Viability Score — in under 2 minutes. Powered by a specialized multi-agent pipeline (Strategy, Finance, Marketing, Risk/Compliance agents), an adversarial Critic that stress-tests assumptions, and a deterministic financial rules engine ensuring cross-report math consistency. Grounded in live market data and India-specific regulatory frameworks (DPDPA, GST, DPIIT).",
      target_customers: "Early-stage & aspiring startup founders across India (especially first-time and Tier-2/3 founders lacking finance/strategy backgrounds), student entrepreneurs & university E-Cells, DPIIT startup incubators/accelerators, and angel networks/micro-VCs needing automated deal screening.",
      customer_segment: 'B2B Mid-Market / SMB',
      competitors: "Traditional business consulting firms (Big 4 / boutique consultancies), generic LLMs (ChatGPT, Claude without business validation rules), Upmetrics, LivePlan, and manual Excel templates.",
      revenue_model: "Tiered B2B/B2C SaaS subscriptions billed in INR by usage (ventures analyzed, report depth, team seats) + institutional cohort screening licenses for incubators/accelerators + premium document export add-ons.",
      pricing_strategy: "Starter at ₹1499/month (Solo Founders: 3 ventures/mo, core reports), Professional at ₹3,999/month (Unlimited ventures, full 13 reports, PDF/DOCX exports, financial models), Enterprise/Cohort at ₹29,999/month (Incubators/VCs: 50+ cohort screening, ranked scoring, API & team seats).",
      budget: 50000,
      preferred_funding: 500000,
      team_size: 4,
      timeline: '18 months',
      goals_text: "1. Build an India-specific compliance, tax (GST), and market knowledge base for jurisdiction-aware venture analysis\n2. Onboard 2,000 paying founders and 25+ incubator/investor clients in year one\n3. Add regional-language report generation for 5 major Indian languages (Hindi, Tamil, Telugu, Marathi, Bengali)\n4. Scale to 25,000+ active founders and 100+ institutional clients to reach ₹5 Crore ARR by Month 24",
      notes: "Fully aligned with India's DPIIT Startup India framework and Digital Personal Data Protection Act (DPDPA 2023). Total serviceable addressable market (SAM) estimated at ₹500–1,000 Crore across 1.5L+ startups and 500+ incubators."
    }
  },
  {
    id: 'medisetu',
    title: 'MediSetu — ABDM HealthTech SaaS',
    tag: 'India • HealthTech • B2B',
    data: {
      name: 'MediSetu',
      industry: 'HealthTech',
      target_country: 'India',
      currency: 'INR',
      stage: 'prototype',
      problem_statement: "Over 1 million small private clinics and 40,000+ nursing homes in India still rely on paper registers and unencrypted WhatsApp chats, resulting in lost patient histories, rampant billing errors, and zero analytics. Furthermore, the Indian government's mandatory Ayushman Bharat Digital Mission (ABDM) pushes clinics to digitize, yet existing Hospital Information Systems (HIS) are prohibitively expensive (₹15,000+/mo), overly complex, and unusable for non-tech-savvy doctors in tier-2/3 cities.",
      solution_description: 'MediSetu is a lightweight, mobile-first cloud EHR and clinic management SaaS built specifically for India\'s small healthcare practices. It combines patient digital health records (EHR), smart appointment scheduling, automated GST billing, and pharmacy inventory in one unified dashboard. MediSetu is ABDM-compliant out-of-the-box (instant ABHA health-ID generation), operates on low-end hardware with offline-first synchronization for patchy internet, and supports regional Indian languages.',
      target_customers: 'Solo-practitioner clinics, multi-doctor polyclinics, specialty dental/pediatric practices, and small nursing homes (5–50 beds) in Tier-2 and Tier-3 Indian cities managed by time-poor, cost-sensitive doctors and clinic administrators.',
      customer_segment: 'B2B Mid-Market / SMB',
      competitors: 'Practo Prime, Eka Care, Doc-on, Qikwell, and legacy pen-and-paper / unorganized WhatsApp workflows.',
      revenue_model: 'Tiered B2B SaaS monthly/annual per-clinic subscriptions + value-added transaction fees on e-pharmacy orders, teleconsultation routing, and insurance claim processing.',
      pricing_strategy: 'Starter at ₹999/month (Solo Doctors: EHR, Appointments, Basic Billing), Professional at ₹2,499/month (Polyclinics: ABDM/ABHA integration, Pharmacy, Multi-staff), Enterprise at ₹6,999/month (Nursing Homes: Inpatient, Analytics & Priority Support).',
      budget: 50000,
      preferred_funding: 500000,
      team_size: 4,
      timeline: '18 months',
      goals_text: "1. Achieve full ABDM (Ayushman Bharat Digital Mission) M1, M2 & M3 certification\n2. Onboard 500 paying clinics across Tier-2/3 pilot clusters in Year 1\n3. Expand regional language localization to 5 states (Hindi, Marathi, Telugu, Tamil, Bengali)\n4. Scale to 10,000+ active clinics and achieve ₹5 Crore ARR by Month 24",
      notes: "Compliant with India's Digital Personal Data Protection Act (DPDPA 2023) and ABDM health data governance frameworks. Serviceable addressable market (SAM) estimated at ₹3,000–5,000 Crore."
    }
  },
  {
    id: 'synthetix',
    title: 'Synthetix Risk — Autonomous AI Compliance',
    tag: 'USA • B2B AI • Enterprise',
    data: {
      name: 'Synthetix Risk',
      industry: 'AI & Automation',
      target_country: 'United States',
      currency: 'USD',
      stage: 'prototype',
      problem_statement: "Enterprise financial institutions and health providers spend over $380B annually on manual regulatory compliance checks (SOC2, HIPAA, EU AI Act, FINRA), taking months to review internal AI workflows and data governance policies with 34% human audit failure rates.",
      solution_description: 'Synthetix Risk is an autonomous multi-agent audit pipeline that continuously stress-tests enterprise LLM applications and data pipelines for regulatory compliance, data leakage, and statutory violations in real-time with zero human code changes.',
      target_customers: 'Chief Information Security Officers (CISOs), Chief Risk Officers (CROs), and enterprise engineering leads at FinTech, HealthTech, and Fortune 500 SaaS companies.',
      customer_segment: 'B2B Enterprise',
      competitors: 'OneTrust, Vanta, Drata, BigID, and legacy manual consulting firms (Big 4 audit practices).',
      revenue_model: 'Annual recurring enterprise SaaS contracts based on monitored agent nodes and compliance volume.',
      pricing_strategy: 'Starter at $499/month (10 Agent Nodes), Professional at $1,499/month (50 Nodes + Real-time Sentry), Enterprise at $4,999/month (Unlimited Nodes, Dedicated SOC2 Assurance & SLA).',
      budget: 150000,
      preferred_funding: 1500000,
      team_size: 5,
      timeline: '12 months',
      goals_text: "1. Complete SOC2 Type II and HIPAA automated certification modules\n2. Secure 15 Fortune 500 paid enterprise pilot contracts\n3. Expand real-time inference monitoring to support Claude, OpenAI, and Llama 3 deployments\n4. Reach $3M ARR by Month 18",
      notes: "Directly solves EU AI Act Article 14 human oversight and US SEC automated trading algorithmic compliance mandates."
    }
  },
  {
    id: 'paynexus',
    title: 'PayNexus — Real-time Cross-Border FX Engine',
    tag: 'UK • FinTech • Global',
    data: {
      name: 'PayNexus',
      industry: 'FinTech',
      target_country: 'United Kingdom',
      currency: 'GBP',
      stage: 'early_revenue',
      problem_statement: "Mid-market UK & European exporters lose 2.8% to 4.5% on cross-border FX spread and settlement fees when paying overseas suppliers, suffering 3–5 day settlement delays via legacy SWIFT routing.",
      solution_description: 'PayNexus is an intelligent B2B treasury and instant cross-border settlement rails integrating local payment networks (FCA regulated) to deliver sub-10 second FX conversion at wholesale interbank rates + 0.25% transparent spread.',
      target_customers: 'UK & EU mid-market e-commerce merchants, wholesale import/export firms, and digital global agencies with £1M–£50M annual cross-border transaction volume.',
      customer_segment: 'B2B Mid-Market / SMB',
      competitors: 'Wise Business, Airwallex, Revolut Business, traditional tier-1 commercial banks (Barclays, HSBC).',
      revenue_model: 'Volume-based basis point fee (25 bps on FX conversions) + £199/month treasury SaaS subscription for multi-currency automated hedging.',
      pricing_strategy: 'Starter at £99/month (up to £50k FX/mo), Growth at £299/month (up to £250k FX/mo + hedging), Enterprise at £799/month (unlimited FX + dedicated treasury API).',
      budget: 100000,
      preferred_funding: 1200000,
      team_size: 6,
      timeline: '15 months',
      goals_text: "1. Secure full UK FCA Authorized Payment Institution (API) license\n2. Process £50M in quarterly annualized payment volume\n3. Integrate 12 local currency clearing corridors across APAC and Latin America\n4. Achieve £2M annual Net Revenue Run-rate",
      notes: "Fully integrated with Bank of England Faster Payments Scheme and SEPA Instant rails."
    }
  }
];

export function BusinessIdeaWizard({ onComplete }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [activePreset, setActivePreset] = useState(PRESET_BRIEFS[0].id);
  const [formData, setFormData] = useState(PRESET_BRIEFS[0].data);

  const applyPreset = (preset) => {
    setActivePreset(preset.id);
    setFormData(preset.data);
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleFileUpload = async (e) => {
    const files = Array.from(e.target.files);
    setUploadedFiles(prev => [...prev, ...files]);
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      const goalsArray = formData.goals_text
        .split('\n')
        .map(g => g.replace(/^\d+[\.\)]\s*/, '').trim())
        .filter(Boolean);

      const { goals_text, ...restData } = formData;
      const payload = {
        ...restData,
        goals: goalsArray
      };

      const project = await api.createProject(payload);
      
      for (const f of uploadedFiles) {
        try {
          await api.uploadDocument(project.id, f);
        } catch (err) {
          console.error(`Failed to upload ${f.name}:`, err);
        }
      }

      await api.generateReports(project.id);
      onComplete(project);
    } catch (err) {
      alert('Error creating venture: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-10 px-4">
      {/* Fast Load Preset Briefs Bar */}
      <div className="mb-6 glass-panel-gold p-4 rounded-2xl border border-gold-500/30 space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BookmarkCheck className="w-4 h-4 text-gold-400" />
            <span className="text-xs font-bold text-white uppercase tracking-wider font-display">
              Select Consulting Engagement Template
            </span>
          </div>
          <span className="text-[10px] text-gold-300/80 font-mono">1-Click Fast Fill</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {PRESET_BRIEFS.map((p) => {
            const isSelected = activePreset === p.id;
            return (
              <button
                key={p.id}
                type="button"
                onClick={() => applyPreset(p)}
                className={`p-3.5 rounded-xl text-left transition-all btn-press border card-tilt-hover ${
                  isSelected 
                    ? 'bg-gradient-to-br from-gold-500/25 via-slate-900 to-slate-950 border-gold-400 shadow-xl shadow-gold-500/15 scale-[1.02]' 
                    : 'bg-slate-900/80 border-white/10 hover:border-gold-500/40'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-white line-clamp-1">{p.title}</span>
                  {isSelected && (
                    <span className="w-2 h-2 rounded-full bg-gold-400 animate-pulse" />
                  )}
                </div>
                <div className="text-[10px] text-gold-300/80 font-mono">{p.tag}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Progress Bar & Step Pills */}
      <div className="mb-8 space-y-3">
        <div className="grid grid-cols-4 gap-2">
          {[
            { num: 1, name: 'Charter' },
            { num: 2, name: '10x Solution' },
            { num: 3, name: 'Market & Moats' },
            { num: 4, name: 'Cap & Milestones' },
          ].map((s) => (
            <button
              key={s.num}
              type="button"
              onClick={() => setStep(s.num)}
              className={`py-2 px-2 rounded-xl text-center border transition-all ${
                step === s.num
                  ? 'bg-gold-500/20 border-gold-500/50 text-white font-bold shadow-md shadow-gold-500/10'
                  : step > s.num
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400 font-medium'
                  : 'bg-white/5 border-white/5 text-slate-500'
              }`}
            >
              <div className="text-[10px] font-mono uppercase">Step {s.num}</div>
              <div className="text-xs truncate">{s.name}</div>
            </button>
          ))}
        </div>
        <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-gold-500 via-primary-500 to-emerald-400 transition-all duration-300 rounded-full"
            style={{ width: `${(step / 4) * 100}%` }}
          />
        </div>
      </div>

      <div className="glass-panel p-8 rounded-2xl border border-white/10 shadow-2xl relative specular-border">
        {/* Step 1: Core Concept */}
        {step === 1 && (
          <div className="space-y-6 animate-step-slide">
            <div className="border-b border-white/10 pb-4">
              <h2 className="text-lg font-bold text-white flex items-center gap-2 font-display">
                <Building2 className="w-5 h-5 text-gold-400" />
                <span>1. Venture Charter & Strategic Identity</span>
              </h2>
              <p className="text-xs text-slate-400 mt-1">Specify your venture entity, core industry vertical, and regulatory jurisdiction.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Venture / Startup Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleChange('name', e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl glass-input text-sm font-semibold"
                  placeholder="e.g. MediSetu"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Industry Domain</label>
                <select
                  value={formData.industry}
                  onChange={(e) => handleChange('industry', e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl glass-input text-sm"
                >
                  <option value="HealthTech">HealthTech / Digital Health</option>
                  <option value="B2B SaaS">B2B SaaS / Enterprise</option>
                  <option value="FinTech">FinTech / Payments</option>
                  <option value="E-Commerce">E-Commerce / Consumer</option>
                  <option value="CleanTech">CleanTech / ESG</option>
                  <option value="AI & Automation">AI & Automation</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Target Country (Jurisdiction)</label>
                <select
                  value={formData.target_country}
                  onChange={(e) => {
                    const country = e.target.value;
                    const cur = country === 'India' ? 'INR' : country === 'United Kingdom' ? 'GBP' : country === 'European Union' ? 'EUR' : 'USD';
                    handleChange('target_country', country);
                    handleChange('currency', cur);
                  }}
                  className="w-full px-4 py-2.5 rounded-xl glass-input text-sm"
                >
                  <option value="India">India (INR ₹)</option>
                  <option value="United Kingdom">United Kingdom (GBP £)</option>
                  <option value="United States">United States (USD $)</option>
                  <option value="European Union">European Union (EUR €)</option>
                  <option value="Global">Global / Other (USD $)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Current Stage</label>
                <select
                  value={formData.stage}
                  onChange={(e) => handleChange('stage', e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl glass-input text-sm"
                >
                  <option value="prototype">Prototype / MVP Built</option>
                  <option value="idea">Idea / Concept Stage</option>
                  <option value="early_revenue">Early Revenue / Pilots</option>
                  <option value="scaling">Growth / Scaling</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Problem & Solution */}
        {step === 2 && (
          <div className="space-y-6 animate-step-slide">
            <div className="border-b border-white/10 pb-4">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Target className="w-5 h-5 text-emerald-400" />
                <span>2. Problem & Proposed Solution</span>
              </h2>
              <p className="text-xs text-slate-400 mt-1">Clearly describe the acute market friction and your technological solution.</p>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Problem Statement</label>
              <textarea
                rows={4}
                value={formData.problem_statement}
                onChange={(e) => handleChange('problem_statement', e.target.value)}
                className="w-full px-4 py-3 rounded-xl glass-input text-sm leading-relaxed"
                placeholder="What is the exact pain point, who suffers from it, and what does it cost them?"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Solution & Value Proposition</label>
              <textarea
                rows={4}
                value={formData.solution_description}
                onChange={(e) => handleChange('solution_description', e.target.value)}
                className="w-full px-4 py-3 rounded-xl glass-input text-sm leading-relaxed"
                placeholder="How does your product solve this pain point 10x better than existing alternatives?"
              />
            </div>
          </div>
        )}

        {/* Step 3: Market & Audience */}
        {step === 3 && (
          <div className="space-y-6 animate-step-slide">
            <div className="border-b border-white/10 pb-4">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Globe className="w-5 h-5 text-amber-400" />
                <span>3. Market, Audience & Moats</span>
              </h2>
              <p className="text-xs text-slate-400 mt-1">Identify your buyer personas and competitive positioning.</p>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Target Customer ICP (Ideal Customer Profile)</label>
              <textarea
                rows={3}
                value={formData.target_customers}
                onChange={(e) => handleChange('target_customers', e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl glass-input text-sm"
                placeholder="e.g. Solo-practitioner clinics, polyclinics in Tier-2/3 cities"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Customer Segment</label>
                <select
                  value={formData.customer_segment}
                  onChange={(e) => handleChange('customer_segment', e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl glass-input text-sm"
                >
                  <option value="B2B Mid-Market / SMB">B2B Mid-Market / SMB</option>
                  <option value="B2B Enterprise">B2B Enterprise</option>
                  <option value="B2C Consumer">B2C Consumer</option>
                  <option value="B2B2C Marketplace">B2B2C Marketplace</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Key Competitors</label>
                <input
                  type="text"
                  value={formData.competitors}
                  onChange={(e) => handleChange('competitors', e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl glass-input text-sm"
                  placeholder="e.g. Practo Prime, Eka Care, Doc-on, Paper & WhatsApp"
                />
              </div>
            </div>
          </div>
        )}

        {/* Step 4: Financials, Team, Milestones & Uploads */}
        {step === 4 && (
          <div className="space-y-6 animate-step-slide">
            <div className="border-b border-white/10 pb-4">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <DollarSign className="w-5 h-5 text-primary-400" />
                <span>4. Monetization, Capital, Team & Milestones</span>
              </h2>
              <p className="text-xs text-slate-400 mt-1">Specify pricing, capital ask, team headcount, milestones, and upload financial sheets.</p>
            </div>

            {/* Revenue & Pricing */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Revenue Model</label>
                <input
                  type="text"
                  value={formData.revenue_model}
                  onChange={(e) => handleChange('revenue_model', e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl glass-input text-sm"
                  placeholder="e.g. Monthly Tiered Subscription + Transaction Fees"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Pricing Strategy & Tiers</label>
                <input
                  type="text"
                  value={formData.pricing_strategy}
                  onChange={(e) => handleChange('pricing_strategy', e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl glass-input text-sm"
                  placeholder="e.g. Starter ₹999/mo, Pro ₹2,499/mo, Enterprise ₹6,999/mo"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Launch Budget / Capital Reserve ({formData.currency})</label>
                <input
                  type="number"
                  value={formData.budget}
                  onChange={(e) => handleChange('budget', Number(e.target.value))}
                  className="w-full px-4 py-2.5 rounded-xl glass-input text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Target Funding Requirement ({formData.currency})</label>
                <input
                  type="number"
                  value={formData.preferred_funding}
                  onChange={(e) => handleChange('preferred_funding', Number(e.target.value))}
                  className="w-full px-4 py-2.5 rounded-xl glass-input text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5 flex items-center gap-1">
                  <Users className="w-3.5 h-3.5 text-primary-400" />
                  <span>Founding Team Headcount</span>
                </label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={formData.team_size}
                  onChange={(e) => handleChange('team_size', Number(e.target.value))}
                  className="w-full px-4 py-2.5 rounded-xl glass-input text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5 flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-amber-400" />
                  <span>Execution Timeline</span>
                </label>
                <input
                  type="text"
                  value={formData.timeline}
                  onChange={(e) => handleChange('timeline', e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl glass-input text-sm"
                  placeholder="e.g. 18 months"
                />
              </div>
            </div>

            {/* Strategic Milestones */}
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5 flex items-center gap-1">
                <Milestone className="w-3.5 h-3.5 text-emerald-400" />
                <span>Strategic Business Milestones (1 per line)</span>
              </label>
              <textarea
                rows={3}
                value={formData.goals_text}
                onChange={(e) => handleChange('goals_text', e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl glass-input text-sm font-mono text-xs leading-relaxed"
                placeholder="1. Achieve ABDM certification&#10;2. Onboard 500 clinics&#10;3. Expand to 5 states"
              />
            </div>

            {/* Additional Notes & Regulatory Context */}
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5 flex items-center gap-1">
                <FileText className="w-3.5 h-3.5 text-indigo-400" />
                <span>Additional Notes & Regulatory Context (e.g. DPDPA, ABDM, SAM)</span>
              </label>
              <textarea
                rows={2}
                value={formData.notes}
                onChange={(e) => handleChange('notes', e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl glass-input text-sm"
                placeholder="Any special statutory compliance, tax schemes, or market context..."
              />
            </div>

            {/* Document Upload Area */}
            <div className="pt-2 border-t border-white/10">
              <label className="block text-xs font-medium text-slate-300 mb-2 flex items-center gap-1.5">
                <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
                <span>Upload Financial Model, Pitch Deck or Research (Excel .xlsx, CSV, PDF, DOCX)</span>
              </label>
              
              <div className="border-2 border-dashed border-white/15 rounded-xl p-5 text-center hover:border-primary-500/50 spring-hover transition-all relative cursor-pointer">
                <input 
                  type="file" 
                  multiple 
                  accept=".xlsx,.xls,.csv,.pdf,.docx,.pptx"
                  onChange={handleFileUpload} 
                  className="absolute inset-0 opacity-0 cursor-pointer"
                />
                <Upload className="w-7 h-7 text-slate-400 mx-auto mb-1.5" />
                <p className="text-xs font-medium text-slate-200">Drag & drop files or click to browse</p>
                <p className="text-[11px] text-slate-500 mt-0.5">Supports Excel spreadsheets with financial models, PDFs, and slide decks</p>
              </div>

              {uploadedFiles.length > 0 && (
                <div className="mt-3 space-y-1.5">
                  {uploadedFiles.map((file, idx) => (
                    <div key={idx} className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-lg border border-emerald-500/20 spring-hover">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>{file.name} ({(file.size / 1024).toFixed(1)} KB)</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Wizard Controls */}
        <div className="flex items-center justify-between mt-8 pt-6 border-t border-white/10">
          {step > 1 ? (
            <button
              onClick={() => setStep(step - 1)}
              className="px-4 py-2 text-sm text-slate-300 hover:text-white flex items-center gap-2 rounded-xl glass-input btn-press"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Previous</span>
            </button>
          ) : <div />}

          {step < 4 ? (
            <button
              onClick={() => setStep(step + 1)}
              className="px-6 py-2.5 text-sm bg-primary-600 hover:bg-primary-500 text-white font-medium flex items-center gap-2 rounded-xl shadow-lg shadow-primary-600/30 btn-press transition-all"
            >
              <span>Continue</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="px-8 py-3 text-sm bg-gradient-to-r from-primary-600 to-emerald-500 hover:from-primary-500 hover:to-emerald-400 text-white font-semibold flex items-center gap-2.5 rounded-xl shadow-lg shadow-emerald-500/20 btn-press transition-all disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4" />
              <span>{loading ? 'Initiating Deliberation...' : 'Launch Autonomous Boardroom'}</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
