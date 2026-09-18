import React, { useState } from 'react';
import { Scale, Check, AlertTriangle, ShieldCheck, Trophy, Sparkles } from 'lucide-react';

export function TermSheetCompare({ projectName = "Venture" }) {
  const [offers] = useState([
    {
      fundName: 'Nexus Seed Fund',
      preMoney: '₹8.0 Cr',
      investment: '₹1.5 Cr',
      postMoney: '₹9.5 Cr',
      dilution: '15.8%',
      liqPref: '1.0x Non-Participating',
      antiDilution: 'Broad-Based Weighted Avg',
      boardSeats: '2 Founders : 1 Investor',
      esopRequirement: '10% Unallocated',
      founderScore: 92,
      verdict: 'RECOMMENDED (Founder-Friendly)'
    },
    {
      fundName: 'Apex Growth Ventures',
      preMoney: '₹10.0 Cr',
      investment: '₹2.0 Cr',
      postMoney: '₹12.0 Cr',
      dilution: '16.7%',
      liqPref: '2.0x Participating Preferred',
      antiDilution: 'Full Ratchet',
      boardSeats: '1 Founder : 2 Investors',
      esopRequirement: '15% Unallocated',
      founderScore: 64,
      verdict: 'PREDATORY GOVERNANCE TERMS'
    }
  ]);

  return (
    <div className="bg-gradient-to-br from-slate-900/95 via-slate-950/90 to-[#080B11] p-6 rounded-2xl border border-white/10 shadow-2xl space-y-6">
      <div className="flex items-center justify-between border-b border-white/10 pb-4 flex-wrap gap-2">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-amber-500/20 text-amber-400 rounded-xl border border-amber-500/30">
            <Scale className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-mono font-bold text-amber-400 uppercase tracking-wider block">
              TERM SHEET BATTLES
            </span>
            <h3 className="text-lg font-bold text-white font-display">Side-By-Side Offer Comparison Matrix</h3>
          </div>
        </div>

        <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/30">
          Founder Leverage Index
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {offers.map((offer, idx) => (
          <div
            key={idx}
            className={`p-5 rounded-xl border flex flex-col justify-between space-y-4 ${
              offer.founderScore > 80
                ? 'bg-emerald-950/20 border-emerald-500/30 shadow-lg shadow-emerald-950/30'
                : 'bg-rose-950/20 border-rose-500/30 shadow-lg shadow-rose-950/30'
            }`}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between border-b border-white/10 pb-3">
                <div>
                  <h4 className="text-base font-bold text-white font-display">{offer.fundName}</h4>
                  <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                    offer.founderScore > 80 ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'
                  }`}>
                    {offer.verdict}
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] font-mono text-slate-400 uppercase block">Founder Score</span>
                  <span className={`text-xl font-mono font-black ${offer.founderScore > 80 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {offer.founderScore}/100
                  </span>
                </div>
              </div>

              {/* Terms Breakdown List */}
              <div className="space-y-2 text-xs font-mono">
                <div className="flex justify-between py-1 border-b border-white/5">
                  <span className="text-slate-400">Pre-Money Valuation:</span>
                  <span className="font-bold text-white">{offer.preMoney}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-white/5">
                  <span className="text-slate-400">Investment Capital:</span>
                  <span className="font-bold text-white">{offer.investment}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-white/5">
                  <span className="text-slate-400">Effective Dilution:</span>
                  <span className="font-bold text-white">{offer.dilution}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-white/5">
                  <span className="text-slate-400">Liquidation Preference:</span>
                  <span className={`font-bold ${offer.liqPref.includes('Non-Participating') ? 'text-emerald-300' : 'text-rose-400'}`}>
                    {offer.liqPref}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-white/5">
                  <span className="text-slate-400">Anti-Dilution Clause:</span>
                  <span className={`font-bold ${offer.antiDilution.includes('Weighted') ? 'text-emerald-300' : 'text-rose-400'}`}>
                    {offer.antiDilution}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-white/5">
                  <span className="text-slate-400">Board Representation:</span>
                  <span className={`font-bold ${offer.boardSeats.startsWith('2') ? 'text-emerald-300' : 'text-rose-400'}`}>
                    {offer.boardSeats}
                  </span>
                </div>
              </div>
            </div>

            <div className={`p-3 rounded-lg text-[11px] ${
              offer.founderScore > 80 ? 'bg-emerald-950/40 text-emerald-200 border border-emerald-500/20' : 'bg-rose-950/40 text-rose-200 border border-rose-500/20'
            }`}>
              {offer.founderScore > 80
                ? 'Clean governance structure preserving founder board control and standard exit economics.'
                : 'Warning: 2.0x participating preference and full-ratchet anti-dilution severely penalize founders.'}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
