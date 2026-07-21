import React, { useState, useEffect, useRef } from 'react';
import { supabase } from '../lib/supabaseClient';
import { 
  Layers, 
  Play, 
  RefreshCw, 
  Download, 
  FileText, 
  Users2, 
  CheckCircle, 
  AlertTriangle, 
  Gauge, 
  ChevronRight, 
  Award,
  Sparkles,
  ArrowLeft,
  Calendar,
  DollarSign,
  TrendingUp,
  Activity,
  Briefcase,
  AlertCircle
} from 'lucide-react';

const REPORT_TABS = [
  'Executive Summary',
  'Business Plan',
  'SWOT Analysis',
  'Financial Projection',
  'Investment Readiness Report'
];

export default function Dashboard({ projectId, onBackToWizard }) {
  const [project, setProject] = useState(null);
  const [logs, setLogs] = useState([]);
  const [reports, setReports] = useState([]);
  const [activeReportTab, setActiveReportTab] = useState('Executive Summary');
  const [isPolling, setIsPolling] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState(null);
  const [activeLogTab, setActiveLogTab] = useState('all');
  
  const bottomRef = useRef(null);

  const fetchProjectDetails = async () => {
    try {
      const { data: projData, error: fetchErr } = await supabase
        .from('projects')
        .select('*')
        .eq('id', projectId);
        
      if (fetchErr) throw fetchErr;
      if (projData && projData.length > 0) {
        setProject(projData[0]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchLogsAndReports = async () => {
    try {
      const session = (await supabase.auth.getSession()).data.session;
      const token = session?.access_token;
      const backendUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

      // 1. Fetch Logs
      const logsRes = await fetch(`${backendUrl}/api/reports/project/${projectId}/logs`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (logsRes.ok) {
        const logsData = await logsRes.json();
        setLogs(logsData);
        
        // Auto scroll to latest logs if streaming
        if (bottomRef.current) {
          bottomRef.current.scrollIntoView({ behavior: 'smooth' });
        }
      }

      // 2. Fetch Reports
      const reportsRes = await fetch(`${backendUrl}/api/reports/project/${projectId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (reportsRes.ok) {
        const reportsData = await reportsRes.json();
        setReports(reportsData);
        
        // Stop polling if pipeline execution successfully completes or fails
        const hasCompleted = reportsData.length >= 5;
        const pipelineStatus = logs.find(l => l.agent_name === 'Pipeline Orchestrator' && l.status === 'completed');
        const pipelineFailed = logs.find(l => l.status === 'failed');

        if (hasCompleted || pipelineFailed) {
          setIsPolling(false);
          setIsGenerating(false);
        }
      }
    } catch (err) {
      console.error("Polling error: ", err);
    }
  };

  const handleTriggerPipeline = async () => {
    setError(null);
    setIsGenerating(true);
    setIsPolling(true);
    
    try {
      const session = (await supabase.auth.getSession()).data.session;
      const token = session?.access_token;
      const backendUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      
      const response = await fetch(`${backendUrl}/api/reports/project/${projectId}/generate`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) {
        throw new Error(await response.text());
      }
    } catch (err) {
      setError(err.message || "Failed to trigger report generation.");
      setIsGenerating(false);
    }
  };

  const handleDownload = async (reportId, format) => {
    try {
      const session = (await supabase.auth.getSession()).data.session;
      const token = session?.access_token;
      const backendUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      
      window.open(`${backendUrl}/api/reports/${reportId}/download/${format}?key=${token}`, '_blank');
    } catch (err) {
      console.error("Download failed: ", err);
    }
  };

  // Initial load
  useEffect(() => {
    fetchProjectDetails();
  }, [projectId]);

  // Polling Loop
  useEffect(() => {
    if (!isPolling) return;
    
    fetchLogsAndReports();
    const interval = setInterval(fetchLogsAndReports, 3000);
    return () => clearInterval(interval);
  }, [isPolling, logs.length]);

  const currentReport = reports.find(r => r.report_type === activeReportTab);
  const scores = reports.length > 0 ? reports[0].scores : null;

  // Helpers to render score colors
  const getScoreColor = (score) => {
    if (score >= 80) return 'text-emerald-400 border-emerald-500/30';
    if (score >= 60) return 'text-cyan-400 border-cyan-500/30';
    return 'text-amber-400 border-amber-500/30';
  };

  const getAgentBadge = (agent) => {
    switch (agent) {
      case 'Planning Agent': return 'bg-purple-500/10 text-purple-400 border border-purple-500/20';
      case 'Orchestrator Agent': return 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20';
      case 'Research Agent': return 'bg-blue-500/10 text-blue-400 border border-blue-500/20';
      case 'Strategy Agent': return 'bg-rose-500/10 text-rose-400 border border-rose-500/20';
      case 'Finance Agent': return 'bg-amber-500/10 text-amber-400 border border-amber-500/20';
      case 'Marketing Agent': return 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
      case 'Risk Agent': return 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20';
      case 'Council Agent': return 'bg-orange-500/10 text-orange-400 border border-orange-500/20';
      default: return 'bg-white/5 text-gray-400 border border-white/5';
    }
  };

  return (
    <div className="flex-1 w-full bg-[#06040a] min-h-screen text-gray-100 flex flex-col select-none">
      {/* Background radial blobs */}
      <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[20%] -left-[10%] w-[50%] h-[50%] bg-purple-500/5 rounded-full blur-[140px]"></div>
        <div className="absolute bottom-[20%] -right-[10%] w-[50%] h-[50%] bg-cyan-500/5 rounded-full blur-[140px]"></div>
      </div>

      <div className="z-10 px-6 py-6 md:px-12 flex-1 flex flex-col gap-6 max-w-7xl mx-auto w-full">
        {/* Top workspace nav header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/5 pb-4">
          <div className="flex items-center gap-3">
            <button 
              onClick={onBackToWizard}
              className="p-2 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-all cursor-pointer"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                {project ? project.name : 'Venture Workspace'}
                {isGenerating && (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-purple-500/20 text-purple-400 border border-purple-500/30 animate-pulse">
                    <RefreshCw className="w-3 h-3 animate-spin" />
                    Boardroom Deliberation Active
                  </span>
                )}
              </h1>
              <p className="text-xs text-gray-500 mt-0.5">
                {project ? `${project.industry} | Target customer segment: ${project.target_customers}` : 'Loading venture parameters...'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={handleTriggerPipeline}
              disabled={isGenerating}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold text-white bg-purple-500 hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_0_15px_rgba(168,85,247,0.3)] transition-all cursor-pointer"
            >
              <Play className="w-3.5 h-3.5" />
              Re-run Boardroom Analysis
            </button>
            <button
              onClick={fetchLogsAndReports}
              className="p-2.5 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-gray-300 transition-all cursor-pointer"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Global Error Banner */}
        {error && (
          <div className="p-4 rounded-xl border border-red-500/20 bg-red-500/5 text-red-400 text-sm flex items-center gap-3">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Boardroom Deliberation Active Cover state if reports not ready and polling */}
        {reports.length === 0 && logs.length > 0 && isPolling ? (
          <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 glass rounded-2xl border border-white/5 p-6 flex flex-col justify-between items-center text-center py-20 min-h-[400px]">
              <div className="w-16 h-16 rounded-2xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 mb-4 shadow-[0_0_30px_rgba(168,85,247,0.15)] animate-pulse">
                <Users2 className="w-8 h-8" />
              </div>
              <div className="max-w-md">
                <h2 className="text-xl font-bold text-white mb-2">boardroom deliberation in progress</h2>
                <p className="text-sm text-gray-400">
                  Specialized AI executive agents are evaluating your business model, planning assumptions, competitor strategies, and risk profiles.
                </p>
              </div>
              <div className="w-full max-w-sm mt-8">
                <div className="w-full bg-white/5 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-gradient-to-r from-purple-500 to-cyan-500 h-full animate-progress rounded-full"></div>
                </div>
                <div className="flex justify-between text-[10px] text-gray-500 mt-2 font-semibold">
                  <span>ACTIVATING AGENTS</span>
                  <span>CROSS-CRITIQUE</span>
                  <span>COMPILING DATA</span>
                </div>
              </div>
            </div>

            {/* Live streaming logs */}
            <div className="glass rounded-2xl border border-white/5 p-5 flex flex-col h-[500px]">
              <h3 className="text-xs font-bold text-purple-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                <Activity className="w-4 h-4" /> Boardroom Livestream
              </h3>
              <div className="flex-1 overflow-y-auto space-y-3.5 pr-2 scrollbar-thin">
                {logs.map((log, idx) => (
                  <div key={log.id || idx} className="p-3 rounded-lg bg-white/[0.02] border border-white/5 text-xs animate-fadeIn">
                    <div className="flex justify-between items-start gap-2">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${getAgentBadge(log.agent_name)}`}>
                        {log.agent_name}
                      </span>
                      <span className={`text-[10px] uppercase font-bold tracking-wider ${
                        log.status === 'completed' ? 'text-emerald-400' : log.status === 'started' ? 'text-cyan-400' : 'text-red-400'
                      }`}>
                        {log.status}
                      </span>
                    </div>
                    {log.output_data?.error ? (
                      <p className="text-red-400 mt-2 font-medium">{log.output_data.error}</p>
                    ) : (
                      <p className="text-gray-400 mt-2 line-clamp-2 leading-relaxed">
                        {log.output_data?.assessment || log.output_data?.plan || log.output_data?.scores?.feedback || "Deliberating..."}
                      </p>
                    )}
                  </div>
                ))}
                <div ref={bottomRef} />
              </div>
            </div>
          </div>
        ) : (
          /* Main Workspace Dashboard Grid once reports generated */
          <div className="flex-1 flex flex-col lg:flex-row gap-6">
            
            {/* Left side Workspace: Analytics & Reports tabbed viewer */}
            <div className="flex-1 flex flex-col gap-6">
              
              {/* Analytics Gauge Cards */}
              {scores && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  {/* Overall score gauge */}
                  <div className="glass rounded-2xl border border-white/5 p-5 flex flex-col items-center justify-center text-center">
                    <div className="relative w-24 h-24 flex items-center justify-center">
                      <svg className="w-full h-full transform -rotate-90">
                        <circle cx="48" cy="48" r="40" stroke="rgba(255,255,255,0.05)" strokeWidth="6" fill="transparent" />
                        <circle cx="48" cy="48" r="40" stroke="url(#overallGrad)" strokeWidth="6" fill="transparent" 
                          strokeDasharray={251.2} strokeDashoffset={251.2 - (251.2 * scores.overall_score) / 100}
                          strokeLinecap="round"
                        />
                        <defs>
                          <linearGradient id="overallGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stopColor="#A855F7" />
                            <stop offset="100%" stopColor="#06B6D4" />
                          </linearGradient>
                        </defs>
                      </svg>
                      <div className="absolute text-center">
                        <span className="text-2xl font-black text-white">{scores.overall_score}</span>
                        <p className="text-[8px] text-gray-500 uppercase tracking-widest font-bold">Overall</p>
                      </div>
                    </div>
                    <p className="text-[10px] text-gray-400 font-semibold mt-3 uppercase tracking-wider">Weighted Rubric Score</p>
                  </div>

                  {/* Viability card */}
                  <div className="glass rounded-2xl border border-white/5 p-4 flex flex-col justify-between">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-400 font-semibold">Viability</span>
                      <span className={`text-base font-black px-2 py-0.5 rounded border ${getScoreColor(scores.viability?.score)}`}>
                        {scores.viability?.score}
                      </span>
                    </div>
                    <p className="text-[10px] text-gray-400 line-clamp-3 leading-relaxed mt-2.5 font-medium">
                      {scores.viability?.rationale}
                    </p>
                    <span className="text-[8px] text-gray-500 uppercase tracking-widest font-semibold border-t border-white/5 pt-2 mt-3">
                      Weight: 35%
                    </span>
                  </div>

                  {/* Market Fit card */}
                  <div className="glass rounded-2xl border border-white/5 p-4 flex flex-col justify-between">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-400 font-semibold">Market Fit</span>
                      <span className={`text-base font-black px-2 py-0.5 rounded border ${getScoreColor(scores.market_fit?.score)}`}>
                        {scores.market_fit?.score}
                      </span>
                    </div>
                    <p className="text-[10px] text-gray-400 line-clamp-3 leading-relaxed mt-2.5 font-medium">
                      {scores.market_fit?.rationale}
                    </p>
                    <span className="text-[8px] text-gray-500 uppercase tracking-widest font-semibold border-t border-white/5 pt-2 mt-3">
                      Weight: 35%
                    </span>
                  </div>

                  {/* Financial Soundness card */}
                  <div className="glass rounded-2xl border border-white/5 p-4 flex flex-col justify-between">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-400 font-semibold">Finance Soundness</span>
                      <span className={`text-base font-black px-2 py-0.5 rounded border ${getScoreColor(scores.financial_soundness?.score)}`}>
                        {scores.financial_soundness?.score}
                      </span>
                    </div>
                    <p className="text-[10px] text-gray-400 line-clamp-3 leading-relaxed mt-2.5 font-medium">
                      {scores.financial_soundness?.rationale}
                    </p>
                    <span className="text-[8px] text-gray-500 uppercase tracking-widest font-semibold border-t border-white/5 pt-2 mt-3">
                      Weight: 30%
                    </span>
                  </div>
                </div>
              )}

              {/* Reports Suite tabs header */}
              <div className="glass rounded-2xl border border-white/5 p-5 flex-1 flex flex-col">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/5 pb-4 mb-4">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4.5 h-4.5 text-purple-400" />
                    <h3 className="text-xs font-bold text-purple-400 uppercase tracking-widest">Priority Blueprint Reports</h3>
                  </div>

                  {/* Exporter downloads dropdown actions */}
                  {currentReport && (
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">Download format:</span>
                      <button
                        onClick={() => handleDownload(currentReport.id, 'docx')}
                        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-white/10 hover:border-purple-500/30 bg-white/5 hover:bg-purple-500/5 text-gray-300 hover:text-purple-400 text-[10px] font-bold transition-all cursor-pointer"
                      >
                        <Download className="w-3 h-3" /> DOCX
                      </button>
                      <button
                        onClick={() => handleDownload(currentReport.id, 'pptx')}
                        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-white/10 hover:border-purple-500/30 bg-white/5 hover:bg-purple-500/5 text-gray-300 hover:text-purple-400 text-[10px] font-bold transition-all cursor-pointer"
                      >
                        <Download className="w-3 h-3" /> PPTX
                      </button>
                      <button
                        onClick={() => handleDownload(currentReport.id, 'pdf')}
                        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-white/10 hover:border-purple-500/30 bg-white/5 hover:bg-purple-500/5 text-gray-300 hover:text-purple-400 text-[10px] font-bold transition-all cursor-pointer"
                      >
                        <Download className="w-3 h-3" /> PDF
                      </button>
                    </div>
                  )}
                </div>

                {/* Tabs bar */}
                <div className="flex overflow-x-auto gap-2 border-b border-white/5 pb-2 mb-4 scrollbar-none">
                  {REPORT_TABS.map(tab => {
                    const isGenerated = reports.some(r => r.report_type === tab);
                    const isActive = activeReportTab === tab;
                    return (
                      <button
                        key={tab}
                        onClick={() => setActiveReportTab(tab)}
                        className={`px-4 py-2 rounded-lg text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${
                          isActive 
                            ? 'bg-purple-500 text-white shadow-[0_0_15px_rgba(168,85,247,0.3)]' 
                            : 'text-gray-400 hover:text-white bg-white/5 hover:bg-white/10'
                        }`}
                      >
                        {tab}
                        {isGenerated && <span className="ml-1.5 inline-block w-1.5 h-1.5 rounded-full bg-cyan-400"></span>}
                      </button>
                    );
                  })}
                </div>

                {/* Report Content view container */}
                <div className="flex-1 overflow-y-auto h-[450px] pr-2 scrollbar-thin">
                  {currentReport ? (
                    <div className="space-y-6">
                      {activeReportTab === 'SWOT Analysis' ? (
                        /* Render SWOT Analysis as 2x2 quadrant grid */
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="p-4 rounded-xl border border-emerald-500/10 bg-emerald-500/[0.01]">
                            <h4 className="text-sm font-bold text-emerald-400 uppercase tracking-wider mb-3">Strengths</h4>
                            <ul className="list-disc pl-4 space-y-2 text-xs text-gray-300">
                              {currentReport.content.strengths?.map((item, i) => <li key={i}>{item}</li>)}
                            </ul>
                          </div>
                          <div className="p-4 rounded-xl border border-red-500/10 bg-red-500/[0.01]">
                            <h4 className="text-sm font-bold text-red-400 uppercase tracking-wider mb-3">Weaknesses</h4>
                            <ul className="list-disc pl-4 space-y-2 text-xs text-gray-300">
                              {currentReport.content.weaknesses?.map((item, i) => <li key={i}>{item}</li>)}
                            </ul>
                          </div>
                          <div className="p-4 rounded-xl border border-cyan-500/10 bg-cyan-500/[0.01]">
                            <h4 className="text-sm font-bold text-cyan-400 uppercase tracking-wider mb-3">Opportunities</h4>
                            <ul className="list-disc pl-4 space-y-2 text-xs text-gray-300">
                              {currentReport.content.opportunities?.map((item, i) => <li key={i}>{item}</li>)}
                            </ul>
                          </div>
                          <div className="p-4 rounded-xl border border-amber-500/10 bg-amber-500/[0.01]">
                            <h4 className="text-sm font-bold text-amber-400 uppercase tracking-wider mb-3">Threats</h4>
                            <ul className="list-disc pl-4 space-y-2 text-xs text-gray-300">
                              {currentReport.content.threats?.map((item, i) => <li key={i}>{item}</li>)}
                            </ul>
                          </div>
                        </div>
                      ) : (
                        /* Standard sections view */
                        Object.entries(currentReport.content).map(([secKey, secVal]) => {
                          if (secKey === 'overall_score') return null;
                          return (
                            <div key={secKey} className="space-y-2">
                              <h4 className="text-xs font-bold text-white uppercase tracking-widest border-l-2 border-purple-500 pl-2.5">
                                {secKey.replace('_', ' ')}
                              </h4>
                              <p className="text-xs text-gray-300 leading-relaxed font-medium">
                                {String(secVal)}
                              </p>
                            </div>
                          );
                        })
                      )}
                    </div>
                  ) : (
                    <div className="h-full flex flex-col justify-center items-center text-center text-gray-500">
                      <FileText className="w-10 h-10 mb-2 opacity-50" />
                      <p className="text-sm">Report not yet compiled. Initiating setup analysis.</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Right side boardroom activities log viewer */}
            <div className="w-full lg:w-96 flex flex-col gap-4">
              <div className="glass rounded-2xl border border-white/5 p-5 flex-1 flex flex-col h-[580px]">
                <h3 className="text-xs font-bold text-purple-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                  <Users2 className="w-4.5 h-4.5" /> Boardroom Livestream
                </h3>
                
                {/* Active logs filter tabs */}
                <div className="flex gap-1.5 border-b border-white/5 pb-3 mb-4 text-[10px]">
                  <button 
                    onClick={() => setActiveLogTab('all')}
                    className={`px-3 py-1.5 rounded font-bold cursor-pointer ${activeLogTab === 'all' ? 'bg-purple-500 text-white' : 'text-gray-400 bg-white/5 hover:bg-white/10'}`}
                  >
                    All Activities
                  </button>
                  <button 
                    onClick={() => setActiveLogTab('specialized')}
                    className={`px-3 py-1.5 rounded font-bold cursor-pointer ${activeLogTab === 'specialized' ? 'bg-purple-500 text-white' : 'text-gray-400 bg-white/5 hover:bg-white/10'}`}
                  >
                    Expert Agents
                  </button>
                  <button 
                    onClick={() => setActiveLogTab('reviews')}
                    className={`px-3 py-1.5 rounded font-bold cursor-pointer ${activeLogTab === 'reviews' ? 'bg-purple-500 text-white' : 'text-gray-400 bg-white/5 hover:bg-white/10'}`}
                  >
                    Deliberations
                  </button>
                </div>

                <div className="flex-1 overflow-y-auto space-y-3.5 pr-2 scrollbar-thin">
                  {logs
                    .filter(log => {
                      if (activeLogTab === 'specialized') {
                        return ['Strategy Agent', 'Finance Agent', 'Marketing Agent', 'Risk Agent'].includes(log.agent_name);
                      }
                      if (activeLogTab === 'reviews') {
                        return ['Council Agent', 'Reviewer Agent', 'Critic Agent', 'Business Rules Engine'].includes(log.agent_name);
                      }
                      return true;
                    })
                    .map((log, idx) => (
                      <div key={log.id || idx} className="p-3 rounded-lg bg-white/[0.02] border border-white/5 text-xs">
                        <div className="flex justify-between items-start gap-2">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${getAgentBadge(log.agent_name)}`}>
                            {log.agent_name}
                          </span>
                          <span className={`text-[10px] uppercase font-bold tracking-wider ${
                            log.status === 'completed' ? 'text-emerald-400' : log.status === 'started' ? 'text-cyan-400' : 'text-red-400'
                          }`}>
                            {log.status}
                          </span>
                        </div>
                        {log.output_data?.error ? (
                          <p className="text-red-400 mt-2 font-medium">{log.output_data.error}</p>
                        ) : (
                          <p className="text-gray-400 mt-2 line-clamp-3 leading-relaxed">
                            {log.output_data?.assessment || log.output_data?.plan || log.output_data?.scores?.feedback || "Deliberating..."}
                          </p>
                        )}
                      </div>
                    ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
