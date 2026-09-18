import React, { useState } from 'react';
import { 
  Sliders, TrendingUp, DollarSign, ShieldAlert, Sparkles, 
  FileSpreadsheet, ArrowUpRight, Zap, RefreshCw, BarChart2,
  GitCompareArrows, Layers, Users, Fuel, PieChart, TrendingDown, Activity
} from 'lucide-react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Legend,
  BarChart, Bar, ReferenceLine, Cell,
  ComposedChart, Line, PieChart as RechartsPieChart, Pie,
  LineChart
} from 'recharts';
import { useSimulator } from '../hooks/useSimulator';
import { useCountUp } from '../hooks/useCountUp';
import { api } from '../lib/api';

/* ─── Shared tooltip style ─── */
const tooltipStyle = { backgroundColor: '#111827', borderColor: '#374151', borderRadius: '0.75rem', fontSize: '12px' };

/* ─── Runway Fuel Gauge SVG ─── */
function RunwayFuelGauge({ runwayMonths, maxMonths = 36, size = 120 }) {
  const center = size / 2;
  const strokeW = size * 0.09;
  const r = (size - strokeW * 2) / 2 - 2;
  const pct = Math.min((runwayMonths || 0) / maxMonths, 1);
  const sweepAngle = 180;
  const startAngle = -180;

  const polarToCart = (cx, cy, rad, deg) => {
    const a = ((deg - 90) * Math.PI) / 180;
    return { x: cx + rad * Math.cos(a), y: cy + rad * Math.sin(a) };
  };
  const arc = (cx, cy, rad, sA, eA) => {
    const s = polarToCart(cx, cy, rad, eA);
    const e = polarToCart(cx, cy, rad, sA);
    const large = eA - sA <= 180 ? 0 : 1;
    return `M ${s.x} ${s.y} A ${rad} ${rad} 0 ${large} 0 ${e.x} ${e.y}`;
  };
  const bgPath = arc(center, center + 10, r, startAngle, startAngle + sweepAngle);
  const fillEnd = startAngle + pct * sweepAngle;
  const fillPath = arc(center, center + 10, r, startAngle, Math.max(fillEnd, startAngle + 0.1));

  const color = pct > 0.5 ? '#10B981' : pct > 0.25 ? '#F59E0B' : '#F43F5E';

  return (
    <div className="relative flex flex-col items-center" style={{ width: size, height: size * 0.7 }}>
      <svg width={size} height={size * 0.7} viewBox={`0 0 ${size} ${size * 0.7 + 10}`}>
        <defs>
          <filter id="fuelGlow"><feGaussianBlur stdDeviation="3" /><feMerge><feMergeNode /><feMergeNode in="SourceGraphic" /></feMerge></filter>
        </defs>
        <path d={bgPath} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={strokeW} strokeLinecap="round" />
        <path d={fillPath} fill="none" stroke={color} strokeWidth={strokeW} strokeLinecap="round" filter="url(#fuelGlow)" />
      </svg>
      <div className="absolute bottom-0 text-center">
        <div className="text-lg font-black font-mono" style={{ color }}>{typeof runwayMonths === 'number' ? runwayMonths : '∞'}</div>
        <div className="text-[9px] font-mono text-slate-500 uppercase tracking-wider">Months Runway</div>
      </div>
    </div>
  );
}

