import React, { useState } from 'react';
import { Calendar, CheckCircle2, Clock, Sparkles, Target, Shield, Rocket, ArrowRight } from 'lucide-react';

export function GtmRoadmapGantt({ projectName = "Venture" }) {
  const [activeSprint, setActiveSprint] = useState('all');

  const sprints = [
    {
      phase: 'Weeks 1–4',
      name: 'Discovery & Pilot LOI Validation',
      track: 'GTM & ICP',
      status: 'COMPLETED',
      icon: Target,
      color: 'border-cyan-500/30 bg-cyan-950/20 text-cyan-300',
      tasks: [
        { name: 'Interview 25 ICP decision-makers across target sectors', done: true },
        { name: 'Secure 3 signed Pilot Letters of Intent (LOIs)', done: true },
        { name: 'Establish zero-CAC distribution wedge via 2 university incubators', done: true }
      ]
    },
    {
      phase: 'Weeks 5–8',
      name: 'Product Beta & Statutory Clearance',
      track: 'Engineering & Compliance',
      status: 'IN_PROGRESS',
      icon: Shield,
      color: 'border-emerald-500/30 bg-emerald-950/20 text-emerald-300',
      tasks: [
        { name: 'Deploy multi-tenant MVP with deterministic rules sentry', done: true },
        { name: 'Submit Section 80-IAC Startup India 3-year tax holiday application', done: false },
        { name: 'Verify DPDPA 2023 consent capture and automated erasure pipeline', done: true }
      ]
    },
    {
      phase: 'Weeks 9–12',
      name: 'Commercial Launch & Institutional Roadshow',
      track: 'Fundraising & Scale',
      status: 'UPCOMING',
      icon: Rocket,
      color: 'border-purple-500/30 bg-purple-950/20 text-purple-300',
      tasks: [
        { name: 'Convert 3 pilots to ₹15,000/mo annual enterprise contracts', done: false },
        { name: 'Distribute tokenized Investor Deal Room to 15 Tier-1 seed funds', done: false },
        { name: 'Close ₹1.5 Cr Seed Round at ₹7.5 Cr post-money valuation', done: false }
      ]
    }
  ];

  return (
    <div className="bg-gradient-to-br from-slate-900/95 via-slate-950/90 to-[#080B11] p-6 rounded-2xl border border-white/10 shadow-2xl space-y-6">
      <div className="flex items-center justify-between border-b border-white/10 pb-4 flex-wrap gap-2">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-cyan-500/20 text-cyan-400 rounded-xl border border-cyan-500/30">
            <Calendar className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-mono font-bold text-cyan-400 uppercase tracking-wider block">
              EXECUTION ENGINE
            </span>
            <h3 className="text-lg font-bold text-white font-display">90-Day GTM Sprint Execution Roadmap</h3>
          </div>
        </div>

        <span className="text-xs font-mono font-bold text-cyan-300 bg-cyan-950/60 px-3 py-1 rounded-full border border-cyan-500/30">
          12-Week Milestone Tracker
        </span>
      </div>

      {/* 3 Sprint Phase Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {sprints.map((sprint, idx) => {
          const Icon = sprint.icon;
          return (
            <div key={idx} className={`p-5 rounded-xl border flex flex-col justify-between space-y-4 ${sprint.color}`}>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono font-bold uppercase">{sprint.phase}</span>
                  <span className={`text-[9px] font-mono px-2 py-0.5 rounded font-bold ${
                    sprint.status === 'COMPLETED' ? 'bg-emerald-500/20 text-emerald-300' : sprint.status === 'IN_PROGRESS' ? 'bg-cyan-500/20 text-cyan-300 animate-pulse' : 'bg-slate-800 text-slate-400'
                  }`}>
                    {sprint.status.replace('_', ' ')}
                  </span>
                </div>
                <h4 className="text-sm font-bold text-white font-display flex items-center gap-1.5">
                  <Icon className="w-4 h-4 shrink-0" />
                  <span>{sprint.name}</span>
                </h4>
                <div className="text-[10px] font-mono text-slate-400">Track: {sprint.track}</div>
              </div>

              <div className="space-y-2 pt-2 border-t border-white/5">
                {sprint.tasks.map((task, tIdx) => (
                  <div key={tIdx} className="flex items-start gap-2 text-xs">
                    <CheckCircle2 className={`w-3.5 h-3.5 shrink-0 mt-0.5 ${task.done ? 'text-emerald-400' : 'text-slate-600'}`} />
                    <span className={task.done ? 'text-slate-200 line-through opacity-80' : 'text-slate-300'}>{task.name}</span>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
