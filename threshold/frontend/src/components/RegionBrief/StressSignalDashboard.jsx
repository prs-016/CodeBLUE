import React, { useMemo, useState } from "react";

const METRICS = [
  { key: "threshold_proximity_score", label: "Threshold score", color: "#C0392B" },
  { key: "sst_anomaly", label: "SST anomaly", color: "#E67E22" },
  { key: "o2_current", label: "Dissolved oxygen", color: "#14BDAC" },
  { key: "chlorophyll_anomaly", label: "Chlorophyll anomaly", color: "#8B5CF6" },
  { key: "co2_regional_ppm", label: "Regional CO₂ proxy", color: "#F1C40F" },
  { key: "nitrate_anomaly", label: "Nitrate anomaly", color: "#27AE60" },
  { key: "dhw_current", label: "Degree heating weeks", color: "#E74C3C" },
];

function makePath(points, width, height, padding) {
  if (!points.length) {
    return "";
  }

  const values = points.map((point) => point.value);
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const xStep = (width - padding * 2) / Math.max(points.length - 1, 1);

  return points
    .map((point, index) => {
      const x = padding + index * xStep;
      const y =
        height -
        padding -
        ((point.value - minValue) / Math.max(maxValue - minValue, 0.0001)) * (height - padding * 2);
      return `${index === 0 ? "M" : "L"} ${x} ${y}`;
    })
    .join(" ");
}

export default function StressSignalDashboard({ signals = [], regionName = "Region" }) {
  const [metricKey, setMetricKey] = useState("threshold_proximity_score");
  const width = 940;
  const height = 320;
  const padding = 36;

  const sortedSignals = useMemo(
    () => [...signals].sort((a, b) => new Date(a.date) - new Date(b.date)),
    [signals]
  );

  const sampled = useMemo(() => {
    if (sortedSignals.length <= 120) {
      return sortedSignals;
    }
    const step = Math.ceil(sortedSignals.length / 120);
    return sortedSignals.filter((_, index) => index % step === 0);
  }, [sortedSignals]);

  const metric = METRICS.find((item) => item.key === metricKey) ?? METRICS[0];
  const points = sampled.map((row) => ({ date: row.date, value: Number(row[metric.key] ?? 0) }));
  const path = makePath(points, width, height, padding);
  const current = points[points.length - 1]?.value ?? 0;
  const historicalHigh = Math.max(...points.map((point) => point.value), 0);

  return (
    <section className="rounded-[28px] border border-grey-dark/80 bg-white/[0.03] p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="text-xs uppercase tracking-[0.28em] text-grey-mid">Stress signals</div>
          <h3 className="mt-2 text-2xl font-semibold text-white">{regionName} historical dashboard</h3>
          <p className="mt-1 text-sm text-grey-mid">
            Displays from the earliest available record across the loaded time range.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {METRICS.map((item) => (
            <button
              key={item.key}
              type="button"
              onClick={() => setMetricKey(item.key)}
              className={`rounded-full px-3 py-2 text-xs uppercase tracking-[0.22em] transition ${
                item.key === metricKey ? "bg-white text-navy" : "border border-grey-dark text-grey-mid hover:text-white"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-[minmax(0,1fr)_240px]">
        <div className="rounded-[24px] border border-grey-dark/70 bg-black/20 p-4">
          <svg viewBox={`0 0 ${width} ${height}`} className="h-auto w-full">
            {[0, 1, 2, 3].map((row) => (
              <line
                key={row}
                x1={padding}
                y1={padding + row * ((height - padding * 2) / 3)}
                x2={width - padding}
                y2={padding + row * ((height - padding * 2) / 3)}
                stroke="rgba(189,195,199,0.12)"
                strokeDasharray="6 8"
              />
            ))}
            <path d={path} fill="none" stroke={metric.color} strokeWidth="4" strokeLinecap="round" />
            <text x={padding} y={height - 8} fill="#BDC3C7" fontSize="12">{points[0]?.date || "start"}</text>
            <text x={width - padding} y={height - 8} fill="#BDC3C7" fontSize="12" textAnchor="end">{points[points.length - 1]?.date || "now"}</text>
          </svg>
        </div>

        <div className="space-y-4">
          <div className="rounded-[24px] border border-grey-dark/70 bg-black/20 p-4">
            <div className="text-xs uppercase tracking-[0.22em] text-grey-mid">Current</div>
            <div className="mt-2 font-mono text-3xl text-white">{current.toFixed(2)}</div>
            <div className="mt-2 text-sm text-grey-mid">{metric.label}</div>
          </div>
          <div className="rounded-[24px] border border-grey-dark/70 bg-black/20 p-4">
            <div className="text-xs uppercase tracking-[0.22em] text-grey-mid">Historical high</div>
            <div className="mt-2 font-mono text-3xl text-white">{historicalHigh.toFixed(2)}</div>
            <div className="mt-2 text-sm text-grey-mid">Across the loaded time range</div>
          </div>
          <div className="rounded-[24px] border border-grey-dark/70 bg-black/20 p-4 text-sm text-grey-light">
            <div className="text-xs uppercase tracking-[0.22em] text-grey-mid">Sampling</div>
            <p className="mt-2">
              The chart down-samples long histories so the page stays responsive while still showing multi-decade trend structure.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
