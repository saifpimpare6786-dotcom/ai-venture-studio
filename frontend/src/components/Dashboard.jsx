import React, { useState, useEffect, useRef } from 'react';
import { supabase } from '../lib/supabaseClient';
import { 
  RefreshCw, 
  Download, 
  FileText, 
  ArrowLeft,
  AlertCircle,
  ExternalLink
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  RadarChart, 
  PolarGrid, 
  PolarAngleAxis, 
  PolarRadiusAxis, 
  Radar, 
  RadialBarChart, 
  RadialBar, 
  PolarAngleAxis as RadialPolarAngleAxis 
} from 'recharts';

const REPORT_TABS = [
  'Executive Summary',
  'Business Plan',
  'Strategic Environment Analysis',
  'Financial Projection',
  'Investment Readiness Report',
  'Business Model Canvas',
  'Competitor Analysis',
  'Marketing Plan & Go-To-Market',
  'Risk Assessment & Mitigation Matrix',
  'ESG & Sustainability Recommendations',
  'Pitch Summary & Investor Deck Outline'
];

const isNumericScore = (val) => {
  if (val === null || val === undefined || val === '') return false;
  const num = Number(val);
  return !isNaN(num) && isFinite(num);
};

const getScoreHexColor = (score) => {
  const num = Number(score);
  if (isNaN(num)) return '#98A2B3';
  if (num >= 80) return '#059669'; // Muted Green
  if (num >= 60) return '#0284C7'; // Muted Cyan/Sky
  return '#D97706'; // Muted Amber
};

const RubricCard = ({ title, scoreObj, weight, getScoreColor }) => {
  const scoreVal = scoreObj?.score;
  const rationale = scoreObj?.rationale;
  const numeric = isNumericScore(scoreVal);
  const numericScore = numeric ? Number(scoreVal) : null;
  const hexColor = getScoreHexColor(numericScore);

  return (
    <div className="bg-white rounded-xl border border-[#E4E7EC] shadow-xs p-5 flex flex-col justify-between">
      <div className="flex items-center justify-between">
        <span className="text-xs text-[#1A1D23] font-bold">{title}</span>
        <span className={`text-sm font-black px-2.5 py-0.5 rounded border ${getScoreColor(scoreVal)}`}>
          {numericScore !== null ? numericScore : (scoreVal || 'N/A')}
        </span>
      </div>

      <div className="my-3 flex items-center gap-3">
        {numericScore !== null ? (
          <div className="w-16 h-16 relative flex-shrink-0">
            <ResponsiveContainer width="100%" height="100%">
              <RadialBarChart 
                cx="50%" 
                cy="50%" 
                innerRadius="65%" 
                outerRadius="100%" 
                barSize={6} 
                data={[{ name: title, value: numericScore, fill: hexColor }]} 
                startAngle={90} 
                endAngle={-270}
              >
                <RadialPolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
                <RadialBar
                  background={{ fill: '#F1F5F9' }}
                  dataKey="value"
                  cornerRadius={4}
                />
              </RadialBarChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <span className="text-xs font-black text-[#1A1D23]">{numericScore}</span>
            </div>
          </div>
        ) : null}

        <p className="text-[11px] text-[#4B5565] line-clamp-3 leading-relaxed font-medium flex-1">
          {rationale || 'Evaluation rationale pending analysis.'}
        </p>
      </div>

      <span className="text-[9px] text-[#98A2B3] uppercase tracking-widest font-semibold border-t border-[#E4E7EC] pt-2">
        Weight: {weight}
      </span>
    </div>
  );
};


