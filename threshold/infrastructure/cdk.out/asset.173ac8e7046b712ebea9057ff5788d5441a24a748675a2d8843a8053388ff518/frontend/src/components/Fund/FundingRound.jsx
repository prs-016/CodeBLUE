import React from "react";

function formatMoney(value) {
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`;
  }
  if (value >= 1000) {
    return `$${(value / 1000).toFixed(0)}k`;
  }
  return `$${value}`;
}

export default function FundingRound({ round, onContribute }) {
  const progress = Math.min(100, ((round.raised_amount || 0) / Math.max(round.target_amount || 1, 1)) * 100);

  return (
    <article className="relative flex h-full flex-col overflow-hidden rounded-[28px] border border-grey-dark/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.03),rgba(255,255,255,0.015))] p-5">
      <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-orange via-red-alert to-teal-light" />
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-xs uppercase tracking-[0.22em] text-grey-mid">{round.threat_type}</div>
          <h3 className="mt-2 text-2xl font-semibold text-white">{round.title || round.region_name}</h3>
        </div>
        <div className="rounded-full border border-orange/30 bg-orange/10 px-3 py-1 text-sm text-orange">
          {round.cost_multiplier}x return
        </div>
      </div>

      <p className="mt-4 text-sm text-grey-mid">{round.round_summary}</p>

      <div className="mt-5 grid gap-3 md:grid-cols-2">
        <div className="rounded-[20px] border border-grey-dark/70 bg-black/20 p-4">
          <div className="text-xs uppercase tracking-[0.2em] text-grey-mid">Raised</div>
          <div className="mt-2 font-mono text-2xl text-white">{formatMoney(round.raised_amount || 0)}</div>
        </div>
        <div className="rounded-[20px] border border-grey-dark/70 bg-black/20 p-4">
          <div className="text-xs uppercase tracking-[0.2em] text-grey-mid">Target</div>
          <div className="mt-2 font-mono text-2xl text-white">{formatMoney(round.target_amount || 0)}</div>
        </div>
      </div>

      <div className="mt-5 h-3 overflow-hidden rounded-full bg-grey-dark/70">
        <div className="h-full rounded-full bg-gradient-to-r from-teal-light to-orange" style={{ width: `${Math.max(progress, 4)}%` }} />
      </div>

      <div className="mt-5 rounded-[20px] border border-grey-dark/70 bg-black/20 p-4 text-sm text-grey-light">
        <div className="text-xs uppercase tracking-[0.2em] text-grey-mid">Verified partner</div>
        <div className="mt-2 text-lg text-white">{round.charity_name}</div>
        <div className="mt-1 text-grey-mid">Score {round.verified_score}</div>
      </div>

      <button
        type="button"
        onClick={() => onContribute?.(round)}
        className="mt-5 rounded-full bg-teal px-4 py-3 text-sm font-semibold uppercase tracking-[0.22em] text-navy transition hover:bg-teal-light"
      >
        Contribute
      </button>
    </article>
  );
}
