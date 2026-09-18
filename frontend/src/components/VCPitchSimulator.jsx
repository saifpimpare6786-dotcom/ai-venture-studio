import React, { useState, useEffect } from 'react';
import { Target, Users, ShieldCheck, TrendingUp, Sparkles, RefreshCw, CheckCircle2, AlertCircle, ChevronRight } from 'lucide-react';
import { api } from '../lib/api';

export function VCPitchSimulator({ projectId, projectName }) {
  const [selectedPersona, setSelectedPersona] = useState('blitzscaler');
  const [loading, setLoading] = useState(false);
  const [pitchData, setPitchData] = useState(null);

  const vcArchetypes = [
    { id: 'blitzscaler', label: 'Tier-1 Blitzscaler', icon: TrendingUp, focus: 'TAM Scale & Velocity', color: 'text-cyan-400', border: 'border-cyan-500/30' },
    { id: 'value_hawk', label: 'Unit Economics Hawk', icon: ShieldCheck, focus: 'CAC Payback & Breakeven', color: 'text-emerald-400', border: 'border-emerald-500/30' },
    { id: 'deep_tech', label: 'Deep-Tech IP Specialist', icon: Target, focus: 'Algorithmic Moats & COGS', color: 'text-purple-400', border: 'border-purple-500/30' },
    { id: 'corporate_vc', label: 'Enterprise Corporate VC', icon: Users, focus: 'Procurement & Compliance', color: 'text-amber-400', border: 'border-amber-500/30' }
  ];

  const fetchSimulation = async (persona) => {
    setLoading(true);
    try {
      const res = await api.post(`/api/simulator/vc-pitch/${projectId || 'default'}`, {
        vc_persona: persona
      });
      if (res && res.data) {
        setPitchData(res.data);
      }
    } catch (err) {
      console.error("VC Pitch Simulation error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSimulation(selectedPersona);
  }, [selectedPersona, projectId]);

  return (
    <div className="bg-gradient-to-br from-slate-900/95 via-slate-950/90 to-[#080B11] p-6 rounded-2xl border border-white/10 shadow-2xl space-y-6">
      <div className="flex items-center justify-between border-b border-white/10 pb-4 flex-wrap gap-2">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-cyan-500/20 text-cyan-400 rounded-xl border border-cyan-500/30">
            <Target className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-mono font-bold text-cyan-400 uppercase tracking-wider block">
              PARTNER MEETING COACH
            </span>
            <h3 className="text-lg font-bold text-white font-display">VC Archetype Matchmaking & Pitch Objection Simulator</h3>
          </div>
        </div>

        {pitchData && (
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold text-cyan-300 bg-cyan-950/60 px-3 py-1 rounded-full border border-cyan-500/30">
              Partner Conviction Score: {pitchData.investor_conviction_score}%
            </span>
          </div>
        )}
      </div>

      {/* VC Persona Selector Buttons */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {vcArchetypes.map((archetype) => {
          const Icon = archetype.icon;
          const isSelected = selectedPersona === archetype.id;
          return (
            <button
              key={archetype.id}
              onClick={() => setSelectedPersona(archetype.id)}
              className={`p-3.5 rounded-xl border text-left transition-all btn-press space-y-1 ${
                isSelected
                  ? `bg-slate-900 ${archetype.border} ${archetype.color} shadow-lg scale-[1.02]`
                  : 'bg-slate-950/60 border-white/10 text-slate-400 hover:text-white hover:border-white/20'
              }`}
            >
              <div className="flex items-center justify-between">
                <Icon className="w-4 h-4" />
                {isSelected && <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />}
              </div>
              <div className="text-xs font-bold font-display text-white">{archetype.label}</div>
              <div className="text-[10px] font-mono text-slate-400">{archetype.focus}</div>
            </button>
          );
        })}
      </div>

      {/* Pitch Data Analysis */}
      {loading ? (
        <div className="p-8 text-center text-xs text-slate-400 font-mono flex items-center justify-center gap-2">
          <RefreshCw className="w-4 h-4 animate-spin text-cyan-400" />
          <span>Simulating partner meeting with {selectedPersona} investment committee...</span>
        </div>
      ) : pitchData ? (
        <div className="space-y-4 animate-fade-in">
          <div className="p-4 rounded-xl bg-slate-950/70 border border-white/5 space-y-1">
            <span className="text-[10px] font-mono uppercase text-cyan-400 font-bold">Investment Thesis Lens:</span>
            <p className="text-xs text-slate-300">{pitchData.thesis_focus}</p>
          </div>

          {/* Top 3 Objections and Counter-Scripts */}
          <div className="space-y-3">
            <span className="text-xs font-mono font-bold text-slate-300 uppercase tracking-wider block">
              Top Boardroom Objections & Winning Counter-Arguments
            </span>
            
            {(pitchData.top_objections_and_counters || []).map((item, idx) => (
              <div key={idx} className="p-4 rounded-xl bg-slate-950/80 border border-white/10 space-y-2">
                <div className="flex items-start gap-2 text-xs font-bold text-rose-300">
                  <AlertCircle className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
                  <span>Partner Objection {idx + 1}: "{item.objection}"</span>
                </div>
                <div className="p-3 rounded-lg bg-cyan-950/20 border border-cyan-500/20 text-xs text-cyan-200 leading-relaxed font-mono">
                  <span className="font-bold text-cyan-400 mr-1">Winning Counter-Script:</span>
                  {item.winning_counter}
                </div>
              </div>
            ))}
          </div>

          {/* Tactical Meeting Tips */}
          <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/20 space-y-2">
            <span className="text-xs font-mono font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-4 h-4" /> Tactical Partner Meeting Playbook
            </span>
            <div className="space-y-1.5">
              {(pitchData.partner_meeting_tips || []).map((tip, idx) => (
                <div key={idx} className="flex items-center gap-2 text-xs text-slate-300">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span>{tip}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
