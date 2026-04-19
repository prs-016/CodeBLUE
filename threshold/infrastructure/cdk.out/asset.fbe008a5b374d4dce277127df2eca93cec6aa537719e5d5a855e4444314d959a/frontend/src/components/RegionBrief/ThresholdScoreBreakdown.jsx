import React from "react";

function clampPercent(value, scale = 1) {
  return Math.max(0, Math.min(100, (value / scale) * 100));
}

export default function ThresholdScoreBreakdown({ score = 0, primaryDriver = "", breakdown = [] }) {
  return (
    <section className="rounded-[28px] border border-grey-dark/80 bg-white/[0.03] p-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="text-xs uppercase tracking-[0.28em] text-grey-mid">Threshold score</div>
          <h3 className="mt-2 text-2xl font-semibold text-white">Primary drivers of escalation</h3>
        </div>
        <div className="rounded-2xl border border-red-alert/30 bg-red-alert/10 px-4 py-3 text-right">
          <div className="text-xs uppercase tracking-[0.2em] text-red-200">Current score</div>
          <div className="mt-1 font-mono text-3xl text-white">{score.toFixed(1)} / 10</div>
        </div>
      </div>

      <p className="mt-4 max-w-2xl text-sm text-grey-mid">{primaryDriver}</p>

      <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {breakdown.map((item) => (
          <div key={item.key} className="rounded-[22px] border border-grey-dark/70 bg-black/20 p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-sm text-grey-light">{item.label}</div>
                <div className="mt-1 text-xs uppercase tracking-[0.2em] text-grey-mid">{item.detail}</div>
              </div>
              <div className="font-mono text-lg text-white">
                {typeof item.value === "number" ? item.value.toFixed(item.value > 1 ? 1 : 2) : item.value}
              </div>
            </div>
            <div className="mt-4 h-2 overflow-hidden rounded-full bg-grey-dark/70">
              <div
                className={`h-full rounded-full ${item.key === 'stability' ? 'bg-teal-mid' : 'bg-gradient-to-r from-teal-light via-orange to-red-alert'}`}
                style={{ 
                  width: `${clampPercent(
                    Math.abs(item.value),
                    item.key === "thermal" ? 3 :
                    item.key === "oxygen" ? 8 :
                    item.key === "productivity" ? 2 : 5
                  )}%`
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