/* ─── Unit Economics Mini Gauge ─── */
function MiniGauge({ value, max, label, target, color = '#6366F1', format = (v) => v }) {
  const animVal = useCountUp(value || 0, 1000, 1);
  const pct = Math.min((value || 0) / max, 1);
  const targetPct = target ? Math.min(target / max, 1) : null;
  const r = 32;
  const circum = 2 * Math.PI * r;
  const dashLen = pct * circum * 0.75;
  const targetDash = targetPct ? targetPct * circum * 0.75 : null;

  return (
    <div className="flex flex-col items-center p-3 bg-slate-900/60 rounded-xl border border-white/5 spring-hover">
      <div className="relative" style={{ width: 80, height: 56 }}>
        <svg width={80} height={56} viewBox="0 0 80 56">
          <circle cx={40} cy={40} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={5}
            strokeDasharray={`${circum * 0.75} ${circum}`} strokeLinecap="round"
            transform="rotate(135 40 40)" />
          {targetDash && (
            <circle cx={40} cy={40} r={r} fill="none" stroke="rgba(255,255,255,0.12)" strokeWidth={1.5}
              strokeDasharray={`${targetDash} ${circum}`} strokeLinecap="round"
              transform="rotate(135 40 40)" />
          )}
          <circle cx={40} cy={40} r={r} fill="none" stroke={color} strokeWidth={5}
            strokeDasharray={`${dashLen} ${circum}`} strokeLinecap="round"
            transform="rotate(135 40 40)" style={{ filter: `drop-shadow(0 0 4px ${color}40)` }} />
        </svg>
        <div className="absolute inset-0 flex items-end justify-center pb-0.5">
          <span className="text-sm font-black font-mono text-white">{format(animVal)}</span>
        </div>
      </div>
      <span className="text-[9px] font-mono text-slate-400 uppercase tracking-wider mt-0.5 text-center leading-tight">{label}</span>
    </div>
  );
}


