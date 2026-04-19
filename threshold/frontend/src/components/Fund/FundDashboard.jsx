import React, { useMemo, useState } from "react";
import useFundingRounds from "../../hooks/useFundingRounds";
import DonationModal from "./DonationModal";
import FundingRound from "./FundingRound";
import ImpactRegistry from "./ImpactRegistry";

function formatMoney(value) {
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`;
  }
  return `$${value}`;
}

export default function FundDashboard({
  rounds,
  impact,
  transactions,
  transparency,
}) {
  const state = useFundingRounds();
  const roundList = rounds ?? state.rounds;
  const impactList = impact ?? state.impact;
  const txList = transactions ?? state.transactions;
  const ledger = transparency ?? state.transparency;
  const [selectedRound, setSelectedRound] = useState(null);
  const activeRounds = useMemo(() => roundList.filter((round) => round.status === "Open" || round.status === "active"), [roundList]);

  return (
    <div className="space-y-6">
      <section className="rounded-[32px] border border-grey-dark/80 bg-[radial-gradient(circle_at_top_left,rgba(20,189,172,0.12),transparent_24%),linear-gradient(160deg,rgba(10,22,40,0.98),rgba(14,28,51,0.95))] p-7">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="text-xs uppercase tracking-[0.28em] text-grey-mid">THRESHOLD FUND</div>
            <h2 className="mt-3 text-4xl font-semibold text-white">Deploy capital before collapse costs compound</h2>
            <p className="mt-2 max-w-2xl text-sm text-grey-mid">
              This dashboard keeps the funding round list, partner verification, and on-chain transparency in one integration-friendly component.
            </p>
          </div>
          <div className="rounded-[24px] border border-white/10 bg-black/20 px-5 py-4 text-right">
            <div className="text-xs uppercase tracking-[0.2em] text-grey-mid">{state.source}</div>
            <div className="mt-1 font-mono text-4xl text-white">{formatMoney(ledger.total_volume_usd || 0)}</div>
          </div>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <div className="rounded-[24px] border border-grey-dark/70 bg-black/20 p-4">
            <div className="text-xs uppercase tracking-[0.2em] text-grey-mid">Active rounds</div>
            <div className="mt-2 font-mono text-3xl text-white">{activeRounds.length}</div>
          </div>
          <div className="rounded-[24px] border border-grey-dark/70 bg-black/20 p-4">
            <div className="text-xs uppercase tracking-[0.2em] text-grey-mid">Transactions</div>
            <div className="mt-2 font-mono text-3xl text-white">{ledger.total_transactions || txList.length}</div>
          </div>
          <div className="rounded-[24px] border border-grey-dark/70 bg-black/20 p-4">
            <div className="text-xs uppercase tracking-[0.2em] text-grey-mid">Contract</div>
            <div className="mt-2 text-sm text-white">{ledger.smart_contract_address}</div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
        {activeRounds.map((round) => (
          <FundingRound key={round.id} round={round} onContribute={setSelectedRound} />
        ))}
      </section>

      <ImpactRegistry impact={impactList} transactions={txList} />

      <DonationModal round={selectedRound} open={Boolean(selectedRound)} onClose={() => setSelectedRound(null)} />
    </div>
  );
}
