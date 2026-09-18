import React, { useState, useEffect, useRef } from 'react';
import { 
  Bot, CheckCircle2, Loader2, Sparkles, Terminal, AlertTriangle, 
  Activity, ShieldAlert, FileText, ArrowRight, RefreshCw, Cpu
} from 'lucide-react';
import { api } from '../lib/api';

const PIPELINE_STAGES = [
  { step: 1, label: 'Charter Formulation', agent: 'Senior Planning Architect' },
  { step: 2, label: 'Jurisdiction & Context', agent: 'Managing Orchestrator' },
  { step: 3, label: 'Market Research', agent: 'Market Intelligence Lead' },
  { step: 4, label: 'Authoritative Pricing Anchor', agent: 'Senior Partner (CFO)' },
  { step: 5, label: 'Competitive Whitespace', agent: 'Strategy Director (CSO)' },
  { step: 6, label: 'GTM & ICP Architecture', agent: 'Growth Partner (CMO)' },
  { step: 7, label: 'Risk & Statutory Audit', agent: 'Managing Director (CRO)' },
  { step: 8, label: 'Boardroom Council', agent: 'Executive Advisory Council' },
  { step: 9, label: 'Venture Review', agent: 'Senior Venture Reviewer' },
  { step: 10, label: 'VC Adversarial Stress-Test', agent: 'Adversarial VC General Partner' },
  { step: 11, label: 'Deterministic Scoring', agent: 'Quantitative Scoring Engine' },
  { step: 12, label: '13-Memorandum Synthesis', agent: 'Executive Report Generator' },
];

