import React, { useState } from 'react';
import { FileText, ShieldAlert, CheckCircle, AlertTriangle, Scale, ArrowRight, RefreshCw, Copy, Check } from 'lucide-react';
import { api } from '../lib/api';

export function TermSheetAnalyzer({ projectId, projectName }) {
  const [termSheetText, setTermSheetText] = useState(
`Investment Summary:
- Pre-Money Valuation: ₹10,000,000
- Investment Amount: ₹2,500,000 for Series Seed Preferred Stock
- Liquidation Preference: 2.0x Participating Preferred Stock with standard conversion rights
- Anti-Dilution: Full Ratchet anti-dilution protection upon down rounds
- Board of Directors: 1 Founder Seat, 2 Investor Appointee Seats
- Founder Vesting: 4-year linear vesting with single-trigger acceleration upon termination`
  );
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);

  const handleAnalyze = async () => {
    if (!termSheetText.trim() || loading) return;
    setLoading(true);
    try {
      const res = await api.post(`/api/simulator/term-sheet/${projectId || 'current'}`, {
        term_sheet_text: termSheetText
      });
      setAnalysis(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    if (status === 'FAVORABLE') return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">FAVORABLE</span>;
    if (status === 'AGGRESSIVE_RISK') return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">PREDATORY RISK</span>;
    return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">STANDARD</span>;
  };

  return (
    <div className="bg-gradient-to-br from-slate-900/95 via-slate-950/90 to-[#080B11] p-6 rounded-2xl border border-white/10 shadow-2xl space-y-6">
      <div className="flex items-center justify-between border-b border-white/10 pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-amber-500/20 text-amber-400 rounded-xl border border-amber-500/30">
            <Scale className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-mono font-bold text-amber-400 uppercase tracking-wider block">
              LEGAL CLAUSE GUARD
            </span>
            <h3 className="text-lg font-bold text-white font-display">Term Sheet & Clause Risk Analyzer</h3>
          </div>
        </div>
        <button
          onClick={handleAnalyze}
          disabled={loading || !termSheetText.trim()}
          className="px-4 py-2 bg-gradient-to-r from-amber-600 to-primary-600 hover:from-amber-500 hover:to-primary-500 text-white rounded-xl text-xs font-bold font-mono uppercase tracking-wider flex items-center gap-2 btn-press shadow-lg shadow-amber-600/20 disabled:opacity-50"
        >
          {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <ShieldAlert className="w-4 h-4" />}
          <span>{loading ? 'Analyzing Clauses...' : 'Analyze Term Sheet'}</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Text Area */}
        <div className="space-y-2">
          <label className="text-xs font-mono font-bold text-slate-400 uppercase block">
            Paste Investment Term Sheet / SAFEs:
          </label>
          <textarea
            value={termSheetText}
            onChange={(e) => setTermSheetText(e.target.value)}
            rows={10}
            className="w-full p-4 rounded-xl bg-slate-950/80 border border-white/15 text-xs text-slate-200 font-mono leading-relaxed focus:outline-none focus:border-amber-500 transition-all resize-none custom-scrollbar"
            placeholder="Paste your term sheet clauses here..."
          />
        </div>

        {/* Output Risk Analysis */}
        <div className="space-y-4">
          {analysis ? (
            <div className="p-5 rounded-xl bg-slate-950/80 border border-white/10 space-y-4 animate-fade-in">
              <div className="flex items-center justify-between border-b border-white/10 pb-3">
                <span className="text-xs font-mono font-bold text-white uppercase">Overall Risk Rating</span>
                <span className={`px-2.5 py-1 rounded-full text-xs font-mono font-bold ${
                  analysis.overall_risk_rating.includes('HIGH') ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                }`}>
                  {analysis.overall_risk_rating}
                </span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">{analysis.summary}</p>

              {/* Clause-by-Clause Highlights */}
              <div className="space-y-3 max-h-[220px] overflow-y-auto pr-1 custom-scrollbar">
                {(analysis.clauses_analyzed || []).map((clause, idx) => (
                  <div key={idx} className="p-3 rounded-lg bg-white/[0.02] border border-white/5 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white font-mono">{clause.clause_name}</span>
                      {getStatusBadge(clause.status)}
                    </div>
                    <p className="text-[11px] text-slate-300">{clause.analysis}</p>
                    <div className="p-2 rounded bg-amber-950/20 border border-amber-500/20 text-[11px] text-amber-200 font-mono">
                      <span className="font-bold text-amber-400 mr-1">Counter:</span> {clause.counter_recommendation}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="p-8 rounded-xl bg-slate-950/40 border border-dashed border-white/10 flex flex-col items-center justify-center text-center space-y-2 h-full">
              <Scale className="w-8 h-8 text-slate-600" />
              <p className="text-xs text-slate-400">Click "Analyze Term Sheet" to review liquidation preferences, dilution formulas, and protective rights.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