export default function Dashboard({ projectId, onBackToWizard }) {
  const [project, setProject] = useState(null);
  const [reports, setReports] = useState([]);
  const [sources, setSources] = useState([]);
  const [activeReportTab, setActiveReportTab] = useState('Executive Summary');
  const [isPolling, setIsPolling] = useState(true);
  const [error, setError] = useState(null);

  const inFlightRef = useRef(false);

  // Derive dynamic tabs list combining standard reports and any returned report types
  const dynamicReportTabs = React.useMemo(() => {
    if (!reports || reports.length === 0) return REPORT_TABS;
    const groupedTypes = ['SWOT Analysis', 'PESTLE Analysis', "Porter's Five Forces"];
    const loadedTypes = reports
      .map(r => r.report_type)
      .filter(type => !groupedTypes.includes(type));
    return Array.from(new Set([...REPORT_TABS, ...loadedTypes]));
  }, [reports]);

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

  const fetchReports = async () => {
    if (inFlightRef.current) return;
    inFlightRef.current = true;

    try {
      const { data } = await supabase.auth.getSession();
      const token = data?.session?.access_token;
      
      if (!token) {
        setIsPolling(false);
        setError("Authentication session missing. Please log in again.");
        return;
      }

      const backendUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

      const res = await fetch(`${backendUrl}/api/reports/project/${projectId}/status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (res.status === 401) {
        setIsPolling(false);
        setError("Authentication expired (401 Unauthorized). Please log in again.");
        return;
      }

      if (res.status === 503) {
        console.warn("Transient 503 from backend -- will retry on next poll tick.");
        return;
      }

      if (!res.ok) {
        console.warn(`Backend status query returned HTTP ${res.status}`);
        return;
      }

      const statusData = await res.json();
      const fetchedReports = statusData.reports || [];
      const fetchedSources = statusData.sources || [];
      const projStatus = statusData.status || 'idle';

      setReports(fetchedReports);
      setSources(fetchedSources);

      // Stop polling once project status is complete or failed, or 13 reports generated
      if (projStatus === 'complete' || projStatus === 'failed' || fetchedReports.length >= 13) {
        setIsPolling(false);
      }
    } catch (err) {
      console.error("Polling error: ", err);
    } finally {
      inFlightRef.current = false;
    }
  };

  const handleDownload = async (reportId, format) => {
    try {
      const { data } = await supabase.auth.getSession();
      const token = data?.session?.access_token;
      
      if (!token) {
        setError("Authentication session missing. Please log in again.");
        return;
      }

      const backendUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      
      const res = await fetch(`${backendUrl}/api/reports/${reportId}/download/${format}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (res.status === 401) {
        setError("Authentication expired (401 Unauthorized). Please log in again.");
        return;
      }

      if (!res.ok) {
        throw new Error(`Server error: ${res.statusText}`);
      }

      const blob = await res.blob();
      const contentDisposition = res.headers.get('Content-Disposition');
      let filename = `report_${reportId}.${format}`;
      if (contentDisposition) {
        const match = contentDisposition.match(/filename=["']?([^"';]+)["']?/);
        if (match && match[1]) {
          filename = match[1];
        }
      }

      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(blobUrl);
    } catch (err) {
      console.error("Download failed: ", err);
      setError(`Download failed: ${err.message}`);
    }
  };

  // Initial load & Polling Loop
  useEffect(() => {
    fetchProjectDetails();
    fetchReports();

    if (!isPolling) return;
    
    const interval = setInterval(() => {
      fetchReports();
    }, 4000);

    return () => clearInterval(interval);
  }, [projectId, isPolling]);

  const swotReport = reports.find(r => r.report_type === 'SWOT Analysis');
  const pestleReport = reports.find(r => r.report_type === 'PESTLE Analysis');
  const portersReport = reports.find(r => r.report_type === "Porter's Five Forces");

  const currentReport = reports.find(r => 
    r.report_type === activeReportTab || 
    r.report_type.toLowerCase() === activeReportTab.toLowerCase() ||
    (activeReportTab.startsWith("Investment Readiness") && r.report_type.startsWith("Investment Readiness")) ||
    (activeReportTab.startsWith("Marketing Plan") && r.report_type.startsWith("Marketing Plan"))
  );
  const scores = reports.length > 0 ? reports[0].scores : null;

  // Helpers to render score colors in professional light theme
  const getScoreColor = (score) => {
    if (score >= 80) return 'bg-[#ECFDF5] text-[#059669] border-[#A7F3D0]';
    if (score >= 60) return 'bg-[#EFF6FF] text-[#0284C7] border-[#BAE6FD]';
    return 'bg-[#FFFBEB] text-[#D97706] border-[#FDE68A]';
  };

  // Content renderers for frameworks
  const renderSwotContent = (report) => {
    if (!report || !report.content) {
      return (
        <div className="p-4 rounded-xl border border-dashed border-[#E4E7EC] text-center text-xs text-[#98A2B3]">
          SWOT Analysis exhibit pending compilation...
        </div>
      );
    }
    const content = report.content;
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div className="p-5 rounded-xl border border-[#A7F3D0] bg-[#F0FDF4]">
          <h4 className="text-xs font-extrabold text-[#15803D] uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[#15803D]"></span> Strengths
          </h4>
          <ul className="list-disc pl-4 space-y-2 text-xs text-[#166534] leading-relaxed">
            {Array.isArray(content.strengths) ? content.strengths.map((item, i) => <li key={i}>{item}</li>) : <li>{String(content.strengths || '')}</li>}
          </ul>
        </div>
        <div className="p-5 rounded-xl border border-[#FECACA] bg-[#FEF2F2]">
          <h4 className="text-xs font-extrabold text-[#B91C1C] uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[#B91C1C]"></span> Weaknesses
          </h4>
          <ul className="list-disc pl-4 space-y-2 text-xs text-[#991B1B] leading-relaxed">
            {Array.isArray(content.weaknesses) ? content.weaknesses.map((item, i) => <li key={i}>{item}</li>) : <li>{String(content.weaknesses || '')}</li>}
          </ul>
        </div>
        <div className="p-5 rounded-xl border border-[#99F6E4] bg-[#F0FDFA]">
          <h4 className="text-xs font-extrabold text-[#0D9488] uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[#0D9488]"></span> Opportunities
          </h4>
          <ul className="list-disc pl-4 space-y-2 text-xs text-[#115E59] leading-relaxed">
            {Array.isArray(content.opportunities) ? content.opportunities.map((item, i) => <li key={i}>{item}</li>) : <li>{String(content.opportunities || '')}</li>}
          </ul>
        </div>
        <div className="p-5 rounded-xl border border-[#FDE68A] bg-[#FFFBEB]">
          <h4 className="text-xs font-extrabold text-[#B45309] uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[#B45309]"></span> Threats
          </h4>
          <ul className="list-disc pl-4 space-y-2 text-xs text-[#92400E] leading-relaxed">
            {Array.isArray(content.threats) ? content.threats.map((item, i) => <li key={i}>{item}</li>) : <li>{String(content.threats || '')}</li>}
          </ul>
        </div>
      </div>
    );
  };

  const renderStandardContent = (report) => {
    if (!report || !report.content) {
      return (
        <div className="p-4 rounded-xl border border-dashed border-[#E4E7EC] text-center text-xs text-[#98A2B3]">
          Analysis exhibit pending compilation...
        </div>
      );
    }
    return (
      <div className="space-y-4">
        {Object.entries(report.content).map(([secKey, secVal]) => {
          if (secKey === 'overall_score') return null;
          return (
            <div key={secKey} className="space-y-2 pb-2">
              <h4 className="text-xs font-bold text-[#1A1D23] uppercase tracking-wider border-l-3 border-[#5B4CE0] pl-3 py-0.5">
                {secKey.replace(/_/g, ' ')}
              </h4>
              {Array.isArray(secVal) ? (
                <ul className="list-disc pl-7 space-y-1.5 text-xs text-[#4B5565] leading-relaxed font-medium">
                  {secVal.map((item, idx) => (
                    <li key={idx}>{String(item)}</li>
                  ))}
                </ul>
              ) : typeof secVal === 'object' && secVal !== null ? (
                <div className="pl-3 space-y-1 text-xs text-[#4B5565] font-medium">
                  {Object.entries(secVal).map(([subK, subV]) => (
                    <div key={subK}>
                      <span className="font-bold text-[#1A1D23]">{subK.replace(/_/g, ' ')}: </span>
                      {Array.isArray(subV) ? subV.join(', ') : String(subV)}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-[#4B5565] leading-relaxed font-medium pl-3">
                  {String(secVal)}
                </p>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="flex-1 w-full bg-[#F8F9FB] min-h-screen text-[#4B5565] flex flex-col select-none">
      <div className="z-10 px-6 py-6 md:px-12 flex-1 flex flex-col gap-6 max-w-7xl mx-auto w-full">
        {/* Top workspace nav header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#E4E7EC] pb-4">
          <div className="flex items-center gap-3">
            <button 
              onClick={onBackToWizard}
              className="p-2 rounded-lg border border-[#E4E7EC] bg-white hover:bg-[#FAFAFC] text-[#4B5565] hover:text-[#1A1D23] transition-all cursor-pointer shadow-xs"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <div>
              <h1 className="text-2xl font-extrabold tracking-tight text-[#1A1D23] flex items-center gap-2.5">
                {project ? project.name : 'Venture Workspace'}
                {isPolling && reports.length < 13 && (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-[#F0EEFF] text-[#5B4CE0] border border-[#5B4CE0]/20 animate-pulse">
                    <RefreshCw className="w-3 h-3 animate-spin" />
                    Generating Reports...
                  </span>
                )}
              </h1>
              <p className="text-xs text-[#98A2B3] mt-0.5 font-medium">
                {project ? `${project.industry} | Target customer segment: ${project.target_customers}` : 'Loading venture parameters...'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={fetchReports}
              className="px-3.5 py-2 rounded-lg border border-[#E4E7EC] bg-white hover:bg-[#FAFAFC] text-[#4B5565] transition-all cursor-pointer flex items-center gap-1.5 text-xs font-semibold shadow-xs"
            >
              <RefreshCw className="w-4 h-4 text-[#5B4CE0]" /> Refresh
            </button>
          </div>
        </div>

        {/* Global Error Banner */}
        {error && (
          <div className="p-4 rounded-xl border border-red-200 bg-red-50 text-red-700 text-sm flex items-center gap-3 shadow-xs">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Loading cover state if reports not ready and polling */}
        {reports.length === 0 && isPolling ? (
          <div className="bg-white rounded-2xl border border-[#E4E7EC] shadow-xs p-6 flex flex-col justify-between items-center text-center py-20 min-h-[400px] w-full">
            <div className="w-16 h-16 rounded-2xl bg-[#F0EEFF] border border-[#5B4CE0]/20 flex items-center justify-center text-[#5B4CE0] mb-4 shadow-xs animate-pulse">
              <RefreshCw className="w-8 h-8 animate-spin" />
            </div>
            <div className="max-w-md">
              <h2 className="text-xl font-bold text-[#1A1D23] mb-2">Analyzing Venture Model</h2>
              <p className="text-sm text-[#4B5565]">
                Specialized AI agents are evaluating your business model, planning assumptions, competitor strategies, and risk profiles to compile your report suite.
              </p>
            </div>
            <div className="w-full max-w-sm mt-8">
              <div className="w-full bg-[#F1F5F9] h-1.5 rounded-full overflow-hidden">
                <div className="bg-gradient-to-r from-[#5B4CE0] to-[#0EA5A5] h-full animate-progress rounded-full"></div>
              </div>
              <div className="flex justify-between text-[10px] text-[#98A2B3] mt-2 font-bold tracking-wider">
                <span>ACTIVATING AGENTS</span>
                <span>CROSS-CRITIQUE</span>
                <span>COMPILING REPORTS</span>
              </div>
            </div>
          </div>
        ) : (
          /* Main Workspace Layout */
          <div className="flex-1 flex flex-col gap-6 w-full">
            
            {/* Executive Cover Exhibit Card */}
            {scores && (
              <div className="bg-white rounded-2xl border border-[#E4E7EC] shadow-xs p-6 flex flex-col gap-5 w-full">
                {/* Exhibit Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-[#E4E7EC] pb-4">
                  <div>
                    <span className="text-[10px] uppercase tracking-widest font-bold text-[#98A2B3]">EXHIBIT A</span>
                    <h2 className="text-base md:text-lg font-extrabold text-[#1A1D23]">Executive Scorecard & Strategic Profile</h2>
                  </div>
                  {isNumericScore(scores.overall_score) && (
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#F0EEFF] border border-[#5B4CE0]/20 text-[#5B4CE0] self-start md:self-auto">
                      <span className="text-[10px] font-bold uppercase tracking-wider">Overall Rubric Index</span>
                      <span className="text-sm font-black">{scores.overall_score} / 100</span>
                    </div>
                  )}
                </div>

                {/* Upper Section: Overall Gauge + 3-Axis Radar Chart Exhibit */}
                <div className="grid grid-cols-1 md:grid-cols-5 gap-5">
                  {/* Col 1 (2 cols wide): Overall Gauge & Metrics */}
                  <div className="md:col-span-2 bg-[#F8F9FB] rounded-xl border border-[#E4E7EC] p-5 flex flex-col items-center justify-center text-center">
                    <div className="relative w-28 h-28 flex items-center justify-center">
                      <svg className="w-full h-full transform -rotate-90">
                        <circle cx="56" cy="56" r="46" stroke="#E4E7EC" strokeWidth="7" fill="transparent" />
                        <circle cx="56" cy="56" r="46" stroke="url(#overallGrad)" strokeWidth="7" fill="transparent" 
                          strokeDasharray={289} strokeDashoffset={isNumericScore(scores.overall_score) ? (289 - (289 * Number(scores.overall_score)) / 100) : 0}
                          strokeLinecap="round"
                        />
                        <defs>
                          <linearGradient id="overallGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stopColor="#5B4CE0" />
                            <stop offset="100%" stopColor="#0EA5A5" />
                          </linearGradient>
                        </defs>
                      </svg>
                      <div className="absolute text-center">
                        <span className="text-3xl font-black text-[#1A1D23]">{scores.overall_score}</span>
                        <p className="text-[8px] text-[#98A2B3] uppercase tracking-widest font-bold">Overall</p>
                      </div>
                    </div>
                    <p className="text-[10px] text-[#98A2B3] font-semibold mt-3 uppercase tracking-wider">Weighted Rubric Score (35 / 35 / 30)</p>
                  </div>

                  {/* Col 2 (3 cols wide): Radar Chart Exhibit */}
                  <div className="md:col-span-3 bg-[#F8F9FB] rounded-xl border border-[#E4E7EC] p-4 flex flex-col justify-between min-h-[180px]">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-[#1A1D23] uppercase tracking-wider">Strategic Dimensions Profile</span>
                      <span className="text-[10px] font-semibold text-[#0EA5A5]">3-Axis Radar</span>
                    </div>
                    <div className="w-full h-[150px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <RadarChart cx="50%" cy="50%" outerRadius="70%" data={[
                          { subject: 'Viability', score: isNumericScore(scores.viability?.score) ? Number(scores.viability?.score) : 0, fullMark: 100 },
                          { subject: 'Market Fit', score: isNumericScore(scores.market_fit?.score) ? Number(scores.market_fit?.score) : 0, fullMark: 100 },
                          { subject: 'Financial Soundness', score: isNumericScore(scores.financial_soundness?.score) ? Number(scores.financial_soundness?.score) : 0, fullMark: 100 },
                        ]}>
                          <PolarGrid stroke="#E4E7EC" />
                          <PolarAngleAxis dataKey="subject" tick={{ fill: '#4B5565', fontSize: 10, fontWeight: 700 }} />
                          <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                          <Radar 
                            name="Rubric Score" 
                            dataKey="score" 
                            stroke="#5B4CE0" 
                            fill="#5B4CE0" 
                            fillOpacity={0.25} 
                            dot={{ r: 4, fill: '#0EA5A5', stroke: '#FFFFFF', strokeWidth: 1.5 }} 
                          />
                        </RadarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>

                {/* Lower Section: 3 Rubric Cards with Recharts Radial Gauges & Rationale text */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <RubricCard title="Viability" scoreObj={scores.viability} weight="35%" getScoreColor={getScoreColor} />
                  <RubricCard title="Market Fit" scoreObj={scores.market_fit} weight="35%" getScoreColor={getScoreColor} />
                  <RubricCard title="Financial Soundness" scoreObj={scores.financial_soundness} weight="30%" getScoreColor={getScoreColor} />
                </div>
              </div>
            )}

            {/* Reports Suite tabs header */}
            <div className="bg-white rounded-2xl border border-[#E4E7EC] shadow-xs p-6 flex-1 flex flex-col w-full">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#E4E7EC] pb-4 mb-4">
                <div className="flex items-center gap-2.5">
                  <FileText className="w-5 h-5 text-[#5B4CE0]" />
                  <div>
                    <h3 className="text-xs font-bold text-[#1A1D23] uppercase tracking-wider">Priority Blueprint Reports</h3>
                    <p className="text-[10px] text-[#98A2B3] font-medium">Executive analysis exhibits generated by AI Council</p>
                  </div>
                </div>

                {/* Exporter downloads dropdown actions for standard single reports */}
                {currentReport && activeReportTab !== 'Strategic Environment Analysis' && (
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-[#98A2B3] uppercase tracking-wider font-semibold">Export exhibit:</span>
                    <button
                      onClick={() => handleDownload(currentReport.id, 'docx')}
                      className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-[#E4E7EC] hover:border-[#5B4CE0]/30 bg-white hover:bg-[#F0EEFF] text-[#4B5565] hover:text-[#5B4CE0] text-[11px] font-bold transition-all cursor-pointer shadow-xs"
                    >
                      <Download className="w-3 h-3 text-[#5B4CE0]" /> DOCX
                    </button>
                    <button
                      onClick={() => handleDownload(currentReport.id, 'pptx')}
                      className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-[#E4E7EC] hover:border-[#5B4CE0]/30 bg-white hover:bg-[#F0EEFF] text-[#4B5565] hover:text-[#5B4CE0] text-[11px] font-bold transition-all cursor-pointer shadow-xs"
                    >
                      <Download className="w-3 h-3 text-[#5B4CE0]" /> PPTX
                    </button>
                    <button
                      onClick={() => handleDownload(currentReport.id, 'pdf')}
                      className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-[#E4E7EC] hover:border-[#5B4CE0]/30 bg-white hover:bg-[#F0EEFF] text-[#4B5565] hover:text-[#5B4CE0] text-[11px] font-bold transition-all cursor-pointer shadow-xs"
                    >
                      <Download className="w-3 h-3 text-[#5B4CE0]" /> PDF
                    </button>
                  </div>
                )}
              </div>

              {/* Tabs bar */}
              <div className="flex overflow-x-auto gap-1.5 border-b border-[#E4E7EC] pb-3 mb-5">
                {dynamicReportTabs.map(tab => {
                  const isGenerated = tab === 'Strategic Environment Analysis'
                    ? reports.some(r => ['SWOT Analysis', 'PESTLE Analysis', "Porter's Five Forces"].includes(r.report_type))
                    : reports.some(r => 
                        r.report_type === tab || 
                        r.report_type.toLowerCase() === tab.toLowerCase() ||
                        (tab.startsWith("Investment Readiness") && r.report_type.startsWith("Investment Readiness")) ||
                        (tab.startsWith("Marketing Plan") && r.report_type.startsWith("Marketing Plan"))
                      );
                  const isActive = activeReportTab === tab;
                  return (
                    <button
                      key={tab}
                      onClick={() => setActiveReportTab(tab)}
                      className={`px-3.5 py-2 rounded-lg text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${
                        isActive 
                          ? 'bg-[#5B4CE0] text-white shadow-xs' 
                          : 'text-[#4B5565] hover:text-[#1A1D23] bg-[#F8F9FB] hover:bg-[#F1F5F9] border border-[#E4E7EC]'
                      }`}
                    >
                      {tab}
                      {isGenerated && <span className={`ml-1.5 inline-block w-1.5 h-1.5 rounded-full ${isActive ? 'bg-white' : 'bg-[#0EA5A5]'}`}></span>}
                    </button>
                  );
                })}
              </div>

              {/* Report Content view container - Exhibit Structure */}
              <div className="flex-1 overflow-y-auto h-[520px] pr-3">
                {activeReportTab === 'Strategic Environment Analysis' ? (
                  <div className="space-y-6 bg-white p-2">
                    <div className="border-b border-[#E4E7EC] pb-3 mb-4 flex items-center justify-between">
                      <div>
                        <span className="text-[10px] uppercase tracking-widest font-bold text-[#98A2B3]">Integrated Framework Suite</span>
                        <h2 className="text-xl font-extrabold text-[#1A1D23] mt-0.5">Strategic Environment Analysis</h2>
                      </div>
                      <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-[#F0EEFF] text-[#5B4CE0]">
                        3 Core Frameworks
                      </span>
                    </div>

                    {/* Sub-section 1: SWOT Analysis */}
                    <div className="bg-[#F8F9FB] rounded-xl border border-[#E4E7EC] p-5 space-y-4">
                      <div className="flex items-center justify-between border-b border-[#E4E7EC] pb-3">
                        <div className="flex items-center gap-2">
                          <span className="w-2.5 h-2.5 rounded-full bg-[#5B4CE0]"></span>
                          <h3 className="text-sm font-extrabold text-[#1A1D23] uppercase tracking-wider">
                            SWOT Analysis
                          </h3>
                        </div>
                        {swotReport && (
                          <div className="flex items-center gap-1.5">
                            <span className="text-[10px] text-[#98A2B3] uppercase tracking-wider font-semibold mr-1">Export:</span>
                            <button
                              onClick={() => handleDownload(swotReport.id, 'docx')}
                              className="flex items-center gap-1 px-2 py-1 rounded border border-[#E4E7EC] hover:border-[#5B4CE0]/30 bg-white hover:bg-[#F0EEFF] text-[#4B5565] hover:text-[#5B4CE0] text-[10px] font-bold transition-all cursor-pointer shadow-xs"
                            >
                              <Download className="w-3 h-3 text-[#5B4CE0]" /> DOCX
                            </button>
                            <button
                              onClick={() => handleDownload(swotReport.id, 'pptx')}
                              className="flex items-center gap-1 px-2 py-1 rounded border border-[#E4E7EC] hover:border-[#5B4CE0]/30 bg-white hover:bg-[#F0EEFF] text-[#4B5565] hover:text-[#5B4CE0] text-[10px] font-bold transition-all cursor-pointer shadow-xs"
                            >
                              <Download className="w-3 h-3 text-[#5B4CE0]" /> PPTX
                            </button>
                            <button
                              onClick={() => handleDownload(swotReport.id, 'pdf')}
                              className="flex items-center gap-1 px-2 py-1 rounded border border-[#E4E7EC] hover:border-[#5B4CE0]/30 bg-white hover:bg-[#F0EEFF] text-[#4B5565] hover:text-[#5B4CE0] text-[10px] font-bold transition-all cursor-pointer shadow-xs"
                            >
                              <Download className="w-3 h-3 text-[#5B4CE0]" /> PDF
                            </button>
                          </div>
                        )}
                      </div>
                      {renderSwotContent(swotReport)}
                    </div>

                    {/* Sub-section 2: PESTLE Analysis */}
                    <div className="bg-[#F8F9FB] rounded-xl border border-[#E4E7EC] p-5 space-y-4">
                      <div className="flex items-center justify-between border-b border-[#E4E7EC] pb-3">
                        <div className="flex items-center gap-2">
                          <span className="w-2.5 h-2.5 rounded-full bg-[#0EA5A5]"></span>
                          <h3 className="text-sm font-extrabold text-[#1A1D23] uppercase tracking-wider">
                            PESTLE Analysis
                          </h3>
                        </div>
                        {pestleReport && (
                          <div className="flex items-center gap-1.5">
                            <span className="text-[10px] text-[#98A2B3] uppercase tracking-wider font-semibold mr-1">Export:</span>
                            <button
                              onClick={() => handleDownload(pestleReport.id, 'docx')}
                              className="flex items-center gap-1 px-2 py-1 rounded border border-[#E4E7EC] hover:border-[#5B4CE0]/30 bg-white hover:bg-[#F0EEFF] text-[#4B5565] hover:text-[#5B4CE0] text-[10px] font-bold transition-all cursor-pointer shadow-xs"
                            >
                              <Download className="w-3 h-3 text-[#5B4CE0]" /> DOCX
                            </button>
                            <button
                              onClick={() => handleDownload(pestleReport.id, 'pptx')}
                              className="flex items-center gap-1 px-2 py-1 rounded border border-[#E4E7EC] hover:border-[#5B4CE0]/30 bg-white hover:bg-[#F0EEFF] text-[#4B5565] hover:text-[#5B4CE0] text-[10px] font-bold transition-all cursor-pointer shadow-xs"
                            >
                              <Download className="w-3 h-3 text-[#5B4CE0]" /> PPTX
                            </button>
                            <button
                              onClick={() => handleDownload(pestleReport.id, 'pdf')}
                              className="flex items-center gap-1 px-2 py-1 rounded border border-[#E4E7EC] hover:border-[#5B4CE0]/30 bg-white hover:bg-[#F0EEFF] text-[#4B5565] hover:text-[#5B4CE0] text-[10px] font-bold transition-all cursor-pointer shadow-xs"
                            >
                              <Download className="w-3 h-3 text-[#5B4CE0]" /> PDF
                            </button>
                          </div>
                        )}
                      </div>
                      {renderStandardContent(pestleReport)}
                    </div>

                    {/* Sub-section 3: Porter's Five Forces */}
                    <div className="bg-[#F8F9FB] rounded-xl border border-[#E4E7EC] p-5 space-y-4">
                      <div className="flex items-center justify-between border-b border-[#E4E7EC] pb-3">
                        <div className="flex items-center gap-2">
                          <span className="w-2.5 h-2.5 rounded-full bg-[#D97706]"></span>
                          <h3 className="text-sm font-extrabold text-[#1A1D23] uppercase tracking-wider">
                            Porter's Five Forces
                          </h3>
                        </div>
                        {portersReport && (
                          <div className="flex items-center gap-1.5">
                            <span className="text-[10px] text-[#98A2B3] uppercase tracking-wider font-semibold mr-1">Export:</span>
                            <button
                              onClick={() => handleDownload(portersReport.id, 'docx')}
                              className="flex items-center gap-1 px-2 py-1 rounded border border-[#E4E7EC] hover:border-[#5B4CE0]/30 bg-white hover:bg-[#F0EEFF] text-[#4B5565] hover:text-[#5B4CE0] text-[10px] font-bold transition-all cursor-pointer shadow-xs"
                            >
                              <Download className="w-3 h-3 text-[#5B4CE0]" /> DOCX
                            </button>
                            <button
                              onClick={() => handleDownload(portersReport.id, 'pptx')}
                              className="flex items-center gap-1 px-2 py-1 rounded border border-[#E4E7EC] hover:border-[#5B4CE0]/30 bg-white hover:bg-[#F0EEFF] text-[#4B5565] hover:text-[#5B4CE0] text-[10px] font-bold transition-all cursor-pointer shadow-xs"
                            >
                              <Download className="w-3 h-3 text-[#5B4CE0]" /> PPTX
                            </button>
                            <button
                              onClick={() => handleDownload(portersReport.id, 'pdf')}
                              className="flex items-center gap-1 px-2 py-1 rounded border border-[#E4E7EC] hover:border-[#5B4CE0]/30 bg-white hover:bg-[#F0EEFF] text-[#4B5565] hover:text-[#5B4CE0] text-[10px] font-bold transition-all cursor-pointer shadow-xs"
                            >
                              <Download className="w-3 h-3 text-[#5B4CE0]" /> PDF
                            </button>
                          </div>
                        )}
                      </div>
                      {renderStandardContent(portersReport)}
                    </div>
                  </div>
                ) : currentReport ? (
                  <div className="space-y-6 bg-white p-2">
                    <div className="border-b border-[#E4E7EC] pb-3 mb-4 flex items-center justify-between">
                      <div>
                        <span className="text-[10px] uppercase tracking-widest font-bold text-[#98A2B3]">Strategic Exhibit</span>
                        <h2 className="text-xl font-extrabold text-[#1A1D23] mt-0.5">{activeReportTab}</h2>
                      </div>
                      <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-[#F0EEFF] text-[#5B4CE0]">
                        Verified Analysis
                      </span>
                    </div>

                    {activeReportTab === 'SWOT Analysis' ? (
                      renderSwotContent(currentReport)
                    ) : (
                      renderStandardContent(currentReport)
                    )}
                  </div>
                ) : (
                  <div className="h-full flex flex-col justify-center items-center text-center text-[#98A2B3]">
                    <FileText className="w-10 h-10 mb-2 opacity-40 text-[#5B4CE0]" />
                    <p className="text-xs font-medium">Report exhibit not yet compiled. Initiating setup analysis.</p>
                  </div>
                )}
              </div>
            </div>

            {/* Sources / References Section */}
            <div className="bg-white rounded-2xl border border-[#E4E7EC] shadow-xs p-6 w-full">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-[#E4E7EC] pb-3 mb-4">
                <div className="flex items-center gap-2.5">
                  <ExternalLink className="w-4 h-4 text-[#5B4CE0]" />
                  <h3 className="text-xs font-bold text-[#1A1D23] uppercase tracking-wider">
                    Sources / References
                  </h3>
                </div>
                <span className="text-[10px] text-[#98A2B3] font-medium">
                  Genuinely retrieved web research sources for this venture run
                </span>
              </div>

              {sources && sources.length > 0 ? (
                <ol className="list-decimal pl-5 space-y-2.5 text-xs text-[#4B5565] font-medium">
                  {sources.map((src, index) => (
                    <li key={index} className="leading-relaxed">
                      <a
                        href={src.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[#5B4CE0] hover:text-[#4338CA] font-semibold hover:underline inline-flex items-center gap-1.5 break-all"
                      >
                        {src.title || src.url}
                        <ExternalLink className="w-3 h-3 flex-shrink-0 opacity-70" />
                      </a>
                      {src.title && src.title !== src.url && (
                        <span className="text-[11px] text-[#98A2B3] ml-2 block sm:inline font-normal break-all">
                          ({src.url})
                        </span>
                      )}
                    </li>
                  ))}
                </ol>
              ) : (
                <p className="text-xs text-[#98A2B3] italic">
                  No external sources retrieved for this run.
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

