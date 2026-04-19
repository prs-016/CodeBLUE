import React from "react";

function formatMoney(value) {
  if (value >= 1000000000) {
    return `$${(value / 1000000000).toFixed(1)}B`;
  }
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`;
  }
  return `$${value}`;
}

export default function BranchingPaths({ estimate, region }) {
  const prevention = estimate?.prevention_cost ?? 0;
  const recovery = estimate?.recovery_cost ?? 0;
  const multiplier = estimate?.cost_multiplier ?? 0;
  const breakdown = estimate?.breakdown ?? {};

  return (
    <section className="rounded-[28px] border border-grey-dark/80 bg-white/[0.03] p-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="text-xs uppercase tracking-[0.28em] text-grey-mid">Branching paths</div>
          <h3 className="mt-2 text-2xl font-semibold text-white">Counterfactual cost curve</h3>
        </div>
        <div className="rounded-2xl border border-red-alert/30 bg-red-alert/10 px-4 py-3 text-right">
          <div className="text-xs uppercase tracking-[0.2em] text-red-200">Multiplier</div>
          <div className="mt-1 font-mono text-3xl text-white">{multiplier}x</div>
        </div>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <div className="rounded-[24px] border border-teal-light/30 bg-teal/10 p-5">
          <div className="text-xs uppercase tracking-[0.2em] text-teal-light">Intervene now</div>
          <div className="mt-2 font-mono text-4xl text-white">{formatMoney(prevention)}</div>
          <p className="mt-3 text-sm text-grey-light">
            Modeled prevention stack for {region?.name}: monitoring, response deployment, and resilience spending before threshold closure.
          </p>
        </div>
        <div className="rounded-[24px] border border-red-alert/30 bg-red-alert/10 p-5">
          <div className="text-xs uppercase tracking-[0.2em] text-red-200">Recover later</div>
          <div className="mt-2 font-mono text-4xl text-white">{formatMoney(recovery)}</div>
          <p className="mt-3 text-sm text-grey-light">
            Recovery costs roll up ecosystem loss, displaced livelihoods, and infrastructure damage after the system tips.
          </p>
        </div>
      </div>

      <div className="mt-6 grid gap-3 md:grid-cols-3">
        {Object.entries(breakdown).map(([key, value]) => (
          <div key={key} className="rounded-[20px] border border-grey-dark/70 bg-black/20 p-4">
            <div className="text-xs uppercase tracking-[0.2em] text-grey-mid">{key.replaceAll("_", " ")}</div>
            <div className="mt-2 font-mono text-2xl text-white">{formatMoney(value)}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
