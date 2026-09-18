import React, { useState, useEffect } from 'react';
import { ShieldCheck, CheckCircle2, AlertTriangle, Calendar, FileText, Sparkles, Building, Lock } from 'lucide-react';
import { api } from '../lib/api';

export function DpiitDpdpaComplianceHub({ projectId, projectName }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCompliance = async () => {
      try {
        const res = await api.get(`/api/simulator/india-compliance/${projectId || 'default'}`);
        setData(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchCompliance();
  }, [projectId]);

  if (loading) {
    return (
      <div className="p-8 text-center text-xs text-slate-400 font-mono animate-pulse">
        Auditing statutory DPIIT & DPDPA 2023 compliance frameworks...
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="bg-gradient-to-br from-slate-900/95 via-slate-950/90 to-[#080B11] p-6 rounded-2xl border border-white/10 shadow-2xl space-y-6">
      <div className="flex items-center justify-between border-b border-white/10 pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-emerald-500/20 text-emerald-400 rounded-xl border border-emerald-500/30">
            <Building className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-mono font-bold text-emerald-400 uppercase tracking-wider block">
              STATUTORY INDIA FAST-TRACK
            </span>
            <h3 className="text-lg font-bold text-white font-display">DPIIT Tax Holidays & DPDPA 2023 Compliance Hub</h3>
          </div>
        </div>
        <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/30">
          Section 80-IAC: QUALIFIED
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* DPIIT Section 80-IAC Tax Exemption Card */}
        <div className="p-5 rounded-xl bg-slate-950/70 border border-emerald-500/20 space-y-3.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-emerald-400 font-mono uppercase flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4" /> Startup India Section 80-IAC
            </span>
            <span className="text-[10px] font-mono font-bold text-emerald-300 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-500/30">
              3-Year 100% Tax Holiday
            </span>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">
            {data.dpiit_startup_india.section_80_iac_tax_holiday.benefit}
          </p>

          <div className="space-y-2 pt-2 border-t border-white/5">
            <span className="text-[10px] font-mono text-slate-400 uppercase font-bold">Eligibility Checklist:</span>
            {data.dpiit_startup_india.section_80_iac_tax_holiday.criteria.map((cr, idx) => (
              <div key={idx} className="flex items-center gap-2 text-xs text-slate-200">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span>{cr}</span>
              </div>
            ))}
          </div>

          <div className="p-3 rounded-lg bg-emerald-950/30 border border-emerald-500/20 text-[11px] text-emerald-200 flex items-center justify-between">
            <span>Angel Tax 56(2)(viib) Status:</span>
            <strong className="text-emerald-400">EXEMPT (Form-2 Ready)</strong>
          </div>
        </div>

        {/* DPDPA 2023 Data Protection Card */}
        <div className="p-5 rounded-xl bg-slate-950/70 border border-indigo-500/20 space-y-3.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-indigo-400 font-mono uppercase flex items-center gap-1.5">
              <Lock className="w-4 h-4" /> DPDPA 2023 Data Privacy
            </span>
            <span className="text-[10px] font-mono font-bold text-indigo-300 bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-500/30">
              {data.dpdpa_2023_compliance.fiduciary_tier}
            </span>
          </div>

          <div className="space-y-2 pt-1">
            {data.dpdpa_2023_compliance.checklist.map((item, idx) => (
              <div key={idx} className="p-2.5 rounded-lg bg-white/[0.02] border border-white/5 space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-200">{item.requirement}</span>
                  <span className="text-[10px] font-mono text-indigo-400 font-bold">{item.status}</span>
                </div>
                <div className="text-[10px] font-mono text-slate-400">
                  {item.code_support || item.architecture || item.timeframe}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Statutory Filing Milestones Calendar */}
      <div className="p-4 rounded-xl bg-slate-950/60 border border-white/5 space-y-3">
        <div className="flex items-center gap-2 text-xs font-mono font-bold text-slate-300 uppercase">
          <Calendar className="w-4 h-4 text-gold-400" />
          <span>Annual Statutory MCA & GST Milestone Roadmap</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {data.statutory_calendar.map((cal, idx) => (
            <div key={idx} className="p-3 rounded-lg bg-white/[0.02] border border-white/5 space-y-1">
              <span className="text-[10px] font-mono font-bold text-gold-400 uppercase block">{cal.period}</span>
              <span className="text-xs text-slate-200 font-medium block">{cal.obligation}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
