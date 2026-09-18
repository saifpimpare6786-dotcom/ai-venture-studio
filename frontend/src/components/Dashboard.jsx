import React, { useState, useEffect } from 'react';
import { 
  FileText, BarChart3, ShieldCheck, Download, ExternalLink, 
  Sparkles, CheckCircle, AlertTriangle, Sliders, Layers, ArrowLeft, RefreshCw, Trash2, Target,
  ChevronDown, Info, Scale, Zap, Building, MessageSquare, Calendar, Lock, Mail, Rocket
} from 'lucide-react';
import { 
  Radar, RadarChart, PolarGrid, PolarAngleAxis, 
  PolarRadiusAxis, ResponsiveContainer 
} from 'recharts';
import { VentureSimulator } from './VentureSimulator';
import { ReportContentRenderer } from './ReportContentRenderer';
import { RadialGauge, MiniSparkline } from './ConsultingVisuals';
import { RedTeamShockConsole } from './RedTeamShockConsole';
import { AgentQACockpit } from './AgentQACockpit';
import { TermSheetAnalyzer } from './TermSheetAnalyzer';
import { DpiitDpdpaComplianceHub } from './DpiitDpdpaComplianceHub';
import { BoardroomAudioPlayer } from './BoardroomAudioPlayer';
import { VCPitchSimulator } from './VCPitchSimulator';
import { GtmOutreachGenerator } from './GtmOutreachGenerator';
import { GtmRoadmapGantt } from './GtmRoadmapGantt';
import { TermSheetCompare } from './TermSheetCompare';
import { PartnerInterrogationCockpit } from './PartnerInterrogationCockpit';
import { ArrBridgeWaterfall } from './ConsultingVisuals';
import { useCountUp } from '../hooks/useCountUp';
import { api } from '../lib/api';

const REPORT_CATEGORIES = [
  {
    category: 'Strategic Thesis',
    icon: Sparkles,
    tabs: [
      { id: 'executive_summary', label: 'Executive Summary', icon: Sparkles },
      { id: 'business_model_canvas', label: '9-Block Canvas', icon: Layers },
      { id: 'business_plan', label: 'Business Plan', icon: FileText },
      { id: 'swot_analysis', label: 'SWOT Matrix', icon: BarChart3 },
      { id: 'pestle_analysis', label: 'PESTLE Scope', icon: BarChart3 },
    ]
  },
  {
    category: 'Market & Moats',
    icon: Target,
    tabs: [
      { id: 'competitor_analysis', label: '2×2 Whitespace & Competitors', icon: BarChart3, highlight: true },
      { id: 'gtm_outreach', label: 'GTM Cold Outreach & LOI 🚀', icon: Mail, highlight: true },
      { id: 'gtm_roadmap', label: '90-Day Sprint Gantt 🗺️', icon: Calendar, highlight: true },
      { id: 'porters_five_forces', label: "Porter's 5 Forces", icon: BarChart3 },
      { id: 'marketing_gtm', label: 'GTM & ICP Strategy', icon: FileText },
    ]
  },
  {
    category: 'Financials & Modeling',
    icon: Sliders,
    tabs: [
      { id: 'simulator', label: 'Sensitivity Simulator ⚡', icon: Sliders, highlight: true, featured: true },
      { id: 'financial_projection', label: '3-Year Financials', icon: BarChart3 },
      { id: 'investment_readiness', label: 'Investment Memo', icon: ShieldCheck },
    ]
  },
  {
    category: 'Risk, ESG & Pitch',
    icon: ShieldCheck,
    tabs: [
      { id: 'risk_matrix', label: 'Risk & Statutory Audit', icon: AlertTriangle },
      { id: 'esg_sustainability', label: 'ESG & Governance', icon: ShieldCheck },
      { id: 'pitch_deck', label: '16:9 Pitch Slides', icon: FileText, highlight: true },
    ]
  },
  {
    category: 'Advisory & Deal Tools',
    icon: Zap,
    tabs: [
      { id: 'partner_interrogation', label: 'VC Partner Interrogation 🎙️', icon: Target, highlight: true, featured: true },
      { id: 'vc_pitch', label: 'VC Objection Coach 🤝', icon: Target, highlight: true },
      { id: 'red_team', label: 'Red-Team Crisis Shock ⚡', icon: AlertTriangle, highlight: true },
      { id: 'term_sheet_compare', label: 'Term Sheet Battles ⚔️', icon: Scale },
      { id: 'agent_qa', label: 'Agent Interrogation Q&A', icon: MessageSquare },
      { id: 'term_sheet', label: 'Term Sheet Analyzer', icon: Scale },
      { id: 'india_compliance', label: 'DPIIT & DPDPA Hub 🇮🇳', icon: Building, highlight: true },
    ]
  }
];

