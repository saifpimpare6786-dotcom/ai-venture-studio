import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, Target, MessageSquare, Send, Sparkles, RefreshCw, 
  Scale, Award, AlertTriangle, CheckCircle2, ChevronRight, UserCheck, Flame 
} from 'lucide-react';
import { api } from '../lib/api';

const PARTNER_PERSONAS = [
  {
    id: 'tier1_general_partner',
    name: 'Marcus Vance',
    firm: 'Benchmark / Sequoia Archetype',
    role: 'Senior General Partner',
    avatar: '🏛️',
    focus: 'Unit Economics & Moat Defensibility',
    badgeColor: 'text-amber-400 bg-amber-500/10 border-amber-500/30'
  },
  {
    id: 'technical_ai_gp',
    name: 'Dr. Aris Thorne',
    firm: 'DeepTech AI Capital',
    role: 'Managing Director',
    avatar: '🔬',
    focus: 'Model Flywheel & Inference Margins',
    badgeColor: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30'
  },
  {
    id: 'growth_equity_shark',
    name: 'Eleanor Sterling',
    firm: 'Global Growth Strategies',
    role: 'Growth Partner',
    avatar: '⚡',
    focus: 'Sales Velocity & NRR Expansion',
    badgeColor: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30'
  }
];

export function PartnerInterrogationCockpit({ project }) {
  const [activeTab, setActiveTab] = useState('interrogation'); // 'interrogation' | 'inversion'
  const [selectedPersona, setSelectedPersona] = useState(PARTNER_PERSONAS[0]);
  const [pitchInput, setPitchInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [interrogationData, setInterrogationData] = useState(null);
  const [history, setHistory] = useState([]);

  // Inversion Analysis State
  const [targetValuation, setTargetValuation] = useState(100000000);
  const [inversionData, setInversionData] = useState(null);
  const [inversionLoading, setInversionLoading] = useState(false);

  // Load opening question when project changes
  useEffect(() => {
    if (project?.id) {
      triggerInterrogation('');
      runInversionAnalysis(100000000);
    }
  }, [project?.id, selectedPersona.id]);

  const triggerInterrogation = async (userPitch = '') => {
    if (!project?.id) return;
    setLoading(true);
    try {
      const updatedHistory = userPitch 
        ? [...history, { role: 'user', content: userPitch }] 
        : history;
      
      const res = await api.partnerInterrogation(project.id, {
        user_pitch: userPitch,
        partner_persona: selectedPersona.id,
        history: updatedHistory
      });

      setInterrogationData(res);
      if (userPitch) {
        setHistory([
          ...updatedHistory, 
          { role: 'partner', content: res.probing_question, critique: res.partner_critique }
        ]);
        setPitchInput('');
      }
    } catch (e) {
      console.error('Partner Interrogation error:', e);
    } finally {
      setLoading(false);
    }
  };

  const runInversionAnalysis = async (val) => {
    if (!project?.id) return;
    setInversionLoading(true);
    try {
      const res = await api.inversionAnalysis(project.id, {
        target_valuation: val,
        revenue_multiple: 12.0
      });
      setInversionData(res);
    } catch (e) {
      console.error('Inversion Analysis error:', e);
    } finally {
      setInversionLoading(false);
    }
  };

  const handleValuationChange = (e) => {
    const val = parseFloat(e.target.value);
    setTargetValuation(val);
  };

  const handleValuationCommit = () => {
    runInversionAnalysis(targetValuation);
  };

  return (
    <div className="space-y-6">
      {/* Top Advisory Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-2xl glass-panel border border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gold-500/10 border border-gold-500/30 flex items-center justify-center text-xl">
            🤝
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-white font-display">VC Partner Advisory Chamber</h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 font-semibold">
                Gemma 4:12B Reasoning Engine
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Interactive partner pitch interrogation and reverse-engineered valuation hurdles.
            </p>
          </div>
        </div>

        {/* View Switcher */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-900/80 rounded-xl border border-white/10">
          <button
            onClick={() => setActiveTab('interrogation')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'interrogation'
                ? 'bg-gradient-to-r from-primary-600 to-indigo-600 text-white shadow'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Live Partner Grilling
          </button>
          <button
            onClick={() => setActiveTab('inversion')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'inversion'
                ? 'bg-gradient-to-r from-primary-600 to-indigo-600 text-white shadow'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            "What Must Be True" Inversion
          </button>
        </div>
      </div>

      {activeTab === 'interrogation' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Partner Selector Column */}
          <div className="space-y-4">
            <span className="text-[10px] font-mono uppercase font-bold text-slate-400 tracking-wider block">
              SELECT DILIGENCE PARTNER
            </span>
            <div className="space-y-2.5">
              {PARTNER_PERSONAS.map((p) => {
                const isSelected = selectedPersona.id === p.id;
                return (
                  <div
                    key={p.id}
                    onClick={() => { setSelectedPersona(p); setHistory([]); }}
                    className={`p-3.5 rounded-xl cursor-pointer border transition-all ${
                      isSelected
                        ? 'bg-white/10 border-gold-500/50 shadow-lg shadow-gold-500/10'
                        : 'bg-white/[0.02] border-white/5 hover:border-white/20 hover:bg-white/[0.04]'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <span className="text-2xl">{p.avatar}</span>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sm text-white">{p.name}</span>
                          {isSelected && <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />}
                        </div>
                        <span className="text-[11px] text-slate-400 block">{p.firm}</span>
                        <span className={`text-[9px] font-mono px-2 py-0.5 rounded border inline-block mt-1 ${p.badgeColor}`}>
                          {p.focus}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Live Diligence Verdict */}
            {interrogationData && (
              <div className="p-4 rounded-xl glass-panel-gold border border-gold-500/30 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono uppercase font-bold text-gold-400">Partner Conviction</span>
                  <span className="text-base font-bold font-mono text-white tabular-nums">
                    {interrogationData.verdict_score || 70}/100
                  </span>
                </div>
                <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden border border-white/5">
                  <div 
                    className="h-full bg-gradient-to-r from-amber-500 via-gold-400 to-emerald-400 transition-all duration-700" 
                    style={{ width: `${interrogationData.verdict_score || 70}%` }}
                  />
                </div>
                <div className="pt-1">
                  <span className="text-[10px] font-mono uppercase text-rose-400 font-bold block flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" /> Flagged Vulnerability:
                  </span>
                  <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                    {interrogationData.fatal_flaw_flagged}
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Interrogation Chamber Feed */}
          <div className="lg:col-span-2 space-y-4">
            <div className="p-5 rounded-2xl glass-panel border border-white/10 space-y-4 min-h-[420px] flex flex-col justify-between">
              {/* Question & Critique Display */}
              <div className="space-y-4">
                <div className="flex items-center justify-between border-b border-white/10 pb-3">
                  <div className="flex items-center gap-2.5">
                    <span className="text-2xl">{selectedPersona.avatar}</span>
                    <div>
                      <h4 className="text-sm font-bold text-white">{selectedPersona.name}</h4>
                      <span className="text-[10px] font-mono text-slate-400">{selectedPersona.title}</span>
                    </div>
                  </div>
                  <button
                    onClick={() => triggerInterrogation('')}
                    disabled={loading}
                    className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-white/5 transition-all text-xs flex items-center gap-1"
                    title="Generate New Question"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-gold-400' : ''}`} />
                    <span className="text-[10px] font-mono">Next Challenge</span>
                  </button>
                </div>

                {loading ? (
                  <div className="py-12 flex flex-col items-center justify-center space-y-3">
                    <div className="w-8 h-8 rounded-full border-2 border-primary-500 border-t-transparent animate-spin" />
                    <span className="text-xs font-mono text-slate-400">
                      Gemma 4:12B stress-testing venture assumptions...
                    </span>
                  </div>
                ) : interrogationData ? (
                  <div className="space-y-4">
                    {/* Partner Critique */}
                    <div className="p-3.5 rounded-xl bg-slate-900/90 border border-white/10 space-y-1.5">
                      <span className="text-[10px] font-mono uppercase font-bold text-amber-400 block flex items-center gap-1">
                        <Flame className="w-3 h-3 text-amber-400" /> Partner Evaluation:
                      </span>
                      <p className="text-xs text-slate-200 leading-relaxed font-sans">
                        "{interrogationData.partner_critique}"
                      </p>
                    </div>

                    {/* Razor-sharp Probing Question */}
                    <div className="p-4 rounded-xl bg-gradient-to-r from-primary-950/60 to-indigo-950/60 border border-primary-500/30 space-y-2">
                      <span className="text-[10px] font-mono uppercase font-bold text-primary-300 block flex items-center gap-1">
                        <Target className="w-3.5 h-3.5" /> Core Probing Question:
                      </span>
                      <h3 className="text-sm font-bold text-white leading-relaxed">
                        "{interrogationData.probing_question}"
                      </h3>
                    </div>

                    {/* Suggested Tactical Defenses */}
                    {interrogationData.suggested_defenses?.length > 0 && (
                      <div className="space-y-1.5 pt-1">
                        <span className="text-[10px] font-mono uppercase text-slate-400 block font-semibold">
                          Recommended Founder Defenses:
                        </span>
                        <div className="flex flex-wrap gap-2">
                          {interrogationData.suggested_defenses.map((def, dIdx) => (
                            <button
                              key={dIdx}
                              onClick={() => setPitchInput(def)}
                              className="text-left px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-[11px] text-slate-300 hover:text-white transition-all flex items-center gap-1.5"
                            >
                              <ChevronRight className="w-3 h-3 text-gold-400 shrink-0" />
                              <span>{def}</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-12 text-slate-500 text-xs">
                    Click "Next Challenge" or select a partner to begin interrogation.
                  </div>
                )}
              </div>

              {/* Founder Response Bar */}
              <div className="pt-4 border-t border-white/10 space-y-2">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    if (pitchInput.trim()) triggerInterrogation(pitchInput);
                  }}
                  className="flex items-center gap-2"
                >
                  <input
                    type="text"
                    value={pitchInput}
                    onChange={(e) => setPitchInput(e.target.value)}
                    placeholder="Defend your venture logic or counter the partner's premise..."
                    className="flex-1 bg-slate-950/90 border border-white/15 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-primary-500 transition-all font-sans"
                  />
                  <button
                    type="submit"
                    disabled={loading || !pitchInput.trim()}
                    className="px-4 py-2.5 bg-gradient-to-r from-primary-600 to-indigo-600 hover:from-primary-500 hover:to-indigo-500 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 disabled:opacity-50 transition-all shadow-md"
                  >
                    <span>Defend</span>
                    <Send className="w-3.5 h-3.5" />
                  </button>
                </form>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'inversion' && (
        <div className="space-y-6">
          {/* Target Valuation Slider */}
          <div className="p-5 rounded-2xl glass-panel border border-white/10 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/10 pb-3">
              <div>
                <span className="text-[10px] font-mono uppercase font-bold text-gold-400 tracking-wider block">
                  MAUBOUSSIN / GRAHAM REVERSE-ENGINEERING FRAMEWORK
                </span>
                <h4 className="text-sm font-bold text-white font-display">Target Valuation Inversion Calculator</h4>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-slate-400">Target Enterprise Value:</span>
                <span className="text-base font-bold font-mono text-gold-300 tabular-nums">
                  ${(targetValuation / 1000000).toFixed(0)}M
                </span>
              </div>
            </div>

            <div className="space-y-2">
              <input
                type="range"
                min="25000000"
                max="500000000"
                step="25000000"
                value={targetValuation}
                onChange={handleValuationChange}
                onMouseUp={handleValuationCommit}
                onTouchEnd={handleValuationCommit}
                className="w-full accent-gold-500 h-2 bg-slate-800 rounded-lg cursor-pointer"
              />
              <div className="flex justify-between text-[10px] font-mono text-slate-500">
                <span>$25M (Seed / Series A)</span>
                <span>$100M (Growth Tier)</span>
                <span>$250M (Scale)</span>
                <span>$500M (Decacorn Track)</span>
              </div>
            </div>
          </div>

          {/* Inversion Output Cards */}
          {inversionLoading ? (
            <div className="py-16 flex flex-col items-center justify-center space-y-3 glass-panel rounded-2xl border border-white/10">
              <div className="w-8 h-8 rounded-full border-2 border-gold-500 border-t-transparent animate-spin" />
              <span className="text-xs font-mono text-slate-400">
                Gemma 4:12B reverse-engineering operational hurdles...
              </span>
            </div>
          ) : inversionData ? (
            <div className="space-y-4">
              {/* Quantitative Hurdle Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5 space-y-1">
                  <span className="text-[10px] font-mono uppercase text-slate-500 block">Required Ending ARR</span>
                  <span className="text-lg font-bold font-mono text-emerald-400 tabular-nums">
                    {inversionData.required_arr_formatted}
                  </span>
                  <span className="text-[10px] text-slate-400 block font-mono">
                    @ {inversionData.implied_multiple}
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5 space-y-1">
                  <span className="text-[10px] font-mono uppercase text-slate-500 block">Required Active Logos</span>
                  <span className="text-lg font-bold font-mono text-white tabular-nums">
                    {inversionData.required_active_logos?.toLocaleString()}
                  </span>
                  <span className="text-[10px] text-slate-400 block font-mono">
                    @ ~{inversionData.average_acv_formatted} ACV
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5 space-y-1">
                  <span className="text-[10px] font-mono uppercase text-slate-500 block">Max Churn Ceiling</span>
                  <span className="text-lg font-bold font-mono text-amber-300 tabular-nums">
                    ≤ {inversionData.max_acceptable_annual_churn}
                  </span>
                  <span className="text-[10px] text-slate-400 block font-mono">Annual Logo Churn</span>
                </div>

                <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5 space-y-1">
                  <span className="text-[10px] font-mono uppercase text-slate-500 block">Required NRR Expansion</span>
                  <span className="text-lg font-bold font-mono text-indigo-300 tabular-nums">
                    ≥ {inversionData.required_net_revenue_retention}
                  </span>
                  <span className="text-[10px] text-slate-400 block font-mono">Net Retention Rate</span>
                </div>
              </div>

              {/* 3 Killer Assumptions & Strategic Verdict */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl glass-panel border border-white/10 space-y-2.5">
                  <span className="text-[10px] font-mono uppercase font-bold text-gold-400 block flex items-center gap-1.5">
                    <Target className="w-3.5 h-3.5" /> 3 Mandatory Operational Assumptions
                  </span>
                  <div className="space-y-2">
                    {inversionData.three_killer_assumptions?.map((assump, aIdx) => (
                      <div key={aIdx} className="flex items-start gap-2 text-xs text-slate-300">
                        <span className="text-gold-400 font-mono font-bold shrink-0">{aIdx + 1}.</span>
                        <p className="leading-relaxed">{assump}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="p-4 rounded-xl glass-panel-gold border border-gold-500/30 space-y-2">
                  <span className="text-[10px] font-mono uppercase font-bold text-gold-400 block flex items-center gap-1.5">
                    <Scale className="w-3.5 h-3.5" /> Institutional Strategist Verdict
                  </span>
                  <p className="text-xs text-slate-200 leading-relaxed font-sans">
                    {inversionData.strategic_verdict}
                  </p>
                </div>
              </div>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