export function VentureSimulator({ project, initialPricing = {} }) {
  const {
    params,
    updateParam,
    simulation,
    scenarios,
    activeScenario,
    setActiveScenario,
    aiCommentary,
    requestAiAnalysis,
    loading
  } = useSimulator({
    starter_price: initialPricing.starter || 299,
    growth_price: initialPricing.growth || 799,
    enterprise_price: initialPricing.enterprise || 1999,
    initial_capital: project.budget || 100000,
  });

  const [compareMode, setCompareMode] = useState(false);

  const summary = simulation?.summary || {};
  const monthlyData = simulation?.monthly_projections || [];

  /* ─── Derived Data ─── */

  // Comparison overlay
  const comparisonData = React.useMemo(() => {
    if (!compareMode || !scenarios) return monthlyData;
    const baseD = scenarios.base_case?.monthly_projections || monthlyData;
    const bullD = scenarios.bull_case?.monthly_projections || [];
    const bearD = scenarios.bear_case?.monthly_projections || [];
    return baseD.map((row, i) => ({
      month: row.month,
      mrr_base: row.mrr, mrr_bull: bullD[i]?.mrr || row.mrr * 1.3, mrr_bear: bearD[i]?.mrr || row.mrr * 0.7,
      cash_base: row.cash_balance, cash_bull: bullD[i]?.cash_balance || row.cash_balance * 1.2, cash_bear: bearD[i]?.cash_balance || row.cash_balance * 0.8,
    }));
  }, [compareMode, scenarios, monthlyData]);

  // Net profit waterfall data
  const waterfallData = React.useMemo(() =>
    monthlyData.map(d => ({ month: d.month, net_profit: d.net_profit, fill: d.net_profit >= 0 ? '#10B981' : '#F43F5E' })),
    [monthlyData]
  );

  // Burn vs gross profit
  const burnVsProfitData = React.useMemo(() =>
    monthlyData.map(d => ({ month: d.month, gross_profit: d.gross_profit, total_opex: d.total_opex })),
    [monthlyData]
  );

  // Margin % evolution
  const marginData = React.useMemo(() =>
    monthlyData.map(d => ({ month: d.month, margin_pct: d.mrr > 0 ? Number(((d.gross_profit / d.mrr) * 100).toFixed(1)) : 0 })),
    [monthlyData]
  );

  // Revenue mix donut
  const revenueMixData = React.useMemo(() => {
    const s = params.starter_price * (params.starter_share_pct / 100);
    const g = params.growth_price * (params.growth_share_pct / 100);
    const e = params.enterprise_price * (params.enterprise_share_pct / 100);
    return [
      { name: 'Starter', value: Math.round(s), fill: '#3B82F6' },
      { name: 'Growth', value: Math.round(g), fill: '#6366F1' },
      { name: 'Enterprise', value: Math.round(e), fill: '#8B5CF6' },
    ];
  }, [params]);

  // Animated KPIs
  const animMrr = useCountUp(summary.month_12_mrr || 0, 1000, 0);
  const animLtv = useCountUp(summary.ltv_cac_ratio || 0, 1000, 1);

  // Scenario KPIs
  const scenarioKPIs = React.useMemo(() => {
    if (!scenarios) return null;
    return { base: scenarios.base_case?.summary || summary, bull: scenarios.bull_case?.summary || {}, bear: scenarios.bear_case?.summary || {} };
  }, [scenarios, summary]);

  // P&L heatmap — sample quarterly
  const heatmapQuarters = React.useMemo(() => {
    const quarters = [3, 6, 9, 12, 18, 24, 30, 36];
    return quarters.map(q => {
      const d = monthlyData.find(m => m.month === q) || {};
      return { label: `M${q}`, ...d };
    });
  }, [monthlyData]);

  const handleExcelExport = () => {
    const url = api.getExcelModelUrl(project.name || 'Venture', params);
    window.open(url, '_blank');
  };

  const heatCellColor = (val) => {
    if (val === undefined || val === null) return '';
    if (typeof val !== 'number') return '';
    return val > 0 ? 'text-emerald-400' : val < 0 ? 'text-rose-400' : 'text-slate-400';
  };

  return (
    <div className="space-y-6">
      {/* ═══ HEADER & SCENARIO SWITCHER ═══ */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-panel p-5 rounded-2xl border border-white/10">
        <div>
          <div className="flex items-center gap-2">
            <Sliders className="w-5 h-5 text-primary-400" />
            <h2 className="text-lg font-bold text-white">Interactive Financial & Venture Sensitivity Simulator</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">Adjust growth, pricing, and cost levers to observe 36-month projections in real time.</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setCompareMode(!compareMode)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold btn-press transition-all border ${compareMode ? 'bg-gradient-to-r from-primary-600/30 to-indigo-600/30 text-primary-300 border-primary-500/50 shadow-md shadow-primary-600/20' : 'bg-slate-900/80 text-slate-400 border-white/10 hover:text-slate-200'}`}>
            <GitCompareArrows className="w-4 h-4" /><span>{compareMode ? 'Comparing All' : 'Compare All'}</span>
          </button>
          <div className="flex bg-slate-900/80 p-1 rounded-xl border border-white/10 text-xs">
            {['base_case', 'bull_case', 'bear_case'].map((sc) => (
              <button key={sc} onClick={() => { setActiveScenario(sc); setCompareMode(false); }}
                className={`px-3 py-1.5 rounded-lg capitalize btn-press transition-all font-medium ${!compareMode && activeScenario === sc ? 'bg-primary-600 text-white shadow-md shadow-primary-600/30 scale-[1.02]' : 'text-slate-400 hover:text-slate-200'}`}>
                {sc.replace('_', ' ')}
              </button>
            ))}
          </div>
          <button onClick={handleExcelExport}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 border border-emerald-500/30 rounded-xl text-xs font-semibold btn-press transition-all">
            <FileSpreadsheet className="w-4 h-4" /><span>Export .XLSX</span>
          </button>
        </div>
      </div>

      {/* ═══ ROW 1: KPI Cards + Runway Fuel Gauge ═══ */}
      <div className="grid grid-cols-12 gap-3">
        <div className="col-span-12 lg:col-span-10 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="glass-panel p-4 rounded-xl border border-white/10 spring-hover">
            <span className="text-[10px] uppercase font-semibold text-slate-400 block mb-1">Month 12 MRR</span>
            <span className="text-lg font-bold text-emerald-400">${animMrr.toLocaleString()}</span>
            <span className="text-[10px] text-slate-500 block mt-0.5">ARR: ${((summary.month_12_mrr || 0) * 12).toLocaleString()}</span>
          </div>
          <div className="glass-panel p-4 rounded-xl border border-white/10 spring-hover">
            <span className="text-[10px] uppercase font-semibold text-slate-400 block mb-1">Break-Even</span>
            <span className="text-lg font-bold text-white">Month {summary.break_even_month || 'N/A'}</span>
            <span className="text-[10px] text-slate-500 block mt-0.5">Self-sustaining</span>
          </div>
          <div className="glass-panel p-4 rounded-xl border border-white/10 spring-hover">
            <span className="text-[10px] uppercase font-semibold text-slate-400 block mb-1">Cash Runway</span>
            <span className="text-lg font-bold text-indigo-400">{summary.runway_months} {typeof summary.runway_months === 'number' ? 'Mos' : ''}</span>
            <span className="text-[10px] text-slate-500 block mt-0.5">From initial capital</span>
          </div>
          <div className="glass-panel p-4 rounded-xl border border-white/10 spring-hover">
            <span className="text-[10px] uppercase font-semibold text-slate-400 block mb-1">LTV / CAC Ratio</span>
            <span className="text-lg font-bold text-amber-400">{animLtv}x</span>
            <span className="text-[10px] text-slate-500 block mt-0.5">Target: {'>'} 4.0x</span>
          </div>
          <div className="glass-panel p-4 rounded-xl border border-white/10 spring-hover">
            <span className="text-[10px] uppercase font-semibold text-slate-400 block mb-1">CAC Payback</span>
            <span className="text-lg font-bold text-white">{summary.cac_payback_months || 0} Mos</span>
            <span className="text-[10px] text-slate-500 block mt-0.5">Target: {'<'} 12 mos</span>
          </div>
          <div className="glass-panel p-4 rounded-xl border border-white/10 spring-hover">
            <span className="text-[10px] uppercase font-semibold text-slate-400 block mb-1">Health Index</span>
            <span className={`text-xs font-bold px-2 py-0.5 rounded-md inline-block mt-1 ${summary.health_status === 'GREEN' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : summary.health_status === 'YELLOW' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'}`}>
              {summary.health_status || 'HEALTHY'}
            </span>
          </div>
        </div>

        {/* Runway Fuel Gauge */}
        <div className="col-span-12 lg:col-span-2 glass-panel p-3 rounded-xl border border-white/10 flex items-center justify-center spring-hover">
          <RunwayFuelGauge runwayMonths={typeof summary.runway_months === 'number' ? summary.runway_months : 36} />
        </div>
      </div>

      {/* ═══ SCENARIO COMPARISON TABLE (when compare mode) ═══ */}
      {compareMode && scenarioKPIs && (
        <div className="glass-panel p-5 rounded-2xl border border-primary-500/30 space-y-3">
          <div className="text-[11px] font-mono font-bold text-primary-400 uppercase tracking-wider flex items-center gap-1.5">
            <GitCompareArrows className="w-3.5 h-3.5" /><span>Scenario Comparison — Side-by-Side KPIs</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead><tr className="border-b border-white/10">
                <th className="text-left py-2 px-3 text-slate-400 font-bold uppercase tracking-wider text-[10px]">KPI</th>
                <th className="text-center py-2 px-3 text-rose-400 font-bold uppercase tracking-wider text-[10px]">🐻 Bear</th>
                <th className="text-center py-2 px-3 text-primary-400 font-bold uppercase tracking-wider text-[10px]">📊 Base</th>
                <th className="text-center py-2 px-3 text-emerald-400 font-bold uppercase tracking-wider text-[10px]">🐂 Bull</th>
              </tr></thead>
              <tbody>
                {[
                  { label: 'Month 12 MRR', key: 'month_12_mrr', format: (v) => `$${(v || 0).toLocaleString()}` },
                  { label: 'Break-Even', key: 'break_even_month', format: (v) => `Month ${v || 'N/A'}` },
                  { label: 'Cash Runway', key: 'runway_months', format: (v) => `${v || 'N/A'} Mos` },
                  { label: 'LTV/CAC', key: 'ltv_cac_ratio', format: (v) => `${v || 0}x` },
                  { label: 'CAC Payback', key: 'cac_payback_months', format: (v) => `${v || 0} Mos` },
                  { label: 'Health', key: 'health_status', format: (v) => v || 'N/A' },
                ].map((row, idx) => (
                  <tr key={idx} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                    <td className="py-2 px-3 text-slate-300 font-semibold">{row.label}</td>
                    <td className="py-2 px-3 text-center font-mono font-bold text-rose-300">{row.format(scenarioKPIs.bear[row.key])}</td>
                    <td className="py-2 px-3 text-center font-mono font-bold text-white bg-white/5">{row.format(scenarioKPIs.base[row.key])}</td>
                    <td className="py-2 px-3 text-center font-mono font-bold text-emerald-300">{row.format(scenarioKPIs.bull[row.key])}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ═══ ROW 2: SLIDERS + PRIMARY CHART ═══ */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Sliders Panel */}
        <div className="lg:col-span-5 glass-panel p-5 rounded-2xl border border-white/10 space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2 border-b border-white/10 pb-2">
            <Sliders className="w-4 h-4 text-primary-400" /><span>Interactive Levers & Parameters</span>
          </h3>
          <div className="space-y-3 text-xs">
            {[
              { label: 'Starter Price', key: 'starter_price', min: 19, max: 999, step: 10, prefix: '$', suffix: '/mo', color: 'text-white' },
              { label: 'Growth Price', key: 'growth_price', min: 99, max: 2499, step: 50, prefix: '$', suffix: '/mo', color: 'text-white' },
              { label: 'Enterprise Floor', key: 'enterprise_price', min: 499, max: 9999, step: 100, prefix: '$', suffix: '/mo', color: 'text-white' },
              { label: 'Monthly Growth (%)', key: 'monthly_growth_rate_pct', min: 2, max: 40, step: 1, suffix: '%', color: 'text-emerald-400', accent: 'accent-emerald-500' },
              { label: 'Monthly Churn (%)', key: 'monthly_churn_rate_pct', min: 0.5, max: 15, step: 0.5, suffix: '%', color: 'text-rose-400', accent: 'accent-rose-500' },
              { label: 'CAC', key: 'cac', min: 20, max: 1000, step: 10, prefix: '$', color: 'text-amber-400', accent: 'accent-amber-500' },
              { label: 'Team Headcount', key: 'headcount', min: 1, max: 25, step: 1, suffix: ' members', color: 'text-white' },
            ].map((s) => (
              <div key={s.key}>
                <div className="flex justify-between text-slate-300 mb-1">
                  <span>{s.label}:</span>
                  <span className={`font-bold ${s.color}`}>{s.prefix || ''}{params[s.key]}{s.suffix || ''}</span>
                </div>
                <input type="range" min={s.min} max={s.max} step={s.step} value={params[s.key]}
                  onChange={(e) => updateParam(s.key, e.target.value)}
                  className={`w-full cursor-pointer ${s.accent || 'accent-primary-500'}`} />
              </div>
            ))}
          </div>
        </div>

        {/* Primary MRR + Cash Chart */}
        <div className="lg:col-span-7 glass-panel p-5 rounded-2xl border border-white/10 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2 border-b border-white/10 pb-2 mb-4">
              <BarChart2 className="w-4 h-4 text-emerald-400" />
              <span>{compareMode ? '36-Month Scenario Comparison Overlay' : '36-Month Revenue & Cash Trajectory'}</span>
              {compareMode && <span className="text-[10px] font-mono text-primary-400 bg-primary-500/10 px-2 py-0.5 rounded-full border border-primary-500/30">3 Scenarios</span>}
            </h3>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                {compareMode ? (
                  <AreaChart data={comparisonData}>
                    <defs>
                      <linearGradient id="colorMrrBase" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#10B981" stopOpacity={0.3}/><stop offset="95%" stopColor="#10B981" stopOpacity={0}/></linearGradient>
                      <linearGradient id="colorMrrBull" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#34D399" stopOpacity={0.15}/><stop offset="95%" stopColor="#34D399" stopOpacity={0}/></linearGradient>
                      <linearGradient id="colorMrrBear" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#F43F5E" stopOpacity={0.15}/><stop offset="95%" stopColor="#F43F5E" stopOpacity={0}/></linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
                    <XAxis dataKey="month" stroke="#94A3B8" fontSize={10} tickFormatter={(m) => `M${m}`} />
                    <YAxis stroke="#94A3B8" fontSize={10} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                    <Tooltip contentStyle={tooltipStyle} formatter={(v) => [`$${Number(v).toLocaleString()}`, '']} />
                    <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                    <Area type="monotone" dataKey="mrr_bull" name="🐂 Bull MRR" stroke="#34D399" strokeWidth={1.5} strokeDasharray="6 3" fillOpacity={1} fill="url(#colorMrrBull)" />
                    <Area type="monotone" dataKey="mrr_base" name="📊 Base MRR" stroke="#10B981" strokeWidth={2.5} fillOpacity={1} fill="url(#colorMrrBase)" />
                    <Area type="monotone" dataKey="mrr_bear" name="🐻 Bear MRR" stroke="#F43F5E" strokeWidth={1.5} strokeDasharray="6 3" fillOpacity={1} fill="url(#colorMrrBear)" />
                  </AreaChart>
                ) : (
                  <AreaChart data={monthlyData}>
                    <defs>
                      <linearGradient id="colorMrr" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#10B981" stopOpacity={0.4}/><stop offset="95%" stopColor="#10B981" stopOpacity={0}/></linearGradient>
                      <linearGradient id="colorCash" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#6366F1" stopOpacity={0.4}/><stop offset="95%" stopColor="#6366F1" stopOpacity={0}/></linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
                    <XAxis dataKey="month" stroke="#94A3B8" fontSize={10} tickFormatter={(m) => `M${m}`} />
                    <YAxis stroke="#94A3B8" fontSize={10} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                    <Tooltip contentStyle={tooltipStyle} formatter={(v) => [`$${Number(v).toLocaleString()}`, '']} />
                    <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                    <Area type="monotone" dataKey="mrr" name="MRR ($)" stroke="#10B981" strokeWidth={2} fillOpacity={1} fill="url(#colorMrr)" />
                    <Area type="monotone" dataKey="cash_balance" name="Cash Balance ($)" stroke="#6366F1" strokeWidth={2} fillOpacity={1} fill="url(#colorCash)" />
                    <Area type="monotone" dataKey="total_opex" name="Monthly OpEx ($)" stroke="#F43F5E" strokeWidth={1.5} fillOpacity={0} />
                  </AreaChart>
                )}
              </ResponsiveContainer>
            </div>
          </div>

          {/* AI Commentary */}
          <div className="mt-4 pt-3 border-t border-white/10">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-primary-400" /><span>AI CFO Sensitivity Commentary</span>
              </span>
              <button onClick={() => requestAiAnalysis(project.id)} disabled={loading}
                className="text-[11px] text-primary-400 hover:text-primary-300 flex items-center gap-1 font-medium disabled:opacity-50">
                <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
                <span>{loading ? 'Evaluating...' : 'Refresh AI Analysis'}</span>
              </button>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed bg-slate-900/60 p-3 rounded-xl border border-white/5">
              {aiCommentary || `With a $${params.starter_price} starter tier, $${params.cac} CAC, and ${params.monthly_growth_rate_pct}% monthly growth, your break-even occurs at Month ${summary.break_even_month || 'N/A'}. LTV/CAC ratio of ${summary.ltv_cac_ratio}x indicates strong customer lifetime ROI.`}
            </p>
          </div>
        </div>
      </div>

      {/* ═══ ROW 3: NET PROFIT WATERFALL + BURN vs GROSS PROFIT ═══ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Net Profit Waterfall */}
        <div className="glass-panel p-5 rounded-2xl border border-white/10 space-y-3">
          <h3 className="text-sm font-bold text-white flex items-center gap-2 border-b border-white/10 pb-2">
            <TrendingUp className="w-4 h-4 text-emerald-400" />
            <span>Net Profit / Loss Waterfall</span>
            <span className="text-[10px] font-mono text-slate-500 ml-auto">Green = Profitable · Red = Burn</span>
          </h3>
          <div className="h-52 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={waterfallData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
                <XAxis dataKey="month" stroke="#94A3B8" fontSize={9} tickFormatter={(m) => `M${m}`} interval={2} />
                <YAxis stroke="#94A3B8" fontSize={9} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                <Tooltip contentStyle={tooltipStyle} formatter={(v) => [`$${Number(v).toLocaleString()}`, 'Net Profit']} />
                <ReferenceLine y={0} stroke="#475569" strokeWidth={1.5} strokeDasharray="4 2" label={{ value: 'Break-Even', position: 'insideTopRight', fill: '#94A3B8', fontSize: 9 }} />
                <Bar dataKey="net_profit" name="Net Profit ($)" radius={[2, 2, 0, 0]}>
                  {waterfallData.map((entry, idx) => (
                    <Cell key={idx} fill={entry.fill} fillOpacity={0.8} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Burn Rate vs Gross Profit */}
        <div className="glass-panel p-5 rounded-2xl border border-white/10 space-y-3">
          <h3 className="text-sm font-bold text-white flex items-center gap-2 border-b border-white/10 pb-2">
            <Activity className="w-4 h-4 text-amber-400" />
            <span>Monthly Burn vs. Gross Profit</span>
            <span className="text-[10px] font-mono text-slate-500 ml-auto">Crossover = Operational Profitability</span>
          </h3>
          <div className="h-52 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={burnVsProfitData}>
                <defs>
                  <linearGradient id="colorOpexBar" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#F43F5E" stopOpacity={0.6} />
                    <stop offset="100%" stopColor="#F43F5E" stopOpacity={0.2} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
                <XAxis dataKey="month" stroke="#94A3B8" fontSize={9} tickFormatter={(m) => `M${m}`} interval={2} />
                <YAxis stroke="#94A3B8" fontSize={9} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                <Tooltip contentStyle={tooltipStyle} formatter={(v) => [`$${Number(v).toLocaleString()}`, '']} />
                <Legend wrapperStyle={{ fontSize: '10px', paddingTop: '6px' }} />
                <Bar dataKey="total_opex" name="Monthly OpEx (Burn)" fill="url(#colorOpexBar)" radius={[2, 2, 0, 0]} />
                <Line type="monotone" dataKey="gross_profit" name="Gross Profit" stroke="#10B981" strokeWidth={2.5} dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* ═══ ROW 4: CUSTOMER GROWTH + REVENUE DONUT + UNIT ECON GAUGES + MARGIN ═══ */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Customer Growth Curve */}
        <div className="glass-panel p-4 rounded-2xl border border-white/10 space-y-2">
          <h3 className="text-xs font-bold text-white flex items-center gap-1.5">
            <Users className="w-3.5 h-3.5 text-indigo-400" /><span>Customer Growth Curve</span>
          </h3>
          <div className="h-36 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={monthlyData}>
                <defs>
                  <linearGradient id="colorCust" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366F1" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#6366F1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
                <XAxis dataKey="month" stroke="#94A3B8" fontSize={8} tickFormatter={(m) => `M${m}`} interval={5} />
                <YAxis stroke="#94A3B8" fontSize={8} />
                <Tooltip contentStyle={tooltipStyle} formatter={(v) => [v.toLocaleString(), 'Customers']} />
                <Area type="monotone" dataKey="active_customers" stroke="#6366F1" strokeWidth={2} fillOpacity={1} fill="url(#colorCust)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="text-[10px] text-slate-400 font-mono text-center">
            M36: <span className="text-indigo-300 font-bold">{monthlyData[monthlyData.length - 1]?.active_customers?.toLocaleString() || '—'}</span> active subscribers
          </div>
        </div>

        {/* Revenue Mix Donut */}
        <div className="glass-panel p-4 rounded-2xl border border-white/10 space-y-2">
          <h3 className="text-xs font-bold text-white flex items-center gap-1.5">
            <PieChart className="w-3.5 h-3.5 text-purple-400" /><span>Revenue Mix by Tier</span>
          </h3>
          <div className="h-36 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <RechartsPieChart>
                <Pie data={revenueMixData} cx="50%" cy="50%" innerRadius={30} outerRadius={55}
                  paddingAngle={3} dataKey="value" stroke="none">
                  {revenueMixData.map((entry, idx) => (
                    <Cell key={idx} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} formatter={(v, name) => [`$${v} weighted ARPU`, name]} />
                <Legend wrapperStyle={{ fontSize: '9px' }} />
              </RechartsPieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex items-center justify-center gap-3 text-[9px] text-slate-400">
            {revenueMixData.map((t) => (
              <span key={t.name} className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: t.fill }} />
                <span>{t.name}</span>
              </span>
            ))}
          </div>
        </div>

        {/* Unit Economics Gauges */}
        <div className="glass-panel p-4 rounded-2xl border border-white/10 space-y-2">
          <h3 className="text-xs font-bold text-white flex items-center gap-1.5">
            <DollarSign className="w-3.5 h-3.5 text-gold-400" /><span>Unit Economics</span>
          </h3>
          <div className="grid grid-cols-2 gap-2">
            <MiniGauge value={summary.arpu || 0} max={2000} label="ARPU" color="#6366F1" format={(v) => `$${Math.round(v)}`} />
            <MiniGauge value={summary.ltv || 0} max={50000} label="LTV" color="#10B981" format={(v) => `$${Math.round(v / 1000)}k`} />
            <MiniGauge value={summary.ltv_cac_ratio || 0} max={10} label="LTV:CAC" target={4} color="#D4AF37" format={(v) => `${v}x`} />
            <MiniGauge value={summary.cac_payback_months || 0} max={24} label="Payback" target={12} color="#F59E0B" format={(v) => `${Math.round(v)}mo`} />
          </div>
        </div>

        {/* Gross Margin % Evolution */}
        <div className="glass-panel p-4 rounded-2xl border border-white/10 space-y-2">
          <h3 className="text-xs font-bold text-white flex items-center gap-1.5">
            <TrendingDown className="w-3.5 h-3.5 text-cyan-400" /><span>Gross Margin % Trend</span>
          </h3>
          <div className="h-36 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={marginData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
                <XAxis dataKey="month" stroke="#94A3B8" fontSize={8} tickFormatter={(m) => `M${m}`} interval={5} />
                <YAxis stroke="#94A3B8" fontSize={8} domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
                <Tooltip contentStyle={tooltipStyle} formatter={(v) => [`${v}%`, 'Gross Margin']} />
                <ReferenceLine y={params.gross_margin_pct || 80} stroke="#475569" strokeDasharray="4 2"
                  label={{ value: `${params.gross_margin_pct || 80}% Target`, position: 'insideTopRight', fill: '#94A3B8', fontSize: 8 }} />
                <Line type="monotone" dataKey="margin_pct" stroke="#06B6D4" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="text-[10px] text-slate-400 font-mono text-center">
            Target: <span className="text-cyan-300 font-bold">{params.gross_margin_pct || 80}%</span> · Current: <span className="text-white font-bold">{marginData[marginData.length - 1]?.margin_pct || '—'}%</span>
          </div>
        </div>
      </div>

      {/* ═══ ROW 5: P&L HEATMAP TABLE ═══ */}
      <div className="glass-panel p-5 rounded-2xl border border-white/10 space-y-3">
        <h3 className="text-sm font-bold text-white flex items-center gap-2 border-b border-white/10 pb-2">
          <Layers className="w-4 h-4 text-gold-400" />
          <span>P&L Heatmap — Quarterly Milestones</span>
          <span className="text-[10px] font-mono text-slate-500 ml-auto">{heatmapQuarters.length} Checkpoints</span>
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-white/10">
                <th className="text-left py-2 px-2 text-slate-400 font-bold uppercase tracking-wider text-[10px] sticky left-0 bg-[#0f172a]">Metric</th>
                {heatmapQuarters.map((q) => (
                  <th key={q.label} className="text-center py-2 px-2 text-slate-400 font-bold uppercase tracking-wider text-[10px] min-w-[72px]">{q.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[
                { label: 'Customers', key: 'active_customers', format: (v) => v?.toLocaleString() || '—' },
                { label: 'MRR', key: 'mrr', format: (v) => v ? `$${(v / 1000).toFixed(1)}k` : '—' },
                { label: 'ARR', key: 'arr', format: (v) => v ? `$${(v / 1000).toFixed(0)}k` : '—' },
                { label: 'Gross Profit', key: 'gross_profit', format: (v) => v ? `$${(v / 1000).toFixed(1)}k` : '—' },
                { label: 'OpEx', key: 'total_opex', format: (v) => v ? `$${(v / 1000).toFixed(1)}k` : '—' },
                { label: 'Net Profit', key: 'net_profit', format: (v) => v ? `$${(v / 1000).toFixed(1)}k` : '—' },
                { label: 'Cash Balance', key: 'cash_balance', format: (v) => v ? `$${(v / 1000).toFixed(0)}k` : '—' },
              ].map((row, rIdx) => (
                <tr key={rIdx} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                  <td className="py-1.5 px-2 text-slate-300 font-semibold sticky left-0 bg-[#0f172a]">{row.label}</td>
                  {heatmapQuarters.map((q) => {
                    const val = q[row.key];
                    return (
                      <td key={q.label} className={`py-1.5 px-2 text-center font-mono font-bold ${row.key === 'net_profit' || row.key === 'cash_balance' ? heatCellColor(val) : 'text-slate-200'}`}>
                        {row.format(val)}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