// Section numbering map for consulting-style §-references
const SECTION_NUMBERS = {
  'executive_summary': '§1.0',
  'business_model_canvas': '§2.0',
  'business_plan': '§3.0',
  'swot_analysis': '§4.0',
  'pestle_analysis': '§5.0',
  'competitor_analysis': '§6.0',
  'porters_five_forces': '§7.0',
  'marketing_gtm': '§8.0',
  'financial_projection': '§9.0',
  'investment_readiness': '§10.0',
  'risk_matrix': '§11.0',
  'esg_sustainability': '§12.0',
  'pitch_deck': '§13.0',
};

export function Dashboard({ project, reports = [], onBackToWizard, onRerun, onDelete, onRefreshReports }) {
  const [activeTab, setActiveTab] = useState('executive_summary');
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [localReports, setLocalReports] = useState(reports);

  // Sync when parent reports update
  useEffect(() => {
    setLocalReports(reports);
  }, [reports]);

  const scores = {
    overall: project.overall_score || 82.0,
    viability: project.viability_score || 85.0,
    marketFit: project.market_fit_score || 80.0,
    financial: project.financial_score || 80.0
  };

  // Count-up animated values
  const animViability = useCountUp(scores.viability, 1200, 1);
  const animMarketFit = useCountUp(scores.marketFit, 1200, 1);
  const animFinancial = useCountUp(scores.financial, 1200, 1);

  const ratingGrade = scores.overall >= 80 ? 'AAA — INVESTMENT GRADE' : scores.overall >= 65 ? 'AA — VIABLE VENTURE' : 'BBB — GROWTH WEDGE';

  const radarData = [
    { subject: 'Viability', value: scores.viability, fullMark: 100 },
    { subject: 'Market Fit', value: scores.marketFit, fullMark: 100 },
    { subject: 'Financials', value: scores.financial, fullMark: 100 },
    { subject: 'Moat Defensibility', value: 88, fullMark: 100 },
    { subject: 'Regulatory Safety', value: 92, fullMark: 100 },
  ];

  // Simulated sparkline trend data for metric cards
  const sparkViability = [62, 68, 71, 74, 78, 82, scores.viability];
  const sparkMarket = [55, 60, 65, 70, 73, 76, scores.marketFit];
  const sparkFinancial = [58, 64, 68, 72, 75, 78, scores.financial];

  const currentReport = localReports.find(r => r.report_type === activeTab);
  const rules = project.rules_validation || { is_valid: true, errors: [] };

  const handleRegenerateCurrentReport = async () => {
    if (isRegenerating || !SECTION_NUMBERS[activeTab]) return;
    setIsRegenerating(true);
    try {
      const updated = await api.regenerateSingleReport(project.id, activeTab);
      if (updated && updated.content) {
        setLocalReports(prev => {
          const idx = prev.findIndex(r => r.report_type === activeTab);
          if (idx >= 0) {
            const next = [...prev];
            next[idx] = { ...next[idx], content: updated.content, title: updated.title };
            return next;
          } else {
            return [...prev, updated];
          }
        });
      }
      if (onRefreshReports) {
        await onRefreshReports();
      }
    } catch (err) {
      console.error('Failed to regenerate report:', err);
      alert('Report re-synthesis failed: ' + (err.message || err));
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleDownload = (format) => {
    const win = window.open(api.getExportUrl(project.id, format), '_blank', 'noopener,noreferrer');
    if (win) win.opener = null;
  };

  // Calculate core report completion
  const CORE_REPORT_IDS = [
    'executive_summary', 'business_model_canvas', 'business_plan', 'swot_analysis',
    'pestle_analysis', 'competitor_analysis', 'porters_five_forces', 'marketing_gtm',
    'financial_projection', 'investment_readiness', 'risk_matrix', 'esg_sustainability', 'pitch_deck'
  ];
  const completedReports = reports.filter(r => CORE_REPORT_IDS.includes(r.report_type)).length;
  const totalCoreReports = CORE_REPORT_IDS.length;
  const completionPct = Math.min(100, Math.round((completedReports / totalCoreReports) * 100));

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 space-y-6">
      {/* Executive Engagement Summary Strip */}
      <div className="flex items-center gap-3 flex-wrap text-[10px] font-mono text-slate-400 bg-slate-950/60 px-4 py-2.5 rounded-xl border border-white/5">
        <span className="text-gold-400 font-bold uppercase tracking-wider">Engagement Brief</span>
        <span className="w-px h-3 bg-white/10" />
        <span className="text-slate-200 font-semibold">{project.name}</span>
        <span className="w-px h-3 bg-white/10" />
        <span>{project.industry}</span>
        <span className="w-px h-3 bg-white/10" />
        <span>{project.target_country} ({project.currency || 'USD'})</span>
        <span className="w-px h-3 bg-white/10" />
        <span className="text-emerald-400 font-bold tabular-nums">
          {completedReports}/{totalCoreReports} Deliverables ({completionPct}%) • 8 Advisory Tools Active
        </span>
        <span className="w-px h-3 bg-white/10" />
        {rules.is_valid ? (
          <span className="text-emerald-400 flex items-center gap-1">
            <CheckCircle className="w-3 h-3" />
            Rule Sentry: Coherent
          </span>
        ) : (
          <span className="text-amber-400 flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" />
            Rule Penalty Active
          </span>
        )}
        <span className="w-px h-3 bg-white/10" />
        <span className="text-slate-500">REF: APX-{String(project.id || '').slice(0, 8).toUpperCase()}</span>
      </div>

      {/* Top Consulting Header Bar */}
      <div className="glass-panel-gold p-6 rounded-2xl border border-gold-500/30 shadow-xl space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <button
              onClick={onBackToWizard}
              className="p-2.5 bg-slate-900/80 hover:bg-slate-800 text-slate-300 rounded-xl border border-white/10 text-xs flex items-center gap-1.5 btn-press transition-all"
            >
              <ArrowLeft className="w-4 h-4" />
              <span className="font-semibold hidden sm:inline">New Brief</span>
            </button>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-[10px] uppercase font-mono font-bold text-gold-400 bg-gold-500/10 px-2.5 py-0.5 rounded border border-gold-500/20">
                  CONFIDENTIAL MEMORANDUM
                </span>
                <span className="text-[10px] font-mono text-slate-400">
                  REF: APX-{String(project.id || '').slice(0, 8).toUpperCase()}
                </span>
              </div>
              <h1 className="text-2xl font-bold text-white tracking-tight font-display flex items-center gap-2.5 mt-1">
                <span>{project.name}</span>
                <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-primary-500/20 text-primary-300 border border-primary-500/30">
                  {project.industry} • {project.target_country} ({project.currency || 'USD'})
                </span>
              </h1>
            </div>
          </div>

          {/* Action Buttons & Exports */}
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={onRerun}
              className="px-3.5 py-2 bg-slate-900/80 hover:bg-slate-800 text-slate-200 rounded-xl border border-white/10 text-xs font-semibold flex items-center gap-1.5 btn-press transition-all"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Re-deliberate</span>
            </button>

            <button
              onClick={() => handleDownload('docx')}
              className="px-3.5 py-2 bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 rounded-xl text-xs font-semibold flex items-center gap-1.5 btn-press transition-all"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Word Memo</span>
            </button>

            <button
              onClick={() => handleDownload('pptx')}
              className="px-3.5 py-2 bg-amber-600/20 hover:bg-amber-600/30 text-amber-400 border border-amber-500/30 rounded-xl text-xs font-semibold flex items-center gap-1.5 btn-press transition-all"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Pitch Slides</span>
            </button>

            <button
              onClick={() => handleDownload('pdf')}
              className="px-3.5 py-2 bg-purple-600/20 hover:bg-purple-600/30 text-purple-400 border border-purple-500/30 rounded-xl text-xs font-semibold flex items-center gap-1.5 btn-press transition-all"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Advisory PDF</span>
            </button>

            <button
              onClick={() => handleDownload('xlsx')}
              className="px-3.5 py-2 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 border border-emerald-500/30 rounded-xl text-xs font-semibold flex items-center gap-1.5 btn-press transition-all shadow-md shadow-emerald-600/10"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Excel Model (.xlsx)</span>
            </button>

            {onDelete && (
              <button
                onClick={onDelete}
                title="Delete Memorandum"
                className="p-2 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 rounded-xl text-xs font-semibold flex items-center gap-1 btn-press transition-all"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Score Header & Radar Overview */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Overall Score & Sub-scores */}
        <div className="md:col-span-8 glass-panel p-6 rounded-2xl border border-white/10 flex flex-col justify-between specular-border">
          <div>
            <div className="flex items-center justify-between border-b border-white/10 pb-3 mb-4">
              <div>
                <span className="text-xs uppercase font-bold text-slate-400 tracking-wider block font-mono">
                  Autonomous Venture Readiness Score
                </span>
                <span className="text-xs font-bold text-gold-400 font-display mt-0.5 block flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>{ratingGrade}</span>
                </span>
              </div>
              <div className="flex items-center gap-2">
                {rules.is_valid ? (
                  <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">
                    <CheckCircle className="w-3.5 h-3.5" />
                    <span>Rule Sentry 100% Coherent</span>
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-[11px] font-semibold text-amber-400 bg-amber-500/10 px-2.5 py-1 rounded-full border border-amber-500/20">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span>Rule Penalty Applied</span>
                  </span>
                )}
              </div>
            </div>

            {/* Radial Gauge + Mini Executive Tags */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-6 mb-6">
              <div className="flex items-center gap-6">
                <RadialGauge 
                  score={scores.overall} 
                  size={180} 
                  label="Readiness"
                  grade={ratingGrade}
                />
              </div>

              {/* Mini Executive Tags */}
              <div className="flex flex-col gap-2">
                <span className="text-[10px] font-mono text-cyan-300 bg-cyan-500/10 px-2.5 py-1 rounded-lg border border-cyan-500/20">
                  LTV:CAC &gt; 3.5×
                </span>
                <span className="text-[10px] font-mono text-gold-300 bg-gold-500/10 px-2.5 py-1 rounded-lg border border-gold-500/20">
                  Payback &lt; 12 Mo
                </span>
                <span className="text-[10px] font-mono text-emerald-300 bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/20 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  ▲ Top 5% Benchmark
                </span>
              </div>
            </div>

            {/* 3 Metric Gauges with Sparklines */}
            <div className="grid grid-cols-3 gap-3.5">
              <div className="bg-slate-900/80 p-4 rounded-xl border border-white/10 spring-hover card-tilt-hover">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Viability</span>
                  <span className="text-[10px] font-mono text-primary-400 font-bold">35% Weight</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-2xl font-bold text-primary-400 font-mono">{animViability}</span>
                  <MiniSparkline data={sparkViability} color="#6366F1" />
                </div>
                <div className="w-full bg-white/10 h-2 rounded-full mt-2 overflow-hidden">
                  <div className="bg-gradient-to-r from-primary-600 to-primary-400 h-full rounded-full transition-all duration-700 ease-out" style={{ width: `${scores.viability}%` }} />
                </div>
              </div>

              <div className="bg-slate-900/80 p-4 rounded-xl border border-white/10 spring-hover card-tilt-hover">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Market Wedge</span>
                  <span className="text-[10px] font-mono text-emerald-400 font-bold">35% Weight</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-2xl font-bold text-emerald-400 font-mono">{animMarketFit}</span>
                  <MiniSparkline data={sparkMarket} color="#10B981" />
                </div>
                <div className="w-full bg-white/10 h-2 rounded-full mt-2 overflow-hidden">
                  <div className="bg-gradient-to-r from-emerald-600 to-emerald-400 h-full rounded-full transition-all duration-700 ease-out" style={{ width: `${scores.marketFit}%` }} />
                </div>
              </div>

              <div className="bg-slate-900/80 p-4 rounded-xl border border-white/10 spring-hover card-tilt-hover">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Financials</span>
                  <span className="text-[10px] font-mono text-gold-400 font-bold">30% Weight</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-2xl font-bold text-gold-400 font-mono">{animFinancial}</span>
                  <MiniSparkline data={sparkFinancial} color="#D4AF37" />
                </div>
                <div className="w-full bg-white/10 h-2 rounded-full mt-2 overflow-hidden">
                  <div className="bg-gradient-to-r from-gold-600 to-gold-400 h-full rounded-full transition-all duration-700 ease-out" style={{ width: `${scores.financial}%` }} />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Radar Chart */}
        <div className="md:col-span-4 glass-panel p-4 rounded-2xl border border-white/10 flex items-center justify-center spring-hover">
          <div className="w-full h-56">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData}>
                <PolarGrid stroke="#334155" opacity={0.4} />
                <PolarAngleAxis dataKey="subject" stroke="#94A3B8" fontSize={10} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#475569" fontSize={8} />
                <Radar name="Readiness" dataKey="value" stroke="#D4AF37" fill="#D4AF37" fillOpacity={0.35} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Voice Deliberation Audio Player */}
      <BoardroomAudioPlayer projectName={project.name} />

      {/* Categorized 5-Pillar Tab Navigation */}
      <div className="space-y-3 glass-panel p-4 rounded-2xl border border-white/10">
        <div className="text-[11px] font-mono uppercase font-bold text-slate-400 tracking-wider">
          Consulting Deliverables & Institutional Strategy Suite
        </div>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
          {REPORT_CATEGORIES.map((cat, catIdx) => (
            <div key={catIdx} className="bg-slate-900/60 p-3 rounded-xl border border-white/5 space-y-2">
              <div className="text-[11px] font-bold text-gold-400 flex items-center gap-1.5 border-b border-white/5 pb-1.5">
                <cat.icon className="w-3.5 h-3.5" />
                <span>{cat.category}</span>
              </div>
              <div className="flex flex-col gap-1">
                {cat.tabs.map((tab) => {
                  const Icon = tab.icon;
                  const isActive = activeTab === tab.id;
                  const sectionNum = SECTION_NUMBERS[tab.id];
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold transition-all text-left btn-press ${
                        tab.featured && isActive
                          ? 'bg-gradient-to-r from-primary-600 via-indigo-600 to-emerald-600 text-white shadow-md'
                          : tab.featured
                          ? 'bg-primary-500/10 text-primary-300 border border-primary-500/30 hover:bg-primary-500/20'
                          : isActive
                          ? 'bg-white/15 text-white border border-white/20 shadow-sm'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5 shrink-0" />
                      <span className="truncate">
                        {sectionNum && <span className="text-[10px] font-mono text-slate-500 mr-1.5">{sectionNum}</span>}
                        {tab.label}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Content Area */}
      {activeTab === 'simulator' ? (
        <VentureSimulator project={project} />
      ) : activeTab === 'vc_pitch' ? (
        <VCPitchSimulator projectId={project.id} projectName={project.name} />
      ) : activeTab === 'gtm_outreach' ? (
        <GtmOutreachGenerator projectId={project.id} projectName={project.name} />
      ) : activeTab === 'gtm_roadmap' ? (
        <GtmRoadmapGantt projectName={project.name} />
      ) : activeTab === 'term_sheet_compare' ? (
        <TermSheetCompare projectName={project.name} />
      ) : activeTab === 'red_team' ? (
        <RedTeamShockConsole projectId={project.id} projectName={project.name} />
      ) : activeTab === 'agent_qa' ? (
        <AgentQACockpit projectId={project.id} projectName={project.name} />
      ) : activeTab === 'term_sheet' ? (
        <TermSheetAnalyzer projectId={project.id} projectName={project.name} />
      ) : activeTab === 'india_compliance' ? (
        <DpiitDpdpaComplianceHub projectId={project.id} projectName={project.name} />
      ) : activeTab === 'partner_interrogation' ? (
        <PartnerInterrogationCockpit project={project} />
      ) : (
        <div className="glass-panel p-8 rounded-2xl border border-white/10 shadow-2xl space-y-6">
          <div className="border-b border-white/10 pb-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-2.5">
                {SECTION_NUMBERS[activeTab] && (
                  <span className="text-sm font-mono text-gold-400 bg-gold-500/10 px-2.5 py-1 rounded-lg border border-gold-500/20 font-bold">
                    {SECTION_NUMBERS[activeTab]}
                  </span>
                )}
                <div>
                  <h2 className="text-lg font-bold text-white">
                    {currentReport?.title || activeTab.replace('_', ' ').toUpperCase()}
                  </h2>
                  <p className="text-xs text-slate-400 mt-0.5">Pydantic Coerced Institutional Deliverable</p>
                </div>
              </div>

              {SECTION_NUMBERS[activeTab] && (
                <button
                  onClick={handleRegenerateCurrentReport}
                  disabled={isRegenerating}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-semibold text-gold-400 bg-gold-500/10 hover:bg-gold-500/20 border border-gold-500/30 transition-all btn-press disabled:opacity-50"
                  title="Re-synthesize this section with institutional reasoning"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isRegenerating ? 'animate-spin' : ''}`} />
                  <span>{isRegenerating ? 'Synthesizing...' : 'Regenerate Section'}</span>
                </button>
              )}
            </div>
          </div>

          {activeTab === 'financial_projection' && (
            <div className="mb-6">
              <ArrBridgeWaterfall currency={project.currency} />
            </div>
          )}

          {currentReport?.content ? (
            <ReportContentRenderer content={currentReport.content} reportType={activeTab} project={project} />
          ) : (
            <div className="text-center py-12 text-xs text-slate-500">
              Report content is currently compiling or not yet generated...
            </div>
          )}
        </div>
      )}
    </div>
  );
}
