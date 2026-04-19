import React, { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AlertTriangle, ArrowUpRight, Waves } from "lucide-react";

import { useApiResource } from "../../hooks/useApiResource";

function formatMoney(value) {
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`;
  }
  if (value >= 1000) {
    return `$${(value / 1000).toFixed(0)}k`;
  }
  return `$${value}`;
}

function getThreatColor(threat) {
  if (threat === "thermal") {
    return "#E67E22";
  }
  if (threat === "hypoxia") {
    return "#8B5CF6";
  }
  if (threat === "acidification") {
    return "#14BDAC";
  }
  return "#BDC3C7";
}

function normalizeRow(row) {
  return {
    ...row,
    region_id: row.region_id ?? row.id,
    threshold_score: row.threshold_score ?? row.threshold_proximity_score ?? row.current_score ?? 0,
    coverage_ratio:
      row.coverage_ratio ??
      ((row.committed_funding_usd || 0) / Math.max((row.committed_funding_usd || 0) + (row.funding_gap || 0), 1)),
  };
}

export default function FundingGapRadar({
  data,
  onSelectRegion,
  className = "",
  interactive = true,
}) {
  const navigate = useNavigate();
  const [hoveredId, setHoveredId] = useState(null);
  const state = useApiResource({
    endpoint: data ? null : "/api/v1/funding/gap",
    enabled: !data,
    transform: (rows) => rows.map(normalizeRow),
  });

  const points = useMemo(() => (data ?? state.data ?? []).map(normalizeRow), [data, state.data]);
  const width = 880;
  const height = 580;
  const padding = 80;
  const maxGap = Math.max(...points.map((item) => item.funding_gap), 12000000);
  const hovered = points.find((item) => item.region_id === hoveredId) ?? points[0];

  function xScale(value) {
    return padding + (value / 10) * (width - padding * 2);
  }

  function yScale(value) {
    return height - padding - (value / maxGap) * (height - padding * 2);
  }

  function radius(value) {
    return 14 + Math.sqrt((value || 1000000) / 1000000) * 4.5;
  }

  function handleSelect(regionId) {
    if (!interactive) {
      return;
    }
    if (onSelectRegion) {
      onSelectRegion(regionId);
      return;
    }
    navigate(`/region/${regionId}`);
  }

  return (
    <div className={`rounded-[28px] border border-grey-dark/80 bg-[linear-gradient(160deg,rgba(10,22,40,0.98),rgba(14,28,51,0.94))] p-6 shadow-[0_24px_80px_rgba(0,0,0,0.45)] ${className}`}>
      <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="mb-2 flex items-center gap-2 text-xs uppercase tracking-[0.3em] text-grey-mid">
            <AlertTriangle className="h-4 w-4 text-orange" />
            Funding follows cameras, not data
          </div>
          <h3 className="text-2xl font-semibold text-white">Severity vs funding coverage</h3>
          <p className="mt-1 max-w-2xl text-sm text-grey-mid">
            Bottom-right regions combine high threshold proximity with weak coverage. Arabian Sea and Mekong should sit visibly exposed.
          </p>
        </div>
        <div className="rounded-2xl border border-grey-dark bg-black/20 px-4 py-3 text-right">
          <div className="text-xs uppercase tracking-[0.25em] text-grey-mid">Data Mode</div>
          <div className="mt-1 text-sm font-mono text-teal-light">{data ? "Injected" : state.isFallback ? "Fallback" : "Live API"}</div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_280px]">
        <div className="overflow-hidden rounded-[24px] border border-grey-dark/70 bg-[radial-gradient(circle_at_top,rgba(20,189,172,0.08),transparent_35%),linear-gradient(180deg,rgba(255,255,255,0.02),transparent)] p-3">
          <svg viewBox={`0 0 ${width} ${height}`} className="h-auto w-full">
            <defs>
              <linearGradient id="dangerZone" x1="0%" x2="100%">
                <stop offset="0%" stopColor="rgba(230,126,34,0.05)" />
                <stop offset="100%" stopColor="rgba(192,57,43,0.22)" />
              </linearGradient>
            </defs>

            <rect x={width / 2} y={height / 2} width={width / 2 - padding} height={height / 2 - padding} fill="url(#dangerZone)" rx="24" />

            {[0, 2, 4, 6, 8, 10].map((tick) => (
              <g key={`x-${tick}`}>
                <line x1={xScale(tick)} y1={padding / 2} x2={xScale(tick)} y2={height - padding} stroke="rgba(189,195,199,0.12)" strokeDasharray="6 8" />
                <text x={xScale(tick)} y={height - 28} fill="#BDC3C7" fontSize="13" textAnchor="middle">{tick}</text>
              </g>
            ))}

            {[0, maxGap * 0.25, maxGap * 0.5, maxGap * 0.75, maxGap].map((tick, index) => (
              <g key={`y-${index}`}>
                <line x1={padding} y1={yScale(tick)} x2={width - padding / 2} y2={yScale(tick)} stroke="rgba(189,195,199,0.12)" strokeDasharray="6 8" />
                <text x={28} y={yScale(tick) + 4} fill="#BDC3C7" fontSize="13">{formatMoney(tick)}</text>
              </g>
            ))}

            <line x1={xScale(5)} y1={padding / 2} x2={xScale(5)} y2={height - padding} stroke="rgba(255,255,255,0.16)" strokeDasharray="8 10" />
            <line x1={padding} y1={yScale(maxGap * 0.5)} x2={width - padding / 2} y2={yScale(maxGap * 0.5)} stroke="rgba(255,255,255,0.16)" strokeDasharray="8 10" />

            <text x={padding} y={padding / 2 - 10} fill="#BDC3C7" fontSize="12" letterSpacing="3">OVERFUNDED</text>
            <text x={width - 210} y={padding / 2 - 10} fill="#14BDAC" fontSize="12" letterSpacing="3">WELL-SERVED</text>
            <text x={padding} y={height - 48} fill="#0D7377" fontSize="12" letterSpacing="3">STABLE / MONITOR</text>
            <text x={width - 180} y={height - 48} fill="#C0392B" fontSize="12" letterSpacing="3">DANGER ZONE</text>

            <text x={width / 2} y={height - 8} fill="#F4F6F8" fontSize="14" textAnchor="middle">Threshold Proximity Score</text>
            <text x={-height / 2} y={18} fill="#F4F6F8" fontSize="14" textAnchor="middle" transform="rotate(-90)">Funding Gap</text>

            {points.map((point) => (
              <g
                key={point.region_id}
                onMouseEnter={() => setHoveredId(point.region_id)}
                onMouseLeave={() => setHoveredId(null)}
                onClick={() => handleSelect(point.region_id)}
                className={interactive ? "cursor-pointer" : ""}
              >
                <circle
                  cx={xScale(point.threshold_score)}
                  cy={yScale(point.funding_gap)}
                  r={radius(point.population_affected)}
                  fill={getThreatColor(point.threat_type)}
                  fillOpacity={hoveredId === point.region_id ? 0.96 : 0.74}
                  stroke="rgba(244,246,248,0.85)"
                  strokeWidth={hoveredId === point.region_id ? 3 : 1.5}
                />
                <text
                  x={xScale(point.threshold_score)}
                  y={yScale(point.funding_gap) - radius(point.population_affected) - 10}
                  fill="#F4F6F8"
                  fontSize="12"
                  textAnchor="middle"
                >
                  {point.name}
                </text>
              </g>
            ))}
          </svg>
        </div>

        <div className="flex flex-col gap-4">
          <div className="rounded-[24px] border border-red-alert/30 bg-red-alert/10 p-5">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs uppercase tracking-[0.25em] text-red-200">Priority Focus</div>
                <div className="mt-1 text-xl font-semibold text-white">{hovered?.name}</div>
              </div>
              <Waves className="h-5 w-5 text-orange" />
            </div>
            <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
              <div className="rounded-2xl border border-white/10 bg-black/15 p-3">
                <div className="text-grey-mid">Severity</div>
                <div className="mt-1 font-mono text-2xl text-white">{hovered?.threshold_score?.toFixed(1)}</div>
              </div>
              <div className="rounded-2xl border border-white/10 bg-black/15 p-3">
                <div className="text-grey-mid">Coverage</div>
                <div className="mt-1 font-mono text-2xl text-white">{Math.round((hovered?.coverage_ratio || 0) * 100)}%</div>
              </div>
            </div>
            <p className="mt-4 text-sm text-grey-light/90">{hovered?.primary_driver}</p>
            <button
              type="button"
              onClick={() => handleSelect(hovered?.region_id)}
              className="mt-4 inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-4 py-2 text-sm text-white transition hover:bg-white/10"
            >
              Open region brief
              <ArrowUpRight className="h-4 w-4" />
            </button>
          </div>

          <div className="rounded-[24px] border border-grey-dark bg-black/20 p-5">
            <div className="mb-3 text-xs uppercase tracking-[0.25em] text-grey-mid">Threat legend</div>
            {[
              { label: "Thermal", color: "#E67E22" },
              { label: "Hypoxia", color: "#8B5CF6" },
              { label: "Acidification", color: "#14BDAC" },
            ].map((item) => (
              <div key={item.label} className="mb-3 flex items-center justify-between text-sm text-grey-light">
                <div className="flex items-center gap-3">
                  <span className="h-3 w-3 rounded-full" style={{ backgroundColor: item.color }} />
                  {item.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
