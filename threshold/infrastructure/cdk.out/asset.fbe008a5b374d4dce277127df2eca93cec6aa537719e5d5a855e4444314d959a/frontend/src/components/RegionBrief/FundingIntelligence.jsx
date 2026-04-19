import React, { useState } from "react";
import { Zap } from "lucide-react";
import DonateModal from "./DonateModal";

function formatMoney(value) {
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`;
  }
  if (value >= 1000) {
    return `$${(value / 1000).toFixed(0)}k`;
  }
  return `$${value}`;
}

export default function FundingIntelligence({
  region,
  estimate,
  charities = [],
  roundId,
}) {
  const [donateOpen, setDonateOpen] = useState(false);

  const prevention = estimate?.prevention_cost ?? region?.funding_gap ?? 0;
  const gap = region?.funding_gap ?? Math.max(prevention - (region?.committed_funding_usd || 0), 0);
  const committed = region?.committed_funding_usd ?? 0;
  const coverage = committed / Math.max(committed + gap, 1);

  return (
    <>
      <section className="rounded-[28px] border border-grey-dark/80 bg-white/[0.03] p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="text-xs uppercase tracking-[0.28em] text-grey-mid">Funding intelligence</div>
            <h3 className="mt-2 text-2xl font-semibold text-white">Commitments vs modeled intervention need</h3>
          </div>
          <div className="flex items-center gap-3">
            <div className="rounded-2xl border border-orange/30 bg-orange/10 px-4 py-3">
              <div className="text-xs uppercase tracking-[0.2em] text-orange-200">Coverage</div>
              <div className="mt-1 font-mono text-3xl text-white">{Math.round(coverage * 100)}%</div>
            </div>
            <button
              id="contribute-now-btn"
              onClick={() => setDonateOpen(true)}
              className="relative flex items-center gap-2 rounded-2xl border border-teal-light/40 bg-teal/10 px-5 py-3 text-sm font-semibold text-teal-light transition-all hover:bg-teal/20 hover:border-teal-light/70 hover:shadow-[0_0_20px_rgba(100,220,200,0.2)] active:scale-95"
            >
              {/* Pulse ring */}
              <span className="absolute -inset-px rounded-2xl animate-ping border border-teal-light/20 pointer-events-none" />
              <Zap size={15} className="shrink-0" />
              Contribute Now
            </button>
          </div>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <div className="rounded-[24px] border border-grey-dark/70 bg-black/20 p-4">
            <div className="text-xs uppercase tracking-[0.22em] text-grey-mid">Committed</div>
            <div className="mt-2 font-mono text-3xl text-white">{formatMoney(committed)}</div>
          </div>
          <div className="rounded-[24px] border border-grey-dark/70 bg-black/20 p-4">
            <div className="text-xs uppercase tracking-[0.22em] text-grey-mid">Funding gap</div>
            <div className="mt-2 font-mono text-3xl text-red-alert">{formatMoney(gap)}</div>
          </div>
          <div className="rounded-[24px] border border-grey-dark/70 bg-black/20 p-4">
            <div className="text-xs uppercase tracking-[0.22em] text-grey-mid">Modeled prevention</div>
            <div className="mt-2 font-mono text-3xl text-teal-light">{formatMoney(prevention)}</div>
          </div>
        </div>

        <div className="mt-6 h-3 overflow-hidden rounded-full bg-grey-dark/60">
          <div className="h-full rounded-full bg-gradient-to-r from-teal-light to-orange" style={{ width: `${Math.max(6, coverage * 100)}%` }} />
        </div>

        <div className="mt-6">
          <div className="mb-3 text-xs uppercase tracking-[0.22em] text-grey-mid">Eligible operators in-region</div>
          <div className="grid gap-3 lg:grid-cols-2">
            {charities.map((charity) => (
              <div key={charity.ein || charity.name} className="rounded-[20px] border border-grey-dark/70 bg-black/20 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-lg font-medium text-white">{charity.name}</div>
                    <div className="mt-1 text-xs uppercase tracking-[0.2em] text-grey-mid">{charity.ein || charity.source || "Verified operator"}</div>
                  </div>
                  <div className="rounded-full border border-teal-light/30 bg-teal/10 px-3 py-1 text-sm text-teal-light">
                    {charity.overall_score || charity.score}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <DonateModal
        isOpen={donateOpen}
        onClose={() => setDonateOpen(false)}
        region={region}
        roundId={roundId ?? region?.id ?? "demo-round"}
      />
    </>
  );
}

