import React, { useState, useEffect } from 'react';
import { Mail, Copy, Check, FileSignature, Send, Sparkles, RefreshCw, MessageSquare } from 'lucide-react';
import { api } from '../lib/api';

export function GtmOutreachGenerator({ projectId, projectName }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [copiedKey, setCopiedKey] = useState(null);

  const fetchOutreach = async () => {
    setLoading(true);
    try {
      const res = await api.post(`/api/simulator/gtm-outreach/${projectId || 'default'}`, {});
      if (res && res.data) {
        setData(res.data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOutreach();
  }, [projectId]);

  const copyToClipboard = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  return (
    <div className="bg-gradient-to-br from-slate-900/95 via-slate-950/90 to-[#080B11] p-6 rounded-2xl border border-white/10 shadow-2xl space-y-6">
      <div className="flex items-center justify-between border-b border-white/10 pb-4 flex-wrap gap-2">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-indigo-500/20 text-indigo-400 rounded-xl border border-indigo-500/30">
            <Mail className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-mono font-bold text-indigo-400 uppercase tracking-wider block">
              GTM OUTBOUND ENGINE
            </span>
            <h3 className="text-lg font-bold text-white font-display">Cold Outreach Sequence & B2B Pilot LOI Generator</h3>
          </div>
        </div>

        <button
          onClick={fetchOutreach}
          disabled={loading}
          className="px-3.5 py-1.5 bg-indigo-600/30 hover:bg-indigo-600/40 text-indigo-300 border border-indigo-500/30 rounded-xl text-xs font-mono font-bold flex items-center gap-1.5 btn-press transition-all"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Regenerate Copy</span>
        </button>
      </div>

      {data && (
        <div className="space-y-6 animate-fade-in">
          {/* 3-Step Cold Email Sequence */}
          <div className="space-y-3">
            <span className="text-xs font-mono font-bold text-slate-300 uppercase tracking-wider block">
              3-Step High-Conversion Cold Email Cadence
            </span>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              {data.cold_email_sequence.map((em, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-slate-950/80 border border-white/10 flex flex-col justify-between space-y-3">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono font-bold text-indigo-400 uppercase">{em.step}</span>
                      <button
                        onClick={() => copyToClipboard(`Subject: ${em.subject}\n\n${em.body}`, `email-${idx}`)}
                        className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 btn-press"
                        title="Copy Email"
                      >
                        {copiedKey === `email-${idx}` ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-slate-400" />}
                      </button>
                    </div>
                    <div className="text-xs font-bold text-white font-mono bg-slate-900/80 p-2 rounded border border-white/5">
                      {em.subject}
                    </div>
                    <p className="text-xs text-slate-300 whitespace-pre-line leading-relaxed font-sans">
                      {em.body}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* LinkedIn DM & B2B Pilot LOI */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-2 border-t border-white/10">
            {/* LinkedIn InMail */}
            <div className="p-5 rounded-xl bg-slate-950/70 border border-white/5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-cyan-400 font-mono uppercase flex items-center gap-1.5">
                  <MessageSquare className="w-4 h-4" /> LinkedIn Direct Message Script
                </span>
                <button
                  onClick={() => copyToClipboard(data.linkedin_inmail, 'linkedin')}
                  className="px-2.5 py-1 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 rounded-lg text-xs font-mono font-bold flex items-center gap-1 btn-press"
                >
                  {copiedKey === 'linkedin' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedKey === 'linkedin' ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed font-mono bg-slate-900/60 p-3.5 rounded-lg border border-white/5">
                "{data.linkedin_inmail}"
              </p>
            </div>

            {/* Ready-to-Sign Pilot LOI */}
            <div className="p-5 rounded-xl bg-slate-950/70 border border-emerald-500/20 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-emerald-400 font-mono uppercase flex items-center gap-1.5">
                  <FileSignature className="w-4 h-4" /> Ready-To-Sign Pilot LOI Template
                </span>
                <button
                  onClick={() => copyToClipboard(data.pilot_loi_template, 'loi')}
                  className="px-2.5 py-1 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 rounded-lg text-xs font-mono font-bold flex items-center gap-1 btn-press"
                >
                  {copiedKey === 'loi' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedKey === 'loi' ? 'Copied LOI' : 'Copy LOI'}</span>
                </button>
              </div>
              <textarea
                readOnly
                value={data.pilot_loi_template}
                rows={6}
                className="w-full p-3 rounded-lg bg-slate-900/80 border border-white/10 text-xs text-slate-300 font-mono leading-relaxed resize-none custom-scrollbar focus:outline-none"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
