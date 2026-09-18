import React, { useState, useEffect } from 'react';
import { Volume2, VolumeX, Play, Pause, RotateCcw, Bot, Sparkles, Radio } from 'lucide-react';

export function BoardroomAudioPlayer({ deliberations = [], projectName = "Venture" }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [isSupported, setIsSupported] = useState(true);

  const defaultDeliberations = [
    { agent: 'Strategy Agent', role: 'Venture Architect', text: `We recommend prioritizing B2B university incubator partnerships across India for ${projectName}, securing zero-CAC cohort distribution.` },
    { agent: 'Finance CFO', role: 'Unit Economics', text: `With an ARPU of ₹12,000 and target CAC of ₹8,500, we maintain an 82% gross margin and reach cash breakeven by month 14.` },
    { agent: 'Risk & Legal', role: 'Compliance Officer', text: `We have verified Section 80-IAC tax holiday readiness and structured automated consent erasure under DPDPA 2023.` },
    { agent: 'Adversarial Critic', role: 'Boardroom Critic', text: `Ensure pricing tiers remain insulated against generic LLM wrappers by hardening our proprietary deterministic rules engine.` }
  ];

  const items = deliberations.length > 0 ? deliberations : defaultDeliberations;

  useEffect(() => {
    if (!('speechSynthesis' in window)) {
      setIsSupported(false);
    }
  }, []);

  const speakCurrent = (idx) => {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();

    if (idx >= items.length) {
      setIsPlaying(false);
      setCurrentIdx(0);
      return;
    }

    const item = items[idx];
    const utterance = new SpeechSynthesisUtterance(`${item.agent}. ${item.text}`);
    
    // Assign distinctive voice pitch/rate per persona
    if (item.agent.toLowerCase().includes('strategy')) {
      utterance.pitch = 1.0;
      utterance.rate = 1.05;
    } else if (item.agent.toLowerCase().includes('finance')) {
      utterance.pitch = 0.9;
      utterance.rate = 1.1;
    } else if (item.agent.toLowerCase().includes('risk')) {
      utterance.pitch = 1.1;
      utterance.rate = 0.95;
    } else if (item.agent.toLowerCase().includes('critic')) {
      utterance.pitch = 0.8;
      utterance.rate = 1.0;
    }

    utterance.onend = () => {
      setCurrentIdx(prev => {
        const next = prev + 1;
        if (next < items.length) {
          speakCurrent(next);
          return next;
        } else {
          setIsPlaying(false);
          return 0;
        }
      });
    };

    utterance.onerror = () => {
      setIsPlaying(false);
    };

    window.speechSynthesis.speak(utterance);
  };

  const handleTogglePlay = () => {
    if (isPlaying) {
      window.speechSynthesis.cancel();
      setIsPlaying(false);
    } else {
      setIsPlaying(true);
      speakCurrent(currentIdx);
    }
  };

  const handleReset = () => {
    window.speechSynthesis.cancel();
    setIsPlaying(false);
    setCurrentIdx(0);
  };

  if (!isSupported) return null;

  return (
    <div className="p-4 rounded-2xl bg-gradient-to-r from-indigo-950/70 via-slate-900/90 to-purple-950/60 border border-indigo-500/30 flex items-center justify-between gap-4 shadow-xl flex-wrap">
      <div className="flex items-center gap-3">
        <div className={`p-2.5 rounded-xl bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 ${isPlaying ? 'animate-pulse' : ''}`}>
          <Radio className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono uppercase font-bold text-indigo-400 tracking-wider">
              VOICE DEBATE AUDIO MODE
            </span>
            {isPlaying && (
              <span className="flex h-2 w-2 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
              </span>
            )}
          </div>
          <h4 className="text-xs font-bold text-white font-display">
            {isPlaying ? `Speaking: ${items[currentIdx]?.agent}` : "Listen to Multi-Agent Boardroom Deliberation"}
          </h4>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={handleTogglePlay}
          className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-mono font-bold flex items-center gap-1.5 btn-press shadow-md shadow-indigo-600/30 transition-all"
        >
          {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
          <span>{isPlaying ? 'Pause Audio' : 'Play Debate'}</span>
        </button>

        {isPlaying && (
          <button
            onClick={handleReset}
            className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl border border-white/10 btn-press transition-all"
            title="Reset Audio"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </div>
  );
}
