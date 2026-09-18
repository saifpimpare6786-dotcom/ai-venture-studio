import React, { useState } from 'react';
import { AlertTriangle, ShieldAlert, CheckCircle2, ChevronRight, X, Info, Filter } from 'lucide-react';
import { useCountUp } from '../hooks/useCountUp';

/**
 * RadialGauge — Animated SVG circular arc gauge.
 * Consulting-grade hero metric visualization (McKinsey / BCG style).
 * 
 * @param {number} score - Value 0-100
 * @param {number} size - SVG diameter in px (default 200)
 * @param {string} label - Label text below score
 * @param {string} grade - Grade text (e.g., "AAA — INVESTMENT GRADE")
 */
export function RadialGauge({ score = 0, size = 200, label, grade }) {
  const animatedScore = useCountUp(score, 1400, 1);
  
  const center = size / 2;
  const strokeWidth = size * 0.07;
  const radius = (size - strokeWidth * 2) / 2 - 4;
  const circumference = 2 * Math.PI * radius;
  
  // Start from the top (rotate -90deg equivalent via SVG arc)
  const startAngle = -225; // Start at bottom-left
  const sweepAngle = 270;  // Sweep 270 degrees (3/4 circle for gauge look)
  const arcLength = (sweepAngle / 360) * circumference;
  const filledLength = (animatedScore / 100) * arcLength;
  const dashOffset = arcLength - filledLength;

  // Color interpolation based on score
  const getScoreColor = (s) => {
    if (s >= 80) return { stroke: 'url(#gaugeGradientGold)', glow: 'rgba(212, 175, 55, 0.4)' };
    if (s >= 65) return { stroke: 'url(#gaugeGradientIndigo)', glow: 'rgba(99, 102, 241, 0.4)' };
    return { stroke: 'url(#gaugeGradientAmber)', glow: 'rgba(245, 158, 11, 0.4)' };
  };

  const colors = getScoreColor(score);

  // Convert polar to cartesian for arc path
  const polarToCartesian = (cx, cy, r, angleDeg) => {
    const angleRad = ((angleDeg - 90) * Math.PI) / 180;
    return {
      x: cx + r * Math.cos(angleRad),
      y: cy + r * Math.sin(angleRad),
    };
  };

  const describeArc = (cx, cy, r, startAng, endAng) => {
    const start = polarToCartesian(cx, cy, r, endAng);
    const end = polarToCartesian(cx, cy, r, startAng);
    const largeArcFlag = endAng - startAng <= 180 ? 0 : 1;
    return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArcFlag} 0 ${end.x} ${end.y}`;
  };

  const bgArcPath = describeArc(center, center, radius, startAngle, startAngle + sweepAngle);
  const endAngle = startAngle + (animatedScore / 100) * sweepAngle;
  const fillArcPath = describeArc(center, center, radius, startAngle, Math.max(endAngle, startAngle + 0.1));

  return (
    <div className="relative inline-flex flex-col items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="drop-shadow-lg">
        <defs>
          <linearGradient id="gaugeGradientGold" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#D4AF37" />
            <stop offset="50%" stopColor="#F5D76E" />
            <stop offset="100%" stopColor="#D4AF37" />
          </linearGradient>
          <linearGradient id="gaugeGradientIndigo" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#6366F1" />
            <stop offset="100%" stopColor="#818CF8" />
          </linearGradient>
          <linearGradient id="gaugeGradientAmber" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#F59E0B" />
            <stop offset="100%" stopColor="#FBBF24" />
          </linearGradient>
          <filter id="gaugeGlow">
            <feGaussianBlur stdDeviation="4" result="glow" />
            <feMerge>
              <feMergeNode in="glow" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Background Track */}
        <path
          d={bgArcPath}
          fill="none"
          stroke="rgba(255, 255, 255, 0.08)"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />

        {/* Filled Arc */}
        <path
          d={fillArcPath}
          fill="none"
          stroke={colors.stroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          filter="url(#gaugeGlow)"
          style={{
            transition: 'stroke 0.5s ease',
          }}
        />

        {/* Tick marks */}
        {[0, 25, 50, 75, 100].map((tick) => {
          const tickAngle = startAngle + (tick / 100) * sweepAngle;
          const inner = polarToCartesian(center, center, radius - strokeWidth - 2, tickAngle);
          const outer = polarToCartesian(center, center, radius - strokeWidth - 8, tickAngle);
          return (
            <line
              key={tick}
              x1={inner.x}
              y1={inner.y}
              x2={outer.x}
              y2={outer.y}
              stroke="rgba(255, 255, 255, 0.2)"
              strokeWidth={1.5}
            />
          );
        })}
      </svg>

      {/* Center Number */}
      <div className="absolute inset-0 flex flex-col items-center justify-center" style={{ paddingBottom: size * 0.08 }}>
        <div className="flex items-baseline gap-1">
          <span
            className="font-black font-mono tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-white via-slate-100 to-gold-400"
            style={{ fontSize: size * 0.22 }}
          >
            {animatedScore}
          </span>
          <span
            className="font-semibold text-slate-500 font-mono"
            style={{ fontSize: size * 0.09 }}
          >
            /100
          </span>
        </div>
        {label && (
          <span
            className="text-slate-400 font-mono uppercase tracking-wider font-bold mt-0.5"
            style={{ fontSize: Math.max(size * 0.05, 9) }}
          >
            {label}
          </span>
        )}
        {grade && (
          <span
            className="text-gold-400 font-display font-bold mt-1 flex items-center gap-1"
            style={{ fontSize: Math.max(size * 0.055, 10) }}
          >
            {grade}
          </span>
        )}
      </div>
    </div>
  );
}

/**
 * MiniSparkline — Tiny inline trend chart for metric cards.
 * Renders a ~60px wide sparkline with no axes.
 */
export function MiniSparkline({ data = [], color = '#6366F1', width = 64, height = 24 }) {
  if (!data.length) return null;

  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;

  const points = data.map((val, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((val - min) / range) * (height - 4) - 2;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg width={width} height={height} className="opacity-60">
      <defs>
        <linearGradient id={`spark-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polyline
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
      {/* Fill area */}
      <polygon
        fill={`url(#spark-${color.replace('#', '')})`}
        points={`0,${height} ${points} ${width},${height}`}
      />
    </svg>
  );
}