export function DeliberationStream({ projectId, onComplete, onRetry }) {
  const [messages, setMessages] = useState([]);
  const [status, setStatus] = useState('deliberating');
  const [currentStep, setCurrentStep] = useState(0);
  const [lastHeartbeat, setLastHeartbeat] = useState(Date.now());
  const [isConnected, setIsConnected] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const messagesEndRef = useRef(null);

  // Auto-scroll on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (!projectId) return;

    setIsConnected(true);
    setErrorMessage(null);

    const eventSource = api.createEventSource(
      projectId,
      (data) => {
        setIsConnected(true);
        setLastHeartbeat(Date.now());
        setMessages(prev => {
          // Avoid duplicate messages with same agent and step
          const exists = prev.some(m => m.step === data.step && m.agent === data.agent && m.message === data.message);
          if (exists) return prev;
          return [...prev, data];
        });

        if (typeof data.step === 'number') {
          setCurrentStep(data.step);
        }
        if (data.status) {
          setStatus(data.status);
          if (data.status === 'failed') {
            setErrorMessage(data.message || 'Deliberation halted due to a pipeline fault.');
          }
        }
      },
      (endData) => {
        const finalStatus = endData.status || 'completed';
        setStatus(finalStatus);
        if (finalStatus === 'failed') {
          setErrorMessage('Pipeline ended with an error status.');
        } else if (onComplete) {
          onComplete();
        }
      },
      (err) => {
        console.warn('SSE transient error / reconnecting:', err);
      },
      (hbData) => {
        setIsConnected(true);
        setLastHeartbeat(Date.now());
        if (hbData.status) setStatus(hbData.status);
      }
    );

    return () => {
      eventSource.close();
      setIsConnected(false);
    };
  }, [projectId]);

  const agentColors = {
    'Pipeline Orchestrator': 'text-blue-400 bg-blue-500/10 border-blue-500/30',
    'Planning Architect': 'text-primary-400 bg-primary-500/10 border-primary-500/30',
    'Market Intelligence Agent': 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30',
    'Chief Financial Officer': 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
    'Chief Strategy Officer': 'text-indigo-400 bg-indigo-500/10 border-indigo-500/30',
    'Chief Marketing Officer': 'text-pink-400 bg-pink-500/10 border-pink-500/30',
    'Chief Risk Officer': 'text-amber-400 bg-amber-500/10 border-amber-500/30',
    'Boardroom Council': 'text-purple-400 bg-purple-500/10 border-purple-500/30',
    'Venture Reviewer': 'text-teal-400 bg-teal-500/10 border-teal-500/30',
    'Adversarial VC Critic': 'text-rose-400 bg-rose-500/10 border-rose-500/30',
    'Deterministic Rules Sentry': 'text-emerald-300 bg-emerald-500/10 border-emerald-500/30',
    'Analytics & Scoring Engine': 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30',
    'Report Generator Engine': 'text-green-400 bg-green-500/10 border-green-500/30',
    'Pipeline Error Sentry': 'text-rose-400 bg-rose-500/20 border-rose-500/40',
  };

  const currentStageIndex = Math.min(Math.max(currentStep, 0), 12);
  const progressPercent = Math.min(Math.round(((currentStageIndex + (status === 'completed' ? 1 : 0)) / 13) * 100), 100);
  const activeAgentName = messages.length > 0 ? messages[messages.length - 1].agent : 'Pipeline Orchestrator';

  return (
    <div className="glass-panel p-6 rounded-2xl border border-white/10 shadow-2xl space-y-5">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary-600/20 border border-primary-500/30 rounded-xl text-primary-400 relative">
            <Cpu className="w-5 h-5" />
            {status === 'deliberating' && (
              <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-400 rounded-full animate-ping" />
            )}
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
              <span>Live Autonomous Deliberation Chamber</span>
              <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20 font-mono">
                SSE Live Bus
              </span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Multi-agent reasoning with Gate 1 Pricing Anchor & Gate 2 Adversarial Stress-Testing
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {status === 'deliberating' && (
            <span className="flex items-center gap-1.5 text-xs text-amber-400 bg-amber-500/10 px-3 py-1.5 rounded-full border border-amber-500/20 animate-pulse">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-400" />
              <span className="font-medium">Active: {activeAgentName}</span>
            </span>
          )}
          {status === 'completed' && (
            <span className="flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-full border border-emerald-500/20">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span className="font-semibold">Deliberation Concluded</span>
            </span>
          )}
          {status === 'failed' && (
            <span className="flex items-center gap-1.5 text-xs text-rose-400 bg-rose-500/10 px-3 py-1.5 rounded-full border border-rose-500/20">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span className="font-semibold">Fault Intercepted</span>
            </span>
          )}
        </div>
      </div>

      {/* Dynamic Visual Progress Stepper */}
      <div className="space-y-2 bg-slate-950/40 p-4 rounded-xl border border-white/5">
        <div className="flex items-center justify-between text-xs">
          <span className="text-slate-400 font-medium">Pipeline Progress</span>
          <span className="text-primary-400 font-mono font-bold">{progressPercent}%</span>
        </div>
        
        {/* Progress bar line */}
        <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden relative">
          <div 
            className="h-full bg-gradient-to-r from-primary-500 via-indigo-500 to-emerald-400 transition-all duration-500 rounded-full"
            style={{ width: `${progressPercent}%` }}
          />
        </div>

        {/* Active Stage Label */}
        <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
          <span>
            Current Stage: <strong className="text-slate-200">
              {currentStep === 0 ? 'Session Initialization' : 
               currentStep >= 12 ? 'Synthesizing 13 Executive Reports' :
               PIPELINE_STAGES.find(s => s.step === currentStep)?.label || `Deliberation Step ${currentStep}`}
            </strong>
          </span>
          <span className="text-[10px] text-slate-500 font-mono">
            {messages.length} messages logged
          </span>
        </div>
      </div>

      {/* Active Boardroom Chamber Seats Horseshoe */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-[11px] font-mono font-bold text-slate-400 uppercase tracking-wider px-1">
          <span>Executive Boardroom Seats</span>
          <span className="text-gold-400">Autonomous Quorum</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
          {[
            { role: 'CFO', title: 'Senior Partner', name: 'Chief Financial Officer', desc: 'Pricing & Economics', icon: '🏛️' },
            { role: 'CSO', title: 'Strategy Director', name: 'Chief Strategy Officer', desc: 'Whitespace & Sizing', icon: '🧭' },
            { role: 'CMO', title: 'Growth Partner', name: 'Chief Marketing Officer', desc: 'GTM & ICP Channels', icon: '🚀' },
            { role: 'CRO', title: 'Managing Director', name: 'Chief Risk Officer', desc: 'Risk & Governance', icon: '🛡️' },
            { role: 'VC', title: 'General Partner', name: 'Adversarial VC Critic', desc: 'Adversarial Stress-Test', icon: '⚔️' },
            { role: 'Council', title: 'Lead Partner', name: 'Boardroom Council', desc: '13-Report Synthesis', icon: '📜' },
          ].map((seat, sIdx) => {
            const isSpeaker = activeAgentName.includes(seat.name) || (seat.role === 'CFO' && activeAgentName.includes('Financial')) || (seat.role === 'CSO' && activeAgentName.includes('Strategy')) || (seat.role === 'CMO' && activeAgentName.includes('Marketing')) || (seat.role === 'CRO' && activeAgentName.includes('Risk')) || (seat.role === 'VC' && activeAgentName.includes('Critic'));
            return (
              <div
                key={sIdx}
                className={`p-2.5 rounded-xl border transition-all text-center space-y-1 ${
                  isSpeaker && status === 'deliberating'
                    ? 'bg-gradient-to-b from-gold-500/20 to-slate-900 border-gold-400 shadow-lg shadow-gold-500/20 scale-[1.03] animate-speaker-ring'
                    : 'bg-slate-950/60 border-white/10 opacity-75'
                }`}
              >
                <div className="text-base">{seat.icon}</div>
                <div className="text-[11px] font-bold text-white line-clamp-1">{seat.role}</div>
                <div className="text-[9px] text-slate-400 font-mono line-clamp-1">{seat.desc}</div>
                {isSpeaker && status === 'deliberating' && (
                  <span className="inline-block text-[8px] font-bold uppercase text-gold-400 bg-gold-500/20 px-1.5 py-0.2 rounded font-mono">
                    Deliberating
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Error Alert Banner if pipeline failed */}
      {status === 'failed' && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl space-y-2">
          <div className="flex items-center gap-2 text-rose-400 text-xs font-semibold">
            <ShieldAlert className="w-4 h-4" />
            <span>Deliberation Error Sentry</span>
          </div>
          <p className="text-xs text-rose-200">{errorMessage || 'An error occurred during multi-agent inference.'}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-2 flex items-center gap-1.5 px-3 py-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-semibold shadow transition-all"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry Deliberation</span>
            </button>
          )}
        </div>
      )}

      {/* Discussion Log Stream */}
      <div className="space-y-3 max-h-96 overflow-y-auto pr-2 custom-scrollbar">
        {messages.length === 0 ? (
          <div className="text-center py-10 text-xs text-slate-400 flex flex-col items-center justify-center gap-3">
            <Loader2 className="w-6 h-6 animate-spin text-primary-400" />
            <div className="space-y-1 text-center">
              <p className="font-semibold text-slate-200">Connecting to Autonomous Chamber Bus...</p>
              <p className="text-[11px] text-slate-500">Convening Lead Planning Architect, CFO, CSO, CMO, CRO, and Adversarial VC Critic.</p>
            </div>
          </div>
        ) : (
          messages.map((m, idx) => {
            const badgeStyle = agentColors[m.agent] || 'text-slate-300 bg-white/5 border-white/10';
            const isLatest = idx === messages.length - 1 && status === 'deliberating';
            return (
              <div 
                key={idx} 
                className={`p-3.5 rounded-xl border transition-all animate-msg-enter text-xs space-y-1.5 ${
                  isLatest ? 'bg-slate-900/90 border-primary-500/40 shadow-lg shadow-primary-500/10' : 'bg-slate-900/50 border-white/5 hover:border-white/10'
                }`}
                style={{ animationDelay: `${Math.min(idx * 20, 100)}ms` }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`px-2.5 py-0.5 rounded-md font-semibold border ${badgeStyle} flex items-center gap-1.5`}>
                      <Bot className="w-3 h-3" />
                      <span>{m.agent}</span>
                      <span className="opacity-60 text-[10px]">({m.role})</span>
                    </span>
                    {isLatest && (
                      <span className="flex items-center gap-1 text-[10px] text-primary-300 bg-primary-500/20 px-2 py-0.5 rounded-full border border-primary-500/40 font-medium animate-speaker-ring">
                        <Activity className="w-3 h-3 text-primary-400 animate-pulse" />
                        <span>Speaking</span>
                      </span>
                    )}
                  </div>
                  <span className="text-[10px] text-slate-500 font-mono">Step {m.step}</span>
                </div>
                <p className="text-slate-200 pl-1 leading-relaxed whitespace-pre-wrap">{m.message}</p>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}
