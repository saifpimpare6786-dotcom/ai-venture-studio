import React, { useState } from 'react';
import { MessageSquare, Send, Sparkles, User, Bot, HelpCircle, Shield, TrendingUp, Target, Scale, Zap } from 'lucide-react';
import { api } from '../lib/api';

export function AgentQACockpit({ projectId, projectName }) {
  const [selectedPersona, setSelectedPersona] = useState('finance');
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([
    {
      sender: 'agent',
      persona: 'finance',
      text: `Hello! I am the Senior Venture Capital Finance Partner for ${projectName || 'this venture'}. Ask me anything regarding unit economics, CAC payback, 3-year ARR growth, or margin optimization.`,
      sources: ['Financial Feasibility Engine']
    }
  ]);

  const personas = [
    { id: 'strategy', label: 'Strategy Agent', icon: Target, color: 'text-primary-400', border: 'border-primary-500/30' },
    { id: 'finance', label: 'Finance CFO', icon: TrendingUp, color: 'text-emerald-400', border: 'border-emerald-500/30' },
    { id: 'marketing', label: 'Head of GTM', icon: Zap, color: 'text-cyan-400', border: 'border-cyan-500/30' },
    { id: 'risk', label: 'Risk & Legal', icon: Shield, color: 'text-amber-400', border: 'border-amber-500/30' },
    { id: 'critic', label: 'Adversarial Critic', icon: Scale, color: 'text-rose-400', border: 'border-rose-500/30' }
  ];

  const handleSend = async (e) => {
    e.preventDefault();
    if (!question.trim() || loading) return;

    const userText = question.trim();
    setQuestion('');
    setHistory(prev => [...prev, { sender: 'user', text: userText }]);
    setLoading(true);

    try {
      const res = await api.post(`/api/simulator/interrogate/${projectId}`, {
        agent_persona: selectedPersona,
        question: userText
      });

      setHistory(prev => [
        ...prev,
        {
          sender: 'agent',
          persona: res.data.agent_persona,
          text: res.data.response,
          sources: res.data.data_sources_referenced || []
        }
      ]);
    } catch (err) {
      setHistory(prev => [
        ...prev,
        {
          sender: 'agent',
          persona: selectedPersona,
          text: 'Unable to complete analysis. Please retry your inquiry.',
          sources: []
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gradient-to-br from-slate-900/95 via-slate-950/90 to-[#080B11] p-6 rounded-2xl border border-white/10 shadow-2xl space-y-5">
      <div className="flex items-center justify-between border-b border-white/10 pb-4 flex-wrap gap-2">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-500/20 text-indigo-400 rounded-xl">
            <MessageSquare className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-mono font-bold text-indigo-400 uppercase tracking-wider block">
              INTERACTIVE BOARDROOM
            </span>
            <h3 className="text-lg font-bold text-white font-display">Direct Agent Persona Interrogation</h3>
          </div>
        </div>

        {/* Persona Selectors */}
        <div className="flex items-center gap-1.5 flex-wrap">
          {personas.map((p) => {
            const Icon = p.icon;
            const isSelected = selectedPersona === p.id;
            return (
              <button
                key={p.id}
                onClick={() => setSelectedPersona(p.id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold flex items-center gap-1.5 btn-press transition-all border ${
                  isSelected
                    ? `bg-indigo-600/30 ${p.color} ${p.border} shadow-md`
                    : 'bg-slate-950/60 text-slate-400 border-white/10 hover:text-white'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{p.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Conversation Thread */}
      <div className="space-y-4 max-h-[380px] overflow-y-auto p-4 rounded-xl bg-slate-950/70 border border-white/5 custom-scrollbar">
        {history.map((msg, idx) => (
          <div
            key={idx}
            className={`flex gap-3 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.sender === 'agent' && (
              <div className="w-8 h-8 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center shrink-0 text-indigo-300">
                <Bot className="w-4 h-4" />
              </div>
            )}
            
            <div
              className={`max-w-2xl p-4 rounded-2xl text-xs leading-relaxed space-y-2 ${
                msg.sender === 'user'
                  ? 'bg-primary-600 text-white rounded-br-none shadow-md'
                  : 'bg-slate-900/90 text-slate-200 border border-white/10 rounded-bl-none shadow-md'
              }`}
            >
              {msg.sender === 'agent' && (
                <div className="flex items-center justify-between border-b border-white/5 pb-1 mb-1">
                  <span className="font-mono font-bold text-[10px] uppercase text-indigo-400">
                    ● {msg.persona} Agent Response
                  </span>
                </div>
              )}
              <p className="whitespace-pre-line">{msg.text}</p>

              {msg.sources && msg.sources.length > 0 && (
                <div className="flex items-center gap-1.5 flex-wrap pt-1.5 border-t border-white/5 text-[10px] font-mono text-slate-400">
                  <span>Referenced:</span>
                  {msg.sources.map((s, sIdx) => (
                    <span key={sIdx} className="bg-white/5 px-2 py-0.5 rounded text-indigo-300">
                      {s}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {msg.sender === 'user' && (
              <div className="w-8 h-8 rounded-xl bg-primary-600/20 border border-primary-500/30 flex items-center justify-center shrink-0 text-primary-300">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-xs text-indigo-400 font-mono py-2 animate-pulse">
            <Bot className="w-4 h-4 animate-spin" />
            <span>Consulting {selectedPersona} agent analytical data...</span>
          </div>
        )}
      </div>

      {/* Input Prompt Form */}
      <form onSubmit={handleSend} className="flex gap-2">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={`Ask @${selectedPersona} a specific question about ${projectName || 'your venture'}...`}
          className="flex-1 px-4 py-2.5 bg-slate-950/80 border border-white/15 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-all font-mono"
        />
        <button
          type="submit"
          disabled={!question.trim() || loading}
          className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded-xl text-xs font-bold font-mono uppercase flex items-center gap-1.5 btn-press shadow-md shadow-indigo-600/20"
        >
          <Send className="w-3.5 h-3.5" />
          <span>Ask</span>
        </button>
      </form>
    </div>
  );
}