/**
 * ConcentricRings — TAM/SAM/SOM nested circles SVG.
 * Classic VC pitch deck market sizing visual.
 */
export function ConcentricRings({ tam, sam, som, size = 220 }) {
  const center = size / 2;
  const rings = [
    { label: 'TAM', value: tam, radius: size * 0.42, color: 'rgba(99, 102, 241, 0.15)', stroke: 'rgba(99, 102, 241, 0.5)', textColor: '#818CF8' },
    { label: 'SAM', value: sam, radius: size * 0.30, color: 'rgba(6, 182, 212, 0.18)', stroke: 'rgba(6, 182, 212, 0.6)', textColor: '#22D3EE' },
    { label: 'SOM', value: som, radius: size * 0.17, color: 'rgba(16, 185, 129, 0.25)', stroke: 'rgba(16, 185, 129, 0.7)', textColor: '#34D399' },
  ];

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <defs>
          <filter id="ringGlow">
            <feGaussianBlur stdDeviation="3" result="glow" />
            <feMerge>
              <feMergeNode in="glow" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        {rings.map((ring, idx) => (
          <g key={ring.label}>
            <circle
              cx={center}
              cy={center}
              r={ring.radius}
              fill={ring.color}
              stroke={ring.stroke}
              strokeWidth={1.5}
              strokeDasharray="4 3"
              className="animate-[pulse-slow_4s_infinite]"
              style={{ animationDelay: `${idx * 300}ms` }}
            />
            <text
              x={center}
              y={center - ring.radius + 14}
              textAnchor="middle"
              fill={ring.textColor}
              fontSize={10}
              fontWeight="700"
              fontFamily="monospace"
              className="uppercase"
            >
              {ring.label}
            </text>
            <text
              x={center}
              y={center - ring.radius + 27}
              textAnchor="middle"
              fill="rgba(255,255,255,0.7)"
              fontSize={9}
              fontWeight="600"
              fontFamily="monospace"
            >
              {ring.value || 'N/A'}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}

/**
 * RiskHeatmapGrid — Institutional 2D Likelihood × Impact 3x3 Heatmap.
 * Formatted strictly according to institutional enterprise risk governance standards (ISO 31000).
 *
 * Risk Level Mapping:
 * [2, 2] High Likelihood × High Impact   -> CRITICAL (Rose/Red)
 * [2, 1] High Likelihood × Med Impact    -> HIGH (Orange)
 * [1, 2] Med Likelihood  × High Impact   -> HIGH (Orange)
 * [2, 0] High Likelihood × Low Impact    -> MODERATE (Amber)
 * [1, 1] Med Likelihood  × Med Impact    -> MODERATE (Amber)
 * [0, 2] Low Likelihood  × High Impact   -> MODERATE (Amber)
 * [1, 0] Med Likelihood  × Low Impact    -> LOW (Emerald)
 * [0, 1] Low Likelihood  × Med Impact    -> LOW (Emerald)
 * [0, 0] Low Likelihood  × Low Impact    -> LOW (Emerald)
 */
export function RiskHeatmapGrid({ risks = [] }) {
  const [selectedCell, setSelectedCell] = useState(null);

  function parseCoordinate(val, defaultVal = 1) {
    if (val === undefined || val === null) return defaultVal;
    if (typeof val === 'number') {
      if (val >= 3) return 2;
      if (val === 2) return 1;
      return 0;
    }
    const s = String(val).toLowerCase().trim();
    if (['severe', 'critical', 'high', 'catastrophic', 'tier 3', 'very high', '3', 'h'].some(w => s.includes(w))) return 2;
    if (['medium', 'moderate', 'med', 'mod', 'intermediate', 'tier 2', '2', 'm'].some(w => s.includes(w))) return 1;
    if (['low', 'minor', 'negligible', 'tier 1', 'very low', '1', 'l'].some(w => s.includes(w))) return 0;
    return defaultVal;
  }

  // Categorize risks into a clean 3x3 grid
  const riskMap = {
    '2-2': [], '2-1': [], '2-0': [],
    '1-2': [], '1-1': [], '1-0': [],
    '0-2': [], '0-1': [], '0-0': []
  };

  risks.forEach((risk) => {
    if (!risk) return;
    const r = typeof risk === 'object' ? risk : { risk: String(risk) };

    const rawLikelihood = r.likelihood ?? r.probability ?? r.prob ?? r.likelihood_rating;
    const rawImpact = r.impact ?? r.impact_severity ?? r.impact_level ?? r.severity ?? r.risk_rating ?? r.rating;

    let likelihood = 1;
    let impact = 1;

    if (rawLikelihood !== undefined && rawLikelihood !== null) {
      likelihood = parseCoordinate(rawLikelihood, 1);
    } else {
      const text = (r.risk || r.statutory_act || r.description || r.compliance_gap || '').toLowerCase();
      if (text.includes('critical') || text.includes('severe')) likelihood = 2;
      else if (text.includes('high')) likelihood = 1;
      else if (text.includes('low')) likelihood = 0;
    }

    if (rawImpact !== undefined && rawImpact !== null) {
      impact = parseCoordinate(rawImpact, 1);
    } else if (rawLikelihood !== undefined && rawLikelihood !== null) {
      impact = likelihood;
    } else {
      const text = (r.risk || r.statutory_act || r.description || r.compliance_gap || '').toLowerCase();
      if (text.includes('critical') || text.includes('severe')) impact = 2;
      else if (text.includes('high')) impact = 2;
      else if (text.includes('low')) impact = 0;
    }

    likelihood = Math.max(0, Math.min(2, likelihood));
    impact = Math.max(0, Math.min(2, impact));

    const key = `${likelihood}-${impact}`;
    if (riskMap[key]) {
      riskMap[key].push(r);
    }
  });

  const CELL_METADATA = {
    '2-2': {
      tier: 'CRITICAL',
      label: 'Critical Severity',
      scoreText: 'Severe Impact × High Likelihood',
      bgPopulated: 'bg-rose-500/20 border-rose-500/70 text-rose-300 shadow-lg shadow-rose-950/40 hover:bg-rose-500/30',
      bgEmpty: 'bg-rose-950/15 border-rose-500/25 text-rose-500/40 hover:border-rose-500/40 hover:bg-rose-950/25',
      badge: 'bg-rose-500/20 text-rose-300 border border-rose-500/40',
      accentDot: 'bg-rose-500 shadow-rose-500/80',
      numColor: 'text-rose-400',
      glowRing: 'ring-rose-500/50'
    },
    '2-1': {
      tier: 'HIGH',
      label: 'High Exposure',
      scoreText: 'Moderate Impact × High Likelihood',
      bgPopulated: 'bg-orange-500/20 border-orange-500/60 text-orange-300 shadow-md shadow-orange-950/30 hover:bg-orange-500/30',
      bgEmpty: 'bg-orange-950/15 border-orange-500/20 text-orange-500/40 hover:border-orange-500/35 hover:bg-orange-950/25',
      badge: 'bg-orange-500/20 text-orange-300 border border-orange-500/40',
      accentDot: 'bg-orange-500 shadow-orange-500/80',
      numColor: 'text-orange-400',
      glowRing: 'ring-orange-500/50'
    },
    '1-2': {
      tier: 'HIGH',
      label: 'High Exposure',
      scoreText: 'Severe Impact × Moderate Likelihood',
      bgPopulated: 'bg-orange-500/20 border-orange-500/60 text-orange-300 shadow-md shadow-orange-950/30 hover:bg-orange-500/30',
      bgEmpty: 'bg-orange-950/15 border-orange-500/20 text-orange-500/40 hover:border-orange-500/35 hover:bg-orange-950/25',
      badge: 'bg-orange-500/20 text-orange-300 border border-orange-500/40',
      accentDot: 'bg-orange-500 shadow-orange-500/80',
      numColor: 'text-orange-400',
      glowRing: 'ring-orange-500/50'
    },
    '2-0': {
      tier: 'MODERATE',
      label: 'Moderate Risk',
      scoreText: 'Low Impact × High Likelihood',
      bgPopulated: 'bg-amber-500/15 border-amber-500/50 text-amber-300 shadow-sm hover:bg-amber-500/25',
      bgEmpty: 'bg-amber-950/10 border-amber-500/20 text-amber-500/40 hover:border-amber-500/35 hover:bg-amber-950/20',
      badge: 'bg-amber-500/15 text-amber-300 border border-amber-500/30',
      accentDot: 'bg-amber-500 shadow-amber-500/80',
      numColor: 'text-amber-400',
      glowRing: 'ring-amber-500/50'
    },
    '1-1': {
      tier: 'MODERATE',
      label: 'Moderate Risk',
      scoreText: 'Moderate Impact × Moderate Likelihood',
      bgPopulated: 'bg-amber-500/15 border-amber-500/50 text-amber-300 shadow-sm hover:bg-amber-500/25',
      bgEmpty: 'bg-amber-950/10 border-amber-500/20 text-amber-500/40 hover:border-amber-500/35 hover:bg-amber-950/20',
      badge: 'bg-amber-500/15 text-amber-300 border border-amber-500/30',
      accentDot: 'bg-amber-500 shadow-amber-500/80',
      numColor: 'text-amber-400',
      glowRing: 'ring-amber-500/50'
    },
    '0-2': {
      tier: 'MODERATE',
      label: 'Moderate Risk',
      scoreText: 'Severe Impact × Low Likelihood',
      bgPopulated: 'bg-amber-500/15 border-amber-500/50 text-amber-300 shadow-sm hover:bg-amber-500/25',
      bgEmpty: 'bg-amber-950/10 border-amber-500/20 text-amber-500/40 hover:border-amber-500/35 hover:bg-amber-950/20',
      badge: 'bg-amber-500/15 text-amber-300 border border-amber-500/30',
      accentDot: 'bg-amber-500 shadow-amber-500/80',
      numColor: 'text-amber-400',
      glowRing: 'ring-amber-500/50'
    },
    '1-0': {
      tier: 'LOW',
      label: 'Low / Minor',
      scoreText: 'Low Impact × Moderate Likelihood',
      bgPopulated: 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300 shadow-sm hover:bg-emerald-500/25',
      bgEmpty: 'bg-emerald-950/10 border-emerald-500/20 text-emerald-500/40 hover:border-emerald-500/30 hover:bg-emerald-950/20',
      badge: 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30',
      accentDot: 'bg-emerald-500 shadow-emerald-500/80',
      numColor: 'text-emerald-400',
      glowRing: 'ring-emerald-500/50'
    },
    '0-1': {
      tier: 'LOW',
      label: 'Low / Minor',
      scoreText: 'Moderate Impact × Low Likelihood',
      bgPopulated: 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300 shadow-sm hover:bg-emerald-500/25',
      bgEmpty: 'bg-emerald-950/10 border-emerald-500/20 text-emerald-500/40 hover:border-emerald-500/30 hover:bg-emerald-950/20',
      badge: 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30',
      accentDot: 'bg-emerald-500 shadow-emerald-500/80',
      numColor: 'text-emerald-400',
      glowRing: 'ring-emerald-500/50'
    },
    '0-0': {
      tier: 'LOW',
      label: 'Low / Acceptable',
      scoreText: 'Low Impact × Low Likelihood',
      bgPopulated: 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300 shadow-sm hover:bg-emerald-500/25',
      bgEmpty: 'bg-emerald-950/10 border-emerald-500/20 text-emerald-500/40 hover:border-emerald-500/30 hover:bg-emerald-950/20',
      badge: 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30',
      accentDot: 'bg-emerald-500 shadow-emerald-500/80',
      numColor: 'text-emerald-400',
      glowRing: 'ring-emerald-500/50'
    }
  };

  const criticalCount = riskMap['2-2'].length;
  const highCount = riskMap['2-1'].length + riskMap['1-2'].length;
  const moderateCount = riskMap['2-0'].length + riskMap['1-1'].length + riskMap['0-2'].length;
  const lowCount = riskMap['1-0'].length + riskMap['0-1'].length + riskMap['0-0'].length;

  const activeRisks = selectedCell ? (riskMap[selectedCell] || []) : [];
  const selectedMeta = selectedCell ? CELL_METADATA[selectedCell] : null;

  return (
    <div className="bg-slate-950/70 p-5 rounded-2xl border border-white/10 space-y-4">
      {/* Top Header & Distribution Summary */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold text-white uppercase tracking-wider">
              Risk Exposure Heatmap
            </span>
            <span className="text-[10px] font-mono text-gold-400 bg-gold-500/10 px-2 py-0.5 rounded-full border border-gold-500/30 font-semibold">
              ISO 31000
            </span>
          </div>
          <p className="text-[11px] text-slate-400 mt-0.5">
            2D Severity Matrix: Likelihood (Y-Axis) × Impact (X-Axis)
          </p>
        </div>

        {/* Executive Tier Counts */}
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-rose-500/10 border border-rose-500/30 text-[10px] font-mono font-bold text-rose-300">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse" />
            <span>CRITICAL: {criticalCount}</span>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-orange-500/10 border border-orange-500/30 text-[10px] font-mono font-bold text-orange-300">
            <span className="w-1.5 h-1.5 rounded-full bg-orange-500" />
            <span>HIGH: {highCount}</span>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-amber-500/10 border border-amber-500/30 text-[10px] font-mono font-bold text-amber-300">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
            <span>MODERATE: {moderateCount}</span>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-[10px] font-mono font-bold text-emerald-300">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            <span>LOW: {lowCount}</span>
          </div>
        </div>
      </div>

      {/* The 3x3 Heatmap Grid */}
      <div className="flex gap-3 pt-1">
        {/* Y-axis labels & title */}
        <div className="flex flex-col justify-between items-end py-3 pr-1 text-[10px] font-mono text-slate-400 font-bold select-none">
          <span className="text-rose-400/90 flex items-center gap-1">
            <span className="w-1 h-1 rounded-full bg-rose-500" />
            HIGH
          </span>
          <span className="text-amber-400/90 flex items-center gap-1">
            <span className="w-1 h-1 rounded-full bg-amber-500" />
            MED
          </span>
          <span className="text-emerald-400/90 flex items-center gap-1">
            <span className="w-1 h-1 rounded-full bg-emerald-500" />
            LOW
          </span>
        </div>

        <div className="flex-1 space-y-2">
          {[2, 1, 0].map((likelihood) => (
            <div key={likelihood} className="grid grid-cols-3 gap-2">
              {[0, 1, 2].map((impact) => {
                const key = `${likelihood}-${impact}`;
                const cellRisks = riskMap[key] || [];
                const meta = CELL_METADATA[key];
                const count = cellRisks.length;
                const isSelected = selectedCell === key;

                return (
                  <button
                    key={impact}
                    onClick={() => setSelectedCell(isSelected ? null : key)}
                    className={`h-16 sm:h-20 rounded-xl border p-2 flex flex-col justify-between text-left transition-all relative group cursor-pointer ${
                      count > 0 ? meta.bgPopulated : meta.bgEmpty
                    } ${
                      isSelected ? `ring-2 ${meta.glowRing} scale-[1.02] shadow-xl` : 'hover:scale-[1.01]'
                    }`}
                    title={`${meta.tier} Risk: ${meta.scoreText} (${count} risks mapped)`}
                  >
                    {/* Top Row inside cell */}
                    <div className="flex items-center justify-between w-full">
                      <div className="flex items-center gap-1.5">
                        <span className={`w-1.5 h-1.5 rounded-full ${meta.accentDot} ${count > 0 ? 'opacity-100' : 'opacity-30'}`} />
                        <span className={`text-[9px] font-mono font-bold tracking-wider uppercase ${
                          count > 0 ? meta.numColor : 'text-slate-500/70'
                        }`}>
                          {meta.tier}
                        </span>
                      </div>
                      {isSelected && (
                        <span className="text-[9px] font-mono text-gold-400 bg-gold-500/20 px-1.5 py-0.2 rounded border border-gold-500/40">
                          ACTIVE
                        </span>
                      )}
                    </div>

                    {/* Center Numeric Value */}
                    <div className="flex items-baseline justify-between w-full mt-auto">
                      <span className={`text-xl sm:text-2xl font-black font-mono tracking-tight ${
                        count > 0 ? meta.numColor : 'text-slate-600 font-normal'
                      }`}>
                        {count}
                      </span>
                      <span className={`text-[10px] font-mono ${count > 0 ? 'text-slate-300 font-semibold' : 'text-slate-600 font-normal'}`}>
                        {count === 1 ? '1 risk' : `${count} risks`}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          ))}

          {/* X-axis labels */}
          <div className="grid grid-cols-3 gap-2 pt-1">
            {[
              { label: 'LOW', desc: 'Negligible Impact', color: 'text-emerald-400' },
              { label: 'MEDIUM', desc: 'Moderate Impact', color: 'text-amber-400' },
              { label: 'HIGH', desc: 'Catastrophic Impact', color: 'text-rose-400' }
            ].map((col) => (
              <div key={col.label} className="text-center space-y-0.5">
                <span className={`text-[10px] font-mono font-bold tracking-wider block ${col.color}`}>
                  {col.label}
                </span>
                <span className="text-[9px] font-mono text-slate-500 block hidden sm:block">
                  {col.desc}
                </span>
              </div>
            ))}
          </div>

          <div className="text-center text-[10px] font-mono text-slate-400 uppercase tracking-widest font-bold pt-1 flex items-center justify-center gap-1.5">
            <span>IMPACT SEVERITY</span>
            <ChevronRight className="w-3 h-3 text-slate-500" />
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 pt-1 border-t border-white/5">
        <span className="flex items-center gap-1">
          <span>↑ LIKELIHOOD / PROBABILITY</span>
        </span>
        <span className="text-slate-400">
          Click any cell to inspect filtered risk details
        </span>
      </div>

      {/* Selected Cell Drill-Down Drawer */}
      {selectedCell && selectedMeta && (
        <div className="mt-3 p-4 rounded-xl bg-slate-900/90 border border-white/15 space-y-3 animate-fadeIn">
          <div className="flex items-center justify-between border-b border-white/10 pb-2">
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${selectedMeta.accentDot}`} />
              <span className="text-xs font-mono font-bold text-white uppercase">
                Zone Inspection: {selectedMeta.tier} ({activeRisks.length} {activeRisks.length === 1 ? 'Risk' : 'Risks'})
              </span>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full ${selectedMeta.badge}`}>
                {selectedMeta.scoreText}
              </span>
            </div>
            <button
              onClick={() => setSelectedCell(null)}
              className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-white/10 transition-all cursor-pointer"
              title="Close inspection"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          {activeRisks.length === 0 ? (
            <div className="text-center py-4 text-xs text-slate-500 italic">
              No risks currently mapped to this specific Likelihood × Impact coordinate.
            </div>
          ) : (
            <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
              {activeRisks.map((r, idx) => {
                const title = r.statutory_act || r.risk || r.vulnerability || r.risk_title || `Risk #${idx + 1}`;
                const desc = r.compliance_gap || r.description || r.risk_description || '';
                const mit = r.mitigation_action || r.mitigation || r.mitigation_strategy || '';
                const pillar = r.pillar || r.category || 'General Risk';

                return (
                  <div key={idx} className="p-2.5 rounded-lg bg-slate-950/60 border border-white/5 space-y-1 text-xs">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-semibold text-white truncate">{title}</span>
                      <span className="text-[9px] font-mono text-slate-400 bg-white/5 px-2 py-0.5 rounded border border-white/10 shrink-0">
                        {pillar}
                      </span>
                    </div>
                    {desc && <p className="text-slate-300 text-[11px] leading-relaxed">{desc}</p>}
                    {mit && (
                      <div className="text-[11px] text-emerald-400/90 pt-0.5 flex items-start gap-1">
                        <span className="font-bold shrink-0">Mitigation:</span>
                        <span className="text-slate-300">{mit}</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * CompetitiveMatrix2x2 — Institutional 2x2 Competitive Whitespace Map.
 * Maps competitors across X/Y strategic axes, highlighting our venture in the top-right Whitespace quadrant.
 */
export function CompetitiveMatrix2x2({ 
  competitors = [], 
  projectName = "Our Venture",
  xAxisLabel = "Technology & Domain Specialization",
  yAxisLabel = "Execution Speed & Local Regulatory Depth"
}) {
  const defaultCompetitors = [
    { name: "Legacy ERP / Consulting", x: 25, y: 30, tag: "High Cost / Slow", isLeader: false },
    { name: "Generic AI Wrappers", x: 35, y: 75, tag: "Fast / Generic", isLeader: false },
    { name: "Niche Point Solutions", x: 70, y: 25, tag: "Manual Silos", isLeader: false },
    { name: projectName, x: 88, y: 88, tag: "Market Whitespace", isLeader: true }
  ];

  const items = competitors.length > 0 ? competitors.map((c, i) => ({
    name: typeof c === 'string' ? c : c.name || c.competitor_name || `Competitor ${i+1}`,
    x: c.x || (i === 0 ? 30 : i === 1 ? 40 : 65),
    y: c.y || (i === 0 ? 35 : i === 1 ? 70 : 30),
    tag: c.tag || (c.isLeader ? "Whitespace Leader" : "Incumbent / Alternative"),
    isLeader: Boolean(c.isLeader)
  })) : defaultCompetitors;

  // Ensure our venture is placed in top right
  if (!items.some(it => it.isLeader)) {
    items.push({ name: projectName, x: 88, y: 88, tag: "Strategic Moat", isLeader: true });
  }

  return (
    <div className="bg-gradient-to-br from-slate-900/95 via-slate-950/90 to-[#080B11] p-5 rounded-2xl border border-white/10 space-y-4 relative overflow-hidden shadow-xl">
      <div className="flex items-center justify-between border-b border-white/10 pb-3">
        <div>
          <span className="text-[10px] font-mono uppercase font-bold text-gold-400 tracking-wider block">
            STRATEGIC POSITIONING
          </span>
          <h4 className="text-sm font-bold text-white font-display">2×2 Competitive Whitespace Matrix</h4>
        </div>
        <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/30 font-bold">
          Top-Right Whitespace
        </span>
      </div>

      {/* 2x2 Radar Grid Canvas */}
      <div className="relative w-full aspect-[16/10] max-h-[320px] bg-slate-950/80 rounded-xl border border-white/5 p-6 flex flex-col justify-between overflow-hidden">
        {/* Quadrant Background Zones */}
        <div className="absolute inset-0 grid grid-cols-2 grid-rows-2 opacity-30 pointer-events-none">
          <div className="border-r border-b border-white/10 bg-rose-500/[0.03] p-2 flex items-start justify-start">
            <span className="text-[9px] font-mono text-slate-500 uppercase">Commodity Trap</span>
          </div>
          <div className="border-b border-white/10 bg-emerald-500/[0.08] p-2 flex items-start justify-end">
            <span className="text-[9px] font-mono text-emerald-400 font-bold uppercase">✦ Whitespace Champion</span>
          </div>
          <div className="border-r border-white/10 bg-slate-500/[0.02] p-2 flex items-end justify-start">
            <span className="text-[9px] font-mono text-slate-600 uppercase">Legacy Incumbents</span>
          </div>
          <div className="bg-indigo-500/[0.03] p-2 flex items-end justify-end">
            <span className="text-[9px] font-mono text-indigo-400 uppercase">Niche Silos</span>
          </div>
        </div>

        {/* Competitor Nodes */}
        {items.map((node, nIdx) => (
          <div
            key={nIdx}
            className="absolute -translate-x-1/2 -translate-y-1/2 group cursor-pointer transition-transform hover:scale-110 z-10"
            style={{ left: `${node.x}%`, top: `${100 - node.y}%` }}
          >
            {node.isLeader ? (
              <div className="flex flex-col items-center">
                <div className="relative">
                  <div className="w-5 h-5 rounded-full bg-emerald-500 border-2 border-white shadow-lg shadow-emerald-500/50 flex items-center justify-center animate-pulse">
                    <div className="w-2 h-2 rounded-full bg-white" />
                  </div>
                  <div className="absolute -inset-1.5 rounded-full border border-emerald-400/50 animate-ping pointer-events-none" />
                </div>
                <div className="mt-1 px-2.5 py-0.5 rounded-md bg-emerald-950/90 border border-emerald-400/50 text-[10px] font-bold text-emerald-200 font-mono whitespace-nowrap shadow-md">
                  ★ {node.name}
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center">
                <div className="w-3 h-3 rounded-full bg-slate-600 border border-white/30 shadow-sm" />
                <div className="mt-0.5 px-1.5 py-0.5 rounded bg-slate-900/80 border border-white/10 text-[9px] font-medium text-slate-400 whitespace-nowrap">
                  {node.name}
                </div>
              </div>
            )}
          </div>
        ))}

        {/* Axes Labels */}
        <div className="absolute bottom-1.5 left-1/2 -translate-x-1/2 text-[9px] font-mono text-slate-400 uppercase tracking-wider font-bold">
          {xAxisLabel} →
        </div>
        <div className="absolute top-1/2 left-1.5 -translate-y-1/2 -rotate-90 text-[9px] font-mono text-slate-400 uppercase tracking-wider font-bold whitespace-nowrap">
          {yAxisLabel} →
        </div>
      </div>
    </div>
  );
}

/**
 * FinancialSensitivitySimulator — Interactive valuation & ARR sensitivity slider.
 * Allows founders to adjust Conversion Rate & CAC to visualize dynamic ARR & Breakeven updates.
 */
export function FinancialSensitivitySimulator({ initialArpu = 12000, initialCac = 8500, currency = 'INR' }) {
  const [conversionRate, setConversionRate] = React.useState(3.5);
  const [cac, setCac] = React.useState(initialCac);
  const [trafficVolume, setTrafficVolume] = React.useState(25000);

  const isINR = currency === 'INR' || currency === '₹';
  const isGBP = currency === 'GBP' || currency === '£';
  const isEUR = currency === 'EUR' || currency === '€';
  const sym = isINR ? '₹' : isGBP ? '£' : isEUR ? '€' : '$';

  // Dynamic calculations
  const annualCustomers = Math.round((trafficVolume * (conversionRate / 100)));
  const annualRevenue = annualCustomers * initialArpu;
  const totalCacExpense = annualCustomers * cac;
  const grossProfit = annualRevenue * 0.82; // 82% margin
  const netContribution = grossProfit - totalCacExpense;
  const ltvCacRatio = ((initialArpu * 3 * 0.82) / Math.max(cac, 1)).toFixed(1);

  const formatLarge = (amt) => {
    if (isINR) {
      return `${sym}${(amt / 10000000).toFixed(2)} Cr`;
    }
    return `${sym}${(amt / 1000000).toFixed(2)}M`;
  };

  const formatSmall = (amt) => {
    if (isINR) {
      return `${sym}${(amt / 100000).toFixed(1)} Lakhs`;
    }
    return `${sym}${(amt / 1000).toFixed(1)}k`;
  };

  return (
    <div className="bg-gradient-to-br from-slate-900/95 via-slate-950/90 to-[#080B11] p-5 rounded-2xl border border-indigo-500/30 shadow-2xl space-y-4">
      <div className="flex items-center justify-between border-b border-white/10 pb-3">
        <div>
          <span className="text-[10px] font-mono uppercase font-bold text-indigo-400 tracking-wider block">
            INTERACTIVE FINANCIAL MODELING
          </span>
          <h4 className="text-sm font-bold text-white font-display">Unit Economics Sensitivity Simulator</h4>
        </div>
        <span className="text-[10px] font-mono font-bold text-gold-400 bg-gold-500/10 px-2.5 py-1 rounded-full border border-gold-500/30">
          LTV/CAC: {ltvCacRatio}x
        </span>
      </div>

      {/* Sliders Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-4 rounded-xl bg-slate-950/60 border border-white/5">
        {/* Slider 1: Conversion Rate */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-mono">
            <span className="text-slate-400">Conversion Rate:</span>
            <span className="text-primary-300 font-bold">{conversionRate}%</span>
          </div>
          <input
            type="range"
            min="1.0"
            max="10.0"
            step="0.5"
            value={conversionRate}
            onChange={(e) => setConversionRate(parseFloat(e.target.value))}
            className="w-full accent-primary-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
          />
        </div>

        {/* Slider 2: Target CAC */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-mono">
            <span className="text-slate-400">Target CAC:</span>
            <span className="text-primary-300 font-bold">{sym}{cac.toLocaleString()}</span>
          </div>
          <input
            type="range"
            min={isINR ? 2000 : 50}
            max={isINR ? 25000 : 1500}
            step={isINR ? 500 : 25}
            value={cac}
            onChange={(e) => setCac(parseInt(e.target.value))}
            className="w-full accent-primary-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
          />
        </div>

        {/* Slider 3: Annual Leads / Traffic */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-mono">
            <span className="text-slate-400">Annual Pipeline:</span>
            <span className="text-primary-300 font-bold">{trafficVolume.toLocaleString()} Leads</span>
          </div>
          <input
            type="range"
            min="5000"
            max="100000"
            step="5000"
            value={trafficVolume}
            onChange={(e) => setTrafficVolume(parseInt(e.target.value))}
            className="w-full accent-primary-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
          />
        </div>
      </div>

      {/* Real-time Output Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
        <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5 space-y-1">
          <span className="text-[10px] font-mono uppercase text-slate-500 block">Acquired Customers</span>
          <span className="text-base font-bold font-mono text-white">{annualCustomers.toLocaleString()}</span>
        </div>
        <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5 space-y-1">
          <span className="text-[10px] font-mono uppercase text-slate-500 block">Projected ARR</span>
          <span className="text-base font-bold font-mono text-emerald-400">{formatLarge(annualRevenue)}</span>
        </div>
        <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5 space-y-1">
          <span className="text-[10px] font-mono uppercase text-slate-500 block">Net Contribution</span>
          <span className="text-base font-bold font-mono text-indigo-300">{formatSmall(netContribution)}</span>
        </div>
        <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5 space-y-1">
          <span className="text-[10px] font-mono uppercase text-slate-500 block">Health Rating</span>
          <span className={`text-base font-bold font-mono ${parseFloat(ltvCacRatio) >= 3.0 ? 'text-emerald-400' : 'text-amber-400'}`}>
            {parseFloat(ltvCacRatio) >= 3.0 ? 'Top Tier (VC-Ready)' : 'Moderate CAC'}
          </span>
        </div>
      </div>
    </div>
  );
}

/**
 * ArrBridgeWaterfall — Institutional Goldman Sachs / McKinsey ARR Bridge Waterfall.
 * Visually decomposes ARR growth: Starting ARR -> New Bookings -> Expansion -> Gross Churn -> Ending ARR.
 */
export function ArrBridgeWaterfall({
  currency = 'USD',
  startingArr = 1200000,
  newBookings = 2850000,
  expansionArr = 1100000,
  churnArr = 320000,
  title = "36-Month ARR Bridge & Retention Decomposition"
}) {
  const endingArr = startingArr + newBookings + expansionArr - churnArr;
  const currSym = currency === 'INR' ? '₹' : currency === 'GBP' ? '£' : currency === 'EUR' ? '€' : '$';

  const fmt = (v) => {
    if (Math.abs(v) >= 1000000) return `${currSym}${(v / 1000000).toFixed(2)}M`;
    if (Math.abs(v) >= 1000) return `${currSym}${(v / 1000).toFixed(0)}k`;
    return `${currSym}${v.toLocaleString()}`;
  };

  const steps = [
    { label: "Starting ARR", value: startingArr, type: "base", delta: startingArr, heightPct: Math.min(100, Math.max(20, (startingArr / endingArr) * 85)) },
    { label: "+ New Logo Bookings", value: newBookings, type: "add", delta: newBookings, heightPct: Math.min(100, Math.max(25, (newBookings / endingArr) * 85)) },
    { label: "+ Net Expansion", value: expansionArr, type: "add", delta: expansionArr, heightPct: Math.min(100, Math.max(15, (expansionArr / endingArr) * 85)) },
    { label: "- Logo Churn", value: -churnArr, type: "sub", delta: -churnArr, heightPct: Math.min(100, Math.max(12, (churnArr / endingArr) * 85)) },
    { label: "Ending ARR", value: endingArr, type: "total", delta: endingArr, heightPct: 92 }
  ];

  const nrr = Math.round(((startingArr + expansionArr - churnArr) / startingArr) * 100);

  return (
    <div className="bg-gradient-to-br from-slate-900/95 via-slate-950/90 to-[#0A0D14] p-5 rounded-2xl border border-white/10 space-y-4 shadow-xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/10 pb-3">
        <div>
          <span className="text-[10px] font-mono uppercase font-bold text-gold-400 tracking-wider block">
            FINANCIAL WATERFALL ARCHITECTURE
          </span>
          <h4 className="text-sm font-bold text-white font-display">{title}</h4>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono text-slate-400 bg-white/5 px-2.5 py-1 rounded-lg border border-white/5">
            Implied NRR: <strong className="text-emerald-400">{nrr}%</strong>
          </span>
          <span className="text-[11px] font-mono text-gold-300 bg-gold-500/10 px-2.5 py-1 rounded-lg border border-gold-500/20 font-bold">
            Target Ending: {fmt(endingArr)}
          </span>
        </div>
      </div>

      {/* Waterfall Visual Bars */}
      <div className="h-56 pt-6 pb-2 px-2 flex items-end justify-between gap-3 sm:gap-6 bg-slate-950/60 rounded-xl border border-white/5">
        {steps.map((step, idx) => {
          const isBase = step.type === "base";
          const isTotal = step.type === "total";
          const isAdd = step.type === "add";
          const isSub = step.type === "sub";

          const barBg = isTotal
            ? "bg-gradient-to-t from-gold-600 via-gold-500 to-amber-300 border-gold-400/80 shadow-gold-500/20"
            : isBase
            ? "bg-gradient-to-t from-slate-700 to-slate-500 border-slate-400/50"
            : isAdd
            ? "bg-gradient-to-t from-emerald-700 via-emerald-600 to-emerald-400 border-emerald-400/80 shadow-emerald-500/20"
            : "bg-gradient-to-t from-rose-800 via-rose-600 to-rose-400 border-rose-400/80 shadow-rose-500/20";

          return (
            <div key={idx} className="flex-1 flex flex-col items-center h-full justify-end group">
              <span className={`text-[10px] font-mono font-bold mb-1.5 tabular-nums transition-transform group-hover:scale-110 ${
                isTotal ? "text-gold-300" : isAdd ? "text-emerald-300" : isSub ? "text-rose-300" : "text-slate-300"
              }`}>
                {isAdd ? `+${fmt(step.delta)}` : fmt(step.delta)}
              </span>
              <div
                className={`w-full rounded-t-lg border-t border-x shadow-lg transition-all duration-500 group-hover:brightness-110 ${barBg}`}
                style={{ height: `${step.heightPct}%` }}
              />
              <span className="text-[9px] sm:text-[10px] font-mono text-slate-400 mt-2 text-center leading-tight truncate max-w-[80px]">
                {step.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Footnote Metrics */}
      <div className="grid grid-cols-3 gap-2 pt-1 text-[11px] font-mono">
        <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/5">
          <span className="text-slate-500 block text-[9px] uppercase">New Logo Velocity</span>
          <span className="text-emerald-400 font-bold tabular-nums">+{fmt(newBookings)}</span>
        </div>
        <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/5">
          <span className="text-slate-500 block text-[9px] uppercase">Expansion Lift</span>
          <span className="text-indigo-300 font-bold tabular-nums">+{fmt(expansionArr)}</span>
        </div>
        <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/5">
          <span className="text-slate-500 block text-[9px] uppercase">Annual Gross Churn</span>
          <span className="text-rose-400 font-bold tabular-nums">-{fmt(churnArr)}</span>
        </div>
      </div>
    </div>
  );
}

