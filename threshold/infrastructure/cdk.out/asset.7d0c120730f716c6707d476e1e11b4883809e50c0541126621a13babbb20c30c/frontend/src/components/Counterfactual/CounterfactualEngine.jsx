import React, { useEffect, useMemo, useState } from "react";
import useCounterfactual from "../../hooks/useCounterfactual";
import TimelineScrubber from "./TimelineScrubber";

function DataSourceCell({ value }) {
  if (!value) return null;
  // Split on the first URL (http/https) found in the string
  const urlMatch = value.match(/(https?:\/\/\S+)/);
  if (!urlMatch) {
    return <div className="mt-2 text-sm text-white leading-snug">{value}</div>;
  }
  const url = urlMatch[1];
  const label = value.slice(0, value.indexOf(url)).replace(/:?\s*$/, "").trim();
  return (
    <div className="mt-2 space-y-1.5">
      {label && <div className="text-sm text-white leading-snug">{label}</div>}
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="block truncate font-mono text-[10px] text-teal-light hover:text-white transition-colors"
        title={url}
      >
        {url}
      </a>
    </div>
  );
}

function formatMoney(value) {
  if (value >= 1000000000) {
    return `$${(value / 1000000000).toFixed(1)}B`;
  }
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`;
  }
  return `$${value}`;
}

export default function CounterfactualEngine({
  caseId,
  regionId,
  cases,
  estimate,
  selectedCase,
}) {
  const [activeCaseId, setActiveCaseId] = useState(caseId ?? selectedCase?.case_id);
  const state = useCounterfactual({ caseId: activeCaseId, regionId });
  const availableCases = cases ?? state.cases;

  useEffect(() => {
    if (!activeCaseId && availableCases[0]?.case_id) {
      setActiveCaseId(availableCases[0].case_id);
    }
  }, [activeCaseId, availableCases]);

  const activeCase = useMemo(() => {
    if (selectedCase) {
      return selectedCase;
    }
    return state.selectedCase ?? availableCases.find((item) => item.case_id === activeCaseId) ?? availableCases[0];
  }, [activeCaseId, availableCases, selectedCase, state.selectedCase]);

  const liveEstimate = estimate ?? state.estimate;

  return (
    <div className="space-y-6">
      <section className="rounded-[32px] border border-grey-dark/80 bg-[radial-gradient(circle_at_top_left,rgba(192,57,43,0.15),transparent_24%),linear-gradient(160deg,rgba(10,22,40,0.98),rgba(14,28,51,0.95))] p-7">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="text-xs uppercase tracking-[0.28em] text-grey-mid">Past horizon engine</div>
            <h2 className="mt-3 text-4xl font-semibold text-white">Counterfactual timeline</h2>
            <p className="mt-2 max-w-2xl text-sm text-grey-mid">
              Scrub the last viable intervention window and compare modeled prevention against real recovery costs.
            </p>
          </div>
          <div className="rounded-[24px] border border-white/10 bg-black/20 px-5 py-4 text-right">
            <div className="text-xs uppercase tracking-[0.2em] text-grey-mid">{state.source}</div>
            <div className="mt-1 font-mono text-4xl text-white">{liveEstimate?.cost_multiplier ?? activeCase?.cost_multiplier}x</div>
          </div>
        </div>

        <div className="mt-6 flex flex-wrap gap-3">
          {availableCases.map((item) => (
            <button
              key={item.case_id}
              type="button"
              onClick={() => setActiveCaseId(item.case_id)}
              className={`rounded-full px-4 py-2 text-sm transition ${
                activeCase?.case_id === item.case_id ? "bg-white text-navy" : "border border-grey-dark text-grey-mid hover:text-white"
              }`}
            >
              {item.event ?? item.event_name ?? item.region}
            </button>
          ))}
        </div>
      </section>

      <TimelineScrubber caseStudy={activeCase} />

      <section className="grid gap-4 lg:grid-cols-4">
        <div className="rounded-[24px] border border-grey-dark/70 bg-white/[0.03] p-5">
          <div className="text-xs uppercase tracking-[0.2em] text-grey-mid">Prevention cost</div>
          <div className="mt-2 font-mono text-3xl text-white">{formatMoney(activeCase?.prevention_cost_usd ?? liveEstimate?.prevention_cost ?? 0)}</div>
        </div>
        <div className="rounded-[24px] border border-grey-dark/70 bg-white/[0.03] p-5">
          <div className="text-xs uppercase tracking-[0.2em] text-grey-mid">Recovery cost</div>
          <div className="mt-2 font-mono text-3xl text-white">{formatMoney(activeCase?.recovery_cost_usd ?? liveEstimate?.recovery_cost ?? 0)}</div>
        </div>
        <div className="rounded-[24px] border border-grey-dark/70 bg-white/[0.03] p-5">
          <div className="text-xs uppercase tracking-[0.2em] text-grey-mid">Crossed</div>
          <div className="mt-2 text-2xl text-white">{activeCase?.threshold_crossed_date}</div>
        </div>
        <div className="rounded-[24px] border border-grey-dark/70 bg-white/[0.03] p-5">
          <div className="text-xs uppercase tracking-[0.2em] text-grey-mid">Data source</div>
          <DataSourceCell value={activeCase?.data_source} />
        </div>
      </section>
    </div>
  );
}
