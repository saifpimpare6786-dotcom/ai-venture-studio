import React, { useState } from 'react';
import { Layers, ArrowRight, ShieldCheck, Zap } from 'lucide-react';

export function Auth({ onLogin }) {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (email) {
      onLogin(email, name || 'Founder');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="max-w-md w-full glass-panel-elevated p-8 rounded-2xl border border-white/10 shadow-2xl relative overflow-hidden">
        {/* Ambient Glow */}
        <div className="absolute -top-24 -right-24 w-48 h-48 bg-primary-500/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex items-center gap-3.5 mb-6">
          <div className="p-3 bg-gradient-to-br from-gold-500/20 to-primary-600/20 border border-gold-500/30 rounded-2xl text-gold-400 shadow-lg shadow-gold-500/10">
            <Layers className="w-8 h-8" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-white font-display uppercase">Apex Venture Partners</h1>
            </div>
            <p className="text-xs text-gold-400 font-mono font-semibold tracking-wider">STRATEGY & VENTURE CAPITAL PRACTICE</p>
          </div>
        </div>

        <p className="text-xs text-slate-300 mb-6 leading-relaxed">
          Autonomous multi-agent executive boardroom formulating investment-ready business plans, 2×2 whitespace positioning, and sensitivity models.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 font-mono">Principal / Founder Name</label>
            <input
              type="text"
              placeholder="e.g. Alex Morgan"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-3 rounded-xl glass-input text-sm font-semibold"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 font-mono">Institutional Email</label>
            <input
              type="email"
              required
              placeholder="principal@venturepartners.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 rounded-xl glass-input text-sm"
            />
          </div>

          <button
            type="submit"
            className="w-full py-3.5 px-4 bg-gradient-to-r from-primary-600 to-indigo-600 hover:from-primary-500 hover:to-indigo-500 text-white font-semibold rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-primary-600/30 btn-press transition-all text-sm mt-3"
          >
            <span>Enter Strategy Practice Chamber</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="mt-8 pt-6 border-t border-white/10 flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Local Ollama Air-Gap Mode</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Zap className="w-4 h-4 text-emerald-400" />
            <span className="font-mono font-medium text-emerald-300">Gemma 4:12B Ready</span>
          </div>
        </div>
      </div>
    </div>
  );
}
