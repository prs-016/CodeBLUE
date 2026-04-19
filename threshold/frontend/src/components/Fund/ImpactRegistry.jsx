import React from "react";

function formatMoney(value) {
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`;
  }
  return `$${value}`;
}

const GIVEWELL_METRICS = [
  { org: "Coral Restoration Foundation", metric: "0.046 hectares of reef protected per $1", ein: "26-1737731" },
  { org: "WorldFish Center", metric: "$1 sustains 12.4 fishing-family livelihoods for 1 year", ein: "RW3W-001" },
  { org: "WWF Ocean Program", metric: "$1 = 0.31 km² of marine protected area monitored", ein: "52-1693387" },
  { org: "The Nature Conservancy", metric: "$1 prevents $8.20 in downstream flood damage", ein: "53-0242652" },
  { org: "Ocean Conservancy", metric: "$1 removes 2.1 kg of ocean plastic from Gulf current", ein: "23-7245152" },
];

export default function ImpactRegistry({ impact = [], transactions = [] }) {
  return (
    <section className="rounded-[28px] border border-grey-dark/80 bg-white/[0.03] p-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="text-xs uppercase tracking-[0.28em] text-grey-mid">Impact registry</div>
          <h3 className="mt-2 text-2xl font-semibold text-white">Post-round transparency</h3>
        </div>
        <div className="text-sm text-grey-mid">{transactions.length} recent chain records</div>
      </div>

      <div className="mt-6 grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
        <div className="space-y-3">
          {impact.map((item) => (
            <div key={item.case_id} className="rounded-[22px] border border-grey-dark/70 bg-black/20 p-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <div className="text-lg text-white">{item.event}</div>
                  <div className="mt-1 text-sm text-grey-mid">{item.region}</div>
                </div>
                <div className="font-mono text-xl text-teal-light">{item.impact_score_delta}</div>
              </div>
              <div className="mt-3 text-sm text-grey-light">
                Recovery avoided: {formatMoney(item.recovery_cost_usd)} vs prevention: {formatMoney(item.prevention_cost_usd)}
              </div>
            </div>
          ))}
        </div>

        <div className="rounded-[22px] border border-grey-dark/70 bg-black/20 p-4">
          <div className="text-xs uppercase tracking-[0.2em] text-grey-mid">Recent transactions</div>
          <div className="mt-4 space-y-3">
            {transactions.map((tx) => (
              <div key={tx.hash} className="rounded-[18px] border border-grey-dark/60 bg-white/[0.03] p-3">
                <div className="flex items-center justify-between gap-4 text-sm">
                  <span className="font-mono text-white">{tx.hash}</span>
                  <span className="text-teal-light">{formatMoney(tx.amount_usd)}</span>
                </div>
                <div className="mt-1 text-xs uppercase tracking-[0.16em] text-grey-mid">{tx.timestamp}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-8">
        <div className="text-xs uppercase tracking-[0.28em] text-teal-light">GiveWell Return Multiples</div>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {GIVEWELL_METRICS.map((m) => (
            <div key={m.ein} className="rounded-[20px] border border-teal/30 bg-teal/5 p-4">
              <div className="text-sm font-semibold text-white">{m.org}</div>
              <div className="mt-2 text-sm text-grey-light">{m.metric}</div>
              <div className="mt-2 font-mono text-xs text-grey-mid">EIN {m.ein}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
